from flask import Flask
from flask_sock import Sock

# Flask settings
PORT = 5000
DEBUG = False
INCOMING_CALL_ROUTE = '/'
WEBSOCKET_ROUTE = '/realtime'

app = Flask(__name__)
sock = Sock(app)

@app.route(INCOMING_CALL_ROUTE)
def receive_call():
    pass

@sock.route(WEBSOCKET_ROUTE)
def transcription_websocket(ws):
    pass


if __name__ == "__main__":
    app.run(port=PORT, debug=DEBUG)