
from enum import IntEnum, auto
from typing import Callable

class NL_Event(IntEnum):
    NOEVENT = 0
    NEWLINK = auto()
    DELLINK = auto()

class NL_Message():
    event_actions: dict = {NL_Event.NOEVENT: []}
    def __init__(self, event=NL_Event.NOEVENT, ifname='', ifaddress='',
                 ifup=False, ifrunning=False):
        self.event: NL_Event = event
        self.ifname: str = ifname
        self.ifaddress: str = ifaddress
        self.ifup: bool = ifup
        self.ifrunning: bool = ifrunning
        self.text: str = ''

    @classmethod
    def add_action(cls, event: NL_Event, func: Callable):
        cls.event_actions.setdefault(event, []).append(func)

    def invoke_actions(self):
        action_list = self.event_actions.get(self.event, [])
        for callback in action_list:
            callback()

def event_decorator(event: NL_Event):
    def inner(f):
        def wrapped(*args, **kwargs):
            res = f(*args, **kwargs)
            return res
        NL_Message.add_action(event, f)
        return wrapped
    return inner
