import base64
import json

from flask import Flask, request, Response
from flask_sock import Sock

from twilio_transcriber import TwilioTranscriber

# Flask settings
PORT = 5000
DEBUG = False
INCOMING_CALL_ROUTE = '/'
WEBSOCKET_ROUTE = '/realtime'

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
    app.run(port=PORT, debug=DEBUG)