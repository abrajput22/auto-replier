import requests
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os
from db_connection import save_conversation, get_conversation_history, save_failed_reply

load_dotenv()

# Environment variables
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CONTEXT_WINDOW_SIZE = int(os.getenv("CONTEXT_WINDOW_SIZE", "5"))

# Track processed messages
processed_messages = set()

def generate_dm_reply(message_text, sender_id):
    """Generate AI reply to DM with conversation context"""
    llm = ChatOpenAI(
        model="gemini-2.0-flash",
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    
    # Get conversation history
    history = get_conversation_history(sender_id, CONTEXT_WINDOW_SIZE)
    
    # Build context from history
    context = ""
    if history:
        context = "\nPrevious conversation:\n"
        for conv in history:
            context += f"User: {conv['user_message']}\nBot: {conv['bot_reply']}\n"
    
    prompt = f"""Generate a friendly, helpful DM reply to: "{message_text}"{context}
    
    Requirements:
    - Keep it under 100 characters
    - Be professional and helpful
    - Use conversation context if available
    - Sound natural and conversational
    
    Generate helpful reply:"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()

def get_sender_name(sender_id):
    """Get sender name from Instagram API"""
    try:
        url = f"https://graph.facebook.com/v21.0/{sender_id}"
        params = {
            "fields": "name,username",
            "access_token": PAGE_ACCESS_TOKEN
        }
        response = requests.get(url, params=params)
        data = response.json()
        return data.get("name", data.get("username", f"User_{sender_id[-4:]}"))
    except:
        return f"User_{sender_id[-4:]}"

def send_dm_reply(recipient_id, reply_text):
    """Send DM reply using Facebook Messenger API"""
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": reply_text}
    }
    
    print(f"Sending message to: {recipient_id}")
    print(f"Message: {reply_text}")
    
    response = requests.post(url, json=payload)
    result = response.json()
    print(f"Response: {result}")
    return result

async def process_message(messaging):
    """Process incoming message"""
    try:
        if "message" not in messaging:
            print("No message key found")
            return
        
        message = messaging["message"]
        sender_id = messaging["sender"]["id"]
        message_id = message.get("mid", "")
        
        # Get sender name for better logging
        sender_name = get_sender_name(sender_id)
        
        print(f"\n=== NEW MESSAGE ===")
        print(f"From: {sender_name} ({sender_id})")
        print(f"Message ID: {message_id}")
        
        # Skip if already processed
        if message_id in processed_messages:
            print(f"Already processed message {message_id}")
            return
            
        # Skip our own messages
        if sender_id == IG_USER_ID:
            print("Skipping our own message")
            return
            
        processed_messages.add(message_id)
        
        message_text = message.get("text", "")
        if not message_text:
            print("No text in message")
            return
        
        print(f"Message: '{message_text}'")
        
        # Generate and send reply with context
        reply = generate_dm_reply(message_text, sender_id)
        print(f"Bot Reply: '{reply}'")
        
        result = send_dm_reply(sender_id, reply)
        
        if "message_id" in result or "id" in result:
            print(f"SUCCESS: Reply sent to {sender_name}")
            # Save conversation to database
            save_conversation(sender_id, message_text, reply, message_id)
            print(f"Conversation saved to database")
            print(f"{'='*50}")
        else:
            print(f"FAILED: Could not send reply to {sender_name}")
            print(f"Error: {result}")
            if "error" in result and result["error"].get("code") == 3:
                print("Permission error - need instagram_manage_messages approval")
            
            # Save failed reply to database
            save_failed_reply(sender_id, message_text, reply, message_id, result)
            print(f"Failed reply saved to database")
            print(f"{'='*50}")
    
    except Exception as e:
        print(f"Error processing message: {e}")