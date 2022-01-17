from dataclasses import dataclass
from typing import List

@dataclass
class DataUnit:
    x: int
    y: int
    hp: int
    speed: int
    minreach: int
    maxreach: int
    weapon: str
    armor: List[str]
    formation: str
    uclass: str

@dataclass
class DataPlayer:
    uid: int
    units: List[DataUnit]

@dataclass
class DataRegister:
    uid: int

@dataclass
class DataAttack:
    attacker: DataUnit
    defender: DataUnit

@dataclass
class DataMove:
    mover: DataUnit
    x: int
    y: int

@dataclass
class DataGame:
    turn: int
    players: List[DataPlayer]
