# Instagram Auto-Replier

An AI-powered webhook server that automatically replies to Instagram DMs and Comments using Gemini 2.0 Flash with conversation context and MongoDB storage.

## Features

- 🤖 AI-generated responses using Gemini 2.0 Flash
- 💬 Instagram DM auto-replies with conversation context memory
- 💭 Instagram Comment auto-replies with post context
- 🗄️ MongoDB integration for conversation storage
- 📱 Unified webhook handling for both DMs and Comments
- 🔄 Duplicate message/comment prevention
- 📝 Failed reply logging to database
- 🔐 Secure webhook signature verification
- 🏗️ Modular architecture with separate handlers

## Project Structure

```
auto-replier/
├── webhook_server.py      # Main webhook server
├── dm_handler.py          # DM processing logic
├── comment_handler.py     # Comment processing logic
├── db_connection.py       # MongoDB operations
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
└── README.md             # This file
```

## Setup

### Prerequisites

- Python 3.8+
- Facebook Developer Account
- Instagram Business Account
- Gemini API Key
- MongoDB Atlas Account (free tier available)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/abrajput22/auto-replier.git
cd auto-replier
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```
# Instagram Graph API Credentials
PAGE_ACCESS_TOKEN=your_page_access_token_here
IG_USER_ID=your_instagram_user_id_here
GEMINI_API_KEY=your_gemini_api_key_here
VERIFY_TOKEN=your_webhook_verify_token_here
APP_SECRET=your_facebook_app_secret_here
IG_USERNAME=your_instagram_username_here

# MongoDB Configuration
MONGODB_USERNAME=your_mongodb_username
MONGODB_PASSWORD=your_mongodb_password
DATABASE_NAME=auto-replier
COLLECTION_NAME=conversations
FAIL_COLLECTION_NAME=fail_reply

# Bot Configuration
CONTEXT_WINDOW_SIZE=5
```

### Running the Server

```bash
python webhook_server.py
```

The server will start on `http://localhost:8000`

### Webhook Setup

1. Use ngrok to expose your local server:
```bash
ngrok http 8000
```

2. Configure Facebook webhook in Graph API Explorer:

**For DMs:**
```json
{
  "object": "instagram",
  "callback_url": "https://your-ngrok-url.ngrok.io/webhook",
  "fields": "messages",
  "verify_token": "your_verify_token",
  "access_token": "app_id|app_secret"
}
```

**For Comments:**
```json
{
  "object": "instagram",
  "callback_url": "https://your-ngrok-url.ngrok.io/webhook",
  "fields": "comments",
  "verify_token": "your_verify_token",
  "access_token": "app_id|app_secret"
}
```

## API Endpoints

- `GET /` - Health check
- `GET /webhook` - Webhook verification
- `POST /webhook` - Handle Instagram DMs and Comments
- `GET /test` - Test endpoint
- `GET /debug` - Debug information

## How It Works

### DM Auto-Reply:
1. User sends DM to your Instagram account
2. Facebook sends webhook to your server
3. `dm_handler.py` processes the message
4. Server retrieves conversation history from MongoDB
5. AI generates contextual reply using conversation history
6. Reply is sent back via Facebook Messenger API
7. Conversation is saved to MongoDB

### Comment Auto-Reply:
1. User comments on your Instagram post
2. Facebook sends webhook to your server
3. `comment_handler.py` processes the comment
4. Server retrieves post caption for context
5. AI generates contextual reply using post context
6. Reply is posted as comment reply
7. Interaction is saved to MongoDB

## Configuration

### AI Settings

**DM Replies (`dm_handler.py`):**
- Max 100 characters
- Professional and helpful tone
- Uses conversation context
- Configurable context window size

**Comment Replies (`comment_handler.py`):**
- Max 50 characters
- Uses post caption for context
- Positive and engaging tone
- Natural conversation style

### Context Window (DMs only)
Adjust conversation memory by changing `CONTEXT_WINDOW_SIZE`:
- `5` - Last 5 messages (fast, minimal context)
- `15` - Last 15 messages (balanced, recommended)
- `25` - Last 25 messages (maximum context, slower)

### Database Collections
- `conversations` - Successful message/comment exchanges
- `fail_reply` - Failed reply attempts with error details

## Required Permissions

- `instagram_basic` - Basic Instagram access
- `instagram_manage_messages` - Send DM replies
- `instagram_manage_comments` - Reply to comments
- `pages_show_list` - Access to pages
- `pages_read_engagement` - Read page interactions

## Troubleshooting

- Check `.env` file has correct credentials
- Ensure Instagram account is Business/Creator account
- Verify Instagram is connected to Facebook Page
- Test MongoDB connection: `python db_connection.py`
- Check webhook subscription in Graph API Explorer
- Verify webhook URL is accessible via ngrok
- Check server logs for detailed error messages
- Review failed replies in `fail_reply` collection

## Development Mode Limitations

- Only app admins, developers, and testers can trigger webhooks
- Add testers in Facebook App → Roles → Testers
- For production (all users), submit app for Facebook review

## License

MIT License
