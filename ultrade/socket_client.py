import socketio
import time
from typing import Callable, Optional, TypedDict, Dict, List
from .constants import EVENT_LIST
import asyncio


class SubscribeOptions(TypedDict):
    symbol: str
    streams: List[int]
    options: Dict[str, any]


class SocketClient():
    def __init__(self, url):
        self.socket: Optional[socketio.AsyncClient] = None
        self.url = url
        self.isConnectionExist = False
        self.socket_controller = SocketController()

    async def subscribe(self, options: SubscribeOptions, callback: Callable[[str, List[any]], any]):
        if not self.isConnectionExist:
            self.isConnectionExist = True
            self.socket = socketio.AsyncClient(reconnection_delay_max=1000)
            self.add_event_listeners()
            print("3")
            await self.socket.connect(self.url, transports=["websocket"])
            print("4")

        await self.socket.emit("subscribe", options)

        self.socket_controller.handle_subscribe(options, callback)
        print("qq")
        return

    async def unsubscribe(self, handler_id: str):
        remaining_subscriptions = await self.socket_controller.handle_unsubscribe(self.socket, handler_id)

        if remaining_subscriptions == 0:
            self.isConnectionExist = False
            await self.socket.disconnect()
            self.socket = None

    def add_event_listeners(self):
        self.socket.on('*', self.socket_controller.callback_handler)

        async def reconnect_handler():
            await self.socket.emit("subscribe", self.socket_controller.subscribe_options)
        self.socket.on("reconnect", reconnect_handler)

        async def connect_handler():
            print('ws connection established')
            await self.socket.emit("subscribe", self.socket_controller.subscribe_options)
        self.socket.on("connect", connect_handler)


class SocketController():
    def __init__(self):
        self.subscribe_options = {
            'symbol': "yldy_stbl",
            'streams': [1, 2, 3, 5, 6],
            'options': {"address": "your wallet address here"}
        }
        # self.subscribe_options = []
        self.options_pool: Optional[Dict[str, 'SubscribeOptions']] = {}
        self.callbacks_pool = {event: [(lambda: stream_value, stream_value)]
                               for event, stream_value in EVENT_LIST}

    def event_from_stream(self, stream):
        print("stream", stream)
        for event in self.callbacks_pool:
            if self.callbacks_pool[event][0][1] == stream:
                return event

    def handle_subscribe(self, sub_options, callback):
        handler_id = str(time.time_ns())
        print("1")
        for opt in sub_options["streams"]:
            self.callbacks_pool[self.event_from_stream(
                opt)].append((callback, handler_id))

        self.options_pool[handler_id] = sub_options

        return handler_id

    async def handle_unsubscribe(self, socket, handler_id):
        options = self.options_pool[handler_id]
        for opt in options:
            event = self.event_from_stream(opt)
            self.callbacks_pool[event] = filter(
                lambda elem: elem[1] is not handler_id, self.callbacks_pool[event])
            if len(self.callbacks_pool[event]) < 2:
                await socket.emit("unsubscribe", [opt])

        del self.options_pool[handler_id], options

        return len(self.options_pool.keys())

    async def callback_handler(self, event, args):
        print("handler", event)
        coros = [callback_tuple[0](event, args)
                 for callback_tuple in self.callbacks_pool[event]]
        await asyncio.gather(*coros)
