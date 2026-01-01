

from flask import Flask, render_template, request, jsonify
import os
import json
import sys
import subprocess
import traceback
from werkzeug.utils import secure_filename
from react_agent_system_langgraph import process_user_query

app = Flask(__name__)

# Configuration for both functionalities
UPLOAD_FOLDER = "static/images"
JSON_OUTPUT_FOLDER = "documents"


app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Store conversation history in memory (for chatbot)
conversation_histories = {}

def get_conversation_history(session_id):
    """Get or create conversation history for a session"""
    if session_id not in conversation_histories:
        conversation_histories[session_id] = []
    return conversation_histories[session_id]


# ===== NAVIGATION ROUTES =====
@app.route("/")
def navigation():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Navigation</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .nav-container {
                background: white;
                border-radius: 16px;
                padding: 40px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                text-align: center;
            }
            h1 {
                color: #2c3e50;
                margin-bottom: 30px;
            }
            .nav-buttons {
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            .nav-btn {
                padding: 16px 32px;
                border: none;
                border-radius: 8px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                text-decoration: none;
                color: white;
            }
            .nav-btn-chat {
                background: linear-gradient(135deg, #198754, #198754);
            }
            .nav-btn-edit {
                background: linear-gradient(135deg, #3498db, #2980b9);
            }
            .nav-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            }
            .icon {
                font-size: 1.2rem;
            }
        </style>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    </head>
    <body>
        <div class="nav-container">
            <h1>Choose Application</h1>
            <div class="nav-buttons">
                <a href="/chatbot" class="nav-btn nav-btn-chat">
                    <i class="fas fa-robot icon"></i>
                    Chatbot Assistant
                </a>
                <a href="/edit-json" class="nav-btn nav-btn-edit">
                    <i class="fas fa-edit icon"></i>
                    JSON Editor
                </a>
            </div>
        </div>
    </body>
    </html>
    '''
# ===== ROUTES FOR CHATBOT =====
@app.route("/chatbot")
def index():
    return render_template("index_chatbot.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json["message"]
    # Use a simple session ID (in production, use actual session management)
    session_id = request.remote_addr  # Simple session identifier

    try:
        # Get conversation history for this session
        conversation_history = get_conversation_history(session_id)
        
        # Process with React agent system
        response = process_user_query(user_message, conversation_history)
        
        # Update conversation history in the system
        conversation_histories[session_id] = conversation_history
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({
            "type": "error",
            "content": "Sorry, I'm experiencing technical difficulties. Please try again.",
            "suggestions": [
                "How to add a new region?",
                "Steps to create a distributor",
                "What can you help me with?"
            ]
        })
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

    required_root = ["tutorial_name", "language", "json_filename", "sections"]
    for field in required_root:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    for section in data["sections"]:
        if not section.get("section_title") or not section.get("description"):
            return jsonify({"error": "Section title and description are required"}), 400

        if not section.get("steps"):
            return jsonify({"error": "Each section must have at least one step"}), 400

        for step in section["steps"]:
            if not step.get("description"):
                return jsonify({"error": "Step description is required"}), 400
            # Snapshot is now optional, so no validation for it

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

    # Check required fields
    required_root = ["tutorial_name", "language", "json_filename", "sections", "original_filename"]
    for field in required_root:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    # Validate sections and steps
    for section in data["sections"]:
        if not section.get("section_title") or not section.get("description"):
            return jsonify({"error": "Section title and description are required"}), 400

        if not section.get("steps"):
            return jsonify({"error": "Each section must have at least one step"}), 400

        for step in section["steps"]:
            if not step.get("description"):
                return jsonify({"error": "Step description is required"}), 400
            # Snapshot is now optional, so no validation for it

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
            return jsonify({
                "success": True,
                "message": "Vector database updated successfully!",
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