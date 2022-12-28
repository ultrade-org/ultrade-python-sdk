import socketio
import time

socket = None
options = {
  'symbol': "yldy_stbl",
  'streams': [ 4,5,6,7,8,9],
  'options': {"address": "47HZBXMZ4V34L4ONFGQESWJYVSDVIRSZPBQM3B7WUZZXZ2622EXXXO6GSU", "partnerId": "87654321"}
}
opts = {"sid":"oA8iJaSHOM7bo7nIAAAc","upgrades":[],"pingInterval":25000,"pingTimeout":20000,"maxPayload":1000000}
socket_pool = {}
class NameSpace(socketio.ClientNamespace):
    def on_event_handler(event, args):
        print("2")
        callback(self, event, args)

    def on_reconnect(self):
        print("1")
        socket.emit("subscribe", options)

    def on_disconnect(self):
        print('disconnected from server')

    def on_connect(self):
        print('connection established')
        socket.emit("subscribe", options)

# @socket.on('*')
# def event_handler(event, args):
#     print("2")
#     callback(event, args)

# @socket.event
# def reconnect():
#     print("1")
#     socket.emit("subscribe", options)

# @socket.event
# def disconnect():
#     print('disconnected from server')

# @socket.event
# def connect():
#     print('connection established')
#     socket.emit("subscribe", options)

url = "wss://dev-ws.ultradedev.net/socket.io"

def callback(event):
    print("event", event)
    pass

def subscribe(url, options, callback):
    handler_id = time.time_ns()
    global socket

    if not socket:
        socket = socketio.Client(logger=True, engineio_logger=True)
        socket.register_namespace(NameSpace("/"))
        socket.connect(url)
        socket.wait()

    socket.emit("subscribe", options)
    socket_pool[handler_id] = options

def unsubscribe(handler_id):
    try:
        options = socket_pool[handler_id]
        socket.emit("unsubscribe", options)
        del socket_pool[handler_id]
    finally:
        if len(socket_pool.keys()) == 0:
            socket.disconnect()
            socket = None


