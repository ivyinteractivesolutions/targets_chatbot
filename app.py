

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import json
import sys
import subprocess
import traceback
from werkzeug.utils import secure_filename
from react_agent_system_langgraph import process_user_query, refresh_knowledge_base
from session_manager import SessionManager

app = Flask(__name__)

# Enable CORS for all routes and all origins
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuration for both functionalities
UPLOAD_FOLDER = "static/images"
JSON_OUTPUT_FOLDER = "documents"


app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Session Management
session_manager = SessionManager()

def get_current_user_id():
    """Placeholder for actual user authentication"""
    return "default_user"  # For now, everything is under 'default_user'

def validate_tutorial_data(data, check_original=False):
    """Shared validation logic for tutorial JSON data"""
    required_root = ["tutorial_name", "language", "json_filename", "sections"]
    if check_original:
        required_root.append("original_filename")
        
    for field in required_root:
        if not data.get(field):
            return f"{field} is required"

    for section in data.get("sections", []):
        if not section.get("section_title") or not section.get("description"):
            return "Section title and description are required"

        if not section.get("steps"):
            return "Each section must have at least one step"

        for step in section["steps"]:
            if not step.get("description"):
                return "Step description is required"
    return None


# ===== ROUTES FOR CHATBOT =====
@app.route("/chatbot")
def index():
    return render_template("index_chatbot.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    session_id = request.json.get("session_id")
    user_id = get_current_user_id()

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    try:
        # Get session data
        session_data = session_manager.get_session(user_id, session_id)
        if not session_data:
            return jsonify({"error": "Session not found"}), 404
            
        full_history = session_data.get("history", [])
        
        # Get last tutorial context from request
        last_tutorial = request.json.get("last_tutorial", [])
        
        # Convert objects to simple strings for the LangGraph agent
        # The agent expects a list of "User: ..." and "Assistant: ..." strings
        simple_history = []
        for msg in full_history:
            if isinstance(msg, dict):
                role = "User" if msg.get("role") == "user" else "Assistant"
                simple_history.append(f"{role}: {msg.get('content', '')}")
            else:
                simple_history.append(str(msg))

        # Process with React agent system
        response = process_user_query(user_message, simple_history, last_tutorial)
        
        # Update full history with objects
        full_history.append({"role": "user", "content": user_message})
        
        # Store the full response object for the assistant message
        assistant_msg = {
            "role": "assistant",
            "content": response.get("content", ""),
            "data": response # Store the whole thing for rich rendering
        }
        full_history.append(assistant_msg)
        
        # If this is the first message, update the title
        title = None
        if len(full_history) <= 2: 
            title = user_message
            
        session_manager.save_session(user_id, session_id, full_history, title=title)
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        traceback.print_exc()
        return jsonify({
            "type": "error",
            "content": "Sorry, I'm experiencing technical difficulties. Please try again.",
            "suggestions": [
                "How to add a new region?",
                "Steps to create a distributor",
                "What can you help me with?"
            ]
        })

# ===== SESSION ENDPOINTS =====
@app.route("/sessions", methods=["GET"])
def list_sessions():
    user_id = get_current_user_id()
    sessions = session_manager.list_sessions(user_id)
    return jsonify({"sessions": sessions})

@app.route("/sessions", methods=["POST"])
def create_session():
    user_id = get_current_user_id()
    session_id = session_manager.create_session(user_id)
    return jsonify({"session_id": session_id})

@app.route("/sessions/<session_id>", methods=["GET"])
def get_session(session_id):
    user_id = get_current_user_id()
    session_data = session_manager.get_session(user_id, session_id)
    if not session_data:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(session_data)

@app.route("/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    user_id = get_current_user_id()
    success = session_manager.delete_session(user_id, session_id)
    if success:
        return jsonify({"message": "Session deleted successfully"})
    return jsonify({"error": "Session not found"}), 404

@app.route("/sessions/<session_id>", methods=["PUT"])
def rename_session(session_id):
    user_id = get_current_user_id()
    new_title = request.json.get("title")
    if not new_title:
        return jsonify({"error": "Title is required"}), 400
        
    success = session_manager.rename_session(user_id, session_id, new_title)
    if success:
        return jsonify({"message": "Session renamed successfully"})
    return jsonify({"error": "Session not found"}), 404
# ===== ROUTES FOR JSON EDITOR =====
@app.route("/edit-json")
def edit_json():
    return render_template("index_edit_json.html")

@app.route("/upload-image", methods=["POST"])
def upload_image():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image = request.files["image"]
    
    # Get the old filename if provided (for renaming)
    old_filename = request.form.get("old_filename", "").strip()
    
    if old_filename and os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], old_filename)):
        # Use the old filename
        filename = secure_filename(old_filename)
    else:
        # Use the original filename
        filename = secure_filename(image.filename)
    
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    image.save(save_path)

    return jsonify({
        "path": f"static/images/{filename}",
        "renamed": bool(old_filename)
    })

