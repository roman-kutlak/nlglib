from .nlg import Nlg
from .macroplanning import formula_to_rst
from .fol import expr
from .simplifications import simplification_ops
from .simplifications import Heuristic
from .reg import Context


def translate(formula, templates=[], simplifications=[]):
    if isinstance(formula, str):
        formula = expr(formula)
    pipeline = Nlg()
    if simplifications:
        for s in filter(lambda x: x in simplification_ops, simplifications):
            formula = simplification_ops[s](formula)
    doc = formula_to_rst(formula)
    context = Context(ontology=None)
    context.templates = templates
    text = pipeline.process_nlg_doc2(doc, None, context)
    return text

# def minimise_search(f, h_file, ops=LOGIC_OPS, max=-1):
