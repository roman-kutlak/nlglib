import unittest

from nlglib.fol import expr, Expr
from nlglib.macroplanning import formula_to_rst, PredicateMsg


class TestPredicateMsg(unittest.TestCase):

    def test_simple_predicate(self):
        p = expr('Happy(john)')
        spec = formula_to_rst(p)
        self.assertEqual(PredicateMsg(Expr('Happy', ['john'])), spec)


if __name__ == '__main__':
    unittest.main()
