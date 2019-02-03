"""This module provides classes for performing syntactic aggregation.

For example, 'Roman is programming.' and 'Roman is singing' can be
put together to create 'Roman is programming and singing.' 

"""

import logging
from copy import deepcopy

from nlglib.features import NUMBER, category
from nlglib.macroplanning import Document, Paragraph
from nlglib.microplanning import *


class ElementError(Exception):
    pass


class AggregationError(Exception):
    pass


class SentenceAggregator:
    """Sentence aggregator looks for similarly looking syntactic structures
    and aggregates them together to decrease repetition.

    """

    def __init__(self, logger=None):
        """Create a new SentenceAggregator. """
        self.logger = logger or logging.getLogger(__name__)

    def __call__(self, msg, **kwargs):
        return self.aggregate(msg, **kwargs)

    def aggregate(self, msg, **kwargs):
        """Perform aggregation on the message depending on its category.

        If the object has attribute 'aggregate', it will be called with args (self, **kwargs).
        Otherwise, get the object's category (`msg.category`) or type name
        and try to look up the attribute with the same name in `self` (dynamic dispatch).
        List, set and tuple are aggregated by `element_list()`. Lastly,
        if no method matches, return `msg`.

        """
        cat = msg.category if hasattr(msg, 'category') else type(msg).__name__
        self.logger.debug('Aggregating {0}: {1}'.format(cat, repr(msg)))

        if msg is None:
            return None

        if hasattr(msg, 'aggregate'):
            return msg.aggregate(self, **kwargs)

        # support dynamic dispatching
        attribute = cat.lower()
        if hasattr(self, attribute):
            fn = getattr(self, attribute)
            return fn(msg, **kwargs)
        elif isinstance(msg, (list, set, tuple)):
            return self.element_list(msg, **kwargs)
        else:
            return msg

    def document(self, doc, **kwargs):
        """ Perform aggregation on a document - possibly before lexicalisation. """
        self.logger.debug('Aggregating document.')
        if doc is None: return None
        title = self.aggregate(doc.title, **kwargs)
        sections = [self.aggregate(x, **kwargs) for x in doc.sections if x is not None]
        return Document(title, *sections)

    def paragraph(self, para, **kwargs):
        """ Perform syntactic aggregation on the constituents. """
        self.logger.debug('Aggregating paragraph.')
        if para is None: return None
        messages = [self.aggregate(x, **kwargs) for x in para.messages if x is not None]
        return Paragraph(*messages)

    def element_list(self, element, marker='and', **kwargs):
        self.logger.debug('Aggregating a list')
        elements = []
        if len(element) > 1:
            elements = self.synt_aggregation([self.aggregate(x, **kwargs) for x in element],
                                             marker=marker)
        elif len(element) == 1:
            elements.append(self.aggregate(element[0]))
        return elements

    def clause(self, clause, **kwargs):
        """Check if clause contains a coordinated element and if so, aggregate. """
        self.logger.debug('Aggregating a clause:\n' + repr(clause))
        subj = self.aggregate(clause.subject, **kwargs)
        obj = self.aggregate(clause.complements, **kwargs)
        vp = self.aggregate(clause.predicate, **kwargs)
        vp.features.update(clause.predicate.features)
        c = deepcopy(clause)
        c.subject = subj
        c.predicate = vp
        c.complements = obj
        self.logger.debug('...result:\n' + repr(c))
        return c

    def coordination(self, cc, **kwargs):
        self.logger.debug('Aggregating coordination.')
        coords = self.element_list(cc.coords, marker=cc.conj, **kwargs)
        if len(coords) == 1:
            result = coords[0]
            result.features.update(cc.features)
            return result
        else:
            return Coordination(*coords, conj=cc.conj, features=cc.features)

    def add_elements(self, lhs, rhs, conj='and', **kwargs):
        if lhs.category == rhs.category == category.NOUN_PHRASE:
            return self.aggregate_noun_phrase(lhs, rhs, **kwargs)

        e1 = deepcopy(lhs)
        e2 = deepcopy(rhs)

        if e1.category == category.COORDINATION:
            cc = e1
            if e2 not in cc.coords:
                cc.coords.append(e2)

        elif isinstance(e2, Coordination):
            cc = e2
            if e1 not in cc.coords:
                cc.coords.append(e1)
        else:
            cc = Coordination(e1, e2, conj=conj)
        cc[NUMBER] = NUMBER.plural
        return cc

    def aggregate_noun_phrase(self, lhs, rhs, **kwargs):
        """Aggregate two noun phrases"""
        del kwargs  # unused for now
        if lhs.head == rhs.head:
            rv = deepcopy(lhs)
            rv.premodifiers.extend(rhs.premodifiers)
            return rv
        elif lhs.premodifiers == rhs.premodifiers:
            rv = deepcopy(lhs)
            rv.head = CC(deepcopy(lhs.head), deepcopy(rhs.head), features={'NUMBER': 'plural'})
            return rv
        else:
            return CC(deepcopy(lhs), deepcopy(rhs), features={'NUMBER': 'plural'})

    def try_to_aggregate(self, sent1, sent2, marker='and', **kwargs):
        """ Attempt to combine two elements into one by replacing the differing
        elements by a conjunction.

        """
        del kwargs  # unused for now

        if sent1 is None or sent2 is None:
            return None

        replacement = Var("REPLACEMENT", "REPLACEMENT")
        for e1 in sentence_iterator(sent1):
            s1 = deepcopy(sent1)
            s1.replace(e1, replacement)  # replace one element

            for e2 in sentence_iterator(sent2):
                s2 = deepcopy(sent2)
                s2.replace(e2, replacement)  # replace one element

                if s1 == s2:
                    self.logger.debug('Aggregating:\n\t%s\n\t%s' % (str(s1), str(s2)))
                    cc = self.add_elements(e1, e2, conj=marker)
                    s1.replace(replacement, cc)
                    self.logger.debug('Result of aggregation:\n%s' % repr(s1))
                    return s1
        return None

    def synt_aggregation(self, elements, max=3, marker='and', **kwargs):
        """ Take a list of elements and combine elements that are synt. similar.

        elements - a list of elements to combine
        max      - a maximum number of elements to aggregate

        The algorithm relies on shared structure of the elements. If, for
        example, two elements share the subject, combine the VPs into
        a conjunction. Do not combine more than 'max' elements into each other.

        """
        if elements is None: return
        if len(elements) < 2: return elements
        self.logger.debug('performing synt. aggr on:\n' + repr(elements))
        aggregated = []
        # first try partial syntax aggregation  (e.g., clause + adj, etc)
        # assume format [clause, mod, mod, clause, clause, mod, clause, mod, mod...]
        new_elements = []
        i = 0
        while i < len(elements):
            e = elements[i]
            if is_clause_type(e) and i + 1 < len(elements):
                try:
                    next = elements[i + 1]
                    while not is_clause_type(next):
                        e = e + next
                        i += 1
                        if i + 1 >= len(elements):
                            break
                        next = elements[i + 1]
                except AggregationError:
                    pass
            new_elements.append(e)
            i += 1
        if len(new_elements) < 2:
            return new_elements
        i = 0
        while i < len(new_elements):
            msg, increment = self._do_aggregate(new_elements, i, max, marker, **kwargs)
            if isinstance(msg, Clause):
                if ('PROPER', 'true') in msg.subject.features:
                    msg.predicate['NUMBER'] = 'SINGULAR'
            aggregated.append(msg)
            i += increment

        return aggregated

    def _do_aggregate(self, elements, i, max, marker='and', **kwargs):
        del kwargs  # unused for now

        lhs = elements[i]
        j = i + 1
        increment = 1
        while j < len(elements) and self._can_aggregate(lhs, max):
            self.logger.debug('LHS = %s' % lhs)
            rhs = elements[j]
            if self._can_aggregate(rhs, max):
                tmp = self.try_to_aggregate(lhs, rhs, marker)
                if tmp is not None:
                    lhs = tmp
                    increment += 1
                    j += 1
                else:
                    break
            # cannot aggregate. can we skip it?
            elif self._can_skip(elements, j):
                j += 1
                increment += 1
            else:
                break
        return lhs, increment

    def _can_aggregate(self, message, max):
        """ Return true if this message can be aggregated.
        max - maximum number of coordinates in a coordingated clause
        If the message does not have a coordinated clause or if the number
        of coordinates is less then 'max', return True.

        """
        if message is None: return False
        for part in sentence_iterator(message):
            if not isinstance(part, Coordination):
                continue
            else:
                return len(part.coords) < max
        # simple sentence - no coordinated clause
        return True

    def _can_skip(self, elements, j):
        """ Return true if this element can be skipped. """
        return elements[j] is None


