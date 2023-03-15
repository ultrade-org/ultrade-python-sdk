import socketio
import time
from typing import Callable, Optional, TypedDict, Dict, List

socket_pool: Optional[Dict[str, 'SubscribeOptions']] = {}


class SubscribeOptions(TypedDict):
    symbol: str
    streams: List[int]
    options: Dict[str, any]


class SocketService():
    def __init__(self, url):
        self.subscribe_options = []
        self.socket = socketio.AsyncClient(reconnection_delay_max=1000)
        self.url = url
        pass

    async def subscribe(self, options: SubscribeOptions, callback: Callable[[str, List[any]], any]):
        handler_id = str(time.time_ns())
        self.add_event_listeners(options, callback)
        await self.socket.connect(self.url, transports=["websocket"])
        await self.socket.wait()

        await self.socket.emit("subscribe", options)
        socket_pool[handler_id] = options

        return handler_id

    async def unsubscribe(self, handler_id: str):
        options = socket_pool[handler_id]
        await self.socket.emit("unsubscribe", options)
        del socket_pool[handler_id]

    def add_event_listeners(self, options: SubscribeOptions, callback: Callable[[str, List[any]], any]):
        self.socket.on('*', callback)

        async def reconnect_handler():
            await self.socket.emit("subscribe", options)
        self.socket.on("reconnect", reconnect_handler)

        async def connect_handler():
            print('ws connection established')
            await self.socket.emit("subscribe", options)
        self.socket.on("connect", connect_handler)
