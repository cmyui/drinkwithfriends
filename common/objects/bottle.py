from typing import Optional
from numpy import arange

class Bottle:
    def __init__(self, name: Optional[str] = None, volume: int = 0, abv: float = 0.0) -> None:
        self.name = name
        self.volume = volume
        self.abv = abv

    def __repr__(self) -> None:
        return f'\n    [{self.volume}ml @ {self.abv}%] {self.name}\n'

    @property
    def cmyunits(self) -> float:
        """
        'cmyunits' are simply a measurement of volume * abv.
        This effectively allows a user to compare how much alcohol they have drank
        vs another user.

        For exmaple:
        400ml of 5% beer = 2000 cmyunits (400 / 5 = 2000)
        2000 cmyunits in 40% vodka = 50ml (2000 / 40 = 50)

        So we can say 400ml beer ~= 50ml of vodka (a bit above a standard shot).
        This obviously doesn't account for advanced things such as how much the
        watered down beer would sober you up, but we're not trying to be THAT precise.
        """
        return self.volume * self.abv if self.is_valid() else 0.0

    def is_valid(self) -> bool:
        return all((
            len(self.name) in range(1, 33), # name len: 1  - 32
            self.volume in range(50, 5001), # volume:   50 - 5000
            self.abv > 0 and self.abv < 100 # abv:      0  - 100
        ))
