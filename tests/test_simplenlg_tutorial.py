import logging
import unittest

from nlglib.features import category, NUMBER, GENDER, TENSE, ASPECT, NEGATED
from nlglib.microplanning import *
from nlglib.macroplanning import Document, Paragraph
from nlglib.realisation.simplenlg import Realiser


class TestSimplenlgTutorial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.realiser = Realiser(host='roman.kutlak.info')

    def test_tense(self):
        expected = 'Mary chases the monkey.'
        c = Clause('Mary', 'chase', 'the monkey')
        actual = self.realiser(c)
        self.assertEqual(expected, actual)
        expected = 'Mary chased the monkey.'
        c[TENSE] = TENSE.past
        actual = self.realiser(c)
        self.assertEqual(expected, actual)
        expected = 'Mary will chase the monkey.'
        c[TENSE] = TENSE.future
        actual = self.realiser(c)
        self.assertEqual(expected, actual)

    def test_negation(self):
        expected = 'Mary does not chase the monkey.'
        c = Clause('Mary', 'chase', 'the monkey')
        c[NEGATED] = NEGATED.true
        actual = self.realiser(c)
        self.assertEqual(expected, actual)

    def test_interrogative(self):
        expected = 'Does Mary chase the monkey?'
        c = Clause('Mary', 'chase', 'the monkey')
        c['INTERROGATIVE_TYPE'] = 'YES_NO'
        actual = self.realiser(c)
        self.assertEqual(expected, actual)
        expected = 'Who does Mary chase?'
        c['INTERROGATIVE_TYPE'] = 'WHO_OBJECT'
        actual = self.realiser(c)
        self.assertEqual(expected, actual)

    def test_complements(self):
        expected = 'Mary chases the monkey very quickly despite her exhaustion.'
        c = Clause('Mary', 'chase', 'the monkey',
                   complements=['very quickly', 'despite her exhaustion'])
        actual = self.realiser(c)
        self.assertEqual(expected, actual)

    def test_modifiers(self):
        expected = 'Fast Mary chases the monkey.'
        subject = NP('Mary')
        verb = VP('chase')
        objekt = NP('the', 'monkey')
        subject += Adjective('fast')
        c = Clause(self)
        c.subject = subject
        c.predicate = verb
        c.object = objekt
        actual = self.realiser(c)
        self.assertEqual(expected, actual)
        expected = 'Fast Mary quickly chases the monkey.'
        verb += Adverb('quickly')
        c = Clause(subject, verb, objekt)
        actual = self.realiser(c)
        self.assertEqual(expected, actual)

    def test_coordinations(self):
        expected = 'Mary and it giraffe chase the monkey.'
        subject1 = NP('Mary')
        subject2 = NP('your', 'giraffe')
        subj1 = Coordination(subject1, subject2)
        subj2 = CC(subject1, subject2)
        assert subj1 == subj2
        c = Clause(subj1, VP('chase'), NP('the', 'monkey'))
        actual = self.realiser(c)
        self.assertEqual(expected, actual)
        expected = 'Mary and your giraffe chase the monkey, George and Martha.'
        subject1 = NP('Mary')
        subject2 = NP('your giraffe')
        subj = subject1 + subject2
        obj = NP('the monkey') + NP('George')
        obj += NP('Martha')
        c = Clause(subj, VP('chase'), obj)
        actual = self.realiser(c)
        self.assertEqual(expected, actual)
        expected = 'Mary and your giraffe chase the monkey, George or Martha.'
        obj.conj = 'or'
        actual = self.realiser(c)
        self.assertEqual(expected, actual)

    def test_prepositional_phrase(self):
        expected = 'Mary chases the monkey in the park.'
        c = Clause('Mary', 'chase', 'the monkey')
        c.complements += PP('in', 'the park')
        actual = self.realiser(c)
        self.assertEqual(expected, actual)
        c = Clause('Mary', 'chase', 'the monkey')
        c.complements += PP('in', NP('the', 'park'))
        actual = self.realiser(c)
        self.assertEqual(expected, actual)

    def test_coordinated_clause(self):
        expected = 'My cat liked fish.'
        s1 = Clause('my cat', 'like', 'fish', features={'TENSE': 'PAST'})
        s2 = Clause('my dog', 'like', 'big bones', features=[TENSE.present])
        s3 = Clause('my horse', 'like', 'grass', features=[TENSE.future])
        actual = self.realiser(s1)
        self.assertEqual(expected, actual)
        expected = 'My dog likes big bones.'
        actual = self.realiser(s2)
        self.assertEqual(expected, actual)
        expected = 'My horse will like grass.'
        actual = self.realiser(s3)
        self.assertEqual(expected, actual)
        expected = 'my cat liked fish and my dog likes big bones'
        actual = self.realiser(s1 + s2)
        self.assertEqual(expected, actual)
        expected = 'my cat liked fish and my dog likes big bones and my horse will like grass'
        c1 = CC(s1, s2, s3)
        actual = self.realiser(c1)
        self.assertEqual(expected, actual)
        # alternate syntax
        c2 = s1 + s2 + s3
        actual = self.realiser(c2)
        self.assertEqual(expected, actual)

    def test_subordinate_clause(self):
        expected = 'I am happy because I ate fish.'
        p = Clause("I", "be", "happy")
        q = Clause("I", "eat", "fish")
        q['COMPLEMENTISER'] = "because"
        q['TENSE'] = 'PAST'
        p.complements += q
        actual = self.realiser(p)
        self.assertEqual(expected, actual)

    def test_paragraph(self):
        p1 = Clause('Mary', 'chase', 'the monkey')
        p2 = Clause(NP('the', 'monkey'), 'fight', 'back')
        p3 = Clause('Mary', 'be', 'nervous')
        paragraph = Paragraph(p1, p2, p3)
        expected = 'Mary chases the monkey. The monkey fights back. Mary is nervous.'
        actual = self.realiser(paragraph)
        self.assertEqual(expected, str(actual))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()
