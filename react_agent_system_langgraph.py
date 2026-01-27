# react_agent_system_langgraph.py
import os
import json
import re
from typing import TypedDict, Any, Dict, List, Annotated, Optional
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_classic.schema import HumanMessage, SystemMessage

from chat import get_bot_response, format_step_text

load_dotenv()
MODEL = os.getenv("OPENAI_MODEL")

# ==================== STATE DEFINITION ====================
class AgentState(TypedDict):
    """Enhanced state for LangGraph"""
    user_query: str
    llm_intent: str
    confidence: float
    detected_language: str
    is_confused: bool
    requires_clarification: bool
    step_to_clarify: Optional[int]
    response: Dict[str, Any]
    conversation_history: Annotated[List[str], "append"]
    last_tutorial: List[Dict[str, Any]]
    suggestions: List[str]
    next_node: str
    processing_path: List[str]
    validation_results: Dict[str, Any]

# ==================== LLM-BASED TOOLS ====================
class RequestAnalyzer:
    """Combined Intent and Language Analyzer to reduce latency"""
    
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.0, model=MODEL)
        
    def analyze(self, user_query: str, conversation_history: List[str]) -> Dict[str, Any]:
        """Analyze intent and language in a single pass"""
        
        history_context = ""
        if conversation_history:
            history_context = "\nRecent conversation:\n" + "\n".join(conversation_history[-3:])
        
        system_prompt = """You are the 'Request Analyzer' for MIRA, a Management Portal assistant.
Analyze the user query to determine the primary intent.

Available Intents:
- "tutorial": Use this for ANY request asking for steps, instructions, "how to", "Add...", "Create...", "View details...", or questions about specific system entities (Wallet, Bank, Region, Distributor, Area, etc.). 
- "capabilities": ONLY use this when the user asks about MIRA herself (e.g., "What can you do?", "Who are you?", "System features"). 
- "general": Greetings, chit-chat, or simple conversational emotional markers.
- "clarify": User explicitly asks for an explanation of a specific step or says "Help me with step X".
- "history_recall": User asks about previous questions or answers (e.g., "What was my last question?", "What did you say about Bank?").
- "summarization": User asks for a summary of the whole chat (e.g., "Summarize our chat," "What is the conversation that I did to you?").
- "fallback": Unclear or completely out-of-scope queries.

CRITICAL: If a query mentions a specific system action (Add, View, Create, Setup) or a system entity (Wallet, Bank, etc.), it MUST be "tutorial".

Return JSON format:
{
    "intent": "tutorial",
    "confidence": 0.9,
    "language": "English", 
    "is_confused": false,
    "step_number": null,
    "original_query": "user query here"
}

Language Detection Rules:
- If user uses Roman Urdu words (e.g., 'kaisay', 'kahan', 'madad'), classify as "Roman-Urdu".
- If user uses Urdu script, classify as "Urdu".
- If user uses any OTHER language (e.g., Spanish, French), classify as "English" (so we can politely refuse in English).
- Default to "English".
"""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"{history_context}\n\nUser Query: {user_query}")
            ]
            
            response = self.llm.invoke(messages)
            result = json.loads(response.content.strip())
            
            # Normalize Intent
            valid_intents = ["general", "tutorial", "capabilities", "clarify", "history_recall", "summarization", "fallback"]
            result["intent"] = result.get("intent", "fallback").lower()
            if result["intent"] not in valid_intents:
                result["intent"] = "fallback"
            
            # Normalize Confidence
            result["confidence"] = max(0.0, min(1.0, result.get("confidence", 0.5)))
            
            # Normalize Language
            raw_lang = result.get("language", "english").lower()
            if any(variant in raw_lang for variant in ["hindi", "urdu", "roman", "hinglish"]):
                result["language"] = "Roman-Urdu"
            else:
                result["language"] = "English"
                
            result["is_confused"] = bool(result.get("is_confused", False))
            result["step_number"] = result.get("step_number")
            
            return result
            
        except Exception as e:
            # Fallback safe response
            return {
                "intent": "fallback",
                "confidence": 0.3,
                "language": "English",
                "is_confused": False,
                "step_number": None
            }


