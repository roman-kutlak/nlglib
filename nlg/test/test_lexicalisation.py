import unittest

from nlg.structures import MsgSpec, Message, String, PlaceHolder, Clause, NP, VP

from nlg.lexicalisation import templates
from nlg.lexicalisation import lexicalise_message_spec, lexicalise_message


class DummyMsg(MsgSpec):
    def __init__(self):
        super().__init__('dummy')

    def arg_subject(self):
        return NP('Boris')

# add a template for the message spec.
templates.templates['dummy'] = Clause(
            PlaceHolder('arg_subject'), VP('is', 'fast'))

class TestLexicalisation(unittest.TestCase):
    """ Tests for converting a MsgSpec into an NLG Element. """

    def test_lexicalise_msg_spec(self):
        """ Test lexicalisation of MsgSpec. """
        msg = DummyMsg()
        res = lexicalise_message_spec(msg)
        expected = [String('Boris'), String('is'), String('fast')]
        self.assertEqual(expected, list(res.constituents()))

    def test_lexicalise_msg(self):
        """ Test lexicalisation of Message. """
        # a message with 1 nucleus and 2 satelites
        m = Message('Elaboration', DummyMsg(), DummyMsg(), DummyMsg())
        lex = lexicalise_message(m)
        tmp = list(lexicalise_message_spec(DummyMsg()).constituents())
        expected = tmp + tmp + tmp
        self.assertEqual(expected, list(lex.constituents()))



if __name__ == '__main__':
    unittest.main()
