import unittest

from nlglib.structures import MsgSpec, Message, Document
from nlglib.structures import String, Var, Clause, NounPhrase, VerbPhrase
from nlglib.macroplanning import StringMsg

from nlglib.lexicalisation import Lexicaliser

from nlglib.realisation.basic import Realiser


class DummyMsg(MsgSpec):
    def __init__(self):
        super().__init__('dummy')

    def arg_subject(self):
        return NounPhrase('Boris')


lex = Lexicaliser(templates={
    'dummy': Clause(Var('arg_subject'), 'is', 'fast')
})

realiser = Realiser()


class TestLexicalisation(unittest.TestCase):
    """ Tests for converting a MsgSpec into an NLG Element. """

    def test_string_msg(self):
        """ Test lexicalising a message with "canned text". """
        msg = StringMsg('this is some text')
        result = lex.msg_spec(msg)
        expected = Clause(subject='this is some text')
        self.assertEqual(expected, result)

    def test_lexicalise_msg_spec(self):
        """ Test lexicalisation of MsgSpec. """
        msg = DummyMsg()
        res = lex.msg_spec(msg)
        expected = list(Clause('Boris', 'is', 'fast').constituents())
        self.assertEqual(expected, list(res.constituents()))

    def test_lexicalise_msg(self):
        """ Test lexicalisation of Message. """
        # a message with 1 nuclei and 2 satellites
        m = Message('Elaboration', DummyMsg(), DummyMsg(), DummyMsg())
        lexicalised = lex.rhet_rel(m)
        tmp = list(lex.msg_spec(DummyMsg()).constituents())
        expected = tmp + tmp + tmp
        self.assertEqual(expected, list(lexicalised.constituents()))

    def test_lexicalise_document(self):
        """ Test lexicalisation of Document. """
        m1 = Message('Leaf', DummyMsg())
        m2 = Message('Elaboration', DummyMsg(), DummyMsg())
        s1 = Document(m1, title='Section One')
        s2 = Document(m2, title='Section Two')
        d = Document(s1, s2, title='Doc Title')
        tmp = lex.document(d)
        expected = 'Doc Title\n\n' + \
            'Section One' + \
            '\n\nBoris is fast.' + \
            '\n\nSection Two' + \
            '\n\nBoris is fast. Boris is fast.'
        actual = realiser(tmp)
        print(str(actual))
        print(repr(actual))
        self.assertEqual(expected, str(actual))


if __name__ == '__main__':
    unittest.main()
