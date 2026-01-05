import sqlite3
import uuid
import json
from datetime import datetime
from database import get_db_connection, init_db

class SessionManager:
    def __init__(self):
        # Ensure database is initialized
        init_db()

    def create_session(self, user_id):
        session_id = str(uuid.uuid4())
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Session (session_id, user_id, date, time, title) VALUES (?, ?, ?, ?, ?)",
            (session_id, user_id, date_str, time_str, "New Chat")
        )
        conn.commit()
        conn.close()
        return session_id

    def get_session(self, user_id, session_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get session info
        cursor.execute(
            "SELECT * FROM Session WHERE session_id = ? AND user_id = ?",
            (session_id, user_id)
        )
        session_row = cursor.fetchone()
        
        if not session_row:
            conn.close()
            return None
            
        # Get messages
        cursor.execute(
            "SELECT * FROM SessionInformation WHERE session_id = ? ORDER BY id ASC",
            (session_id,)
        )
        message_rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in message_rows:
            # Reconstruct history format: user question, then assistant response
            if row['question']:
                history.append({"role": "user", "content": row['question']})
            
            if row['response']:
                assistant_msg = {"role": "assistant", "content": row['response']}
                if row['response_metadata']:
                    try:
                        assistant_msg['data'] = json.loads(row['response_metadata'])
                    except:
                        pass
                history.append(assistant_msg)
                
        return {
            "session_id": session_row['session_id'],
            "user_id": session_row['user_id'],
            "title": session_row['title'],
            "created_at": f"{session_row['date']} T{session_row['time']}",
            "updated_at": session_row['updated_at'],
            "history": history
        }

    def save_session(self, user_id, session_id, history, title=None):
        # Note: 'history' in 'save_session' is the FULL history list.
        # However, for efficiency with SQLite, we might just want to append the LAST turn.
        # But to maintain compatibility with the current app.py, we'll check what's already there
        # and only insert the new parts.
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update title if provided
        if title:
            short_title = title[:50] + ("..." if len(title) > 50 else "")
            cursor.execute(
                "UPDATE Session SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                (short_title, session_id)
            )
        else:
            cursor.execute(
                "UPDATE Session SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                (session_id,)
            )

        # To keep it simple and robust while matching save_session(history) logic:
        # We find which turns are NOT in the database yet.
        # Actually, app.py calls save_session after appending user AND assistant message.
        # So the last two items in history are usually the new ones.
        
        cursor.execute("SELECT COUNT(*) FROM SessionInformation WHERE session_id = ?", (session_id,))
        count = cursor.fetchone()[0]
        
        # history items are {"role": "user", "content": "..."} or {"role": "assistant", "content": "...", "data": {...}}
        # We group them into pairs (question, response)
        
        turns = []
        for i in range(0, len(history), 2):
            q = history[i]['content'] if i < len(history) else None
            r_msg = history[i+1] if i+1 < len(history) else None
            r = r_msg['content'] if r_msg else None
            r_meta = json.dumps(r_msg.get('data')) if r_msg and r_msg.get('data') else None
            turns.append((q, r, r_meta))
            
        # If we have more turns than in DB, insert the new ones
        new_turns = turns[count:] # This assumes 1 pair = 1 row
        
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        
        for q, r, r_meta in new_turns:
            cursor.execute(
                "INSERT INTO SessionInformation (session_id, question, response, date, time, response_metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, q, r, date_str, time_str, r_meta)
            )
            
        conn.commit()
        conn.close()
        return self.get_session(user_id, session_id)

    def list_sessions(self, user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT session_id, title, updated_at FROM Session WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def delete_session(self, user_id, session_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        # Due to ON DELETE CASCADE, deleting from Session will delete from SessionInformation
        cursor.execute(
            "DELETE FROM Session WHERE session_id = ? AND user_id = ?",
            (session_id, user_id)
        )
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def rename_session(self, user_id, session_id, new_title):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Session SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ? AND user_id = ?",
            (new_title, session_id, user_id)
        )
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
