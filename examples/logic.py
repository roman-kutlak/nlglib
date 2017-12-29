import logging

from nlglib.realisation.simplenlg.realisation import Realiser
from nlglib.lexicalisation import Lexicaliser
from nlglib.macroplanning import *
from nlglib.microplanning import *
from nlglib.features import TENSE


def run():

    realise = Realiser(host='roman.kutlak.info')
    lex = Lexicaliser(templates={
        'x': String('X'),
        'arthur': Male('Arthur'),
        'shrubbery': Clause(Var(0), VP('find', NP('a', 'shrubbery'), features=[TENSE.future])),
        'knight': Clause(Var(0), VP('is', NP('a', 'knight'))),
        'say_ni': Clause(Var(0), VP('say', Interjection('"Ni!"'))),
    })
    print(realise(lex(formula_to_rst(expr(r'x')))))
    print(realise(lex(formula_to_rst(expr(r'-x')))))

    print(realise(lex(formula_to_rst(expr(r'x = 5')))))
    print(realise(lex(formula_to_rst(expr(r'x != 5')))))

    print(realise(lex(formula_to_rst(expr(r'knight(arthur)')))))
    print(realise(lex(formula_to_rst(expr(r'-knight(arthur)')))))
    print(realise(lex(formula_to_rst(expr(r'say_ni(arthur)')))))
    print(realise(lex(formula_to_rst(expr(r'-say_ni(arthur)')))))
    print(realise(lex(formula_to_rst(expr(r'shrubbery(arthur)')))))
    print(realise(lex(formula_to_rst(expr(r'-shrubbery(arthur)')))))

    print(realise(lex(formula_to_rst(expr(r'knight(arthur) & say_ni(arthur)')))))
    print(realise(lex(formula_to_rst(expr(r'say_ni(arthur) | knight(arthur)')))))
    print(realise(lex(formula_to_rst(expr(r'say_ni(arthur) -> knight(arthur)')))))
    print(realise(lex(formula_to_rst(expr(r'knight(arthur) <-> say_ni(arthur)')))))

    print(realise(lex(formula_to_rst(expr(r'say_ni(arthur) & -knight(arthur)')))))
    print(realise(lex(formula_to_rst(expr(r'say_ni(arthur) | -knight(arthur)')))))
    print(realise(lex(formula_to_rst(expr(r'say_ni(arthur) -> -knight(arthur)')))))
    print(realise(lex(formula_to_rst(expr(r'-knight(arthur) <-> say_ni(arthur)')))))
    print(realise(lex(formula_to_rst(expr(r'-knight(arthur) <-> -say_ni(arthur)')))))
    print(realise(lex(formula_to_rst(expr(r'-(knight(arthur) <-> say_ni(arthur))')))))

    print(realise(lex(formula_to_rst(expr(r'say_ni(arthur) & knight(arthur) & shrubbery(arthur)')))))
    print(realise(lex(formula_to_rst(expr(r'say_ni(arthur) | knight(arthur) | shrubbery(arthur)')))))


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    run()
