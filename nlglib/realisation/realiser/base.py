from nlglib.spec.list import ListElement


class Realiser:
    """Class representing a full surface realiser (syntax, morph, ...)"""

    def __init__(self, lexicon):
        self.lexicon = lexicon

    def realise(self, element):
        if hasattr(element, 'realise'):
            rv = element.realise()
        elif hasattr(element, 'realise_syntax'):
            rv = element.realise_syntax()
            if hasattr(rv, 'realise_morphology'):
                rv = rv.realise_morphology()
        else:
            rv = str(element)
        if not rv:
            return ''
        if isinstance(rv, ListElement):
            rv = ' '.join([x.realisation for x in rv])
        elif hasattr(rv, 'realisation'):
            rv = rv.realisation
        return rv

    def __call__(self, element):
        return self.realise(element)
