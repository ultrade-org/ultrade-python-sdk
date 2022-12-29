import socketio
import time

socket: socketio.Client = None
socket_pool = {}

def subscribe(url, options, callback):
    handler_id = str(time.time_ns())
    global socket

    if not socket:
        socket = socketio.Client()
        add_event_listeners(socket, options, callback)
        socket.connect(url)

    socket.emit("subscribe", options)
    socket_pool[handler_id] = options

    return handler_id

def unsubscribe(handler_id):
    global socket
    try:
        options = socket_pool[handler_id]
        socket.emit("unsubscribe", options)
        del socket_pool[handler_id]
    finally:
        if len(socket_pool.keys()) == 0:
            socket.disconnect()
            socket = None

def add_event_listeners(socket, options, callback):
    socket.on('*', callback)

    def reconnect_handler():
        socket.emit("subscribe", options)
    socket.on("reconnect",reconnect_handler)

    def connect_handler():
        print('ws connection established')
        socket.emit("subscribe", options)
    socket.on("connect", connect_handler)
