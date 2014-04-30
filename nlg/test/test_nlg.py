import unittest
import time
import sys

from nlg.nlg import *
from nlg.structures import *


#class TestGre(unittest.TestCase):
#    def setUp(self):
##        self.p = Planner()
#        self.dom = self.p.get_domain('logistics')
#        self.prob = self.p.get_problem('logistics', 'logistics-1.pddl')
#        self.context = Context(self.dom, self.prob)
#        self.reg = REG()
#
#    def test_reg(self):
#        res = self.reg.gre('tru1', self.context)
#        self.assertEqual('truck 1', str(res))
#        res = self.reg.gre('obj12', self.context)
#        self.assertEqual('a drum', str(res))
#
#
#class TestNlg(unittest.TestCase):
#    
#    def setUp(self):
#        self.p = Planner()
#        self.plan = self.p.plan_for_goal('Logistics-1')
#        self.nlg = Nlg()
#    
#    def tearDown(self):
#        pass
#    
#    def test_setup(self):
#        self.assertNotEqual(None, self.plan)
#        self.assertNotEqual(None, self.nlg)
#    
#    def test_lexicalise(self):
#        pass

def get_clause():
    clause = Clause(NP(Word('you', 'NOUN')),
                    VP(Word('say', 'VERB'), String('hello')))
    clause._features['FORM'] = "IMPERATIVE"
    return clause


def get_test_doc():
    m1 = Message('Leaf', Clause(String('hello'), None))
    m2 = Message('Elaboration', get_clause())
    para = Paragraph(m1, m2)
    return para


class TestNlg(unittest.TestCase):
    def test_realisation(self):
        gen = Nlg()
        para = get_test_doc()
        result = gen.process_nlg_doc(para, None, None)
        expected = '    Hello. You say hello.'
        self.assertEqual(expected, result)

    def test_realisation2(self):
        gen = Nlg()
        result = gen.process_nlg_doc2(get_clause(), None, None)
        expected = 'Say hello.'
        self.assertEqual(expected, result)

        result = gen.process_nlg_doc2(get_test_doc(), None, None)
        expected = '    Hello. Say hello.'
        self.assertEqual(expected, result)

    def test_string_msg(self):
        msg = StringMsgSpec('This is some text.')
        gen = Nlg()
        result = gen.process_nlg_doc(msg, None, None)
        expected = 'This is some text.'
        self.assertEqual(expected, result)
