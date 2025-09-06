# Instagram Auto-Replier

An AI-powered webhook server that automatically replies to Instagram DMs using OpenAI's language models.

## Features

- 🤖 AI-generated responses using Gemini 2.0 Flash
- 📱 Instagram DM webhook integration
- 🔄 Duplicate message prevention
- 📝 Failed reply logging
- 🔐 Secure environment variable configuration

## Setup

### Prerequisites

- Python 3.8+
- Facebook Developer Account
- Instagram Business Account
- Gemini API Key

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
PAGE_ACCESS_TOKEN=your_page_access_token_here
IG_USER_ID=your_instagram_user_id_here
GEMINI_API_KEY=your_gemini_api_key_here
VERIFY_TOKEN=your_webhook_verify_token_here
APP_SECRET=your_facebook_app_secret_here
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
2. Facebook sends webhook to your server
3. Server generates AI reply using Gemini
4. Reply is sent back to user via Facebook Messenger API
5. Message ID is stored to prevent duplicates

## Configuration

The AI prompt can be customized in the `generate_dm_reply()` function. Current settings:
- Max 100 characters
- Professional and helpful tone
- Includes 1 relevant emoji
- Natural conversation style

## Troubleshooting

- Check `.env` file has correct credentials
- Ensure Instagram account is connected to Facebook Page
- Verify webhook URL is accessible via ngrok
- Check server logs for detailed error messages

## License

MIT License