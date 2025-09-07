from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

# MongoDB configuration variables
MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
DATABASE_NAME = os.getenv("DATABASE_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
FAIL_COLLECTION_NAME = os.getenv("FAIL_COLLECTION_NAME")

# MongoDB connection with escaped credentials
username = quote_plus(MONGODB_USERNAME)
password = quote_plus(MONGODB_PASSWORD)
MONGODB_URI = f"mongodb+srv://{username}:{password}@cluster0.kvalswb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

def save_conversation(sender_id, user_message, bot_reply, message_id):
    """Save conversation to MongoDB"""
    conversation_entry = {
        "timestamp": datetime.utcnow(),
        "user_message": user_message,
        "bot_reply": bot_reply,
        "message_id": message_id
    }
    
    collection.update_one(
        {"_id": sender_id},
        {"$push": {"conversations": conversation_entry}},
        upsert=True
    )

def get_conversation_history(sender_id, limit=5):
    """Get recent conversation history for a sender"""
    user_data = collection.find_one({"_id": sender_id})
    if not user_data or "conversations" not in user_data:
        return []
    
    conversations = user_data["conversations"]
    return conversations[-limit:] if conversations else []

def save_failed_reply(sender_id, user_message, bot_reply, message_id, error):
    """Save failed reply to MongoDB"""
    fail_collection = db[FAIL_COLLECTION_NAME]
    
    failed_entry = {
        "timestamp": datetime.utcnow(),
        "sender_id": sender_id,
        "user_message": user_message,
        "bot_reply": bot_reply,
        "message_id": message_id,
        "error": error
    }
    
    fail_collection.insert_one(failed_entry)

def test_connection():
    """Test MongoDB connection"""
    try:
        client.admin.command('ping')
        print("MongoDB connection successful")
        return True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return False
    
if __name__ == "__main__":
    print("Testing MongoDB connection...")
    if test_connection():
        print("Database setup complete!")
    else:
        print("Database connection failed!")
    
    # Close connection
    client.close()