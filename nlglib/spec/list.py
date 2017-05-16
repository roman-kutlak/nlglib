# encoding: utf-8

"""Definition of the ListElement container class."""

from .base import NLGElement
from ..lexicon.feature.internal import COMPONENTS


class ListElement(NLGElement):

    """
    ListElement is used to define elements that can be grouped
    together and treated in a similar manner. The list element itself
    adds no additional meaning to the realisation. For example, the
    syntax processor takes a phrase element and produces a list element
    containing inflected word elements. Phrase elements only have
    meaning within the syntax processing while the morphology processor
    (the next in the sequence) needs to work with inflected words.
    Using the list element helps to keep the inflected word elements
    together.

    There is no sorting within the list element and components are added
    in the order they are given.

    """

    def __init__(self, element=None):
        """The ListElement inherits factory, category and all features
        from the phrase.

        """
        super(ListElement, self).__init__()
        self.features = {COMPONENTS: []}
        if element:
            if isinstance(element, list):
                self.extend(element)
            elif isinstance(element, NLGElement):
                self.category = element.category
                self.features.update(element.features)
                self.append(element)

    def __bool__(self):
        return bool(len(self))

    def __len__(self):
        return len(self.features[COMPONENTS])

    def __getitem__(self, key):
        return self.features[COMPONENTS][key]

    def __setitem__(self, key, value):
        self.features[COMPONENTS][key] = value
        value.parent = self

    def __delitem__(self, key):
        self.features[COMPONENTS][key].parent = None
        del self.features[COMPONENTS][key]

    def __iter__(self):
        return iter(self.features[COMPONENTS])

    def append(self, element):
        self.features[COMPONENTS].append(element)
        element.parent = self

    def extend(self, elements):
        self.features[COMPONENTS].extend(elements)
        for element in elements:
            element.parent = self

    @property
    def children(self):
        return self.features[COMPONENTS]

    @children.setter
    def children(self, value):
        self.features[COMPONENTS] = value
        for child in value:
            child.parent = self

    @property
    def head(self):
        return self[0] if self else None

    def realise_syntax(self):
        """Return a new ListElement containing the syntax realisation of
        each of the current ListElement elements.

        Return None if the ListElement is elided.

        """
        if self.elided:
            return None
        realised_list = ListElement()
        for element in self:
            realised_list.append(element.realise_syntax())
        if len(realised_list) == 1:
            return realised_list.head
        else:
            return realised_list

    def realise_morphology(self):
        """Return a new ListElement containing the morphology realisation
        of each of the current ListElement elements.

        """
        realisations = [element.realise_morphology() for element in self]
        return ListElement(realisations)

    def realise_orthography(self):
        raise NotImplementedError
