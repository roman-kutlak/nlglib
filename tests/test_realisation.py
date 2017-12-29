import unittest

from nlglib.microplanning import *
from nlglib.macroplanning import *
from nlglib.realisation.basic import Realiser, RealisationVisitor


def get_clause():
    clause = Clause(NounPhrase(Word('you', 'NOUN')),
                    VerbPhrase(Word('say', 'VERB'), String('hello')))
    return clause


def get_test_doc():
    m1 = RhetRel('Leaf', Clause(String('hello'), None))
    c = get_clause()
    c.features['FORM'] = "IMPERATIVE"
    m2 = RhetRel('Elaboration', c)
    para = Document(None, m1, m2)
    return para


class TestRealiser(unittest.TestCase):

    def test_simple(self):
        realiser = Realiser()
        text = realiser(get_clause())
        expected = 'You say hello.'
        self.assertEqual(expected, text)

    def test_complex(self):
        c = get_clause()

        realiser = Realiser()
        text = realiser.realise(c)
        expected = 'You say hello.'
        self.assertEqual(expected, text)

        c.features['FORM'] = "IMPERATIVE"

        text = realiser.realise(c)
        expected = 'Say hello.'
        # TODO: implement imperative in simple realisation?
        # self.assertEqual(expected, text)

        text = realiser.realise(get_test_doc())
        expected = Document(None, 'Hello.', 'You say hello.')
        self.assertEqual(expected, text)


class TestStringRealisation(unittest.TestCase):

    def test_string(self):
        v = RealisationVisitor()
        s = String('hello')
        expected = 'hello'
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_word(self):
        v = RealisationVisitor()
        s = Word('house', 'NOUN')
        expected = 'house'
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

        v = RealisationVisitor()
        s = Word('house', 'NOUN', {'NUMBER': 'PLURAL'})
        expected = 'houses'
        s.accept(v)
        actual = str(v)
        # TODO: implement pluralisation?
        # self.assertEqual(expected, actual)

    def test_var(self):
        v = RealisationVisitor()
        s = Var(0, 'truck1')
        expected = 'truck1'
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_coordination(self):
        w1 = Word('truck', 'NOUN')
        w2 = Word('car', 'NOUN')
        w3 = Word('motorbike', 'NOUN')

        v = RealisationVisitor()
        expected = ''
        s = Coordination()
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

        v = RealisationVisitor()
        expected = 'truck'
        s = Coordination(w1)
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

        v = RealisationVisitor()
        expected = 'truck and car'
        s = Coordination(w1, w2)
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

        v = RealisationVisitor()
        expected = 'truck, car and motorbike'
        s = Coordination(w1, w2, w3)
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_clause(self):
        v = RealisationVisitor()
        c = Clause(Word('Peter', 'NOUN'),
                   Word('run', 'VERB'))
        expected = 'Peter run'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

        v = RealisationVisitor()
        c = Clause(Word('Peter', 'NOUN'),
                   Word('run', 'VERB'),
                   front_modifiers=[String('yesterday')])
        expected = 'yesterday Peter run'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

        v = RealisationVisitor()
        c = Clause(Word('Peter', 'NOUN'),
                   Word('run', 'VERB'),
                   front_modifiers=[String('yesterday')],
                   postmodifiers=[String('abundantly')])
        expected = 'yesterday Peter run abundantly'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

        v = RealisationVisitor()
        c = Clause(Word('Peter', 'NOUN'),
                   Word('run', 'VERB'),
                   front_modifiers=['yesterday'],
                   postmodifiers=['abundantly'])
        expected = 'yesterday Peter run abundantly'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_np(self):
        v = RealisationVisitor()
        c = NounPhrase(Word('house', 'NOUN'),
                       Word('this', 'DETERMINER'))
        expected = 'this house'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

        v = RealisationVisitor()
        c = NounPhrase(Word('house', 'NOUN'),
                       Word('this', 'DETERMINER'),
                       premodifiers=['tall', 'yellow'],
                       postmodifiers=['that we lived in'])
        expected = 'this tall yellow house that we lived in'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_vp(self):
        v = RealisationVisitor()
        c = VerbPhrase(Word('hit', 'VERB'),
                       String('the ball'),
                       String('with the bat'))
        expected = 'hit the ball with the bat'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

        v = RealisationVisitor()
        c = VerbPhrase(Word('hit', 'VERB'),
                       NounPhrase(Word('ball', 'NOUN'), 'the'),
                       String('with the bat'))
        expected = 'hit the ball with the bat'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_pp(self):
        v = RealisationVisitor()
        c = PrepositionPhrase(Word('in', 'PREPOSITION'),
                              String('the house'))
        expected = 'in the house'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

        v = RealisationVisitor()
        c = PrepositionPhrase(Word('in', 'PREPOSITION'),
                              NounPhrase(Word('house', 'NOUN'), Word('the', 'DETERMINER')))
        expected = 'in the house'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_adjp(self):
        v = RealisationVisitor()
        c = AdjectivePhrase(Word('green', 'ADJECTIVE'))
        expected = 'green'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_advp(self):
        v = RealisationVisitor()
        c = AdverbPhrase(Word('rarely', 'ADVERB'))
        expected = 'rarely'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_complex(self):
        house = NounPhrase('house', 'the')
        shopping = NounPhrase('shopping', 'the')
        put = VerbPhrase('put', shopping, PrepositionPhrase('in', house))
        s = Clause(NounPhrase('Peter'), put)
        expected = 'Peter put the shopping in the house'
        v = RealisationVisitor()
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)


# main
if __name__ == '__main__':
    unittest.main()
