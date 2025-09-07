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
from db_connection import save_conversation, get_conversation_history, save_failed_reply

load_dotenv()

app = FastAPI()

# Environment variables
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
APP_SECRET = os.getenv("APP_SECRET")
IG_USERNAME = os.getenv("IG_USERNAME")

# Track processed comments
processed_comments = set()

print(f"=== WEBHOOK SERVER STARTING ===")
print(f"PAGE_ACCESS_TOKEN: {'SET' if PAGE_ACCESS_TOKEN else 'NOT SET'}")
print(f"IG_USER_ID: {IG_USER_ID}")
print(f"VERIFY_TOKEN: {VERIFY_TOKEN}")
print(f"APP_SECRET: {'SET' if APP_SECRET else 'NOT SET'}")
print(f"IG_USERNAME: {IG_USERNAME}")
print(f"=================================")

def generate_comment_reply(comment_text, post_caption):
    """Generate AI reply to comment using post context"""
    llm = ChatOpenAI(
        model="gemini-2.0-flash",
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    
    prompt = f"""Generate a friendly reply to this Instagram comment: "{comment_text}"
    
    Post context: "{post_caption}"
    
    Requirements:
    - Use post context to make reply more relevant
    - Keep it under 50 characters
    - Be positive and engaging
    - Sound natural and conversational
    
    Generate contextual reply:"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()

def get_post_caption(post_id):
    """Get post caption"""
    url = f"https://graph.facebook.com/v22.0/{post_id}"
    params = {
        "fields": "caption",
        "access_token": PAGE_ACCESS_TOKEN
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data.get("caption", "")

def reply_to_comment(comment_id, reply_text):
    """Reply to a specific comment"""
    url = f"https://graph.facebook.com/v22.0/{comment_id}/replies"
    data = {
        "message": reply_text,
        "access_token": PAGE_ACCESS_TOKEN
    }
    
    response = requests.post(url, data=data)
    return response.json()

@app.get("/webhook")
async def verify_webhook(request: Request):
    """Webhook verification for Facebook"""
    print(f"Verification attempt: {dict(request.query_params)}")
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verified successfully")
        return PlainTextResponse(challenge)
    else:
        print(f"Webhook verification failed - mode: {mode}, token: {token}")
        raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/webhook")
async def handle_webhook(request: Request):
    """Handle incoming webhook events"""
    print(f"\n=== WEBHOOK RECEIVED ===")
    print(f"Headers: {dict(request.headers)}")
    
    try:
        body = await request.body()
        print(f"Raw body: {body.decode()}")
        
        signature = request.headers.get("X-Hub-Signature-256", "")
        print(f"Signature: {signature}")
        
        if not verify_signature(body, signature):
            print("Signature verification failed")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        data = json.loads(body)
        print(f"Parsed data: {json.dumps(data, indent=2)}")
        
        if data.get("object") == "instagram":
            print("Processing Instagram webhook")
            for entry in data.get("entry", []):
                print(f"Entry: {entry}")
                for change in entry.get("changes", []):
                    print(f"Change field: {change.get('field')}")
                    if change.get("field") == "comments":
                        print("Found comment event!")
                        await process_comment(change.get("value", {}))
                    else:
                        print(f"Ignoring field: {change.get('field')}")
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
        print("Warning: No APP_SECRET set, skipping signature verification")
        return True
    
    if not signature:
        print("Warning: No signature provided")
        return False
    
    expected_signature = "sha256=" + hmac.new(
        APP_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    is_valid = hmac.compare_digest(expected_signature, signature)
    if not is_valid:
        print(f"Expected: {expected_signature}")
        print(f"Received: {signature}")
    
    return is_valid

async def process_comment(comment_data):
    """Process incoming comment"""
    try:
        comment_id = comment_data.get("id")
        post_id = comment_data.get("parent_id")
        comment_text = comment_data.get("text", "")
        commenter_username = comment_data.get("from", {}).get("username", "")
        
        print(f"\n=== NEW COMMENT ===")
        print(f"Comment ID: {comment_id}")
        print(f"Post ID: {post_id}")
        print(f"From: {commenter_username}")
        print(f"Text: {comment_text}")
        
        # Skip if already processed
        if comment_id in processed_comments:
            print("Already processed")
            return
        
        # Skip our own comments
        if commenter_username == IG_USERNAME:
            print("Skipping our own comment")
            return
        
        processed_comments.add(comment_id)
        
        # Get post caption for context
        post_caption = get_post_caption(post_id)
        
        # Generate reply
        reply = generate_comment_reply(comment_text, post_caption)
        print(f"Generated reply: {reply}")
        
        # Send reply
        result = reply_to_comment(comment_id, reply)
        
        if "id" in result:
            print(f"SUCCESS: Reply sent")
            # Save to database
            save_conversation(comment_id, comment_text, reply, comment_id)
        else:
            print(f"FAILED: {result}")
            # Save failed reply
            save_failed_reply(comment_id, comment_text, reply, comment_id, result)
    
    except Exception as e:
        print(f"Error processing comment: {e}")

@app.get("/")
async def root():
    return {"message": "Instagram Comment Auto-Reply Webhook is running"}

@app.post("/test")
async def test_webhook(request: Request):
    """Test endpoint to see any incoming data"""
    print(f"\n=== TEST WEBHOOK RECEIVED ===")
    body = await request.body()
    print(f"Raw body: {body.decode()}")
    print(f"Headers: {dict(request.headers)}")
    return {"status": "test received"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

# python comment_webhook.py