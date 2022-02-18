# encoding: utf-8

"""Definition of the french Lexicon."""



from .lexicon import Lexicon
from .lang import FRENCH
from .feature.category import CONJUNCTION


class FrenchLexicon(Lexicon):

    """Lexicon defining specific rules for the french language."""

    language = FRENCH

    @property
    def conjunction_coordination(self):
        return self.first('et', category=CONJUNCTION)
