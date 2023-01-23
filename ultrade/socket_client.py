import socketio
import time
from typing import Callable, Optional, TypedDict, Dict, List

socket: Optional[socketio.AsyncClient] = None
socket_pool: Optional[Dict[str, 'SubscribeOptions']] = {}


class SubscribeOptions(TypedDict):
    symbol: str
    streams: List[int]
    options: Dict[str, any]


async def subscribe(url: str, options: SubscribeOptions, callback: Callable[[str, List[any]], any]):
    handler_id = str(time.time_ns())
    global socket

    if not socket:
        socket = socketio.AsyncClient(reconnection_delay_max=1000)
        add_event_listeners(socket, options, callback)
        await socket.connect(url, transports=["websocket"])
        await socket.wait()

    await socket.emit("subscribe", options)
    socket_pool[handler_id] = options

    return handler_id


async def unsubscribe(handler_id: str):
    global socket
    try:
        options = socket_pool[handler_id]
        await socket.emit("unsubscribe", options)
        del socket_pool[handler_id]
    finally:
        if len(socket_pool.keys()) == 0:
            await socket.disconnect()
            socket = None


def add_event_listeners(socket: socketio.Client, options: SubscribeOptions, callback: Callable[[str, List[any]], any]):
    socket.on('*', callback)

    async def reconnect_handler():
        await socket.emit("subscribe", options)
    socket.on("reconnect", reconnect_handler)

    async def connect_handler():
        print('ws connection established')
        await socket.emit("subscribe", options)
    socket.on("connect", connect_handler)
