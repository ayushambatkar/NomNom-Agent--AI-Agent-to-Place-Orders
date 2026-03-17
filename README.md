# NomNom Restaurant Assistant 🍽️

A conversational AI-powered restaurant assistant built with Streamlit and Groq.

## Features

- **Guest browsing** - Explore restaurants without signing up
- **Phone login** - Authenticate with OTP for full features
- **Restaurant search** - Find restaurants by city or cuisine
- **Detailed info** - View menus, hours, and reviews
- **Reservations** - Book tables (requires login)
- **Natural conversation** - Powered by Google Gemini

## Quick Setup

### 1. Install dependencies

```bash
cd nomnom_agent
pip install -r requirements.txt
```

Or install individually:
```bash
pip install streamlit google-genai python-dotenv requests
```

### 2. Get your Gemini API key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Copy the key

### 3. Configure environment

Edit the `.env` file:
```env
GEMINI_API_KEY=your-gemini-api-key-here
API_BASE_URL=http://localhost:3000
```

### 4. Start the backend API

Make sure your NomNom API server is running:
```bash
cd ../nomnom_api
npm run start:dev
```

### 5. Run the assistant

```bash
streamlit run main.py
```

The app will open at `http://localhost:8501`

## Project Structure

```
nomnom_agent/
├── main.py           # Streamlit UI + chat interface
├── agent.py          # Gemini agent with tool calling
├── api_client.py     # HTTP client for backend APIs
├── session_state.py  # Streamlit session management
├── requirements.txt  # Python dependencies
├── .env              # Environment variables
└── README.md         # This file
```

## How It Works

1. **Session Management**: On first load, the app automatically creates a guest session
2. **Tool Calling**: The Gemini model can call Python functions to interact with the backend API
3. **Automatic Function Execution**: The google-genai SDK handles tool calling automatically
4. **Conversation History**: Chat context is preserved within the session

## Available Tools

The agent has access to these functions:

| Tool | Description |
|------|-------------|
| `guest_login()` | Create a guest session |
| `login(phone, otp)` | Phone authentication with OTP |
| `get_restaurants(city, cuisine)` | Search restaurants |
| `get_restaurant_details(id)` | Get restaurant info |
| `create_reservation(...)` | Book a table |
| `get_current_user_info()` | Get user profile |

## Usage Examples

Try these prompts:

- "Show me Italian restaurants in New York"
- "I want to make a reservation for 4 people"
- "What's the menu at [restaurant name]?"
- "Login with my phone +1234567890"
- "Show my reservations"

## Troubleshooting

### API Key Issues
- Make sure `GEMINI_API_KEY` is set correctly in `.env`
- Check that the key is valid at [Google AI Studio](https://aistudio.google.com)

### Backend Connection
- Ensure the NomNom API is running on the configured `API_BASE_URL`
- Check for CORS issues if running on different ports

### Rate Limits
- Free Gemini API has rate limits
- Wait a moment and retry if you hit limits

## License

MIT
