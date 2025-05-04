from flask import Flask, request, jsonify
import os.path
import datetime
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

app = Flask(__name__)
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_credentials():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

@app.route('/get-events', methods=['GET'])
def get_events():
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    output = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        output.append({'start': start, 'summary': event.get('summary', 'No title')})
    return jsonify(output)

@app.route('/add-event', methods=['POST'])
def add_event():
    data = request.json
    title = data.get('title')
    start_time = data.get('start_time')  # Format: YYYY-MM-DDTHH:MM:SS
    duration_minutes = int(data.get('duration', 60))

    if not title or not start_time:
        return jsonify({'error': 'Missing title or start_time'}), 400

    start_dt = datetime.datetime.fromisoformat(start_time)
    end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)

    event = {
        'summary': title,
        'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'UTC'},
        'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'UTC'},
    }

    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    event_result = service.events().insert(calendarId='primary', body=event).execute()

    return jsonify({'status': 'Event created', 'event': event_result})

if __name__ == '__main__':
    app.run(debug=True)
