import socketio
import time
from typing import Callable, Optional, TypedDict, Dict, List
from .constants import EVENT_LIST


class SubscribeOptions(TypedDict):
    symbol: str
    streams: List[int]
    options: Dict[str, any]


class SocketService():
    def __init__(self, url):
        self.subscribe_options = []
        self.socket: Optional[socketio.AsyncClient] = None
        self.url = url
        self.socket_pool: Optional[Dict[str, 'SubscribeOptions']] = {}
        self.isConnectionExist = False
        self.callbacks = {event: [] for event in EVENT_LIST}

    async def subscribe(self, options: SubscribeOptions, callback: Callable[[str, List[any]], any]):
        if not self.isConnectionExist:
            self.isConnectionExist = True
            self.socket = socketio.AsyncClient(reconnection_delay_max=1000)
            self.add_event_listeners()
            await self.socket.connect(self.url, transports=["websocket"])
            await self.socket.wait()

        handler_id = str(time.time_ns())

        await self.socket.emit("subscribe", options)
        self.socket_pool[handler_id] = {options, callback}

        return handler_id

    async def unsubscribe(self, handler_id: str):
        try:
            options = self.socket_pool[handler_id]
            await self.socket.emit("unsubscribe", options)
            del self.socket_pool[handler_id]
        finally:
            if len(self.socket_pool.keys()) == 0:
                await self.socket.disconnect()
                self.socket = None

    def add_event_listeners(self):
        self.socket.on('*', self.callback_handler)

        async def reconnect_handler():
            await self.socket.emit("subscribe", self.subscribe_options)
        self.socket.on("reconnect", reconnect_handler)

        async def connect_handler():
            print('ws connection established')
            await self.socket.emit("subscribe", self.subscribe_options)
        self.socket.on("connect", connect_handler)

    async def callback_handler():
        pass
