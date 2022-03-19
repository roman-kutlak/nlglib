import logging

from nlglib.macroplanning.struct import Document, Paragraph
from nlglib.lexicon.feature import category


logger = logging.getLogger(__name__)


class BaseProcessor:

    def __call__(self, nlg_element, **kwargs):
        return self.process(nlg_element, **kwargs)

    def process(self, nlg_element, **kwargs):
        """Process an element based on its category (or type name)"""
        cat = nlg_element.category if hasattr(nlg_element, 'category') else type(nlg_element).__name__
        logger.debug(f'processing {cat}: {nlg_element!r}')

        if nlg_element is None:
            return ''

        # support dynamic dispatching
        attribute = cat.lower()
        if hasattr(self, attribute):
            fn = getattr(self, attribute)
            return fn(nlg_element, **kwargs)
        elif cat in category.PHRASE_CATEGORIES:
            return self.phrase(nlg_element, **kwargs)
        elif cat in category.LEXICAL_CATEGORIES:
            return self.element(nlg_element, **kwargs)
        elif isinstance(nlg_element, (list, set, tuple)):
            return self.list_element(nlg_element, **kwargs)
        else:
            raise NotImplementedError(f'Unknown category "{cat}"')

    def document(self, nlg_element, **kwargs):
        """Process a `Document`"""
        logger.debug('Processing a document')
        if nlg_element is None:
            return None
        title = self.process(nlg_element.title, **kwargs)
        sections = [self.process(x, **kwargs) for x in nlg_element.sections]
        return Document(title, *sections)

    def paragraph(self, nlg_element, **kwargs):
        """Process a `Paragraph`"""
        logger.debug('Processing a paragraph')
        if nlg_element is None:
            return None
        sentences = [self.process(x, **kwargs) for x in nlg_element.sentences]
        return Paragraph(*sentences)

    def list_element(self, elt, **kwargs):
        """Process a list"""
        logger.debug('Processing a list')
        return [self.process(x, **kwargs) for x in elt]

    def phrase(self, elt, **kwargs):
        raise NotImplementedError()

    def element(self, elt, **kwargs):
        raise NotImplementedError()

    def canned_text(self, elt, **kwargs):
        return elt
