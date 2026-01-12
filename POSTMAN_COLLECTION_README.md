# Postman Collection - Chatbot API

This Postman collection contains all the API endpoints for testing the Chatbot Assistant API.

## 📥 Importing the Collection

1. Open Postman
2. Click **Import** button (top left)
3. Select the file: `Chatbot_API.postman_collection.json`
4. The collection will appear in your Postman sidebar

## 🔧 Configuration

### Base URL
The collection uses a variable `base_url` which is set to:
```
https://primehouzz.com/assistant/chat
```

You can modify this in the collection variables:
1. Right-click on the collection → **Edit**
2. Go to the **Variables** tab
3. Update the `base_url` value if needed

### Session ID
The collection automatically saves the `session_id` when you create a new session. This allows you to use the same session across multiple requests.

## 📋 Collection Structure

### 1. Session Management
- **List All Sessions** - `GET /sessions`
- **Create New Session** - `POST /sessions` (auto-saves session_id)
- **Get Session Details** - `GET /sessions/:id`
- **Rename Session** - `PUT /sessions/:id`
- **Delete Session** - `DELETE /sessions/:id`

### 2. Chat Messages
- **Send Message - Tutorial Request** - Example: "How to add a new region?"
- **Send Message - Capabilities Request** - Example: "What can you help me with?"
- **Send Message - General Question** - Example: "Hello, how are you?"
- **Send Message - With Tutorial Context** - For clarifying specific steps
- **Send Message - Error Case** - Tests error handling (missing session_id)

### 3. Test Scenarios
Pre-configured workflows for common use cases:
- **Complete Chat Flow** - End-to-end workflow
- **Tutorial Flow with Clarification** - Request tutorial → Clarify step

## 🚀 Quick Start

### Basic Workflow

1. **Create a Session**
   - Run: `Session Management → Create New Session`
   - The `session_id` will be automatically saved

2. **Send a Message**
   - Run: `Chat Messages → Send Message - Tutorial Request`
   - The session_id variable will be automatically used

3. **View Session History**
   - Run: `Session Management → Get Session Details`
   - See the full conversation history

### Complete Test Flow

Use the **Test Scenarios → Complete Chat Flow** folder:
1. Run requests in order (1 → 2 → 3 → 4)
2. Each step builds on the previous one
3. Verify the session title is set after the first message

## 📝 Request Examples

### Create Session
```http
POST /sessions
```
No body required. Returns `{ "session_id": "..." }`

### Send Message
```http
POST /chat
Content-Type: application/json

{
    "message": "How to add a new region?",
    "session_id": "{{session_id}}",
    "last_tutorial": []
}
```

### Get Session
```http
GET /sessions/{{session_id}}
```

### Rename Session
```http
PUT /sessions/{{session_id}}
Content-Type: application/json

{
    "title": "My Updated Chat Title"
}
```

## 🔍 Response Types

The `/chat` endpoint returns different response types:

### Tutorial Response
```json
{
    "type": "tutorial",
    "content": "Here's a step-by-step guide...",
    "steps": [
        {
            "step_number": 1,
            "text": "Navigate to Settings...",
            "image": "/static/images/step1.png"
        }
    ],
    "suggested_actions": ["How to edit a region?"]
}
```

### Capabilities Response
```json
{
    "type": "capabilities",
    "title": "What I Can Help You With",
    "content": "I'm MIRA, your Management Portal assistant...",
    "features": [
        {
            "icon": "🏢",
            "title": "Region Management",
            "description": "Add, edit, and manage regions..."
        }
    ],
    "footer_cta": "Ask me anything about managing your portal!"
}
```

### General Response
```json
{
    "type": "general",
    "content": "Hello! How can I help you today?",
    "suggested_actions": ["How to add a new region?"]
}
```

### Error Response
```json
{
    "type": "error",
    "content": "Sorry, I'm experiencing technical difficulties...",
    "suggestions": ["How to add a new region?"]
}
```

## ⚠️ Error Cases

### 400 Bad Request
- Missing `session_id` in chat request
- Missing `title` in rename request

### 404 Not Found
- Session ID doesn't exist
- Invalid session ID format

### 500 Internal Server Error
- Server-side processing error
- May return error response in expected format

## 🧪 Testing Tips

1. **Use Variables**: The collection automatically manages `session_id` - you don't need to copy-paste it
2. **Test Scenarios**: Use the pre-configured test scenarios for common workflows
3. **Check Responses**: Verify response types match expected formats
4. **Error Testing**: Use the error case examples to test error handling
5. **Session Management**: Test creating, renaming, and deleting sessions

## 🔄 Auto-Saved Variables

The collection automatically saves:
- `session_id` - When you create a new session
- `last_tutorial_steps` - When you receive a tutorial response (in test scenarios)

## 📊 Response Validation

The collection includes basic tests:
- Response time < 5000ms
- Valid JSON response

You can add more specific tests in the **Tests** tab of each request.

## 🛠️ Customization

### Adding New Requests
1. Right-click on a folder → **Add Request**
2. Configure method, URL, headers, and body
3. Use `{{base_url}}` and `{{session_id}}` variables

### Modifying Base URL
1. Collection → **Edit** → **Variables**
2. Update `base_url` value
3. All requests will use the new URL

### Adding Tests
1. Select a request
2. Go to **Tests** tab
3. Write JavaScript test code
4. Use `pm.test()` and `pm.expect()` for assertions

## 📚 API Documentation

For detailed API documentation, see:
- `REACT_API_IMPLEMENTATION_PLAN.md` - Complete API reference
- `app.py` - Backend implementation

## 🐛 Troubleshooting

### Session ID Not Found
- Make sure you've created a session first
- Check that the `Create New Session` request ran successfully
- Verify the `session_id` variable is set in collection variables

### Connection Errors
- Verify the base URL is correct
- Check your internet connection
- Ensure the server is running and accessible

### Invalid Responses
- Check request body format (JSON)
- Verify required fields are present
- Review error response for details

## 📞 Support

For issues or questions:
1. Check the API documentation
2. Review request/response examples
3. Test with the provided scenarios

---

**Happy Testing! 🚀**

