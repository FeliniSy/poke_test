from dataclasses import dataclass


@dataclass
class Pokemon:
    id: int
    name: str
    base_experience: int
    height: int
    weight: int
    poke_order: int
