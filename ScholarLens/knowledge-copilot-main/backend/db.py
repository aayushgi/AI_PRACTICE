import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("CHAT_DB_NAME", "chatdb"),
        user=os.getenv("CHAT_DB_USER", "postgres"),
        password=os.getenv("CHAT_DB_PASSWORD"),
        host=os.getenv("CHAT_DB_HOST", "localhost"),
        port=int(os.getenv("CHAT_DB_PORT", 5432))
    )

def save_message(user_id, role, content, chat_id="default"):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO chat_messages (user_id, chat_id, role, content)
                VALUES (%s, %s, %s, %s)
            """, (user_id, chat_id, role, content))
        conn.commit()
    except Exception as e:
        print(f"Error saving message: {e}")
    finally:
        if conn:
            conn.close()

def get_last_messages(user_id, chat_id='default', limit=20):
    conn = None
    rows = []
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT role, content 
                FROM chat_messages 
                WHERE user_id = %s
                AND chat_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (user_id, chat_id, limit))
            rows = cursor.fetchall()
    except Exception as e:
        print(f"Error fetching messages: {e}")
    finally:
        if conn:
            conn.close()
    
    # Returning list of chat from old to new 
    return [{"role": role, "content": content} for role, content in reversed(rows)]

def get_messages_paginated(user_id, chat_id='default', cursor_id=None, limit=20):
    conn = None
    rows = []
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:  # Fixed: cursor()
            if cursor_id:
                cursor.execute("""
                    SELECT id, role, content 
                    FROM chat_messages
                    WHERE user_id = %s
                    AND chat_id = %s
                    AND id < %s
                    ORDER BY id DESC
                    LIMIT %s
                """, (user_id, chat_id, cursor_id, limit))
            else:
                cursor.execute("""
                    SELECT id, role, content 
                    FROM chat_messages
                    WHERE user_id = %s
                    AND chat_id = %s
                    ORDER BY id DESC
                    LIMIT %s
                """, (user_id, chat_id, limit))
            
            rows = cursor.fetchall()
    except Exception as e:
        print(f"Error fetching messages: {e}")
    finally:
        if conn:
            conn.close()
    
    # Return messages (old to new) with id for pagination
    return [{"id": id, "role": role, "content": content} for id, role, content in reversed(rows)]

def set_chat_session_title(user_id, new_title, chat_id="default"):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE chat_sessions 
                SET title = %s
                WHERE user_id = %s
                AND chat_id = %s
            """,(new_title, user_id, chat_id))
        conn.commit()
    except Exception as e:
        print(f"Error updating chat session title: {e}")
    finally:
        if conn:
            conn.close()

# For new chats
def add_chat_session(user_id, chat_id="default", title="New Chat"):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO chat_sessions
                (user_id, chat_id, title)
                VALUES(%s, %s, %s)
            """, (user_id, chat_id, title))
        conn.commit()
    except Exception as e:
        print(f"Error adding chat session: {e}")
    finally:
        if conn:
            conn.close()

def get_chat_sessions(user_id):
    conn=None
    rows=[]
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT chat_id, title
                FROM chat_sessions
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user_id,))
            rows=cursor.fetchall()
    except Exception as e:
        print(f"Error fetching chat sessions: {e}")
    finally:
        if conn:
            conn.close()
    
    return [{"chat_id": chat_id, "title": title} for chat_id, title in rows]

def delete_chat_session(user_id, chat_id="default"):
    conn=None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM chat_sessions
                WHERE user_id = %s
                AND chat_id = %s
            """, (user_id, chat_id))
            cursor.execute("""
                DELETE FROM chat_messages
                WHERE user_id = %s
                AND chat_id = %s
            """, (user_id, chat_id))
        conn.commit()
    except Exception as e:
        print(f"Error deleting chat session: {e}")
    finally:
        if conn:
            conn.close()