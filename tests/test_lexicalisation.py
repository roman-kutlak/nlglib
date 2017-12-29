import unittest

from nlglib.macroplanning import MsgSpec, RhetRel, Document, StringMsg, Paragraph
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
        result = lex.message_specification(msg)
        expected = Clause(subject='this is some text')
        self.assertEqual(expected, result)

    def test_lexicalise_message_specification(self):
        """ Test lexicalisation of MsgSpec. """
        msg = DummyMsg()
        res = lex.message_specification(msg)
        expected = list(Clause('Boris', 'is', 'fast').elements(recursive=True))
        self.assertEqual(expected, list(res.elements(recursive=True)))

    def test_lexicalise_rst_relation(self):
        """ Test lexicalisation of RhetRel. """
        # a rhet relation with 3 nuclei
        m = RhetRel('Elaboration', DummyMsg(), DummyMsg(), DummyMsg())
        lexicalised = lex.rst_relation(m)
        tmp = list(lex.message_specification(DummyMsg()).elements(recursive=True))
        expected = tmp + tmp + tmp
        self.assertEqual(expected, list(lexicalised.elements(recursive=True)))

    def test_lexicalise_paragraph(self):
        """ Test lexicalisation of Document. """
        m1 = RhetRel('Leaf', DummyMsg())
        m2 = RhetRel('Elaboration', DummyMsg(), DummyMsg())
        p = Paragraph(m1, m2)
        tmp = lex.paragraph(p)
        expected = 'Boris is fast. Boris is fast. Boris is fast.'
        actual = realiser(tmp)
        self.assertEqual(expected, str(actual))

    def test_lexicalise_document(self):
        """ Test lexicalisation of Document. """
        m1 = RhetRel('Leaf', DummyMsg())
        m2 = RhetRel('Elaboration', DummyMsg(), DummyMsg())
        s1 = Document('Section One', m1)
        s2 = Document('Section Two', m2)
        d = Document('Doc Title', s1, s2)
        tmp = lex.document(d)
        expected = 'Doc Title\n\n' + \
            'Section One' + \
            '\n\nBoris is fast.' + \
            '\n\nSection Two' + \
            '\n\nBoris is fast. Boris is fast.'
        actual = realiser(tmp)
        self.assertEqual(expected, str(actual))


if __name__ == '__main__':
    unittest.main()
