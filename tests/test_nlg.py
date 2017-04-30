import unittest

from nlglib.pipeline import Pipeline
from nlglib.structures import *
from nlglib.macroplanning import StringMsgSpec


def get_clause():
    clause = Clause(NounPhrase(Word('you', 'NOUN')),
                    VerbPhrase(Word('say', 'VERB'), String('hello')))
    clause._features['FORM'] = "IMPERATIVE"
    return clause


def get_test_doc():
    m1 = Message('Leaf', Clause(String('hello'), String('')))
    m2 = Message('Elaboration', get_clause())
    para = Paragraph(m1, m2)
    return para


class TestNlg(unittest.TestCase):
    def test_realisation(self):
        gen = Pipeline(__name__)
        para = get_test_doc()
        result = gen.process(para)
        expected = '    Hello. You say hello.'
        self.assertEqual(expected, result)

    def test_realisation2(self):
        gen = Pipeline(__name__)
        result = gen.process(get_clause())
        expected = 'Say hello.'
        self.assertEqual(expected, result)

        result = gen.process(get_test_doc())
        expected = '    Hello. Say hello.'
        self.assertEqual(expected, result)

    def test_string_msg(self):
        msg = StringMsgSpec('This is some text.')
        gen = Pipeline(__name__)
        result = gen.process(msg)
        expected = 'This is some text.'
        self.assertEqual(expected, result)
