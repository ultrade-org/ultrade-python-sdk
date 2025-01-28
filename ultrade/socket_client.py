import socketio
import time
from typing import Callable, Optional, TypedDict, Dict, List
from .constants import EVENT_LIST
import asyncio


class SubscribeOptions(TypedDict):
    symbol: str
    streams: List[int]
    options: Dict[str, any]


class SocketClient:
    def __init__(self, url):
        self.socket: Optional[socketio.AsyncClient] = None
        self.url = url
        self.isConnectionExist = False
        self.socket_controller = SocketController()
        self.subscribe_options = {}

    def get_sub_options(self):
        options = {
            "options": self.subscribe_options["options"],
            "symbol": self.subscribe_options["symbol"],
            "streams": self.socket_controller.streams_pool,
        }
        return options

    async def subscribe(
        self, options: SubscribeOptions, callback: Callable[[str, List[any]], any]
    ):
        if (
            self.subscribe_options.get("symbol")
            and options["symbol"] != self.subscribe_options["symbol"]
        ):
            raise Exception("Socket client support only one pair per instance")

        if not self.isConnectionExist:
            self.subscribe_options = options
            self.isConnectionExist = True
            self.socket = socketio.AsyncClient(reconnection_delay_max=1000, logger=True)

            sub_id = self.socket_controller.handle_subscribe(options, callback)
            self.add_event_listeners()
            await self.socket.connect(self.url, transports=["websocket"])

            return sub_id

        sub_id = self.socket_controller.handle_subscribe(options, callback)

        return sub_id

    async def unsubscribe(self, handler_id: str):
        streams_to_unsubscribe = await self.socket_controller.handle_unsubscribe(
            handler_id
        )
        if len(streams_to_unsubscribe) > 0:
            options = self.get_sub_options()
            options["streams"] = streams_to_unsubscribe
            await self.socket.emit("unsubscribe", options)

        if len(self.get_sub_options()["streams"]) == 0:
            self.isConnectionExist = False
            await self.socket.disconnect()
            self.socket = None

    def add_event_listeners(self):
        self.socket.on("*", self.socket_controller.callback_handler)

        async def reconnect_handler():
            await self.socket.emit("subscribe", self.get_sub_options())

        self.socket.on("reconnect", reconnect_handler)

        async def connect_handler():
            await self.socket.emit("subscribe", self.get_sub_options())

        self.socket.on("connect", connect_handler)


class SocketController:
    def __init__(self):
        self.options_pool: Optional[Dict[str, "SubscribeOptions"]] = {}
        self.callbacks_pool = {
            event: [(lambda *args: stream_value, stream_value)]
            for event, stream_value in EVENT_LIST
        }
        self.streams_pool = []

    def event_from_stream(self, stream):
        matching_events = []
        for event in self.callbacks_pool:
            if self.callbacks_pool[event][0][1] == stream:
                matching_events.append(event)
        return matching_events

    def handle_subscribe(self, sub_options, callback):
        handler_id = str(time.time_ns())
        for opt in sub_options["streams"]:
            if opt not in self.streams_pool:
                self.streams_pool.append(opt)
            events = self.event_from_stream(opt)
            for event in events:
                self.callbacks_pool[event].append((callback, handler_id))

        self.options_pool[handler_id] = sub_options

        return handler_id

    async def handle_unsubscribe(self, handler_id):
        if handler_id not in self.options_pool:
            print(f"Warning: No subscription found for handler ID {handler_id}")
            return []
        sub_options = self.options_pool[handler_id]
        streams_to_delete = []
        for opt in sub_options["streams"]:
            events = self.event_from_stream(opt)
            for event in events:
                self.callbacks_pool[event] = [
                    elem for elem in self.callbacks_pool[event] if elem[1] != handler_id
                ]

                if len(self.callbacks_pool[event]) < 2:
                    self.streams_pool.remove(opt)
                    streams_to_delete.append(opt)

        del self.options_pool[handler_id], sub_options

        return streams_to_delete

    async def callback_handler(self, event, args, id=None):
        if event not in self.callbacks_pool:
            print(f"Warning: No callbacks found for event {event}")
            print(f"Event: {event}. Args: {args}")
            return

        coros = [
            self.make_async(callback_tuple[0], event, args)
            for callback_tuple in self.callbacks_pool[event]
        ]

        await asyncio.gather(*coros)

    async def make_async(self, func, *args):
        await asyncio.get_event_loop().run_in_executor(None, func, *args)
