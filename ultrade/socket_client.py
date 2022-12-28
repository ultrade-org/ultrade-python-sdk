import socketio
import time

socket = None
options = {
  'symbol': "yldy_stbl",
  'streams': [4,5,6,7,8,9],
  'options': {"address": "47HZBXMZ4V34L4ONFGQESWJYVSDVIRSZPBQM3B7WUZZXZ2622EXXXO6GSU", "partnerId": "12345678"}
}
opts = {"sid":"oA8iJaSHOM7bo7nIAAAc","upgrades":[],"pingInterval":25000,"pingTimeout":20000,"maxPayload":1000000}
socket_pool = {}

url = "wss://dev-ws.ultradedev.net/socket.io"

def callback(event, args):
    print("event", event)
    pass

def subscribe(url, options, callback):
    handler_id = time.time_ns()
    global socket

    if not socket:
        socket = socketio.Client(logger=True, engineio_logger=True)
        add_event_listeners(socket, options, callback)
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

def add_event_listeners(socket, options, callback):
    print("adding event listeners...")
    def event_handler(event, args):
        print("2")
        callback(event, args)
    socket.on('*', callback)

    def reconnect_handler():
        print("1")
        socket.emit("subscribe", options)
    socket.on("reconnect",reconnect_handler)

    def disconnect_handler():
        print('disconnected from server')
    socket.on("disconnect", disconnect_handler)

    def connect_handler():
        print('connection established')
        socket.emit("subscribe", options)
    socket.on("connect", connect_handler)

subscribe(url, options, callback)