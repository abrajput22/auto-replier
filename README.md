# Instagram Auto-Replier

An AI-powered webhook server that automatically replies to Instagram DMs using Gemini 2.0 Flash with conversation context and MongoDB storage.

## Features

- 🤖 AI-generated responses using Gemini 2.0 Flash
- 💬 Conversation context memory (configurable window size)
- 🗄️ MongoDB integration for conversation storage
- 📱 Instagram DM webhook integration
- 🔄 Duplicate message prevention
- 📝 Failed reply logging to database
- 🔐 Secure webhook signature verification
- 🔐 Secure environment variable configuration

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

2. Configure Facebook webhook:
   - Webhook URL: `https://your-ngrok-url.ngrok.io/webhook`
   - Verify Token: Your `VERIFY_TOKEN` from `.env`
   - Subscribe to: `messages`

## API Endpoints

- `GET /` - Health check
- `GET /webhook` - Webhook verification
- `POST /webhook` - Handle Instagram messages
- `GET /test` - Test endpoint
- `GET /debug` - Debug information

## How It Works

1. User sends DM to your Instagram account
2. Facebook sends webhook to your server with signature verification
3. Server retrieves conversation history from MongoDB
4. Server generates contextual AI reply using Gemini with conversation context
5. Reply is sent back to user via Facebook Messenger API
6. Successful conversation is saved to MongoDB
7. Failed replies are logged to separate MongoDB collection
8. Message ID is stored to prevent duplicates

## Configuration

### AI Settings
The AI prompt can be customized in the `generate_dm_reply()` function. Current settings:
- Max 100 characters
- Professional and helpful tone
- Uses conversation context for better responses
- Natural conversation style

### Context Window
Adjust conversation memory by changing `CONTEXT_WINDOW_SIZE`:
- `5` - Last 5 messages (fast, minimal context)
- `15` - Last 15 messages (balanced, recommended)
- `25` - Last 25 messages (maximum context, slower)

### Database Collections
- `conversations` - Successful message exchanges
- `fail_reply` - Failed reply attempts with error details

## Troubleshooting

- Check `.env` file has correct credentials
- Ensure Instagram account is connected to Facebook Page
- Verify webhook URL is accessible via ngrok
- Test MongoDB connection: `python db_connection.py`
- Check server logs for detailed error messages
- Verify App Secret for signature validation
- Check MongoDB collections for conversation history
- Review failed replies in `fail_reply` collection

## License

MIT License
