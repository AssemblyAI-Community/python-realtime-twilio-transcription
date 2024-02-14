import json

from flask import Flask, request, Response
from flask_sock import Sock

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
        Speak to see your audio data printed to the console
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
                print('twilio connected')
            case "start":
                print('twilio started')
            case "media": 
                payload = data['media']['payload']
                print(payload)
            case "stop":
                print('twilio stopped')


if __name__ == "__main__":
    app.run(port=PORT, debug=DEBUG)