@app.route("/save-json", methods=["POST"])
def save_json():
    data = request.json
    error = validate_tutorial_data(data)
    if error:
        return jsonify({"error": error}), 400

    json_filename = data["json_filename"].replace(".json", "")
    file_path = os.path.join(JSON_OUTPUT_FOLDER, f"{json_filename}.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump({
            "tutorial_name": data["tutorial_name"],
            "language": data["language"],
            "sections": data["sections"]
        }, f, indent=2)

    return jsonify({"message": "JSON saved successfully"})

@app.route("/load-json", methods=["GET"])
def load_json():
    filename = request.args.get("filename", "").strip()
    if not filename:
        return jsonify({"error": "Filename is required"}), 400

    # Ensure .json extension
    if not filename.endswith(".json"):
        filename += ".json"

    file_path = os.path.join(JSON_OUTPUT_FOLDER, filename)
    
    if not os.path.exists(file_path):
        return jsonify({"error": f"File '{filename}' not found"}), 404

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"Failed to load file: {str(e)}"}), 500

@app.route("/update-json", methods=["POST"])
def update_json():
    data = request.json
    error = validate_tutorial_data(data, check_original=True)
    if error:
        return jsonify({"error": error}), 400

    # Determine filenames
    original_filename = data["original_filename"]
    new_filename = data["json_filename"].replace(".json", "") + ".json"
    
    original_path = os.path.join(JSON_OUTPUT_FOLDER, original_filename)
    new_path = os.path.join(JSON_OUTPUT_FOLDER, new_filename)

    # Check if original file exists
    if not os.path.exists(original_path):
        return jsonify({"error": f"Original file '{original_filename}' not found"}), 404

    # If filename changed, delete old file
    if original_filename != new_filename and os.path.exists(original_path):
        os.remove(original_path)

    # Save updated data
    try:
        with open(new_path, "w", encoding="utf-8") as f:
            json.dump({
                "tutorial_name": data["tutorial_name"],
                "language": data["language"],
                "sections": data["sections"]
            }, f, indent=2, ensure_ascii=False)
        
        message = "JSON updated successfully"
        if original_filename != new_filename:
            message += f" (renamed to {new_filename})"
        
        return jsonify({"message": message, "new_filename": new_filename})
    except Exception as e:
        return jsonify({"error": f"Failed to update file: {str(e)}"}), 500

@app.route("/list-json-files", methods=["GET"])
def list_json_files():
    try:
        files = []
        for filename in os.listdir(JSON_OUTPUT_FOLDER):
            if filename.endswith(".json"):
                file_path = os.path.join(JSON_OUTPUT_FOLDER, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        files.append({
                            "filename": filename,
                            "tutorial_name": data.get("tutorial_name", ""),
                            "language": data.get("language", ""),
                            "sections_count": len(data.get("sections", []))
                        })
                    except:
                        files.append({
                            "filename": filename,
                            "tutorial_name": filename,
                            "language": "unknown",
                            "sections_count": 0
                        })
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/delete-json", methods=["POST"])
def delete_json():
    data = request.json
    filename = data.get("filename", "").strip()
    
    if not filename:
        return jsonify({"error": "Filename is required"}), 400
    
    # Ensure .json extension
    if not filename.endswith(".json"):
        filename += ".json"
    
    file_path = os.path.join(JSON_OUTPUT_FOLDER, filename)
    
    if not os.path.exists(file_path):
        return jsonify({"error": f"File '{filename}' not found"}), 404
    
    try:
        os.remove(file_path)
        return jsonify({"message": f"File '{filename}' deleted successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to delete file: {str(e)}"}), 500


@app.route("/update-vectordb", methods=["POST"])
def update_vectordb():
    """
    Endpoint to update the vector database by running ingest.py
    """
    try:
        # Robustly find the python executable
        python_exe = sys.executable
        venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "Scripts", "python.exe")
        if os.path.exists(venv_python):
            python_exe = venv_python
            
        # Run the ingest.py script
        result = subprocess.run(
            [python_exe, "ingest.py"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))  # Run from app directory
        )
        
        if result.returncode == 0:
            # Refresh knowledge base cache so it knows about new tutorials
            refresh_knowledge_base()
            
            return jsonify({
                "success": True,
                "message": "Vector database updated and AI knowledge refreshed successfully!",
                "output": result.stdout.strip()
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Failed to update vector database",
                "error": result.stderr.strip()
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error updating vector database: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500
if __name__ == "__main__":
    app.run(debug=True, port=5000)