class KnowledgeBase:
    """Loads and caches available tutorial topics from the documents directory"""
    
    def __init__(self, doc_dir: str = "documents"):
        self.doc_dir = doc_dir
        self.capabilities: Dict[str, List[str]] = {
            "english": [],
            "roman-urdu": []
        }
        self.refresh()

    def refresh(self):
        """Re-scan documents and refresh cached topics"""
        self.capabilities["english"] = []
        self.capabilities["roman-urdu"] = []
        self._load_knowledge()

    def _load_knowledge(self):
        """Extract unique section titles from ChromaDB metadata as the single source of truth"""
        try:
            # Connect to vector store to get current indexed topics
            embeddings = OpenAIEmbeddings(model=os.getenv("EMBEDDING_MODEL"))
            vectordb = Chroma(
                persist_directory=os.getenv("CHROMA_PERSIST_DIR"), 
                embedding_function=embeddings
            )
            
            # Fetch all metadata currently in MIRA's memory
            data = vectordb.get(include=['metadatas'])
            metadatas = data.get('metadatas', [])
            
            for meta in metadatas:
                title = meta.get("section_title")
                lang_code = meta.get("language", "").lower()
                
                # Normalize language key
                base_lang = "english"
                if "roman" in lang_code or "ur" in lang_code:
                    base_lang = "roman-urdu"
                    
                if title and title not in self.capabilities[base_lang]:
                    self.capabilities[base_lang].append(title)
                    
        except Exception as e:
            # Silently handle empty DB during first run
            pass

    def get_topics(self, language: str) -> List[str]:
        """Get topics for a language"""
        lang_key = "roman-urdu" if "roman" in language.lower() or "urdu" in language.lower() else "english"
        return self.capabilities.get(lang_key, [])


class DynamicSuggestionGenerator:
    """Dynamic suggestion generation"""
    
    def __init__(self, knowledge_base: KnowledgeBase = None):
        self.llm = ChatOpenAI(temperature=0.3, model=MODEL)
        self.kb = knowledge_base or KnowledgeBase()
    
    def generate(self, user_query: str, intent: str, conversation_history: List[str], language: str = "English") -> List[str]:
        """Generate context-aware suggestions"""
        
        history_context = "\n".join(conversation_history[-4:]) if conversation_history else "No recent history"
        
        # Determine strict language instruction
        lang_instruction = f"Strictly generate suggestions in {language}."
        input_lang = language.lower().replace(" ", "-")
        if input_lang in ["roman-urdu", "urdu"]:
            lang_instruction = "Strictly generate suggestions in Roman Urdu (Urdu written in English alphabets)."

        # Get grounded topics
        available_topics = self.kb.get_topics(language)
        topics_str = ", ".join(available_topics[:15]) # Limit to 15 topics for prompt brevity

        # Custom instruction for fallback
        if intent == "fallback":
            query_context = "Ignore the user query as it was out of scope. Suggest 4 diverse, valid actions based on the available topics."
        else:
            query_context = f"User Query: {user_query}"

        system_prompt = f"""Generate 4 relevant follow-up questions for MIRA, a Management Portal assistant.
{lang_instruction}

CRITICAL: Only suggest actions that MIRA can actually do. 
Available topics MIRA can help with: [{topics_str}]

Guidelines:
1. Every suggestion MUST directly relate to the available topics listed above.
2. If Intent is 'fallback', DO NOT hallucinate based on the user's invalid query. Suggest broad, valid system actions instead.
3. If the user query is about a specific valid topic (e.g., 'Region'), suggest sub-tasks like 'View details of Region'.
4. Do NOT hallucinate features MIRA doesn't have.

{query_context}
Intent: {intent}
Recent History: {history_context}

Return ONLY a JSON array of strings: ["Suggestion 1", "Suggestion 2", ...]"""
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content="Generate suggestions")
            ])
            
            content = response.content.strip()
            
            # Use regex to find the JSON array in case there's conversational filler
            match = re.search(r"(\[.*\])", content, re.DOTALL)
            if match:
                suggestions = json.loads(match.group(1))
            else:
                # Direct attempt if regex fails
                suggestions = json.loads(content)
                
            if isinstance(suggestions, list) and len(suggestions) > 0:
                return suggestions
            else:
                raise Exception("Empty suggestions list")
            
        except Exception:
            input_lang = language.lower().replace(" ", "-")
            if input_lang in ["roman-urdu", "urdu"]:
                return [
                    "Naya region kaisay add karain?",
                    "Distributor bananay ke steps kya hain?",
                    "Aap mairi kaisay madad kar saktay hain?"
                ]
            return [
                "How to add a new region?",
                "Steps to create a distributor",
                "What can you help me with?"
            ]


