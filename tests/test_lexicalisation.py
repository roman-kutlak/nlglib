import unittest

from nlglib.structures import MsgSpec, Message, Document
from nlglib.structures import String, Var, Clause, NounPhrase, VerbPhrase
from nlglib.macroplanning import StringMsgSpec

from nlglib.lexicalisation import templates
from nlglib.lexicalisation import lexicalise_message_spec
from nlglib.lexicalisation import lexicalise_message
from nlglib.lexicalisation import lexicalise_document

from nlglib.realisation.backends.simplenlg import realise as real


class DummyMsg(MsgSpec):
    def __init__(self):
        super().__init__('dummy')

    def arg_subject(self):
        return NounPhrase('Boris')

# add a template for the message spec.
templates.templates['dummy'] = Clause(Var('arg_subject'), 'is', 'fast')


class TestLexicalisation(unittest.TestCase):
    """ Tests for converting a MsgSpec into an NLG Element. """

    def test_string_msg(self):
        """ Test lexicalising a message with "canned text". """
        msg = StringMsgSpec('this is some text')
        res = lexicalise_message_spec(msg)
        expected = [String('this is some text')]
        result = list(res.constituents())
        self.assertEqual(expected, result)

    def test_lexicalise_msg_spec(self):
        """ Test lexicalisation of MsgSpec. """
        msg = DummyMsg()
        res = lexicalise_message_spec(msg)
        expected = [String('Boris'), String('is'), String('fast')]
        self.assertEqual(expected, list(res.constituents()))

    def test_lexicalise_msg(self):
        """ Test lexicalisation of Message. """
        # a message with 1 nuclei and 2 satellites
        m = Message('Elaboration', DummyMsg(), DummyMsg(), DummyMsg())
        lex = lexicalise_message(m)
        tmp = list(lexicalise_message_spec(DummyMsg()).constituents())
        expected = tmp + tmp + tmp
        self.assertEqual(expected, list(lex.constituents()))

    def test_lexicalise_document(self):
        """ Test lexicalisation of Document. """
        m1 = Message('Leaf', DummyMsg())
        m2 = Message('Elaboration', DummyMsg(), DummyMsg())
        p = Document(m1, m2)
        s = Document('Section One', Document(m1))
        d = Document('Doc Title', s, Document('Section Two', Document(m2)))
        tmp = lexicalise_document(d)
        expected = 'Doc Title\n' + \
            'Section One' + \
            '\n\tBoris is fast' + \
            '\n\nSection Two' + \
            '\n\tBoris is fast Boris is fast'
        actual = real(tmp)
        print(actual)
        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
