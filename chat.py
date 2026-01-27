import os
import json
import re
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR")
MODEL_NAME = os.getenv("OPENAI_MODEL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in .env file")

# Enhanced prompt for better context handling
prompt = ChatPromptTemplate.from_template("""
You are **MIRA**, the in-system guide for the Management Portalof Targets System.

Objective:
Explain each step clearly like you're sitting next to the user, using a friendly and instructional tone.

Behavior:
- Start with the ice breaker like "Sure! Here is the step by step answer to your query."
- Use step-by-step formatting.
- Match user's input language (English, Urdu, or Roman Urdu).
- Do not invent extra fields or pages.
- If partial context found, say "Here's what I found so far."
- After each steps completed, ask nicely from the user that "Feel free to ask any more questions"

<context>
{context}
</context>

User's Question: {input}
""")

def build_components():
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, openai_api_key=OPENAI_API_KEY)
    vectordb = Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)
    
    # Increased k to 5 to capture competing matches (like Post vs Product)
    retriever = vectordb.as_retriever(search_kwargs={"k": 5})  
    
    llm = ChatOpenAI(model=MODEL_NAME, temperature=0.0)
    
    return {
        "retriever": retriever, 
        "llm": llm,
        "vectordb": vectordb
    }

# Initialize global components
_components = build_components()

def get_components():
    """Get the current global components."""
    return _components

def refresh_components():
    """Refresh the global components to pick up vector database changes."""
    global _components
    print("REFRESHING: Re-initializing retrieval components...", flush=True)
    _components = build_components()
    # Clear cache on refresh so we don't serve stale data
    _response_cache.clear() 
    print("SUCCESS: Retrieval components re-initialized.", flush=True)
    return _components

def format_step_text(text: str) -> str:
    """
    Bold terms within single quotes and remove the quotes.
    Preserves original casing.
    """
    if not isinstance(text, str):
        return text
    # Bold anything inside single quotes and remove the quotes
    # Preserves casing and avoids matching apostrophes in contractions (like you'll)
    return re.sub(r"(?<!\w)'([^']+)'(?!\w)", r"**\1**", text)

# Simple in-memory cache to reduce LLM calls
# Store: query -> response
_response_cache = {}

# Enhanced bot response with better selection logic
def get_bot_response(user_query: str, conversation_history: list = None):
    """
    Return tutorial type responses with LLM-based precise selection.
    Uses caching and smart filtering to reduce latency.
    """
    # 0. Check Cache
    if user_query in _response_cache:
        print(f"CACHE HIT: Returning cached response for '{user_query}'", flush=True)
        return _response_cache[user_query]

    try:
        components = get_components()
        retriever = components["retriever"]
        vectordb = components["vectordb"] # Use vector db directly for scoring
        llm = components["llm"]
        
        # 1. Retrieve top candidates with scores
        # We use similarity_search_with_score to get distance (lower is better)
        docs_with_scores = vectordb.similarity_search_with_score(user_query, k=5)
        
        if not docs_with_scores:
            return {
                "type": "error",
                "content": "Sorry, I couldn't find relevant steps for your query."
            }
        
        docs = [d[0] for d in docs_with_scores]
        top_score = docs_with_scores[0][1] # Distance
        
        # Smart Optimization: If top match is very close (distance < 0.3), skip expensive LLM selection
        # This reduces latency for obvious queries like "How to add region"
        selected_title = "NONE"
        matched_doc = None
        
        if top_score < 0.15:
            print(f"FAST MATCH: Top score {top_score:.4f} is good enough. Skipping LLM selection.", flush=True)
            matched_doc = docs[0]
            selected_title = matched_doc.metadata.get("section_title")
        else:
            # 2. Extract unique candidate titles for the LLM to choose from
            potential_sections = []
            seen_titles = set()
            for doc in docs:
                title = doc.metadata.get("section_title")
                if title and title not in seen_titles:
                    potential_sections.append(title)
                    seen_titles.add(title)
            
            # 3. Use LLM to select the single best title from the candidates
            selection_prompt = f"""User asked: "{user_query}"
            
Available tutorial sections:
{chr(10).join([f"- {s}" for s in potential_sections])}

Instructions:
Select the ONE section title that EXACTLY matches what the user is asking for.
CRITICAL RULES:
1. Do NOT assume relationships between distinct objects (e.g., "Shoes" are NOT "Products", "Employees" are NOT "Agents").
2. If the user's specific topic is NOT listed above, return "NONE".
3. Be strict. Better to return "NONE" than a wrong tutorial.

Return ONLY the title of the section or "NONE". No other text.
"""
            selection_response = llm.invoke(selection_prompt)
            selected_title = selection_response.content.strip().strip('"').strip("'")
            
            # Exact matching logic
            for doc in docs:
                if doc.metadata.get("section_title") == selected_title:
                    matched_doc = doc
                    break
        
        final_response = {}
        
        if not matched_doc or selected_title == "NONE":
            final_response = {
                "type": "no_relevant_content",
                "content": "I'm sorry, I couldn't find any information about that in the system."
            }
        else:
            selected_doc = matched_doc

            # 4. Process only the selected document (the single "chunk")
            all_steps = []
            steps_json = selected_doc.metadata.get("steps_json")
            if steps_json:
                steps_data = json.loads(steps_json)
                for step_item in steps_data:
                    step_text = step_item.get("description")
                    image_path = step_item.get("snapshot")
                    
                    if image_path and not image_path.startswith("/"):
                        image_path = "/" + image_path.lstrip("/")
                        
                    formatted_text = format_step_text(step_text)
                    all_steps.append({
                        "text": formatted_text,
                        "image": image_path
                    })

            section_title = selected_doc.metadata.get("section_title", "")
            
            final_response = {
                "type": "tutorial",
                "steps": all_steps,
                "section_title": section_title,
                "content": f"Sure! Here is the step by step answer to your query."
            }
        
        # Cache the successful response
        _response_cache[user_query] = final_response
        return final_response

    except Exception as e:
        print(f"Error in get_bot_response: {e}")
        return {
            "type": "error",
            "content": f"Sorry, I encountered an error: {str(e)}"
        }
