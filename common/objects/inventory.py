from typing import Optional, List
from random import randint

from common.objects.bottle import Bottle

from colorama import init as clr_init, Fore as colour
clr_init(autoreset=True)

class BottleCollection:
    def __init__(self, name: str = None, bottles: Optional[List[Bottle]] = []) -> None:
        self.name = name
        self.bottles = bottles

        self.unit: str = 'bottles' # SHIT design
        #self.finished_bottles: Optional[List[Bottle]] = None # maybe later

    @property
    def is_empty(self) -> bool: # cursed
        return not len(self.bottles)

    #def __repr__(self) -> None:
    #    if not len(self.bottles): return 'Your inventory is empty!\n'
    #    return '\n'.join(f'#{i + 1}. [{b.volume}ml @ {b.abv}%] {b.name} ' for i, b in enumerate(self.bottles))

    def display(self) -> None:
        print(
            f'{colour.GREEN}{self.name}',
            '=========', sep='\n'
        )
        if not self.bottles:
            print(f'You have no {self.unit} to display!')
            return
        print('\n'.join(f'#{i + 1} - [{b.volume}ml @ {b.abv}%] {b.name}' for i, b in enumerate(self.bottles)))
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