class GreetingGenerator:
    """Personalizes the introduction for tutorial steps"""
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.3, model=MODEL)

    def generate(self, user_query: str, section_title: str, language: str = "English") -> str:
        """Generate a personalized greeting"""
        system_prompt = f"""You are 'MIRA', the portal assistant. 
Create a ONE-LINE, natural greeting to introduce a list of tutorial steps.
The greeting should bridge the user's question and the topic, using the USER'S terminology where appropriate.

User's Question: {user_query}
Retrieved Topic: {section_title}
Language: {language}

CRITICAL:
- If Language is "English", the greeting MUST be in English.
- If Language is "Roman Urdu", the greeting MUST be in Roman Urdu.
- Do NOT output in Spanish, French, or any other language, even if the user input is in that language.

Examples:
Input: "where is the agents page?"
Topic: "Where is Agent page located"
Response: "Here are the steps to find the agents page:"

Input: "create new stuff"
Topic: "Add New Item"
Response: "Here are the steps to create new stuff:"

Input: "bank kahan hai?"
Topic: "Where is Bank page located"
Response: "Bank page kahan hai, iske baray mein steps yeh hain:"

Rules:
- Keep it to a single line.
- End with a colon (:).
- Be polite and direct.
- Mirror the user's keywords/terminology if safe to do so.
"""
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"User's Question: {user_query}")
            ])
            return response.content.strip()
        except Exception:
            # Fallback to generic if LLM fails
            if language.lower() in ["urdu", "roman-urdu"]:
                return "Yeh rahe steps:"
            return "Here are the steps:"


