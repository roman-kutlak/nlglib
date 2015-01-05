import unittest

from nlg.fol import *

class TestFOL(unittest.TestCase):

    def test_parsing(self):
        s = 'x'
        expected = Expr('x')
        e = parse_formula(s)
        self.assertEqual(expected, e)
        
        s = '?x'
        expected = Expr('?x')
        e = parse_formula(s)
        self.assertEqual(expected, e)
        
        s = 'Happy(x)'
        expected = Expr('Happy', Expr('x'))
        e = parse_formula(s)
        self.assertEqual(expected, e)
        
        s = 'Rich(?x) & Happy(?x)'
        expected = Expr(OP_AND, Expr('Rich', Expr('?x')),
                                Expr('Happy', Expr('?x')))
        e = parse_formula(s)
        self.assertEqual(expected, e)
        
        s = 'forall ?x: Rich(?x) -> Happy(?x)'
        expected = Quantifier(OP_FORALL, ['?x'],
                              Expr(OP_IMPLIES, Expr('Rich', Expr('?x')),
                                               Expr('Happy', Expr('?x'))))
        e = parse_formula(s)
        self.assertEqual(expected, e)
        # TODO: add more tests for parsing

    def test_operators(self):
        a = Expr('x')
        b = Expr('y')
        c = a & b
        expected = Expr(OP_AND, Expr('x'), Expr('y'))
        self.assertEqual(expected, c)
        # TODO: test other overloaded operators

    def test_testers(self):
        pass
#        self.assertEqual(True, is_symbol())


if __name__ == '__main__':
    unittest.main()
