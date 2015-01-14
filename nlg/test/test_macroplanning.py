import unittest

from nlg.fol import expr, Expr
from nlg.macroplanning import PredicateMsgSpec


class TestPredicateMsgSpec(unittest.TestCase):

    def test_simple_predicate(self):
        p = expr('Happy(john)')
        spec = fol_to_msg(p)
        self.assertEqual(PredicateMsgSpec(Expr('Happy', ['john'])), spec)
