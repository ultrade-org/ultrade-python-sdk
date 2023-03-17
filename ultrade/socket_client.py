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
        self.subscribe_options = {}

    def get_sub_options(self):
        options = {'options': self.subscribe_options["options"],
                   'symbol': self.subscribe_options["symbol"], 'streams': self.socket_controller.streams_pool}
        return options

    async def subscribe(self, options: SubscribeOptions, callback: Callable[[str, List[any]], any]):
        if not self.isConnectionExist:
            self.subscribe_options = options
            self.isConnectionExist = True
            self.socket = socketio.AsyncClient(
                reconnection_delay_max=1000, logger=True)

            sub_id = self.socket_controller.handle_subscribe(options, callback)
            self.add_event_listeners()
            await self.socket.connect(self.url, transports=["websocket"])

            return sub_id

        sub_id = self.socket_controller.handle_subscribe(options, callback)
        await self.socket.emit("subscribe", self.get_sub_options())
        return sub_id

    async def unsubscribe(self, handler_id: str):
        remaining_subscriptions = await self.socket_controller.handle_unsubscribe(self.socket, handler_id)

        if remaining_subscriptions == 0:
            self.isConnectionExist = False
            await self.socket.disconnect()
            self.socket = None

    def add_event_listeners(self):
        self.socket.on('*', self.socket_controller.callback_handler)

        async def reconnect_handler():
            await self.socket.emit("subscribe", self.get_sub_options())
        self.socket.on("reconnect", reconnect_handler)

        async def connect_handler():
            print('ws connection established')
            await self.socket.emit("subscribe", self.get_sub_options())
        self.socket.on("connect", connect_handler)


class SocketController():
    def __init__(self):
        self.options_pool: Optional[Dict[str, 'SubscribeOptions']] = {}
        self.callbacks_pool = {event: [(lambda *args: stream_value, stream_value)]
                               for event, stream_value in EVENT_LIST}
        self.streams_pool = []

    def event_from_stream(self, stream):
        for event in self.callbacks_pool:
            if self.callbacks_pool[event][0][1] == stream:
                return event

    def handle_subscribe(self, sub_options, callback):
        handler_id = str(time.time_ns())
        for opt in sub_options["streams"]:
            self.streams_pool.append(opt)
            self.callbacks_pool[self.event_from_stream(
                opt)].append((callback, handler_id))

        self.options_pool[handler_id] = sub_options

        return handler_id

    async def handle_unsubscribe(self, socket, handler_id):
        sub_options = self.options_pool[handler_id]
        for opt in sub_options["streams"]:
            event = self.event_from_stream(opt)
            self.callbacks_pool[event] = [
                elem for elem in self.callbacks_pool[event] if elem[1] != handler_id]

            if len(self.callbacks_pool[event]) < 2:
                self.streams_pool.remove(opt)
                await socket.emit("unsubscribe", [opt])

        del self.options_pool[handler_id], sub_options

        return len(self.options_pool.keys())

    async def callback_handler(self, event, args):
        coros = [self.make_async(callback_tuple[0], event, args)
                 for callback_tuple in self.callbacks_pool[event]]

        await asyncio.gather(*coros)

    async def make_async(self, func, *args):
        await asyncio.get_event_loop().run_in_executor(None, func, *args)
