import requests
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os
from db_connection import save_conversation, save_failed_reply

load_dotenv()

# Environment variables
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
IG_USERNAME = os.getenv("IG_USERNAME")

# Track processed comments
processed_comments = set()

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
            print(f"SUCCESS: Comment reply sent")
            # Save to database
            save_conversation(comment_id, comment_text, reply, comment_id)
        else:
            print(f"FAILED: {result}")
            # Save failed reply
            save_failed_reply(comment_id, comment_text, reply, comment_id, result)
    
    except Exception as e:
        print(f"Error processing comment: {e}")