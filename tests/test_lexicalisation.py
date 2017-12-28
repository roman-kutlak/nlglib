import unittest

from nlglib.macroplanning import MsgSpec, RhetRel, Document, StringMsg
from nlglib.microplanning import Var, Clause, NounPhrase

from nlglib.lexicalisation import Lexicaliser

from nlglib.realisation.basic import Realiser


class DummyMsg(MsgSpec):
    def __init__(self):
        super().__init__('dummy')

    @staticmethod
    def arg_subject():
        return NounPhrase('Boris')


lex = Lexicaliser(templates={
    'dummy': Clause(Var('arg_subject'), 'is', 'fast')
})

realiser = Realiser()


class TestLexicalisation(unittest.TestCase):
    """ Tests for converting a MsgSpec into an NLG Element. """

    def test_string_msg(self):
        """ Test lexicalising a rhetRel with "canned text". """
        msg = StringMsg('this is some text')
        result = lex.msg_spec(msg)
        expected = Clause(subject='this is some text')
        self.assertEqual(expected, result)

    def test_lexicalise_msg_spec(self):
        """ Test lexicalisation of MsgSpec. """
        msg = DummyMsg()
        res = lex.msg_spec(msg)
        expected = list(Clause('Boris', 'is', 'fast').elements(recursive=True))
        self.assertEqual(expected, list(res.elements(recursive=True)))

    def test_lexicalise_rhet_rel(self):
        """ Test lexicalisation of RhetRel. """
        # a rhet relation with 3 nuclei
        m = RhetRel('Elaboration', DummyMsg(), DummyMsg(), DummyMsg())
        lexicalised = lex.rhet_rel(m)
        tmp = list(lex.msg_spec(DummyMsg()).elements(recursive=True))
        expected = tmp + tmp + tmp
        self.assertEqual(expected, list(lexicalised.elements(recursive=True)))

    def test_lexicalise_document(self):
        """ Test lexicalisation of Document. """
        m1 = RhetRel('Leaf', DummyMsg())
        m2 = RhetRel('Elaboration', DummyMsg(), DummyMsg())
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
