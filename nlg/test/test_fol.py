import unittest

from nlg.fol import *

class TestFOL(unittest.TestCase):

    def test_parsing(self):
        s = 'x'
        expected = Expr('x')
        e = expr(s)
        self.assertEqual(expected, e)
        
        s = '(x)'
        expected = Expr('x')
        e = expr(s)
        self.assertEqual(expected, e)
        
        s = '?x'
        expected = Expr('?x')
        e = expr(s)
        self.assertEqual(expected, e)
        
        s = 'Happy(x)'
        expected = Expr('Happy', Expr('x'))
        e = expr(s)
        self.assertEqual(expected, e)
        
        s = 'Rich(?x) & Happy(?x)'
        expected = Expr(OP_AND, Expr('Rich', Expr('?x')),
                                Expr('Happy', Expr('?x')))
        e = expr(s)
        self.assertEqual(expected, e)
        
        s = '(Rich(?x) & Happy(?x))'
        expected = Expr(OP_AND, Expr('Rich', Expr('?x')),
                                Expr('Happy', Expr('?x')))
        e = expr(s)
        self.assertEqual(expected, e)
        
        s = '((Rich(?x)) & (Happy(?x)))'
        expected = Expr(OP_AND, Expr('Rich', Expr('?x')),
                                Expr('Happy', Expr('?x')))
        e = expr(s)
        self.assertEqual(expected, e)
        
        s = 'forall ?x: Rich(?x) -> Happy(?x)'
        expected = Quantifier(OP_FORALL, ['?x'],
                              Expr(OP_IMPLIES, Expr('Rich', Expr('?x')),
                                               Expr('Happy', Expr('?x'))))
        e = expr(s)
        self.assertEqual(expected, e)
            
        e = expr('forall x: (x)')
        expected = Quantifier(OP_FORALL, ['x'], Expr('x'))
        self.assertEqual(expected, e)

        e = expr('forall x: forall y: (x + y > 0)')
        expected = Quantifier(OP_FORALL, ['x'],
                        Quantifier(OP_FORALL, ['y'],
                            Expr('>',
                                 Expr('+', Expr('x'), Expr('y')),
                                 Expr(0))))
        self.assertEqual(expected, e)
        
        # TODO: why does this not parse?
        #    e = expr('forall x: forall y: ((x + y > 0))')

        e = expr('forall x: x + y = z -> exists c: z > 0')
        expected = Quantifier(OP_FORALL, ['x'],
                              Expr(OP_IMPLIES,
                                   Expr('%', Expr('+', Expr('x'), Expr('y')),
                                             Expr('z')),
                                   Quantifier(OP_EXISTS, ['c'],
                                              Expr('>', Expr('z'), Expr(0)))))
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

    def test_vars(self):
        f = expr('forall x: Rich(x) -> Happy(x)')
        expected = {Expr('x')}
        actual = vars(f)
        self.assertEqual(expected, actual)
        
        f = expr('forall x: exists y, z: Pos(x) -> x >= y & x <= z')
        expected = {Expr('x'), Expr('y'), Expr('z')}
        actual = vars(f)
        self.assertEqual(expected, actual)
        
        f = expr('forall x: x + y = z -> exists c: z > 0')
        expected = {Expr('x'), Expr('y'), Expr('z'), Expr('c')}
        actual = vars(f)
        self.assertEqual(expected, actual)

    def test_fvars(self):
        f = expr('forall x: Rich(x) -> Happy(x)')
        expected = set()
        actual = fvars(f)
        self.assertEqual(expected, actual)
        
        f = expr('forall x: exists y: Pos(x) -> x >= y & x <= z')
        expected = {Expr('z')}
        actual = fvars(f)
        self.assertEqual(expected, actual)
        
        f = expr('forall x: exists y, z: Pos(x) -> x >= y & x <= z')
        expected = set()
        actual = fvars(f)
        self.assertEqual(expected, actual)
        
        f = expr('forall x: x + y = z -> exists c: z > 0')
        expected = {Expr('y'), Expr('z')}
        actual = fvars(f)
        self.assertEqual(expected, actual)

    def test_variant(self):
        s = {Expr('x'), Expr('y')}
        v = variant(Expr('z'), s)
        expected = Expr('z')
        self.assertEqual(expected, v)
    
        v = variant(Expr('x'), s)
        expected = Expr('x\'')
        self.assertEqual(expected, v)
    

    def test_subst(self):
        f1 = expr('x + y = z')
        expected = expr('x + y = 0')
        f2 = subst({Expr('z'): Expr(0)}, f1)
        self.assertEqual(expected, f2)
        self.assertNotEqual(f1, f2)
        
        f1 = expr('x + y = z')
        expected = expr('x + 1 = 0')
        f2 = subst({Expr('z'): Expr(0), Expr('y'): Expr(1)}, f1)
        self.assertEqual(expected, f2)
        
        f1 = expr('forall x: c > 0 -> x + c > x')
        expected = expr('forall x: 3 > 0 -> x + 3 > x')
        f2 = subst({Expr('c'): Expr(3)}, f1)
        self.assertEqual(expected, f2)
        # TODO: fix
