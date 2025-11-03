from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, make_response
import os
from datetime import datetime
import random
import pandas as pd
import requests
from dotenv import load_dotenv
import google.generativeai as genai
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import threading
import time

# Load environment variables from home directory
load_dotenv(os.path.expanduser('~/.env'))

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API'))

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Flask app
app = Flask(__name__)
app.secret_key = 'auto_dialer_secret_key'

# Constants
LOGS_FILE = 'data/call_logs.csv'
RECORDINGS_DIR = 'recordings/'

# Ensure directories exist
os.makedirs('data', exist_ok=True)
os.makedirs(RECORDINGS_DIR, exist_ok=True)

# In-memory call status storage (in production, use database)
call_statuses = {}

def generate_call_message(reason):
    """Generate a natural call message using Gemini API"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        Create a natural, professional phone message for an automated call with the following purpose: "{reason}".

        The message should be:
        - Concise (20-30 seconds when spoken)
        - Professional and polite
        - Include a call-to-action
        - Sound like a human caller
        - End with contact information request
        - on behalf of Darshil's Company

        Generate only the spoken message, no additional text.
        """

        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating message with Gemini: {e}")
        return f"Hello, this is an automated call regarding: {reason}. Please call us back."

def make_call(phone_number, message):
    """Initiate a call using Twilio"""
    try:
        # Generate TwiML for the call
        twiml = generate_twiml(message)

        # Get base URL for webhooks (in production, use ngrok or similar)
        base_url = request.host_url.rstrip('/')

        # Make the call
        call = twilio_client.calls.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            twiml=twiml,
            record=True,
            status_callback=f"{base_url}/twilio/status",
            status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
            recording_status_callback=f"{base_url}/twilio/recording"
        )

        # Initialize call status
        call_statuses[call.sid] = {
            'status': 'initiated',
            'duration': 0,
            'recording_url': None
        }

        return call.sid, "initiated"
    except Exception as e:
        return None, str(e)

def generate_twiml(message):
    """Generate TwiML for the call"""
    response = VoiceResponse()

    # Say the message
    response.say(message, voice='alice')

    # Add a random disconnect time between 30-60 seconds
    disconnect_time = random.randint(30, 60)

    # Pause for the disconnect time
    response.pause(length=disconnect_time)

    # Hang up
    response.hangup()

    return str(response)

