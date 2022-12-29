import socketio
import time
from typing import Callable, Optional

socket: Optional[socketio.Client] = None
socket_pool: Optional[dict[str, 'SubscribeOptions']] = {}

class SubscribeOptions():
    symbol: str
    streams: list[int]
    options: dict[str, any]

def subscribe(url: str, options: SubscribeOptions, callback: Callable[[str, list[any]], any]):
    handler_id = str(time.time_ns())
    global socket

    if not socket:
        socket = socketio.Client()
        add_event_listeners(socket, options, callback)
        socket.connect(url)

    socket.emit("subscribe", options)
    socket_pool[handler_id] = options

    return handler_id

def unsubscribe(handler_id: str):
    global socket
    try:
        options = socket_pool[handler_id]
        socket.emit("unsubscribe", options)
        del socket_pool[handler_id]
    finally:
        if len(socket_pool.keys()) == 0:
            socket.disconnect()
            socket = None

def add_event_listeners(socket: socketio.Client, options: SubscribeOptions, callback: Callable[[str, list[any]], any]):
    socket.on('*', callback)

    def reconnect_handler():
        socket.emit("subscribe", options)
    socket.on("reconnect",reconnect_handler)

    def connect_handler():
        print('ws connection established')
        socket.emit("subscribe", options)
    socket.on("connect", connect_handler)
