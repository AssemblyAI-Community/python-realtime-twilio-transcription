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
        You have connected to the Flask application
    </Say>
</Response>
""".strip()
        return Response(xml, mimetype='text/xml')
    else:
        return f"Real-time phone call transcription app"

@sock.route(WEBSOCKET_ROUTE)
def transcription_websocket(ws):
    pass


if __name__ == "__main__":
    app.run(port=PORT, debug=DEBUG)