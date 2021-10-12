
from enum import IntEnum, auto
from typing import Callable

class NL_Event(IntEnum):
    NOEVENT = 0
    NEWLINK = auto()
    DELLINK = auto()

class NL_Message():
    event_actions: dict = {NL_Event.NOEVENT: []}
    def __init__(self):
        self._event: NL_Event = NL_Event.NOEVENT
        self._ifname: str = ''
        self._ifaddress: str = ''
        self._ifup: bool = False
        self._ifrunning: bool = False

    @classmethod
    def add_action(cls, event: NL_Event, func: Callable):
        cls.event_actions[event].setdefault(event, []).append(func)

    def invoke_actions(self):
        for callback in self.event_actions[self._event]:
            callback(self)

def event_decorator(event: NL_Event):
    def inner(f):
        NL_Message.add_action(event, f)
        def wrapped(*args, **kwargs):
            res = f(*args, **kwargs)
            return res
        return wrapped
    return inner
