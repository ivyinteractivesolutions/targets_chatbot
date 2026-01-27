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
    if not docs_dir.exists():
        print(f"ERROR: Documents directory {docs_dir} does not exist.")
        return all_docs
        
    files = [f for f in os.listdir(docs_dir) if f.endswith(".json")]
    print(f"DEBUG: Manually listing files: {files}")
    
    for filename in files:
        path = docs_dir / filename
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            tutorial_name = data.get("tutorial_name")
            language = data.get("language")
            sections = data.get("sections", [])

            for section in sections:
                section_title = section.get("section_title")
                section_description = section.get("description")
                section_steps = section.get("steps", [])

                text_for_embedding = (
                    f"Tutorial: {tutorial_name} | "
                    f"Language: {language} | "
                    f"Section: {section_title} | "
                    f"Task: {section_description} | "
                    f"Steps: {len(section_steps)} steps to complete this task"
                )
                
                meta = {
                    "content_type": "tutorial",
                    "tutorial_name": tutorial_name,
                    "language": language,
                    "section_title": section_title,
                    "source": path.name,
                    "steps_json": json.dumps(section_steps),
                    "section_description": section_description
                }

                all_docs.append({"text": text_for_embedding, "metadata": meta})
        except Exception as e:
            print(f"  ERROR: Failed to process {path.name}: {e}")
    
    return all_docs

def compute_hash(text: str, metadata: dict) -> str:
    """Generate a stable hash for checking changes."""
    content = f"{text}{json.dumps(metadata, sort_keys=True)}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def run_ingestion():
    """Main ingestion logic exposed as a function for app.py to call directly."""
    print("Loading JSON files from:", DOCS_DIR, flush=True)
    docs = load_json_docs(DOCS_DIR)

    if not docs:
        print("No docs found in documents folder.", flush=True)
        return "No documents found to ingest."

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
    output_messages = []

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
            msg = f"{action_label} Found changes in '{d['metadata']['tutorial_name']}' - Section: {d['metadata']['section_title']}"
            print(msg, flush=True)
            output_messages.append(msg)

    # 3. Handle deletions (items in DB but not in local files)
    ids_to_delete = existing_ids - set(current_ids)
    if ids_to_delete:
        print(f"COMMENCING DELETIONS: Found {len(ids_to_delete)} sections that are no longer present.", flush=True)
        for del_id in ids_to_delete:
            meta = existing_metadatas[del_id]
            msg = f"REMOVED: Old section '{meta.get('section_title')}' from '{meta.get('tutorial_name')}'"
            print(msg, flush=True)
            output_messages.append(msg)
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

    summary = f"FINAL SUMMARY: MIRA now knows a total of {len(current_ids)} tutorial steps across all files."
    print(f"\n{summary}\n", flush=True)
    output_messages.append(summary)
    
    return "\n".join(output_messages)

def cleanup_orphaned_images():
    """
    Scans all JSON files and deletes any images in static/images that are no longer referenced.
    """
    print("CLEANUP: Starting orphaned image cleanup...", flush=True)
    
    referenced_images = set()
    
    # 1. Collect all referenced images from JSON files
    if not DOCS_DIR.exists():
        return "Documents directory not found."
        
    for filename in os.listdir(DOCS_DIR):
        if filename.endswith(".json"):
            try:
                with open(DOCS_DIR / filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for section in data.get("sections", []):
                    for step in section.get("steps", []):
                        snapshot = step.get("snapshot")
                        if snapshot:
                            # Normalize path: remove leading slash for comparison
                            rel_path = snapshot.lstrip("/")
                            # We only care about images in our static/images folder
                            if rel_path.startswith("static/images/"):
                                referenced_images.add(rel_path.split("/")[-1])
            except Exception as e:
                print(f"  ERROR: Could not read {filename} during cleanup: {e}")

    # 2. Scan static/images folder
    image_dir = Path("static/images")
    if not image_dir.exists():
        return "Image directory not found."
        
    deleted_count = 0
    errors = 0
    
    for img_file in os.listdir(image_dir):
        # Avoid deleting .gitkeep or other system files if they exist
        if img_file.startswith("."):
            continue
            
        if img_file not in referenced_images:
            try:
                os.remove(image_dir / img_file)
                print(f"  REMOVED: Orphaned image '{img_file}'", flush=True)
                deleted_count += 1
            except Exception as e:
                print(f"  ERROR: Failed to delete '{img_file}': {e}")
                errors += 1
                
    result = f"CLEANUP COMPLETE: Deleted {deleted_count} orphaned images."
    if errors > 0:
        result += f" ({errors} errors occurred)"
    print(result, flush=True)
    return result

if __name__ == "__main__":
    run_ingestion()
    cleanup_orphaned_images()