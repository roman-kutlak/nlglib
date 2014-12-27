import unittest

from nlg.lexicon import *

regular = [ ('road', 'roads'),
            ('flower', 'flowers'),
            ('girl', 'girls') ]

irregular = [ ('person', 'people'),
              ('child', 'children'),
              ('foot', 'feet'),
              ('woman', 'women'),
              ('goose', 'geese') ]

testwords = [ ('berry', 'berries'),
              ('activity', 'activities'),
              ('daisy', 'daisies'),
              ('church', 'churches'),
              ('bus', 'buses'),
              ('fox', 'foxes'),
              ('stomach', 'stomachs'),
              ('epoch', 'epochs'),
              ('knife', 'knives'),
              ('half', 'halves'),
              ('scarf', 'scarves'),
              ('chief', 'chiefs'),
              ('spoof', 'spoofs'),
              ('solo', 'solos'),
              ('zero', 'zeros'),
              ('avocado', 'avocados'),
              ('studio', 'studios'),
              ('zoo', 'zoos'),
              ('embryo', 'embryos'),
              ('buffalo', 'buffaloes'),
              ('domino', 'dominoes'),
              ('echo', 'echoes'),
              ('embargo', 'embargoes'),
              ('hero', 'heroes'),
              ('mosquito', 'mosquitoes'),
              ('potato', 'potatoes'),
              ('tomato', 'tomatoes'),
              ('torpedo', 'torpedoes'),
              ('veto', 'vetoes'),
              ('banjo', 'banjoes'),
              ('cargo', 'cargoes'),
              ('flamingo', 'flamingoes'),
              ('fresco', 'frescoes'),
              ('ghetto', 'ghettoes'),
              ('halo', 'haloes'),
              ('mango', 'mangoes'),
              ('memento', 'mementoes'),
              ('motto', 'mottoes'),
              ('tornado', 'tornadoes'),
              ('tuxedo', 'tuxedoes'),
              ('volcano', 'volcanoes') ]

class TestPluralisation(unittest.TestCase):

    def test_regular(self):
        for word, expected in regular:
            actual = pluralise_noun(word)
            self.assertEqual(expected, actual)

    def test_irregular(self):
        for word, expected in irregular:
            actual = pluralise_noun(word)
            self.assertEqual(expected, actual)

    def test_random(self):
        for word, expected in testwords:
            actual = pluralise_noun(word)
            self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
