# 🤖 Auto Dialer

An AI-powered auto dialer application that uses Twilio for making calls and Google Gemini for generating natural conversation messages.

## Features

- **Single Call Mode**: Make individual calls with custom reasons
- **Bulk Call Mode**: Upload CSV files to process multiple calls
- **AI Message Generation**: Uses Google Gemini to create natural, professional call messages
- **Real-time Call Tracking**: Live status updates via Twilio webhooks
- **Call Logging**: Tracks all calls with status, duration, and recordings
- **Recording Downloads**: Automatically saves call recordings locally
- **Standalone CLI**: Command-line interface for automated calling
- **Random Disconnect**: Calls disconnect between 30-60 seconds for testing

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

The app reads API keys from `~/.env` (home directory). Configure your credentials:

```env
# Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Google Gemini API
GEMINI_API=your_google_gemini_api_key
```

### 3. Get API Keys

- **Twilio**: Sign up at [twilio.com](https://twilio.com) and get your Account SID, Auth Token, and phone number
- **Google Gemini**: Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### 4. For Development (Optional)

If you want to test webhooks locally, install ngrok:

```bash
# Install ngrok from https://ngrok.com/
ngrok http 5000
```

This will give you a public URL that Twilio can reach for webhook callbacks.

## Usage

### Web Interface (Flask)

Run the Flask app:

```bash
python app_flask.py
```

Open your browser to `http://localhost:5000`

### Single Call
1. Enter phone number (with country code, e.g., +1234567890)
2. Enter call reason/purpose
3. Click "Generate & Call" - this will:
   - Generate an AI message based on your reason
   - Display the message in a box on the same page
   - Automatically initiate the call after 2 seconds
4. The call will be made with the AI-generated message

### Bulk Calls
1. Upload a CSV file with columns: `phone_number`, `reason`
2. Click "Process Bulk Calls"
3. All calls will be processed automatically

### View Logs
- Click "View All Logs" to see complete call history
- Download logs as CSV file
- **Clear Logs**: Remove all call history with confirmation dialog
- Real-time status updates show: initiated → ringing → answered → completed


## CSV Format for Bulk Calls

Create a CSV file with the following columns:

```csv
phone_number,reason
+1234567890,Follow up on invoice payment
+1987654321,Schedule appointment reminder
+1555123456,Product delivery confirmation
```

## Call Flow

1. User provides phone number and reason
2. Gemini AI generates a natural message based on the reason
3. Twilio initiates the call
4. Call plays the AI-generated message
5. Call records the conversation
6. Call disconnects after 30-60 seconds (random)
7. Call details are logged to CSV

## Recordings

Call recordings are saved in the `recordings/` directory with filenames based on the Twilio Call SID.

## Logs

All call data is stored in `data/call_logs.csv` with the following fields:
- timestamp
- phone_number
- reason
- call_sid (Twilio call identifier)
- status
- duration