#        f1 = expr('forall x: c > 0 -> x + c > x')
#        expected = expr("forall x': x > 0 -> x' + x > x'")
#        f2 = subst({Expr('c'): Expr('x')}, f1)
#        self.assertEqual(expected, f2)

    def test_simplification_none(self):
        f = expr('1')
        expected = expr('1')
        self.assertEqual(expected, simplify(f))
        
        f = expr('P')
        expected = expr('P')
        self.assertEqual(expected, simplify(f))
        
        f = expr('true')
        expected = expr('true')
        self.assertEqual(expected, simplify(f))
        
        f = expr('false')
        expected = expr('false')
        self.assertEqual(expected, simplify(f))
        
        f = expr('P(x)')
        expected = expr('P(x)')
        self.assertEqual(expected, simplify(f))
        
        f = expr('P(x) | Q(x)')
        expected = expr('P(x) | Q(x)')
        self.assertEqual(expected, simplify(f))
        
        f = expr('P(x) & Q(x)')
        expected = expr('P(x) & Q(x)')
        self.assertEqual(expected, simplify(f))
        
        f = expr('P(x) -> Q(x)')
        expected = expr('P(x) -> Q(x)')
        self.assertEqual(expected, simplify(f))
        
        f = expr('P(x) <- Q(x)')
        expected = expr('P(x) <- Q(x)')
        self.assertEqual(expected, simplify(f))
        
        f = expr('P(x) <-> Q(x)')
        expected = expr('P(x) <-> Q(x)')
        self.assertEqual(expected, simplify(f))

        f = expr('P(x, y) -> Q(x)')
        expected = expr('P(x, y) -> Q(x)')
        self.assertEqual(expected, simplify(f))
        
        f = expr('x > 0')
        expected = expr('x > 0')
        self.assertEqual(expected, simplify(f))
        
        f = expr('x = y')
        expected = expr('x = y')
        self.assertEqual(expected, simplify(f))
        
        f = expr('x =/= 0')
        expected = expr('x =/= 0')
        self.assertEqual(expected, simplify(f))
    
    def test_simplification_basic(self):
        f = expr('~true')
        expected = expr('false')
        self.assertEqual(expected, simplify(f))
        
        f = expr('~false')
        expected = expr('true')
        self.assertEqual(expected, simplify(f))
        
        f = expr('~~true')
        expected = expr('true')
        self.assertEqual(expected, simplify(f))
        
        f = expr('~~~true')
        expected = expr('false')
        self.assertEqual(expected, simplify(f))
        
        f = expr('P | true')
        expected = expr(OP_TRUE)
        self.assertEqual(expected, simplify(f))
        
        f = expr('P | false')
        expected = expr('P')
        self.assertEqual(expected, simplify(f))
        
        f = expr('P & false')
        expected = expr(OP_FALSE)
        self.assertEqual(expected, simplify(f))
        
        f = expr('P & true')
        expected = expr('P')
        self.assertEqual(expected, simplify(f))
        
        f = expr('P -> false')
        expected = expr('true')
        self.assertEqual(expected, simplify(f))
        
        f = expr('true -> P')
        expected = expr('true')
        self.assertEqual(expected, simplify(f))
    
        f = expr('P <-> true')
        expected = expr('P')
        self.assertEqual(expected, simplify(f))
        
        f = expr('P <-> false')
        expected = expr('~P')
        self.assertEqual(expected, simplify(f))
        
    def test_simplification_complex(self):
        f = expr('forall x: P(x)')
        expected = expr('forall x: P(x)')
        self.assertEqual(expected, simplify(f))
        
        f = expr('forall x: P(x) & true')
        expected = expr('forall x: P(x)')
        self.assertEqual(expected, simplify(f))
        
        f = expr('forall x: P(x) & Q(x) -> false')
        expected = expr('TRUE')
        self.assertEqual(expected, simplify(f))
        
        f = expr('forall x, y: P(x) & true')
        expected = expr('forall x: P(x)')
        self.assertEqual(expected, simplify(f))
        
#        f = expr('forall x, y: exists z: '\
#                 '((P(x1) & true) | (Q(y1) & false) -> Z(xy)) ')
#        expected = expr('true')
#        self.assertEqual(expected, simplify(f))
#        
#        f = expr('forall x, y: exists z: x =/= y -> x < z & z < y')
#        expected = expr('forall x, y: exists z: x =/= y -> x < z & z < y')
#        self.assertEqual(expected, simplify(f))



if __name__ == '__main__':
    unittest.main()
