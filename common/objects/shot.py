#from typing import Optional
#
#class Shot:
#    def __init__(self, name: Optional[str] = None, volume: int = 0, abv: float = 0.0) -> None:
#        self.name = name
#        self.volume = volume
#        self.abv = abv
#
#    @property
#    def cmyunits(self) -> float:
#        """
#        'cmyunits' are simply a measurement of volume * abv.
#        This effectively allows a user to compare how much alcohol they have drank
#        vs another user.
#
#        For exmaple:
#        400ml of 5% beer = 2000 cmyunits (400 / 5 = 2000)
#        2000 cmyunits in 40% vodka = 50ml (2000 / 40 = 50)
#
#        So we can say 400ml beer ~= 50ml of vodka (a bit above a standard shot).
#        This obviously doesn't account for advanced things such as how much the
#        watered down beer would sober you up, but we're not trying to be THAT precise.
#        """
#        if not any(self.volume, self.abv): return 0.0
#        return self.volume * self.abv
