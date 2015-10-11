from .nlg import Nlg
from .macroplanning import formula_to_rst
from .fol import expr
from .simplifications import simplification_ops
from .simplifications import Heuristic
from .reg import Context


def translate(formula, templates=[], simplifications=[]):
    if isinstance(formula, str):
        formulas = [expr(f) for f in formula.split(';') if f.strip()]
    pipeline = Nlg()
    context = Context(ontology=None)
    context.templates = templates
    translations = []
    for f in formulas:
        if simplifications:
            for s in filter(lambda x: x in simplification_ops, simplifications):
                f = simplification_ops[s](f)
        doc = formula_to_rst(f)
        translations.append(pipeline.process_nlg_doc2(doc, None, context))
    return ' '.join(translations)

# def minimise_search(f, h_file, ops=LOGIC_OPS, max=-1):
