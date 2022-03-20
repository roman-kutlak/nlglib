from nlglib.realisation.processor import BaseProcessor
from nlglib.spec.list import ListElement


class OrtographyProcessor(BaseProcessor):
    """Class in charge of performing English ortography for any type of nlg elements. """

    def list_element(self, elt, **kwargs):
        """Process a list"""
        return ' '.join(OrtographyProcessor._flaten([self.process(x, **kwargs) for x in elt]))

    def phrase(self, elt, **kwargs):
        """Don't morph phrases"""
        words = []
        for c in elt.children:
            words.append(self.process(c, **kwargs))
        return ' '.join(OrtographyProcessor._flaten(words))

    def element(self, elt, **kwargs):
        """Don't morph anything else"""
        return elt.realisation or elt.base_form

    def canned_text(self, elt, **kwargs):
        return elt.realisation

    @staticmethod
    def _flaten(sequence):
        rv = []
        for item in sequence:
            if isinstance(item, (ListElement, list, tuple)):
                rv.extend(OrtographyProcessor._flaten(item))
            else:
                rv.append(item)
        return rv
