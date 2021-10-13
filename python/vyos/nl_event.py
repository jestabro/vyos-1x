import threading
from enum import IntEnum, auto
from typing import Callable

MAX_UINT = 2**32-1

class NL_Event(IntEnum):
    NOEVENT = 0
    NEWLINK = auto()
    DELLINK = auto()
    NEWADDR = auto()
    DELADDR = auto()

class NL_Message():
    event_actions: dict = {NL_Event.NOEVENT: []}
    lock = threading.Lock()
    def __init__(self, event=NL_Event.NOEVENT, ifname='', ifaddress='',
                 ifup=False, ifrunning=False, change_mask=MAX_UINT):
        self.event: NL_Event = event
        self.ifname: str = ifname
        self.ifaddress: str = ifaddress
        self.ifup: bool = ifup
        self.ifrunning: bool = ifrunning
        self.change_mask: int = change_mask
        self.text: str = ''

    @classmethod
    def add_action_on_event(cls, event: NL_Event, func: Callable):
        cls.lock.acquire()
        cls.event_actions.setdefault(event, []).append(func)
        cls.lock.release()

    @classmethod
    def del_action_on_event(cls, event: NL_Event, func: Callable):
        cls.lock.acquire()
        try:
            cls.event_actions.setdefault(event, []).remove(func)
        except ValueError:
            pass
        finally:
            cls.lock.release()

    def run_actions(self):
        self.lock.acquire()
        action_list = self.event_actions.get(self.event, [])
        for callback in action_list:
            callback()
        self.lock.release()

def action_on_event(event: NL_Event):
    def inner(f):
        def wrapped(*args, **kwargs):
            res = f(*args, **kwargs)
            return res
        NL_Message.add_action_on_event(event, f)
        return wrapped
    return inner

def no_action_on_event(event: NL_Event):
    def inner(f):
        def wrapped(*args, **kwargs):
            res = f(*args, **kwargs)
            return res
        NL_Message.del_action_on_event(event, f)
        return wrapped
    return inner