# ==================== LANGGRAPH NODES ====================
class AgentNodes:
    """Collection of LangGraph nodes"""
    
    def __init__(self):
        self.refresh()
    
    def refresh(self):
        """Re-initialize all internal components with fresh retrieval indices."""
        from chat import get_components
        self.knowledge_base = KnowledgeBase()
        self.request_analyzer = RequestAnalyzer()
        self.suggestion_generator = DynamicSuggestionGenerator(self.knowledge_base)
        self.greeting_generator = GreetingGenerator()
        self.general_llm = ChatOpenAI(temperature=0.9, model=MODEL)
        self.tutorial_llm = ChatOpenAI(temperature=0.0, model=MODEL)
        
        # Share the same vectordb and embeddings from chat.py to save resources
        components = get_components()
        self.vectordb = components.get("vectordb")
    
    def analyze_request(self, state: AgentState) -> AgentState:
        """Analyze intent and language in one step"""
        analysis_result = self.request_analyzer.analyze(
            state["user_query"], 
            state["conversation_history"]
        )
        
        state["llm_intent"] = analysis_result["intent"]
        state["confidence"] = analysis_result["confidence"]
        state["detected_language"] = analysis_result["language"]
        state["is_confused"] = analysis_result["is_confused"]
        state["step_to_clarify"] = analysis_result["step_number"]
        state["requires_clarification"] = analysis_result["intent"] == "clarify" and not analysis_result["step_number"]
        
        # Store validation results as well for backward compatibility
        state["validation_results"]["language_analysis"] = {
            "language": analysis_result["language"],
            "has_emotional_content": False
        }
        
        state["processing_path"].append("analyze_request")
        return state
    
    def route_decision(self, state: AgentState) -> AgentState:
        """Decide which agent to route to"""
        intent = state["llm_intent"]
        confidence = state.get("confidence", 0.5)
        
        # Determine next node
        if confidence < 0.4:
            state["next_node"] = "fallback_agent"
        else:
            route_map = {
                "general": "general_agent",
                "tutorial": "tutorial_agent",
                "capabilities": "capabilities_agent",
                "clarify": "clarification_agent",
                "history_recall": "history_summary_agent",
                "summarization": "history_summary_agent",
                "fallback": "fallback_agent"
            }
            state["next_node"] = route_map.get(intent, "fallback_agent")
        
        state["processing_path"].append("route_decision")
        return state
    
    def general_agent(self, state: AgentState) -> AgentState:
        """Handle general conversations"""
        lang_info = state["validation_results"].get("language_analysis", {})
        is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]
        
        if is_urdu:
            system_prompt = "You are MIRA, a Roman-Urdu Management Portal assistant. You must STRICTLY answer only in Roman Urdu. Do not use English script or any other language."
        else:
            system_prompt = "You are MIRA, a Management Portal assistant. You must STRICTLY answer only in English. If the user speaks a different language (e.g., Spanish, French, Arabic), politely reply in English stating that you only support English and Roman Urdu."
        
        # Parallelize General LLM response and Suggestion Generation
        with ThreadPoolExecutor() as executor:
            future_content = executor.submit(
                self._generate_general_response, 
                system_prompt, 
                state["conversation_history"], 
                state["user_query"],
                is_urdu
            )
            future_suggestions = executor.submit(
                self.suggestion_generator.generate,
                state["user_query"],
                "general",
                state["conversation_history"],
                "Roman Urdu" if is_urdu else "English"
            )
            
            content = future_content.result()
            suggestions = future_suggestions.result()
        
        state["response"] = {
            "type": "general",
            "content": content,
            "suggested_actions": suggestions,
            "is_urdu": is_urdu
        }
        
        state["suggestions"] = suggestions
        state["processing_path"].append("general_agent")
        return state

    def _generate_general_response(self, system_prompt, history, query, is_urdu):
        try:
            messages = [SystemMessage(content=system_prompt)]
            for msg in history[-4:]:
                messages.append(HumanMessage(content=msg))
            messages.append(HumanMessage(content=query))
            
            response = self.general_llm.invoke(messages)
            return response.content
        except Exception:
            return "Hello! How can I help you?" if not is_urdu else "Hi! Main aapki kaisay madad kar sakti hoon."
    
    def capabilities_agent(self, state: AgentState) -> AgentState:
        """Explain system capabilities in a layman-friendly, rich way"""
        lang_info = state["validation_results"].get("language_analysis", {})
        is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]
        
        if is_urdu:
            title = "Hi! Main hoon MIRA"
            subtitle = "Main aapki Management Portal ka har kaam asaan bananay mein madad kar sakti hoon."
            
            features = [
                {
                    "title": "Aam Sawalaat",
                    "description": "Greetings ho ya aam guftagu, main hamesha hazir hoon.",
                    "icon": "👋"
                },
                {
                    "title": "Step-by-Step Tutorials",
                    "description": "Add Region ho ya Distributor setup, har kaam ki tasweeri tutorial mujh se lain.",
                    "icon": "📸"
                },
                {
                    "title": "Easy Explaination",
                    "description": "Agar koi step mushkil lagay, bas mujh se poochain aur main usay asaan alfaz mein bataungi.",
                    "icon": "💡"
                },
                {
                    "title": "Portal Ki Maloomat",
                    "description": "Kaunsi cheez kahan hai? Main portal ke har kone se waqif hoon.",
                    "icon": "🗺️"
                },
                {
                    "title": "Urdu aur English",
                    "description": "Main aap se English aur Roman-Urdu dono mein baat kar sakti hoon.",
                    "icon": "🗣️"
                }
            ]
            cta = "Aap kya seekhna chahte hain?"
        else:
            title = "I'm MIRA, Your Portal Guide"
            subtitle = "I'm here to make managing your portal as simple as having a conversation."
            
            features = [
                {
                    "title": "General Assistance",
                    "description": "From a friendly greeting to general questions, I'm always ready to chat.",
                    "icon": "👋"
                },
                {
                    "title": "Visual Walkthroughs",
                    "description": "Need to add a Region or set up a Distributor? I'll show you exactly how with pictures.",
                    "icon": "📸"
                },
                {
                    "title": "Crystal Clear Clarity",
                    "description": "Confused about a step? Just ask! I'll break it down into even simpler English for you.",
                    "icon": "💡"
                },
                {
                    "title": "Portal Navigation",
                    "description": "I know where every page is located. Just ask me where to find something.",
                    "icon": "🗺️"
                },
                {
                    "title": "Bilingual Support",
                    "description": "Whether you prefer English or Roman-Urdu, I've got you covered.",
                    "icon": "🗣️"
                }
            ]
            cta = "What would you like to learn today?"
        
        suggestions = self.suggestion_generator.generate(
            state["user_query"],
            "capabilities",
            state["conversation_history"],
            language="Roman Urdu" if is_urdu else "English"
        )
        
        state["response"] = {
            "type": "capabilities",
            "title": title,
            "content": subtitle,
            "features": features,
            "footer_cta": cta,
            "suggested_actions": suggestions,
            "is_urdu": is_urdu
        }
        
        state["suggestions"] = suggestions
        state["processing_path"].append("capabilities_agent")
        return state
    
    def tutorial_agent(self, state: AgentState) -> AgentState:
        """Handle tutorial requests"""
        if state["step_to_clarify"]:
            return self._handle_step_clarification(state)
        
        try:
            bot_response = get_bot_response(state["user_query"])
            
            if bot_response.get("type") == "tutorial" and bot_response.get("steps"):
                steps = bot_response["steps"]
                formatted_steps = []
                
                for i, s in enumerate(steps, 1):
                    formatted_steps.append({
                        "step_number": i,
                        "text": s.get("text", s.get("description", "")),
                        "image": s.get("image") or s.get("snapshot")
                    })
                
                
                # Removed redundant LLM summary generation to improve latency
                # summary = self._generate_step_summary(...)
                # Instead, we use static introductions based on language
                
                lang_info = state["validation_results"].get("language_analysis", {})
                is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]
                
                # Dynamic Personalized Greeting and Suggestions in Parallel
                section_title = bot_response.get("section_title", "")
                
                with ThreadPoolExecutor() as executor:
                    future_intro = executor.submit(
                        self.greeting_generator.generate,
                        state["user_query"], 
                        section_title, 
                        "Roman Urdu" if is_urdu else "English"
                    )
                    future_suggestions = executor.submit(
                        self.suggestion_generator.generate,
                        state["user_query"],
                        "tutorial",
                        state["conversation_history"],
                        "Roman Urdu" if is_urdu else "English"
                    )
                    
                    intro = future_intro.result()
                    suggestions = future_suggestions.result()
                
                if is_urdu:
                    summary = f"Main pur-umeed hoon ke in {len(formatted_steps)} steps se aapki madad hui hogi."
                    pro_tip = "Steps ko carefully follow karain."
                    outro = "Shukriya!"
                else:
                    summary = f"I hope these {len(formatted_steps)} steps help you achieve your goal."
                    pro_tip = "Follow each step carefully."
                    outro = "Thank you!"
                
                state["response"] = {
                    "type": "tutorial",
                    "content": intro,
                    "steps": formatted_steps,
                    "summary": summary,
                    "pro_tip": pro_tip,
                    "completion_message": outro,
                    "is_urdu": is_urdu,
                    "suggested_actions": suggestions
                }
                state["response"] = {
                    "type": "tutorial",
                    "content": intro,
                    "steps": formatted_steps,
                    "summary": summary,
                    "pro_tip": pro_tip,
                    "completion_message": outro,
                    "is_urdu": is_urdu,
                    "suggested_actions": suggestions
                }
                
            elif bot_response.get("type") == "no_relevant_content":
                lang_info = state["validation_results"].get("language_analysis", {})
                is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]
                suggestions = self.suggestion_generator.generate(
                    state["user_query"],
                    "fallback", # Use fallback intent to trigger safer suggestions
                    state["conversation_history"],
                    language="Roman Urdu" if is_urdu else "English"
                )
                
                state["response"] = {
                    "type": "no_relevant_content", # Pass this type through to frontend
                    "content": f"It looks like the topic **'{state['user_query']}'** is not related to this system. If you have a general question, feel free to ask! However, I cannot provide a tutorial for this specific topic as it is not part of the system documentation.",
                    "suggested_actions": suggestions
                }

            else:
                lang_info = state["validation_results"].get("language_analysis", {})
                is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]
                suggestions = self.suggestion_generator.generate(
                    state["user_query"],
                    "tutorial",
                    state["conversation_history"],
                    language="Roman Urdu" if is_urdu else "English"
                )
                
                state["response"] = {
                    "type": "tutorial_fallback",
                    "content": f"No steps found for '{state['user_query']}'.",
                    "suggestions": suggestions
                }
                
        except Exception:
            lang_info = state["validation_results"].get("language_analysis", {})
            is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]
            suggestions = self.suggestion_generator.generate(
                state["user_query"],
                "tutorial",
                state["conversation_history"],
                language="Roman Urdu" if is_urdu else "English"
            )
            
            state["response"] = {
                "type": "error",
                "content": "Error retrieving tutorial.",
                "suggestions": suggestions
            }
        
        state["suggestions"] = suggestions
        state["processing_path"].append("tutorial_agent")
        return state
    
    def _handle_step_clarification(self, state: AgentState) -> AgentState:
        """Handle step clarification"""
        step_idx = state["step_to_clarify"]
        last_tutorial = state.get("last_tutorial", [])
        
        if last_tutorial and 1 <= step_idx <= len(last_tutorial):
            step = last_tutorial[step_idx - 1]
            original_text = step.get("text") or step.get("description", "")
            
            clarified_text = self._clarify_single_step(
                original_text, 
                step_idx,
                state["detected_language"]
            )
            
            lang_info = state["validation_results"].get("language_analysis", {})
            is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]
            suggestions = self.suggestion_generator.generate(
                state["user_query"],
                "clarify",
                state["conversation_history"],
                language="Roman Urdu" if is_urdu else "English"
            )
            
            state["response"] = {
                "type": "tutorial_clarify",
                "content": f"Step {step_idx} clarification:",
                "clarified_step": {
                    "step_number": step_idx,
                    "original": original_text,
                    "clarified": clarified_text,
                    "image": step.get("image") or step.get("snapshot")
                },
                "suggested_actions": suggestions,
                "is_urdu": state["detected_language"] in ["urdu", "roman-urdu"]
            }
            
        else:
            lang_info = state["validation_results"].get("language_analysis", {})
            is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]
            suggestions = self.suggestion_generator.generate(
                state["user_query"],
                "clarify",
                state["conversation_history"],
                language="Roman Urdu" if is_urdu else "English"
            )
            
            state["response"] = {
                "type": "tutorial_clarify_error",
                "content": "Please ask for a tutorial first.",
                "suggested_actions": suggestions
            }
        
        state["suggestions"] = suggestions
        return state
    
    def _clarify_single_step(self, step_text: str, step_number: int, language: str) -> str:
        """Clarify a single step"""
        is_urdu = language in ["urdu", "roman-urdu"]
        
        if is_urdu:
            system_prompt = "Explain this step in clearer Roman-Urdu."
        else:
            system_prompt = "Explain this step more clearly."
        
        try:
            response = self.tutorial_llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Step {step_number}: {step_text}")
            ])
            return response.content.strip()
        except Exception:
            return step_text
    

    
    def clarification_agent(self, state: AgentState) -> AgentState:
        """Handle clarification requests"""
        if state["requires_clarification"]:
            lang_info = state["validation_results"].get("language_analysis", {})
            is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]
            
            suggestions = self.suggestion_generator.generate(
                state["user_query"],
                "clarify",
                state["conversation_history"],
                language="Roman Urdu" if is_urdu else "English"
            )
            
            state["response"] = {
                "type": "clarify_question",
                "content": "Which step would you like me to explain?",
                "suggested_actions": suggestions
            }
        else:
            return self.tutorial_agent(state)
        
        state["suggestions"] = suggestions
        state["processing_path"].append("clarification_agent")
        return state
    
    def history_summary_agent(self, state: AgentState) -> AgentState:
        """Handle conversation history recall and summarization"""
        intent = state["llm_intent"]
        history = state.get("conversation_history", [])
        is_urdu = state["detected_language"] in ["urdu", "roman-urdu"]
        
        if not history:
            state["response"] = {
                "type": "general",
                "content": "Hamari abhi koi guftagu nahi hui." if is_urdu else "We haven't had much of a conversation yet!"
            }
            return state

        if intent == "summarization":
            # Summarize the conversation
            system_prompt = f"""Summarize the following chat conversation between a user and MIRA (Management Portal Assistant).
Provide a high-level summary of what was discussed, the topics covered, and any pending questions.
Language: {'Roman-Urdu' if is_urdu else 'English'}
Format: Bullet points.
"""
            history_text = "\n".join(history)
            try:
                response = self.general_llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=f"Conversation History:\n{history_text}")
                ])
                summary_content = response.content
            except Exception:
                summary_content = "Summary generation failed."
            
            state["response"] = {
                "type": "general",
                "content": summary_content,
                "is_urdu": is_urdu
            }
        
        elif intent == "history_recall":
            # Recall specific parts of the history
            history_text = "\n".join(history[-10:])
            system_prompt = f"""The user is asking a question about the previous conversation.
Based on the provided history, answer the user's question accurately.
If they ask for their 'last question', identify it from the history.
If they ask 'what did you say about X', find the relevant assistant response.
Language: {'Roman-Urdu' if is_urdu else 'English'}
History:
{history_text}
"""
            try:
                response = self.general_llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=f"User's Recall Question: {state['user_query']}")
                ])
                recall_content = response.content
            except Exception:
                recall_content = "I'm sorry, I couldn't recall that correctly."
            
            state["response"] = {
                "type": "general",
                "content": recall_content,
                "is_urdu": is_urdu
            }

        state["processing_path"].append("history_summary_agent")
        return state

    def validate_response(self, state: AgentState) -> AgentState:
        """Validate response"""
        if "response" not in state or not state["response"]:
            state["validation_results"]["response_valid"] = False
            return state
        
        response = state["response"]
        is_valid = True
        
        if "type" not in response:
            is_valid = False
        
        if "content" not in response or not response["content"]:
            is_valid = False
        
        state["validation_results"]["response_valid"] = is_valid
        state["processing_path"].append("validate_response")
        return state
    
    def fallback_agent(self, state: AgentState) -> AgentState:
        """Handle fallback cases"""
        lang_info = state["validation_results"].get("language_analysis", {})
        is_urdu = lang_info.get("language", "").lower() in ["urdu", "roman-urdu"]

        suggestions = self.suggestion_generator.generate(
            state["user_query"],
            "fallback",
            state["conversation_history"],
            language="Roman Urdu" if is_urdu else "English"
        )
        
        state["response"] = {
            "type": "fallback",
            "content": "How can I help you today?",
            "suggested_actions": suggestions
        }
        
        state["suggestions"] = suggestions
        state["processing_path"].append("fallback_agent")
        return state