def log_call(phone_number, reason, call_sid, status='initiated', duration=0, recording_url=None):
    """Log call details to CSV"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Create log entry
    log_entry = {
        'timestamp': timestamp,
        'phone_number': phone_number,
        'reason': reason,
        'call_sid': call_sid or 'N/A',
        'status': status,
        'duration': duration or 0,
        'recording_url': recording_url or 'N/A'
    }

    # Load existing logs or create new dataframe
    if os.path.exists(LOGS_FILE):
        df = pd.read_csv(LOGS_FILE)
        # Update existing entry if call_sid exists, otherwise append
        if call_sid and call_sid in df['call_sid'].values:
            df.loc[df['call_sid'] == call_sid, ['status', 'duration', 'recording_url']] = [status, duration, recording_url]
        else:
            df = pd.concat([df, pd.DataFrame([log_entry])], ignore_index=True)
    else:
        df = pd.DataFrame([log_entry])

    # Save to CSV
    df.to_csv(LOGS_FILE, index=False)

def download_recording(recording_url, call_sid):
    """Download recording from Twilio"""
    try:
        response = requests.get(recording_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        if response.status_code == 200:
            filename = f"{RECORDINGS_DIR}{call_sid}.mp3"
            with open(filename, 'wb') as f:
                f.write(response.content)
            return filename
    except Exception as e:
        print(f"Error downloading recording: {e}")
    return None

def load_logs():
    """Load call logs from CSV"""
    if os.path.exists(LOGS_FILE):
        return pd.read_csv(LOGS_FILE)
    return pd.DataFrame(columns=['timestamp', 'phone_number', 'reason', 'call_sid', 'status', 'duration', 'recording_url'])

@app.route('/')
def index():
    """Main dashboard"""
    logs_df = load_logs()
    recent_logs = logs_df.tail(10) if not logs_df.empty else pd.DataFrame()
    return render_template('index.html', logs=recent_logs.to_dict('records') if not recent_logs.empty else [])

@app.route('/call', methods=['POST'])
def initiate_call():
    """Initiate a single call"""
    phone_number = request.form.get('phone_number')
    reason = request.form.get('reason')

    if not phone_number or not reason:
        flash('Phone number and reason are required', 'error')
        return redirect(url_for('index'))

    # Generate AI message
    message = generate_call_message(reason)

    # Make the call
    call_sid, status = make_call(phone_number, message)

    if call_sid:
        log_call(phone_number, reason, call_sid, status)
        flash(f'Call initiated successfully! SID: {call_sid}', 'success')
    else:
        # Clean up error message for logging
        clean_error = "Authentication failed - check API keys" if "invalid username" in str(status) else "Call failed"
        log_call(phone_number, reason, None, clean_error)
        flash(f'Failed to initiate call: {clean_error}', 'error')

    return redirect(url_for('index'))

@app.route('/bulk-call', methods=['POST'])
def bulk_call():
    """Process bulk calls from CSV"""
    if 'csv_file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('index'))

    file = request.files['csv_file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))

    if not file.filename.endswith('.csv'):
        flash('Please upload a CSV file', 'error')
        return redirect(url_for('index'))

    try:
        df = pd.read_csv(file)

        success_count = 0
        for _, row in df.iterrows():
            phone = str(row['phone_number']).strip()
            reason = str(row['reason']).strip()

            message = generate_call_message(reason)
            call_sid, status = make_call(phone, message)

            if call_sid:
                log_call(phone, reason, call_sid, status)
                success_count += 1
            else:
                # Clean up error message for logging
                clean_error = "Authentication failed - check API keys" if "invalid username" in str(status) else "Call failed"
                log_call(phone, reason, None, clean_error)

        flash(f'Processed {len(df)} calls. {success_count} successful.', 'success')

    except Exception as e:
        flash(f'Error processing CSV: {str(e)}', 'error')

    return redirect(url_for('index'))

@app.route('/logs')
def view_logs():
    """View all call logs"""
    logs_df = load_logs()
    logs = logs_df.to_dict('records') if not logs_df.empty else []
    return render_template('logs.html', logs=logs)

@app.route('/download-logs')
def download_logs():
    """Download call logs as CSV"""
    logs_df = load_logs()
    if logs_df.empty:
        return "No logs available", 404

    csv_data = logs_df.to_csv(index=False)
    response = make_response(csv_data)
    response.headers['Content-Disposition'] = 'attachment; filename=call_logs.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

@app.route('/clear-logs', methods=['POST'])
def clear_logs():
    """Clear all call logs and recordings"""
    try:
        # Remove the CSV file
        if os.path.exists(LOGS_FILE):
            os.remove(LOGS_FILE)

        # Clear recordings directory (optional - comment out if you want to keep recordings)
        # import shutil
        # if os.path.exists(RECORDINGS_DIR):
        #     shutil.rmtree(RECORDINGS_DIR)
        #     os.makedirs(RECORDINGS_DIR, exist_ok=True)

        # Clear in-memory call statuses
        global call_statuses
        call_statuses.clear()

        flash('All call logs have been cleared successfully.', 'success')
    except Exception as e:
        flash(f'Error clearing logs: {str(e)}', 'error')

    return redirect(url_for('view_logs'))

@app.route('/generate-message', methods=['POST'])
def generate_message_api():
    """Generate AI message via AJAX"""
    try:
        data = request.get_json()
        reason = data.get('reason', '')

        if not reason:
            return jsonify({'success': False, 'error': 'Reason is required'})

        # Generate AI message
        message = generate_call_message(reason)

        return jsonify({'success': True, 'message': message})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/twilio/status', methods=['POST'])
def twilio_status_callback():
    """Handle Twilio call status updates"""
    call_sid = request.form.get('CallSid')
    call_status = request.form.get('CallStatus')
    call_duration = request.form.get('CallDuration', 0)

    if call_sid:
        # Update in-memory status
        call_statuses[call_sid] = {
            'status': call_status,
            'duration': int(call_duration) if call_duration else 0,
            'recording_url': call_statuses.get(call_sid, {}).get('recording_url')
        }

        # Update CSV log
        logs_df = load_logs()
        if not logs_df.empty and call_sid in logs_df['call_sid'].values:
            logs_df.loc[logs_df['call_sid'] == call_sid, ['status', 'duration']] = [call_status, int(call_duration) if call_duration else 0]
            logs_df.to_csv(LOGS_FILE, index=False)

        # If call is completed, try to fetch recording manually
        if call_status == 'completed':
            fetch_recording_for_call(call_sid)

    return '', 200

def fetch_recording_for_call(call_sid):
    """Manually fetch recording for a completed call"""
    try:
        # Get call details from Twilio
        call = twilio_client.calls(call_sid).fetch()

        # Get recordings for this call
        recordings = twilio_client.recordings.list(call_sid=call_sid, limit=1)

        if recordings:
            recording = recordings[0]
            recording_url = f"https://api.twilio.com{recording.uri[:-5]}"  # Remove .json extension

            # Download the recording
            local_path = download_recording(recording_url + '.mp3', call_sid)

            if local_path:
                # Update status
                if call_sid in call_statuses:
                    call_statuses[call_sid]['recording_url'] = local_path

                # Update CSV log
                logs_df = load_logs()
                if not logs_df.empty and call_sid in logs_df['call_sid'].values:
                    logs_df.loc[logs_df['call_sid'] == call_sid, 'recording_url'] = local_path
                    logs_df.to_csv(LOGS_FILE, index=False)

                print(f"✅ Recording downloaded for call {call_sid}: {local_path}")
            else:
                print(f"❌ Failed to download recording for call {call_sid}")

    except Exception as e:
        print(f"Error fetching recording for call {call_sid}: {e}")

@app.route('/twilio/recording', methods=['POST'])
def twilio_recording_callback():
    """Handle Twilio recording callbacks"""
    call_sid = request.form.get('CallSid')
    recording_url = request.form.get('RecordingUrl')

    if call_sid and recording_url:
        # Download the recording
        local_path = download_recording(recording_url + '.mp3', call_sid)

        # Update status
        if call_sid in call_statuses:
            call_statuses[call_sid]['recording_url'] = local_path

        # Update CSV log
        logs_df = load_logs()
        if not logs_df.empty and call_sid in logs_df['call_sid'].values:
            logs_df.loc[logs_df['call_sid'] == call_sid, 'recording_url'] = local_path or recording_url
            logs_df.to_csv(LOGS_FILE, index=False)

    return '', 200

if __name__ == '__main__':
    # For development, you might want to use ngrok to expose the webhook endpoints
    # Run: ngrok http 5000
    # Then update the webhook URLs in make_call() to use the ngrok URL

    app.run(debug=True, host='0.0.0.0', port=8080)
