from nlglib.nlg import Nlg
from nlglib.macroplanning import formula_to_rst
from nlglib.fol import expr
from nlglib.simplifications import simplification_ops
from nlglib.simplifications import Heuristic
from nlglib.reg import Context


def translate(formula, templates=None, simplifications=None):
    if isinstance(formula, str):
        formulas = [expr(f) for f in formula.split(';') if f.strip()]
    pipeline = Nlg()
    context = Context(ontology=None)
    context.templates = templates or {}
    doc = []
    for f in formulas:
        if simplifications:
            for s in filter(lambda x: x in simplification_ops, simplifications):
                f = simplification_ops[s](f)
        doc.append(formula_to_rst(f))

    translations = pipeline.process_nlg_doc2(doc, None, context)
    return translations

# def minimise_search(f, h_file, ops=LOGIC_OPS, max=-1):