class DifficultyEstimator:
    """Most basic difficulty estimator that returns 0 for any structure,
    resulting in always aggregating syntax trees if possible.

    In general, aggregating elements will increase the reading/comprehension
    difficulty of the resulting element. A subclass of the DifficultyEstimator
    could assess the difficulty of an element by, for example, counting
    non-stop words and the length of the sentence.

    """

    threshold = 1

    def estimate(self, element, context):
        del element, context  # unused for now
        return 0

    def can_aggregate(self, first, second, context):
        """We can aggregate elements if their combined estimate
        is less than or equal to the threshold.

        """
        return self.estimate(first, context) + self.estimate(second, context) <= self.threshold


class AmbiguityEstimator:
    """Most basic ambiguity estimator that returns 0 for any structure,
    resulting in always aggregating syntax trees if possible.

    In general, aggregating elements can introduce ambiguities
    or even mislead readers. For example, consider:
    John bought a house. Peter bought a house.
    ==> John and Peter bought a house.

    We should try to keep ambiguities low by, for example,
    adding some more information as in:
    ==> John and Peter each bought a house.

    """

    threshold = 1

    def estimate(self, element, context):
        del element, context  # unused for now
        return 0

    def can_aggregate(self, first, second, context):
        """We can aggregate elements if their combined estimate
        is less than or equal to the threshold.

        """
        return self.estimate(first, context) + self.estimate(second, context) <= self.threshold
