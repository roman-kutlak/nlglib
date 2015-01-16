import unittest
import time

from nlg.fol import *

class TestFOL(unittest.TestCase):

    def setUp(self):
        self.startTime = time.time()

    def tearDown(self):
        t = time.time() - self.startTime
        print("{0}: {1:.3f}".format(self.id(), t))

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
        
        s = expr('-x')
        e = Expr('-', Expr('x'))
        self.assertEqual(e, s)
        
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
        
        s = 'forall ?x: Rich(?x) ==> Happy(?x)'
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
#        e = expr('forall x: forall y: ((x + y > 0))')

        e = expr('forall x: x + y = z ==> exists c: z > 0')
        expected = Quantifier(OP_FORALL, ['x'],
                              Expr(OP_IMPLIES,
                                   Expr('%', Expr('+', Expr('x'), Expr('y')),
                                             Expr('z')),
                                   Quantifier(OP_EXISTS, ['c'],
                                              Expr('>', Expr('z'), Expr(0)))))
        self.assertEqual(expected, e)
    
        e = expr('(P) | (Q)')
        expected = Expr('P') | Expr('Q')
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
        f = expr('forall x: Rich(x) ==> Happy(x)')
        expected = {Expr('x')}
        actual = vars(f)
        self.assertEqual(expected, actual)
        
        f = expr('forall x: exists y, z: Pos(x) ==> x >= y & x <= z')
        expected = {Expr('x'), Expr('y'), Expr('z')}
        actual = vars(f)
        self.assertEqual(expected, actual)
        
        f = expr('forall x: x + y = z ==> exists c: z > 0')
        expected = {Expr('x'), Expr('y'), Expr('z'), Expr('c')}
        actual = vars(f)
        self.assertEqual(expected, actual)

    def test_fvars(self):
        f = expr('forall x: Rich(x) ==> Happy(x)')
        expected = set()
        actual = fvars(f)
        self.assertEqual(expected, actual)
        
        f = expr('forall x: exists y: Pos(x) ==> x >= y & x <= z')
        expected = {Expr('z')}
        actual = fvars(f)
        self.assertEqual(expected, actual)
        
        f = expr('forall x: exists y, z: Pos(x) ==> x >= y & x <= z')
        expected = set()
        actual = fvars(f)
        self.assertEqual(expected, actual)
        
        f = expr('forall x: x + y = z ==> exists c: z > 0')
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
        
        f1 = expr('forall x: c > 0 ==> x + c > x')
        expected = expr('forall x: 3 > 0 ==> x + 3 > x')
        f2 = subst({Expr('c'): Expr(3)}, f1)
        self.assertEqual(expected, f2)

        f1 = expr('forall x: c > 0 ==> x + c > x')
        expected = expr("forall x': x > 0 ==> x' + x > x'")
        f2 = subst({Expr('c'): Expr('x')}, f1)
        self.assertEqual(expected, f2)

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
        
        f = expr('P(x) ==> Q(x)')
        expected = expr('P(x) ==> Q(x)')
        self.assertEqual(expected, simplify(f))
        
        f = expr('P(x) <== Q(x)')
        expected = expr('P(x) <== Q(x)')
        self.assertEqual(expected, simplify(f))
        
        f = expr('P(x) <=> Q(x)')
        expected = expr('P(x) <=> Q(x)')
        self.assertEqual(expected, simplify(f))

        f = expr('P(x, y) ==> Q(x)')
        expected = expr('P(x, y) ==> Q(x)')
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
        
        f = expr('P ==> false')
        expected = expr('~P')
        self.assertEqual(expected, simplify(f))
        
        f = expr('true ==> P')
        expected = expr('P')
        self.assertEqual(expected, simplify(f))
    
        f = expr('P <=> true')
        expected = expr('P')
        self.assertEqual(expected, simplify(f))
        
        f = expr('P <=> false')
        expected = expr('~P')
        self.assertEqual(expected, simplify(f))
        
    def test_simplification_complex(self):
        f = expr('forall x: P(x)')
        expected = expr('forall x: P(x)')
        self.assertEqual(expected, simplify(f))
        
        f = expr('forall x: P(x) & true')
        expected = expr('forall x: P(x)')
        self.assertEqual(expected, simplify(f))
        
        f = expr('forall x: P(x) & Q(x) ==> false')
        expected = expr('forall x: ~(P(x) & Q(x))')
        self.assertEqual(expected, simplify(f))
        
        f = expr('forall x, y: P(x) & true')
        expected = expr('forall x: P(x)')
        self.assertEqual(expected, simplify(f))
        
        f = expr('forall x: forall y: P(x) & Q(x) ==> false')
        expected = expr('forall x: ~(P(x) & Q(x))')
        self.assertEqual(expected, simplify(f))
        
        f = expr('forall x: exists y: P(x) & Q(x) ==> false')
        expected = expr('forall x: ~(P(x) & Q(x))')
        self.assertEqual(expected, simplify(f))
        
        f = expr('forall x, y: exists z: x =/= y ==> x < z & z < y')
        expected = expr('forall x, y: exists z: x =/= y ==> x < z & z < y')
        self.assertEqual(expected, simplify(f))

        f = expr('forall x, y: (P(x1) & true) | (Q(y1) & false)')
        expected = expr('P(x1)')
        self.assertEqual(expected, simplify(f))

        f = expr('forall x, y: exists z: (P(x1) & true) ==> (Q(y1) & false)')
        expected = expr('~P(x1)')
        self.assertEqual(expected, simplify(f))

        f = expr('forall x, y: exists z: '\
                 '(P(x1) & true) | (Q(y1) & false) ==> Z(xy) ')
        expected = expr('P(x1) ==> Z(xy)')
        self.assertEqual(expected, simplify(f))

        f = expr('forall x, y: exists z: '\
                 '(P(x1) & true) | (Q(y1) & false) <=> true ')
        expected = expr('P(x1)')
        self.assertEqual(expected, simplify(f))

        f = expr('forall x, y: exists z: '\
                 '(P(x1) & true) | (Q(y1) & false) <== Z(xy) | true ')
        expected = expr('true')
        self.assertEqual(expected, simplify(f))

        f = expr('true ==> (P <=> (P <=> false))')
        expected = expr('P <=> ~P')
        self.assertEqual(expected, simplify(f))

        f = expr('exists x, y, z: P(x) ==> Q(z) ==> false')
        expected = expr('exists x, z: P(x) ==> ~Q(z)')
        self.assertEqual(expected, simplify(f))

        f = expr('(forall x, y: P(x) | (P(y) & false)) ==> exists z: Q')
        expected = expr('(forall x: P(x)) ==> Q')
        self.assertEqual(expected, simplify(f))

    def test_nnf(self):
        f = expr('P & Q & R')
        expected = expr('P & (Q & R)')
        self.assertEqual(expected, nnf(f))
        
        f = expr('P | Q | R')
        expected = expr('P | (Q | R)')
        self.assertEqual(expected, nnf(f))
        
        f = expr('P ==> Q')
        expected = expr('~P | Q')
        self.assertEqual(expected, nnf(f))
        
        f = expr('P <== Q')
        expected = expr('P | ~Q')
        self.assertEqual(expected, nnf(f))

        f = expr('P <=> Q')
        expected = expr('(P & Q) | (~P & ~Q)')
        self.assertEqual(expected, nnf(f))

        f = expr('P <=> (Q ==> R)')
        expected = expr('(P & (~Q | R)) | (~P & (Q & ~R))')
        self.assertEqual(expected, nnf(f))

        f = expr('P ==> (Q <=> R)')
        expected = expr('(~P | ((Q & R) | (~Q & ~R)))')
        self.assertEqual(expected, nnf(f))
        
        f = expr('(exists x: P(x)) ==> (forall x: Q(x))')
        expected = expr('(forall x: ~P(x)) | (forall x: Q(x))')
        self.assertEqual(expected, nnf(f))

        f = expr('((exists y: Q(y)) <=> exists z: P(z) & Q(z))')
        expected = expr('(exists y: Q(y)) & (exists z: P(z) & Q(z)) | '
                        '(forall y: ~Q(y)) & (forall z: ~P(z) | ~Q(z))')
        self.assertEqual(expected, nnf(f))

        f = expr('(forall x: P(x)) ==> '\
                 '((exists y: Q(y)) <=> exists z: P(z) & Q(z))')
        expected = Expr(OP_OR,
                        Quantifier(OP_EXISTS, ['x'], expr('~P(x)')),
                        expr('((exists y: Q(y)) & (exists z: P(z) & Q(z))) | '
                            '((forall y: ~Q(y)) & (forall z: ~P(z) | ~Q(z)))'))
        self.assertEqual(expected, nnf(f))

    def test_unique_vars(self):
        f = expr('P(x) & Q(x) & R(x)')
        expected = expr('P(x) & Q(x) & R(x)')
        self.assertEqual(expected, unique_vars(f))
        
        f = expr('forall x: P(x) | Q(x)')
        expected = expr('forall x: P(x) | Q(x)')
        self.assertEqual(expected, unique_vars(f))
        
        f = expr('(forall x: P(x)) | (forall x: Q(x))')
        expected = expr("(forall x: P(x)) | (forall x': Q(x'))")
        self.assertEqual(expected, unique_vars(f))
        
        f = expr('(forall x: P(x)) | (exists x: Q(x))')
        expected = expr("(forall x: P(x)) | (exists x': Q(x'))")
        self.assertEqual(expected, unique_vars(f))

        f = expr("(forall x, x': P(x) | Q(x')) | (forall x: Q(x))")
        expected = expr("(forall x, x': P(x) | Q(x')) | (forall x'': Q(x''))")
        self.assertEqual(expected, unique_vars(f))
        
        f = expr('(forall x: P(x)) & (exists y: Q(y)) & (forall x, y: Z(x, y))')
        expected = expr("(forall x: P(x)) & (exists y: Q(y)) &"
                        "(forall x', y': Z(x', y'))")
        self.assertEqual(expected, unique_vars(f))

        f = expr("(forall x: P(x)) & (exists y: Q(y)) &"
                 "(forall x', y': Z(x', y')) | (forall x', y': Z(x', y'))")
        expected = expr("(forall x: P(x)) & (exists y: Q(y)) &"
                "(forall x', y': Z(x', y')) | (forall x'', y'': Z(x'', y''))")
        self.assertEqual(expected, unique_vars(f))

    def test_pullquants(self):
        # easy forall cases
        f = expr('(forall x: P(x)) & Q')
        e = expr('forall x: P(x) & Q')
        self.assertEqual(e, pullquants(f))
        
        f = expr('P & (forall x: Q(x))')
        e = expr('forall x: P & Q(x)')
        self.assertEqual(e, pullquants(f))

        f = expr('(forall x: P(x)) | Q')
        e = expr('forall x: P(x) | Q')
        self.assertEqual(e, pullquants(f))

        f = expr('P | forall x: Q(x)')
        e = expr('forall x: P | Q(x)')
        self.assertEqual(e, pullquants(f))

        # easy exists cases
        f = expr('(exists x: P(x)) & Q')
        e = expr('exists x: P(x) & Q')
        self.assertEqual(e, pullquants(f))
        
        f = expr('P & (exists x: Q(x))')
        e = expr('exists x: P & Q(x)')
        self.assertEqual(e, pullquants(f))

        f = expr('(exists x: P(x)) | Q')
        e = expr('exists x: P(x) | Q')
        self.assertEqual(e, pullquants(f))

        f = expr('P | (exists x: Q(x))')
        e = expr('exists x: P | Q(x)')
        self.assertEqual(e, pullquants(f))
        
        # variable reduction
        f = expr('(forall x: P(x)) & (forall y: Q(y))')
        e = expr('(forall x: P(x) & Q(x))')
        self.assertEqual(e, pullquants(f))
        
        # catch
        f = expr('(forall x: P(x)) | (forall x: Q(x))')
        e = expr("(forall x: forall x': P(x) | Q(x'))")
        self.assertEqual(e, pullquants(f))

        # variable reduction
        f = expr('(exists x: P(x)) | (exists y: Q(y))')
        e = expr('(exists x: P(x) | Q(x))')
        self.assertEqual(e, pullquants(f))
        
        # catch
        f = expr('(exists x: P(x)) & (exists x: Q(x))')
        e = expr("(exists x: exists x': P(x) & Q(x'))")
        self.assertEqual(e, pullquants(f))
        
        # no rename
        f = expr('P(x) & (forall y: Q(y))')
        e = expr('(forall y: P(x) & Q(y))')
        self.assertEqual(e, pullquants(f))
        
        # rename required
        f = expr('P(x) & (forall x: Q(x))')
        e = expr("(forall x': P(x) & Q(x'))")
        self.assertEqual(e, pullquants(f))

        # rename required
        f = expr('P(x) & (exists x: Q(x))')
        e = expr("(exists x': P(x) & Q(x'))")
        self.assertEqual(e, pullquants(f))
    
        f = expr(" (Q | exists x: P(x)) -> forall z: R(z)")
        e = expr("forall x: forall z: ( ( Q or P(x)) -> R(z) )")
        self.assertEqual(e, pullquants(f))

    def test_pnf(self):
        """ prenex normal form """
        f = expr("(forall x: P(x) | R(y)) ==> "
                 "(exists y, z: Q(y)) | ~(exists z: P(z) & Q(z))")
        e = expr("exists x: forall z: foo")
        foo = expr('~P(x) & ~R(y) | (Q(x) | (~P(z) | ~Q(z)))')
        e.args[0].args[0] = foo
        
        g = expr("exists x: forall z: ~P(x) & ~R(y) | (Q(x) | (~P(z) | ~Q(z)))")
        self.assertEqual(e, pullquants(nnf(simplify(f))))
        self.assertEqual(g, pullquants(nnf(simplify(f))))

    def test_pushquants(self):
        # easy forall cases
        f = expr('forall x: P(x) & Q')
        e = expr('(forall x: P(x)) & Q')
        self.assertEqual(e, pushquants(f))
        
        f = expr('forall x: P & Q(x)')
        e = expr('P & (forall x: Q(x))')
        self.assertEqual(e, pushquants(f))

        f = expr('forall x: P(x) | Q')
        e = expr('(forall x: P(x)) | Q')
        self.assertEqual(e, pushquants(f))

        f = expr('forall x: P | Q(x)')
        e = expr('P | forall x: Q(x)')
        self.assertEqual(e, pushquants(f))

        # easy exists cases
        f = expr('exists x: P(x) & Q')
        e = expr('(exists x: P(x)) & Q')
        self.assertEqual(e, pushquants(f))
        
        f = expr('exists x: P & Q(x)')
        e = expr('P & (exists x: Q(x))')
        self.assertEqual(e, pushquants(f))

        f = expr('exists x: P(x) | Q')
        e = expr('(exists x: P(x)) | Q')
        self.assertEqual(e, pushquants(f))

        f = expr('exists x: P | Q(x)')
        e = expr('P | (exists x: Q(x))')
        self.assertEqual(e, pushquants(f))



        # variable reduction
        f = expr('(forall x: P(x) & Q(x))')
        e = expr('(forall x: P(x)) & (forall x: Q(x))')
        self.assertEqual(e, pushquants(f))
        
        # catch
        f = expr("(forall x: forall x': P(x) | Q(x'))")
        e = expr("(forall x: P(x)) | (forall x': Q(x'))")
        self.assertEqual(e, pushquants(f))

        # variable reduction
        f = expr('(exists x: P(x) | Q(x))')
        e = expr('(exists x: P(x)) | (exists x: Q(x))')
        self.assertEqual(e, pushquants(f))
        
        # catch
        f = expr("(exists x: exists x': P(x) & Q(x'))")
        e = expr("(exists x: P(x)) & (exists x': Q(x'))")
        self.assertEqual(e, pushquants(f))
        
        # no rename
        f = expr('(forall y: P(x) & Q(y))')
        e = expr('P(x) & (forall y: Q(y))')
        self.assertEqual(e, pushquants(f))
        
        # rename required
        f = expr("(forall x': P(x) & Q(x'))")
        e = expr("P(x) & (forall x': Q(x'))")
        self.assertEqual(e, pushquants(f))

        # rename required
        f = expr("(exists x': P(x) & Q(x'))")
        e = expr("P(x) & (exists x': Q(x'))")
        self.assertEqual(e, pushquants(f))
    
        f = expr("forall x: forall z: ( ( Q or P(x)) -> R(z) )")
        e = expr("(Q | exists x: P(x)) -> forall z: R(z)")
        self.assertEqual(e, pushquants(f))






if __name__ == '__main__':
    unittest.main()