# ==================== LANGGRAPH SETUP ====================
def create_agent_graph(checkpointer=None):
    """Create LangGraph with an optional checkpointer"""
    nodes = AgentNodes()
    workflow = StateGraph(AgentState)
    
    # ... (rest of node setup remains the same)
    # Add nodes
    workflow.add_node("analyze_request", nodes.analyze_request)
    workflow.add_node("route_decision", nodes.route_decision)
    workflow.add_node("general_agent", nodes.general_agent)
    workflow.add_node("capabilities_agent", nodes.capabilities_agent)
    workflow.add_node("tutorial_agent", nodes.tutorial_agent)
    workflow.add_node("clarification_agent", nodes.clarification_agent)
    workflow.add_node("history_summary_agent", nodes.history_summary_agent)
    workflow.add_node("validate_response", nodes.validate_response)
    workflow.add_node("fallback_agent", nodes.fallback_agent)
    
    # Set entry point
    workflow.set_entry_point("analyze_request")
    
    # Add edges
    workflow.add_edge("analyze_request", "route_decision")
    
    # Conditional routing
    def route_from_decision(state: AgentState) -> str:
        return state.get("next_node", "fallback_agent")
    
    workflow.add_conditional_edges(
        "route_decision",
        route_from_decision,
        {
            "general_agent": "general_agent",
            "capabilities_agent": "capabilities_agent",
            "tutorial_agent": "tutorial_agent",
            "clarification_agent": "clarification_agent",
            "history_summary_agent": "history_summary_agent",
            "fallback_agent": "fallback_agent"
        }
    )
    
    # Add validation
    workflow.add_edge("general_agent", "validate_response")
    workflow.add_edge("capabilities_agent", "validate_response")
    workflow.add_edge("tutorial_agent", "validate_response")
    workflow.add_edge("clarification_agent", "validate_response")
    workflow.add_edge("history_summary_agent", "validate_response")
    workflow.add_edge("fallback_agent", "validate_response")
    
    workflow.add_edge("validate_response", END)
    
    # Compile graph with provided or new checkpointer
    if checkpointer is None:
        checkpointer = MemorySaver()
        
    graph = workflow.compile(checkpointer=checkpointer)
    return graph, nodes

