from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
import requests
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os
import json
import hmac
import hashlib

load_dotenv()

app = FastAPI()

# Instagram Graph API credentials from environment variables
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mytoken123")
APP_SECRET = os.getenv("APP_SECRET", "your_app_secret")

# Track processed messages to avoid duplicates
processed_messages = set()

def generate_dm_reply(message_text):
    """Generate AI reply to DM"""
    llm = ChatOpenAI(
        model="gemini-2.0-flash",
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    
    prompt = f"""Generate a friendly, helpful DM reply to: "{message_text}"
    
    Requirements:
    - Keep it under 100 characters
    - Be professional and helpful
    - Add 1 relevant emoji
    - Sound natural and conversational
    
    Generate helpful reply:"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()

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

@app.get("/webhook")
async def verify_webhook(request: Request):
    """Webhook verification for Facebook"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verified successfully")
        return PlainTextResponse(challenge)
    else:
        print("Webhook verification failed")
        raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/webhook")
async def handle_webhook(request: Request):
    """Handle incoming webhook events"""
    print(f"Webhook called with headers: {dict(request.headers)}")
    
    try:
        body = await request.body()
        print(f"Received data: {body.decode()}")
        
        if not body:
            print("Empty webhook body")
            return {"status": "ok"}
        
        signature = request.headers.get("X-Hub-Signature-256", "")
        if signature:
            print(f"Signature: {signature}")
        
        if not verify_signature(body, signature):
            print("Signature verification failed")
        
        data = json.loads(body)
        
        if data.get("object") == "instagram":
            print("Processing Instagram webhook")
            for entry in data.get("entry", []):
                for messaging in entry.get("messaging", []):
                    await process_message(messaging)
        elif data.get("object") == "page":
            print("Processing Page webhook")
            for entry in data.get("entry", []):
                for messaging in entry.get("messaging", []):
                    await process_message(messaging)
        else:
            print(f"Unknown object type: {data.get('object')}")
        
        return {"status": "ok"}
    
    except Exception as e:
        print(f"Webhook error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {"status": "error", "message": str(e)}

def verify_signature(payload, signature):
    """Verify webhook signature"""
    if not APP_SECRET or APP_SECRET == "your_app_secret":
        return True  # Skip verification if no secret set
    
    expected_signature = "sha256=" + hmac.new(
        APP_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)

async def process_message(messaging):
    """Process incoming message"""
    try:
        if "message" not in messaging:
            print("No message key found")
            return
        
        message = messaging["message"]
        sender_id = messaging["sender"]["id"]
        message_id = message.get("mid", "")
        
        print(f"Message from {sender_id} (ID: {message_id})")
        
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
        
        print(f"Message text: {message_text}")
        
        # Generate and send reply
        reply = generate_dm_reply(message_text)
        print(f"Generated reply: {reply}")
        
        result = send_dm_reply(sender_id, reply)
        
        if "message_id" in result or "id" in result:
            print("Reply sent successfully")
        else:
            print(f"Failed to send reply: {result}")
            if "error" in result and result["error"].get("code") == 3:
                print("Permission error - need instagram_manage_messages approval")
            
            # Log failed replies
            with open('dm_replies.txt', 'a', encoding='utf-8') as f:
                f.write(f"\n--- {sender_id}: {message_text}\n")
                f.write(f"Reply: {reply}\n")
                f.write(f"Error: {result}\n")
            print("Reply logged to dm_replies.txt")
    
    except Exception as e:
        print(f"Error processing message: {e}")

@app.get("/")
async def root():
    return {"message": "Instagram DM Auto-Reply Webhook is running"}

@app.get("/test")
async def test():
    print("Test endpoint called")
    return {"status": "test successful"}

@app.get("/debug")
async def debug():
    print("Debug endpoint called")
    return {
        "status": "debug",
        "page_token": PAGE_ACCESS_TOKEN[:20] + "..." if PAGE_ACCESS_TOKEN else "not set",
        "ig_user_id": IG_USER_ID,
        "verify_token": VERIFY_TOKEN
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# python webhook_server.py