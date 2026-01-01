import os
import json
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

DOCS_DIR = Path("documents")
PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

def load_json_docs(docs_dir: Path):
    all_docs = []
    for path in docs_dir.glob("*.json"):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        tutorial_name = data.get("tutorial_name")
        language = data.get("language")

        for section in data.get("sections"):
            section_title = section.get("section_title")
            section_description = section.get("description")
            section_steps = section.get("steps", [])

            # Enhanced text for better retrieval - works with existing JSON
            text_for_embedding = (
                f"Tutorial: {tutorial_name} | "
                f"Language: {language} | "
                f"Section: {section_title} | "
                f"Task: {section_description} | "
                f"Steps: {len(section_steps)} steps to complete this task"
            )
            
            # Enhanced metadata - backward compatible
            meta = {
                "content_type": "tutorial",  # New field
                "tutorial_name": tutorial_name,
                "language": language,
                "section_title": section_title,
                "source": path.name,
                "steps_json": json.dumps(section_steps),
                "section_description": section_description  # New field for better context
            }

            all_docs.append({"text": text_for_embedding, "metadata": meta})
    
    return all_docs

def compute_hash(text: str, metadata: dict) -> str:
    """Generate a stable hash for checking changes."""
    content = f"{text}{json.dumps(metadata, sort_keys=True)}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def main():
    print("Loading JSON files from:", DOCS_DIR, flush=True)
    docs = load_json_docs(DOCS_DIR)

    if not docs:
        print("No docs found in documents folder.", flush=True)
        # Optional: clear DB if no docs exist? Probably better to keep it for safety.
        return

    print(f"Loaded {len(docs)} sections from files.\n", flush=True)

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, openai_api_key=OPENAI_API_KEY)
    
    # Connect to existing DB
    vectordb = Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings
    )

    # 1. Get existing content to compare
    print("Reading MIRA's current memory...", flush=True)
    existing_data = vectordb.get()
    existing_ids = set(existing_data['ids'])
    existing_metadatas = {id: meta for id, meta in zip(existing_data['ids'], existing_data['metadatas'])}
    
    # 2. Identify what needs to be updated or added
    to_add_texts = []
    to_add_metadatas = []
    to_add_ids = []
    
    current_ids = []
    
    add_count = 0
    update_count = 0

    for d in docs:
        # Generate stable ID
        id = f"{d['metadata']['source']}_{d['metadata']['section_title']}".replace(" ", "_")
        current_ids.append(id)
        
        # Calculate current hash
        current_hash = compute_hash(d['text'], d['metadata'])
        d['metadata']['content_hash'] = current_hash # Store hash in metadata
        
        # Check if we need to update
        needs_update = False
        action_label = ""
        if id not in existing_ids:
            needs_update = True
            action_label = "NEW:"
            add_count += 1
        else:
            prev_hash = existing_metadatas[id].get('content_hash')
            if prev_hash != current_hash:
                needs_update = True
                action_label = "UPDATED:"
                update_count += 1
        
        if needs_update:
            to_add_texts.append(d['text'])
            to_add_metadatas.append(d['metadata'])
            to_add_ids.append(id)
            print(f"{action_label} Found changes in '{d['metadata']['tutorial_name']}' - Section: {d['metadata']['section_title']}", flush=True)

    # 3. Handle deletions (items in DB but not in local files)
    ids_to_delete = existing_ids - set(current_ids)
    if ids_to_delete:
        print(f"COMMENCING DELETIONS: Found {len(ids_to_delete)} sections that are no longer present.", flush=True)
        for del_id in ids_to_delete:
            meta = existing_metadatas[del_id]
            print(f"REMOVED: Old section '{meta.get('section_title')}' from '{meta.get('tutorial_name')}'", flush=True)
        vectordb.delete(ids=list(ids_to_delete))

    # 4. Perform upsert (add/update)
    if to_add_ids:
        print(f"SYNCING: Now teaching MIRA {len(to_add_ids)} new or updated sections...", flush=True)
        vectordb.add_texts(
            texts=to_add_texts,
            metadatas=to_add_metadatas,
            ids=to_add_ids
        )
        print(f"SUCCESS: MIRA has successfully learned {add_count} new sections and updated {update_count} existing sections.", flush=True)
    else:
        if not ids_to_delete:
            print("STATUS: Everything is already up to date! MIRA didn't find any new changes.", flush=True)
        else:
            print("SUCCESS: MIRA's memory was cleaned up successfully.", flush=True)

    print(f"\nFINAL SUMMARY: MIRA now knows a total of {len(current_ids)} tutorial steps across all files.\n", flush=True)

if __name__ == "__main__":
    main()