def refresh_knowledge_base():
    """Refresh the entire knowledge base and agent system state"""
    try:
        from chat import refresh_components
        print("AGENT SYSTEM: Starting knowledge refresh...", flush=True)
        
        # 1. Refresh retrieval components in chat.py
        refresh_components()
        
        # 2. Re-create graph and nodes but reuse the EXISTING checkpointer
        # This is the KEY to preserving memory
        existing_checkpointer = langgraph_system.checkpointer
        new_graph, new_nodes = create_agent_graph(checkpointer=existing_checkpointer)
        
        # 3. Update the global system instances
        langgraph_system.graph = new_graph
        
        print("AGENT SYSTEM: Knowledge refresh complete.", flush=True)
        return True
    except Exception as e:
        print(f"Error refreshing knowledge base: {e}")
        import traceback
        traceback.print_exc()
        return False

def format_response_recursive(data: Any) -> Any:
    """Recursively apply bold formatting to all strings in a data structure."""
    if isinstance(data, str):
        return format_step_text(data)
    elif isinstance(data, list):
        return [format_response_recursive(item) for item in data]
    elif isinstance(data, dict):
        return {k: format_response_recursive(v) for k, v in data.items()}
    return data

# ==================== MAIN INTERFACE ====================
class LangGraphAgentSystem:
    """Main interface"""
    
    def __init__(self):
        self.checkpointer = MemorySaver()
        self.graph, _ = create_agent_graph(checkpointer=self.checkpointer)
        self.config = {"configurable": {"thread_id": "default_thread"}}
    
    def process_user_query(self, user_query: str, conversation_history: List[str] = None, 
                          last_tutorial: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process user query"""
        if conversation_history is None:
            conversation_history = []
        if last_tutorial is None:
            last_tutorial = []
        
        initial_state: AgentState = {
            "user_query": user_query,
            "llm_intent": "",
            "confidence": 0.0,
            "detected_language": "english",
            "is_confused": False,
            "requires_clarification": False,
            "step_to_clarify": None,
            "response": {},
            "conversation_history": conversation_history,
            "last_tutorial": last_tutorial,
            "suggestions": [],
            "next_node": "",
            "processing_path": [],
            "validation_results": {}
        }
        
        try:
            final_state = self.graph.invoke(initial_state, self.config)
            
            response = final_state["response"]
            assistant_text = response.get("content", "")
            
            conversation_history.append(f"User: {user_query}")
            conversation_history.append(f"Assistant: {assistant_text}")
            
            output = {
                **response,
                "conversation_history": conversation_history,
                "detected_intent": final_state["llm_intent"]
            }
            
            # Post-process the output to bold terms in single quotes
            output = format_response_recursive(output)
            
            return output
            
        except Exception as e:
            return {
                "type": "error",
                "content": f"I encountered an error: {str(e)}",
                "conversation_history": conversation_history,
                "suggested_actions": ["How to add a new region?", "What can you help me with?"]
            }


# ==================== INITIALIZE SYSTEM ====================
langgraph_system = LangGraphAgentSystem()

def refresh_knowledge_base_deprecated():
    """Refresh the knowledge base cache"""
    try:
        langgraph_system.graph = create_agent_graph()
    except Exception as e:
        print(f"Error refreshing knowledge base: {e}")

def process_user_query(user_query: str, conversation_history: List[str] = None, 
                      last_tutorial: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Main entrypoint"""
    return langgraph_system.process_user_query(user_query, conversation_history, last_tutorial)