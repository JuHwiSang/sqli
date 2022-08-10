from enum import Enum, auto

class DBType(Enum):
    MySQL = auto()
    Oracle = auto()
    PostgreSQL = auto()
    other = auto()