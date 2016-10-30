import unittest

from nlglib.lexicon import *


class TestLexicon(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        path = 'tests/data/nih_lexicon_extract.xml'
        cls.lexicon = lexicon_from_nih_xml(path)

    def test_nih_build(self):
        for w in self.lexicon.words:
            self.assertNotEqual(None, w.id)
            self.assertNotEqual('', w.id)

    def test_pos(self):
        tags = self.lexicon.pos_tags_for('house')
        self.assertEqual(True, POS_NOUN in tags)
        self.assertEqual(True, POS_VERB in tags)
        self.assertEqual(True, POS_ADJECTIVE in tags)

    def test_word(self):
        word = self.lexicon.word('house', POS_NOUN)
        self.assertIsNotNone(word)
        self.assertEqual('house', word.word)
        self.assertEqual(POS_NOUN, word.pos)
        self.assertNotEqual('', word.id)

        word = self.lexicon.word('walking')
        self.assertIsNotNone(word)
        self.assertEqual('walking', word.word)
        self.assertEqual('walk', word.base)
        self.assertEqual(POS_VERB, word.pos)
        self.assertNotEqual('', word.id)


regular = [('road', 'roads'),
           ('flower', 'flowers'),
           ('girl', 'girls')]

irregular = [('person', 'people'),
             ('child', 'children'),
             ('foot', 'feet'),
             ('woman', 'women'),
             ('goose', 'geese')]

testwords = [('berry', 'berries'),
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
             ('volcano', 'volcanoes')]

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
