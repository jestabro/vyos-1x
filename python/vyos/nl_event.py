# Copyright 2021 VyOS maintainers and contributors <maintainers@vyos.io>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

import threading
from enum import IntEnum, auto
from typing import Callable

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
                 ifup=False, ifrunning=False, ifup_changed=False,
                 ifrunning_changed=False):
        self.event: NL_Event = event
        self.ifname: str = ifname
        self.ifaddress: str = ifaddress
        self.ifup: bool = ifup
        self.ifrunning: bool = ifrunning
        self.ifup_changed: bool = ifup_changed
        self.ifrunning_changed: bool = ifrunning_changed
        self.text: str = ''

    @classmethod
    def add_action_on_event(cls, event: NL_Event, func: Callable):
        with cls.lock:
            cls.event_actions.setdefault(event, []).append(func)

    @classmethod
    def del_action_on_event(cls, event: NL_Event, func: Callable):
        with cls.lock:
            try:
                cls.event_actions.setdefault(event, []).remove(func)
            except ValueError:
                pass

    def run_actions(self):
        with self.lock:
            action_list = self.event_actions.get(self.event, [])
            for callback in action_list:
                callback()

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
