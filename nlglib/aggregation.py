import logging

from copy import deepcopy
from nlglib.macroplanning import RhetRel, Document, Paragraph
from nlglib.microplanning import *
from nlglib.features import NUMBER, DISCOURSE_FUNCTION


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

        If the `message.category` doesn't match any condition,
        call `msg.aggregate(self, **kwargs)` if `msg` has attr `aggregate`
        otherwise return `String(msg)`

        """
        cat = msg.category if hasattr(msg, 'category') else type(msg)
        self.logger.debug('Aggregating {0}: {1}'.format(cat, repr(msg)))

        if msg is None:
            return None

        if hasattr(msg, 'aggregate'):
            return msg.aggregate(self, **kwargs)

        # support dynamic dispatching
        msg_category = cat.lower()
        if hasattr(self, msg_category):
            fn = getattr(self, msg_category)
            return fn(msg, **kwargs)
        elif isinstance(msg, (list, set, tuple)):
            return self.element_list(msg, **kwargs)
        else:
            return msg

    def element_list(self, element, **kwargs):
        self.logger.debug('Aggregating a list')
        elements = []
        if len(element) > 1:
            elements = self.synt_aggregation([self.aggregate(x, **kwargs) for x in element])
        elif len(element) == 1:
            elements.append(self.aggregate(element[0]))
        return elements

    def clause(self, clause, **kwargs):
        """Check if clause contains a coordinated element and if so, aggregate. """
        self.logger.debug('Aggregating a clause:\n' + repr(clause))
        subj = self.aggregate(clause.subject, **kwargs)
        obj = self.aggregate(clause.complements, **kwargs)
        vp = self.aggregate(clause.predicate, **kwargs)
        vp.addfeatures(clause.predicate.features)
        c = deepcopy(clause)
        c.subject = subj
        c.predicate = vp
        c.complements = obj
        self.logger.debug('...result:\n' + repr(c))
        return c

    def coordination(self, cc, **kwargs):
        self.logger.debug('Aggregating coordination.')
        coords = self.element_list(cc.coords, **kwargs)
        if len(coords) == 1:
            result = coords[0]
            result.features.update(cc.features)
            return result
        else:
            return Coordination(*coords, conj=cc.conj, features=cc.features)

    def rst_relation(self, msg, **kwargs):
        """ Perform syntactic aggregation on the constituents.
        The aggregation is triggered only if the RST relation is
        a sequence or a list.

        """
        self.logger.debug('Aggregating message.')
        if not (msg.rst == 'Sequence' or
                msg.rst == 'Alternative' or
                msg.rst == 'List'): return msg
        # TODO: Sequence and list are probably multi-nucleus and not multi-satellite
        self.logger.debug('Aggregating list or sequence.')
        elements = []
        if len(msg.nuclei) > 1:
            elements = self.synt_aggregation([self.aggregate(s, **kwargs) for s in msg.nuclei], **kwargs)
        elif len(msg.nuclei) == 1:
            elements.append(msg.nucleus)
        if msg.satellite is not None:
            elements.insert(0, msg.satellite)
            # TODO: put elements in nucleus or come up with a different struct.
        return RhetRel(msg.rst, *elements)

    def paragraph(self, para, **kwargs):
        """ Perform syntactic aggregation on the constituents. """
        self.logger.debug('Aggregating paragraph.')
        if para is None: return None
        messages = [self.aggregate(x, **kwargs) for x in para.messages if x is not None]
        return Paragraph(*messages)

    def document(self, doc, **kwargs):
        """ Perform aggregation on a document - possibly before lexicalisation. """
        self.logger.debug('Aggregating document.')
        if doc is None: return None
        title = self.aggregate(doc.title, **kwargs)
        sections = [self.aggregate(x, **kwargs) for x in doc.sections if x is not None]
        return Document(title, *sections)

    def add_elements(self, e1, e2, conj='and', **kwargs):
        if not isinstance(e1, Element) or not isinstance(e2, Element):
            raise ElementError("To add elements they have to be NLGElements")

        cc = Coordination()

        if isinstance(e1, Coordination):
            cc = deepcopy(e1)
            cc.coords.append(deepcopy(e2))
            if DISCOURSE_FUNCTION in e1.features:
                cc.features[DISCOURSE_FUNCTION] = e2.features[DISCOURSE_FUNCTION]

        elif isinstance(e2, Coordination):
            cc = deepcopy(e2)
            cc.coords.append(deepcopy(e1))
            if DISCOURSE_FUNCTION in e1.features:
                cc.features[DISCOURSE_FUNCTION] = e1.features[DISCOURSE_FUNCTION]
        else:
            cc.coords.append(deepcopy(e1))
            cc.coords.append(deepcopy(e2))
            if DISCOURSE_FUNCTION in e2.features:
                cc.features[DISCOURSE_FUNCTION] = e2.features[DISCOURSE_FUNCTION]
            elif DISCOURSE_FUNCTION in e1.features:
                cc.features[DISCOURSE_FUNCTION] = e1.features[DISCOURSE_FUNCTION]
        cc.conj = conj
        # TODO: figure out when it is appropriate to set number to plural
        if cc.coords[0]['PROPER'] != 'true':
            cc[NUMBER] = NUMBER.plural
        return cc

    def try_to_aggregate(self, sent1, sent2, marker='and', **kwargs):
        """ Attempt to combine two elements into one by replacing the differing
        elements by a conjunction.

        """
        if sent1 is None or sent2 is None: return None
        if not isinstance(sent1, Clause) or not isinstance(sent2, Clause):
            return None

        replacement = Var("REPLACEMENT", "REPLACEMENT")
        for e1 in sentence_iterator(sent1):
            s1 = deepcopy(sent1)
            s1.replace(e1, replacement)  # replace one element

            for e2 in sentence_iterator(sent2):
                s2 = deepcopy(sent2)
                s2.replace(e2, replacement)  # replace one element

                if s1.subject is None:
                    if s1.predicate == replacement:
                        continue
                    if (isinstance(s1.predicate, Phrase) and
                            isinstance(s2.predicate, Phrase) and
                            s1.predicate.head != s2.predicate.head):
                        continue

                # if sentences are equal (eg s1: load x; s2: load x) aggregate
                if s1 == s2:
                    self.logger.debug('Aggregating:\n\t%s\n\t%s' % (str(s1), str(s2)))
                    cc = self.add_elements(e1, e2, conj=marker)
                    s1.replace(replacement, cc)
                    self.logger.debug('Result of aggregation:\n%s' % repr(s1))
                    return s1
            # else:
            #     print('Did not aggregate:\n\t%s\n\t%s' % (str(s1), str(s2)))
            #     if (str(s1) == str(s2)):
            #         print('s1 == s2: %s' % str(s1 == s2))
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
                if msg.subject.has_feature('PROPER', 'true'):
                    msg.predicate.set_feature('NUMBER', 'SINGULAR')
            aggregated.append(msg)
            i += increment

        return aggregated

    def _do_aggregate(self, elements, i, max, marker='and', **kwargs):
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
