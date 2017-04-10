from enum import Enum


class ConferenceDay(Enum):
    workshops = 'workshops'
    day_1 = 'day_1'
    day_2 = 'day_2'
    day_3 = 'day_3'
    day_4 = 'day_4'


class SessionSlot(Enum):
    session_1 = 'session_1'
    session_2 = 'session_2'
    session_3 = 'session_3'


class QuickieSlot(Enum):
    slot_1 = 'slot_1'
    slot_2 = 'slot_2'
    slot_3 = 'slot_3'
    slot_4 = 'slot_4'


class Track(Enum):
    cpp = 'cpp'
    other = 'other'


class Room(Enum):
    bristol_suite = 'bristol_suite'
    bristol_1 = 'bristol_1'
    bristol_2 = 'bristol_2'
    bristol_3 = 'bristol_3'
    empire = 'empire'
    great_britain = 'great_britain'
    wallace = 'wallace'
