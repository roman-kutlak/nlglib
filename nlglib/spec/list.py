# encoding: utf-8

"""Definition of the ListElement container class."""

from .base import NLGElement
from .string import StringElement
from nlglib.lexicon.feature import category


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
        super(ListElement, self).__init__(category=category.LIST_ELEMENT)
        self.components = []
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
        return len(self.components)

    def __getitem__(self, key):
        return self.components[key]

    def __setitem__(self, key, value):
        self.components[key] = value
        value.parent = self

    def __delitem__(self, key):
        self.components[key].parent = None
        del self.components[key]

    def __iter__(self):
        return iter(self.components)

    def append(self, element):
        if not isinstance(element, NLGElement):
            element = StringElement(str(element))
        element.parent = self
        self.components.append(element)

    def extend(self, elements):
        for element in elements:
            if not isinstance(element, NLGElement):
                element = StringElement(str(element))
            element.parent = self
            self.components.append(element)

    def insert(self, index, element):
        if not isinstance(element, NLGElement):
            element = StringElement(str(element))
        element.parent = self
        self.components.insert(index, element)

    @property
    def children(self):
        return self.components

    @children.setter
    def children(self, value):
        self.components = value
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
