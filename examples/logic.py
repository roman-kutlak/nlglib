import logging

from nlglib.realisation.simplenlg.realisation import Realiser
from nlglib.lexicalisation import Lexicaliser
from nlglib.macroplanning import *
from nlglib.microplanning import *
from nlglib.structures.factories import *


def run():

    realise = Realiser(host='roman.kutlak.info')
    lex = Lexicaliser(templates={
        'x': Noun('x'),
        'roman': Male('Roman'),
        'happy': Clause(Var(0), VP('is', Adjective('happy'))),
        'rich': Clause(Var(0), VP('is', Adjective('rich'))),
        'content': Clause(Var(0), VP('is', Adjective('content'))),
    })
    print(realise(lex(formula_to_rst(expr(r'x')))))
    print(realise(lex(formula_to_rst(expr(r'-x')))))

    print(realise(lex(formula_to_rst(expr(r'x = 5')))))
    print(realise(lex(formula_to_rst(expr(r'x != 5')))))

    print(realise(lex(formula_to_rst(expr(r'happy(roman)')))))
    print(realise(lex(formula_to_rst(expr(r'-happy(roman)')))))

    print(realise(lex(formula_to_rst(expr(r'rich(roman) & happy(roman)')))))
    print(realise(lex(formula_to_rst(expr(r'rich(roman) | happy(roman)')))))
    print(realise(lex(formula_to_rst(expr(r'rich(roman) -> happy(roman)')))))
    print(realise(lex(formula_to_rst(expr(r'happy(roman) <-> rich(roman)')))))

    print(realise(lex(formula_to_rst(expr(r'rich(roman) & -happy(roman)')))))
    print(realise(lex(formula_to_rst(expr(r'rich(roman) | -happy(roman)')))))
    print(realise(lex(formula_to_rst(expr(r'rich(roman) -> -happy(roman)')))))
    print(realise(lex(formula_to_rst(expr(r'-happy(roman) <-> rich(roman)')))))
    print(realise(lex(formula_to_rst(expr(r'-happy(roman) <-> -rich(roman)')))))
    print(realise(lex(formula_to_rst(expr(r'-(happy(roman) <-> rich(roman))')))))

    print(realise(lex(formula_to_rst(expr(r'rich(roman) & happy(roman) & content(roman)')))))
    print(realise(lex(formula_to_rst(expr(r'rich(roman) | happy(roman) | content(roman)')))))


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    run()
