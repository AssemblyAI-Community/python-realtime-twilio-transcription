import base64
import json
import os

from flask import Flask, request, Response
from flask_sock import Sock
import ngrok
from twilio.rest import Client
from dotenv import load_dotenv
load_dotenv()

from twilio_transcriber import TwilioTranscriber

# Flask settings
PORT = 5000
DEBUG = False
INCOMING_CALL_ROUTE = '/'
WEBSOCKET_ROUTE = '/realtime'

# Twilio authentication
account_sid = os.environ['TWILIO_ACCOUNT_SID']
api_key = os.environ['TWILIO_API_KEY_SID']
api_secret = os.environ['TWILIO_API_SECRET']
client = Client(api_key, api_secret, account_sid)

# Twilio phone number to call
TWILIO_NUMBER = os.environ['TWILIO_NUMBER']

# ngrok authentication
ngrok.set_auth_token(os.getenv("NGROK_AUTHTOKEN"))
app = Flask(__name__)
sock = Sock(app)

@app.route(INCOMING_CALL_ROUTE, methods=['GET', 'POST'])
def receive_call():
    if request.method == 'POST':
        xml = f"""
<Response>
    <Say>
        Speak to see your speech transcribed in the console
    </Say>
    <Connect>
        <Stream url='wss://{request.host}{WEBSOCKET_ROUTE}' />
    </Connect>
</Response>
""".strip()
        return Response(xml, mimetype='text/xml')
    else:
        return f"Real-time phone call transcription app"

@sock.route(WEBSOCKET_ROUTE)
def transcription_websocket(ws):
    while True:
        data = json.loads(ws.receive())
        match data['event']:
            case "connected":
                transcriber = TwilioTranscriber()
                transcriber.connect()
                print('transcriber connected')
            case "start":
                print('twilio started')
            case "media": 
                payload_b64 = data['media']['payload']
                payload_mulaw = base64.b64decode(payload_b64)
                transcriber.stream(payload_mulaw)
            case "stop":
                print('twilio stopped')
                transcriber.close()
                print('transcriber closed')


if __name__ == "__main__":
    try:
        # Open Ngrok tunnel
        listener = ngrok.forward(f"http://localhost:{PORT}")
        print(f"Ngrok tunnel opened at {listener.url()} for port {PORT}")
        NGROK_URL = listener.url()

        # Set ngrok URL to be the webhook for the appropriate Twilio number
        twilio_numbers = client.incoming_phone_numbers.list()
        twilio_number_sid = [num.sid for num in twilio_numbers if num.phone_number == TWILIO_NUMBER][0]
        client.incoming_phone_numbers(twilio_number_sid).update(account_sid, voice_url=f"{NGROK_URL}{INCOMING_CALL_ROUTE}")

        # run the app
        app.run(port=PORT, debug=DEBUG)
    finally:
        # Always disconnect the ngrok tunnel
        ngrok.disconnect()
