from typing import Optional, List

from common.objects.bottle import Bottle

class Inventory:
    def __init__(self, bottles: Optional[List[Bottle]] = None) -> None:
        self.bottles = bottles
        #self.finished_bottles: Optional[List[Bottle]] = None # maybe later

    @property
    def is_empty(self) -> bool: # cursed
        return not bool(len(self.bottles))

    def __repr__(self) -> None:
        if not len(self.bottles): return 'Your inventory is empty!\n'
        return '\n'.join(f'#{i + 1}. [{b.volume}ml @ {b.abv}%] {b.name} ' for i, b in enumerate(self.bottles))

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

    def get_bottle(self, i: int) -> Bottle:
        return self.bottles[i - 1] # Choice will be from list, so +1 (__repr__)
