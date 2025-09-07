from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
import os
import json
import hmac
import hashlib
from dm_handler import process_message
from comment_handler import process_comment

load_dotenv()

app = FastAPI()

# Environment variables
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mytoken123")
APP_SECRET = os.getenv("APP_SECRET", "your_app_secret")

print("=== Instagram Auto-Replier Starting ===")
print(f"Environment loaded: {os.getenv('PAGE_ACCESS_TOKEN') is not None}")
print(f"MongoDB configured: {os.getenv('MONGODB_USERNAME') is not None}")
print("=======================================")

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
    """Handle incoming webhook events for both DMs and Comments"""
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
            print("Signature verification failed - rejecting request")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        data = json.loads(body)
        
        if data.get("object") == "instagram":
            print("Processing Instagram webhook")
            for entry in data.get("entry", []):
                print(f"Entry data: {entry}")
                
                # Handle DM messages
                messaging_events = entry.get("messaging", [])
                if messaging_events:
                    print(f"Found {len(messaging_events)} messaging events")
                    for messaging in messaging_events:
                        await process_message(messaging)
                
                # Handle comment changes
                changes = entry.get("changes", [])
                if changes:
                    print(f"Found {len(changes)} change events")
                    for change in changes:
                        print(f"Change field: {change.get('field')}")
                        print(f"Change value: {change.get('value', {})}")
                        if change.get("field") == "comments":
                            print("Found comment event!")
                            await process_comment(change.get("value", {}))
                        else:
                            print(f"Ignoring field: {change.get('field')}")
                else:
                    print("No changes array found in entry")
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

@app.get("/")
async def root():
    return {"message": "Instagram DM & Comment Auto-Reply Webhook is running"}

@app.get("/test")
async def test():
    print("Test endpoint called")
    return {"status": "test successful"}

@app.get("/debug")
async def debug():
    print("Debug endpoint called")
    return {
        "status": "debug",
        "verify_token": VERIFY_TOKEN,
        "app_secret_set": bool(APP_SECRET and APP_SECRET != "your_app_secret")
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
