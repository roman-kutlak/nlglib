from nlglib.spec.list import ListElement


class Realiser:
    """Class representing a full surface realiser (syntax, morph, ...)"""

    def __init__(self, language):
        self.language = language

    def realise(self, element):
        rv = self.language.process(element)
        if not rv:
            return ''
        if isinstance(rv, (ListElement, list, tuple)):
            rv = ' '.join([x.realisation if hasattr(x, 'realisation') else str(x) for x in rv])
        elif hasattr(rv, 'realisation'):
            rv = rv.realisation
        return rv

    def __call__(self, element):
        return self.realise(element)
