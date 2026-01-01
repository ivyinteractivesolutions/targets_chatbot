import os
import json
import re
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain
from openai import OpenAI

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
    
    # Increased k to 3 to get more context and help disambiguation
    retriever = vectordb.as_retriever(search_kwargs={"k": 1})  
    
    llm = ChatOpenAI(model=MODEL_NAME, temperature=0.0)
    document_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, document_chain)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    return {
        "retriever": retriever, 
        "rag_chain": rag_chain, 
        "memory": memory,
        "llm": llm,
        "vectordb": vectordb
    }

components = build_components()

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

# Enhanced bot response with better error handling
def get_bot_response(user_query: str, conversation_history: list = None):
    """
    Return tutorial type responses.
    conversation_history is optional and will be saved to memory for richer context.
    """
    try:
        retriever = components["retriever"]
        
        # Retrieve multiple relevant sections
        docs = retriever.invoke(user_query)
        
        if not docs:
            return {
                "type": "error",
                "content": "Sorry, I couldn't find relevant steps for your query. Try asking about adding regions, areas, territories, distributors, sections, or sectors."
            }
        
        # Process all retrieved documents
        all_steps = []
        for doc in docs:
            steps_json = doc.metadata.get("steps_json")
            if steps_json:
                steps_data = json.loads(steps_json)
                for step_item in steps_data:
                    step_text = step_item.get("description")
                    image_path = step_item.get("snapshot")
                    
                    if image_path and not image_path.startswith("/"):
                        image_path = "/" + image_path.lstrip("/")
                        
                    # Apply dynamic formatting (only quotes now)
                    formatted_text = format_step_text(step_text)
                    
                    all_steps.append({
                        "text": formatted_text,
                        "image": image_path
                    })

        if not all_steps:
            return {
                "type": "error", 
                "content": "Found relevant sections but no specific steps available."
            }

        # Save question and short summary to memory; also save conversation_history if provided
        save_meta = {"answer": f"Provided tutorial with {len(all_steps)} steps"}
        if conversation_history:
            # store a short serialized history alongside
            try:
                save_meta["conversation_preview"] = json.dumps(conversation_history[-6:])
            except Exception:
                # If serialization fails, ignore
                pass

        components["memory"].save_context(
            {"question": user_query}, 
            save_meta
        )
        
        return {
            "type": "tutorial",
            "steps": all_steps,
            "source_count": len(docs),
            # include optional content text for UI consistent rendering
            "content": f"Sure! Here is the step by step answer to your query. (Found {len(all_steps)} steps.)"
        }

    except Exception as e:
        print(f"Error in get_bot_response: {e}")
        return {
            "type": "error",
            "content": f"Sorry, I encountered an error: {str(e)}"
        }
