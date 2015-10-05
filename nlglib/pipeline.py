from .nlg import Nlg
from .macroplanning import formula_to_rst
from .fol import expr


def translate(formula):
    if isinstance(formula, str):
        formula = expr(formula)
    pipeline = Nlg()
    doc = formula_to_rst(formula)
    text = pipeline.process_nlg_doc2(doc, None, None)
    return text
