import unittest
import time
import sys

import nlg.realisation as realisation
from nlg.structures import *
import nlg.simplenlg as snlg
from nlg.utils import get_user_settings


def get_clause():
    clause = Clause(NP(Word('you', 'NOUN')),
                    VP(Word('say', 'VERB'), String('hello')))
    return clause


def get_test_doc():
    m1 = Message('Leaf', Clause(String('hello'), None))
    c = get_clause()
    c._features['FORM'] = "IMPERATIVE"
    m2 = Message('Elaboration', c)
    para = Paragraph(m1, m2)
    return para


class TestRealiser(unittest.TestCase):
    def test_simple(self):
        text = realisation.realise(get_clause())
        expected = 'you say hello'
        self.assertEqual(expected, text)

    def test_complex(self):
        c = get_clause()

        if realisation.default_server is None:
            raise ServerError('Realiser received an empty ')

        realiser = realisation.Realiser()
        text = realiser.realise(c)
        expected = 'You say hello.'
        self.assertEqual(expected, text)

        c._features['FORM'] = "IMPERATIVE"

        text = realiser.realise(c)
        expected = 'Say hello.'
        self.assertEqual(expected, text)

        text = realiser.realise(get_test_doc())
        expected = Paragraph('Hello.', 'Say hello.')
        self.assertEqual(expected, text)
