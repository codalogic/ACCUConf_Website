from enum import Enum


class ConferenceDay(Enum):
    workshops = 'Workshops Day'
    day_1 = 'Day 1'
    day_2 = 'Day 2'
    day_3 = 'Day 3'
    day_4 = 'Day 4'


class SessionSlot(Enum):
    session_1 = 'Session 1'
    session_2 = 'Session 2'
    session_3 = 'Session 3'


class QuickieSlot(Enum):
    slot_1 = 'Slot 1'
    slot_2 = 'Slot 2'
    slot_3 = 'Slot 3'
    slot_4 = 'Slot 4'


class Track(Enum):
    cpp = 'C++'
    other = 'other'


class Room(Enum):
    bristol_suite = 'Bristol Suite'
    bristol_1 = 'Bristol 1'
    bristol_2 = 'Bristol 2'
    bristol_3 = 'Briostol 3'
    empire = 'Empire Suite'
    great_britain = 'SS Great Britain Suite'



