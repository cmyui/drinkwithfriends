from typing import Optional, List

from common.objects.bottle import Bottle

class Inventory:
    def __init__(self, bottles: Optional[List[Bottle]] = None) -> None:
        self.bottles = bottles
        #self.finished_bottles: Optional[List[Bottle]] = None # maybe later

    def __repr__(self) -> None:
        return '\n'.join(f'[{b.volume}ml @ {b.abv}%] {b.name} ' for b in self.bottles)

    """ Add a bottle to inventory. """

    def __iadd__(self, other: Bottle) -> List[Bottle]:
        self.bottles.append(other)
        return self.bottles

    def __add__(self, other: Bottle) -> List[Bottle]:
        self.bottles.append(other)
        return self.bottles

    """ Remove a bottle from inventory. """

    def __isub__(self, other: Bottle) -> List[Bottle]:
        self.bottles.remove(other)
        return self.bottles

    def __sub__(self, other: Bottle) -> List[Bottle]:
        self.bottles.remove(other)
        return self.bottles
