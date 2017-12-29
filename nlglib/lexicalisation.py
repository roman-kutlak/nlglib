import numbers
import logging

from nlglib.microplanning import *
from nlglib.macroplanning import *
from nlglib.features import category, NEGATED

__all__ = ['Lexicaliser']

log = logging.getLogger(__name__)


class Lexicaliser(object):
    """Lexicaliser performs lexicalisation of objects.
    
    The default implementation can lexicalise `Element`, `MsgSpec`, 
    `RhetRel`, `Document` and `Paragraph` instances.
    
    Lexical templates are (partially) lexicalised syntactic trees (LST)
    or callable objects that return LST.
    
    """

    default_templates = {
        'string_message_spec': Clause(subject=Var('val'))
    }

    def __init__(self, templates=None):
        """Create a new lexicaliser.
        
        :param templates: a dict with templates for lexicalising elements
        
        """
        self.templates = self.default_templates.copy()
        if templates:
            self.templates.update(templates)

    def __call__(self, msg, **kwargs):
        return self.lexicalise(msg, **kwargs)

    def lexicalise(self, msg, **kwargs):
        """Perform lexicalisation on the message depending on its category.

        If the `message.category` doesn't match any condition,
        call `msg.lexicalise(self, **kwargs)`

        """
        cat = msg.category if hasattr(msg, 'category') else type(msg)
        log.debug('Lexicalising {0}: {1}'.format(cat, repr(msg)))

        if msg is None:
            return None
        elif isinstance(msg, numbers.Number):
            return Numeral(msg)
        elif isinstance(msg, str):
            return String(msg)
        elif msg.category in category.element_category:
            return self.element(msg, **kwargs)
        elif isinstance(msg, (list, set, tuple)) or msg.category == category.ELEMENT_LIST:
            return self.element_list(msg, **kwargs)
        elif msg.category == category.MSG:
            return self.message_specification(msg, **kwargs)
        elif msg.category == category.RST:
            return self.rst_relation(msg, **kwargs)
        elif msg.category == category.DOCUMENT:
            return self.document(msg, **kwargs)
        elif msg.category == category.PARAGRAPH:
            return self.paragraph(msg, **kwargs)
        else:
            return msg.lexicalise(self, **kwargs)

    def element_list(self, element, **kwargs):
        log.warning('This should not be called???')
        return ElementList([self(x, **kwargs) for x in element])

    def element(self, element, **kwargs):
        """Return a deep copy of `element` with variables replaced.
        
        The replacement is looked up in self.templates and kwargs['templates']
        using the `key` of the argument (`Var` instance).
        
        """
        rv = deepcopy(element)
        # find arguments
        args = rv.arguments()
        # if there are any variables, replace them by values from templates
        for arg in args:
            template = self.get_template(arg, **kwargs)
            if template is None:
                continue
            msg = 'Replacing\n{0} in \n{1} by \n{2}.'
            log.info(msg.format(repr(arg), repr(rv), repr(template)))
            # avoid infinite recursion of lexicalising args (Var instances)?
            if rv == arg:
                return template
            else:
                # allow nested templates
                lexicalised_arg = self.lexicalise(template, **kwargs)
                rv.replace(arg, lexicalised_arg)
        return rv

    def message_specification(self, msg, **kwargs):
        """Return Element corresponding to given message specification.
    
        If the lexicaliser can not find correct lexicalisation, it returns 
        String(msg) and logs the error.
        
        :param msg: MsgSpec instance
        :param kwargs: extra lexicalisation args (e.g., templates)
        :return lexicalised message specification
        :rtype: Element

        """
        if msg is None:
            return None
        template = None
        try:
            template = self.get_template(msg, **kwargs)
            args = template.arguments()
            # if there are any arguments, replace them by values from the msg
            for arg in args:
                log.info('Replacing argument\n{0} in \n{1}.'
                         .format(str(arg), repr(template)))
                val = msg.value_for(arg.id)
                # check if value is a template and if so, look it up
                if isinstance(val, str):
                    val = self.get_template(String(val), **kwargs)
                lex_val = self(val, **kwargs)
                log_msg = 'Replacement value for {0}: {1}'
                log.info(log_msg.format(str(arg), repr(lex_val)))
                template.replace(arg, lex_val)
            return template
        except Exception as e:
            log.exception('Error in lexicalising MsgSpec: %s', e)
            log.info('\tmsg: ' + repr(msg))
            log.info('\ttemplate: ' + repr(template))
        return String(msg)

    def rst_relation(self, rel, **kwargs):
        """Convert `rel` to Elements. 
        
        This method should convert any concrete rhetorical relations
        into subordinations or coordinations. Abstract rhetorical relations
        will be converted into a sequence (list).
        
        Rhetorical relations can be trees and the leaves should all be 
        concrete so that they can be reduced to clauses 
        (or similar Element instances).
        
        :param rel: RhetRel instance to lexicalise
        :return: ElementList list with lexicalised elements
        :rtype: ElementList
        
        """
        features = deepcopy(getattr(rel, 'features'))
        nuclei = [self(x, **kwargs) for x in rel.nuclei]
        nucleus = nuclei[0]
        satellite = self(rel.satellite, **kwargs)
        # stick each message into a clause
        relation = rel.relation.lower()
        if relation in ('conjunction', 'disjunction'):
            result = Coordination(*nuclei, conj=rel.marker,
                                  features=features)
        elif relation == 'imply':
            log.debug('RST Implication: ' + repr(rel))
            subj = raise_to_phrase(nucleus)
            compl = raise_to_phrase(satellite)
            compl['COMPLEMENTISER'] = 'then'
            result = raise_to_clause(subj)
            result.complements.append(compl)
            result.front_modifiers.append('if')
        elif relation == 'equivalent':
            result = raise_to_phrase(nucleus)
            compl = raise_to_phrase(satellite)
            compl['COMPLEMENTISER'] = 'if and only if'
            result.complements.append(compl)
        elif relation == 'impliedBy':
            result = raise_to_phrase(nucleus)
            compl = raise_to_phrase(satellite)
            compl['COMPLEMENTISER'] = 'if'
            result.complements.append(compl)
        elif relation == 'unless':
            result = raise_to_phrase(nucleus)
            compl = raise_to_phrase(satellite)
            compl['COMPLEMENTISER'] = 'unless'
            result.complements.append(compl)
        elif relation == 'equality':
            result = Clause()
            result.subject = nucleus
            tmp_vp = VerbPhrase('is', object=satellite, features=features)
            result.predicate = tmp_vp
        elif relation == 'inequality':
            result = Clause()
            result.subject(nucleus)
            direct_object = satellite
            features[NEGATED] = NEGATED.true
            result.predicate(VP('is', direct_object, features=features))
        elif relation == 'quantifier':
            # quantifiers have multiple nuclei (variables)
            quant = rel.marker
            cc = Coordination(*nuclei, conj='and')
            np = NounPhrase(cc, String(quant))

            if quant.startswith('there exist'):
                np['COMPLEMENTISER'] = String('such that')
            else:
                np['COMPLEMENTISER'] = String(',')

            result = raise_to_phrase(satellite)

            front_mod = np
            # front_mod should go in front of existing front_mods
            # In CASE of CC, modify the first coordinate
            if result.category == COORDINATION:
                result.coords[0].add_front_modifier(String(front_mod), pos=0)
            else:
                result.premodifiers.insert(0, String(front_mod))
            log.debug('Result:\n' + repr(result))
        elif relation == 'negation':
            result = Clause(Pronoun('it'), VP('is', NP('the', 'case'),
                                              features=(NEGATED.true,)))
            cl = raise_to_phrase(nucleus)
            cl['COMPLEMENTISER'] = 'that'
            result.predicate.complements.append(cl)
        else:
            result = rel.__class__(relation,
                                   *nuclei,
                                   satellite=satellite,
                                   features=rel.features,
                                   marker=rel.marker,
                                   last_element_marker=rel.last_element_marker)
        # handle concrete subordinate clauses
        result.features.update(features)
        return result

    def document(self, doc, **kwargs):
        if doc is None:
            return None
        title = self(doc.title, **kwargs)
        sections = [self(x, **kwargs) for x in doc.sections]
        return Document(title, *sections)

    def paragraph(self, para, **kwargs):
        if para is None:
            return None
        sentences = [self(x, **kwargs) for x in para.sentences]
        return Paragraph(*sentences)

    def get_template(self, item, templates=None, **kwargs):
        """Return the template for given `element`.
        
        The looked templates are `self.templates` and `kwargs['templates']`.
        
        If the template under given key is a callable object, 
        it will be passed `element` and `**kwargs` and should return a template.
        
        :param item: str or something with `key` attribute for lookup
        :param templates: optional templates to look up the item
        :param kwargs: optional arguments passed to `lexicalise()`
        :return: a template or String(str(element))
        :rtype: Element
        
        """
        available_templates = templates or self.templates
        key = item if isinstance(item, str) else item.id
        template = deepcopy(available_templates.get(key))
        if template is None:
            log.warning('No template for "%s"' % key)
            rv = String(item)
        elif hasattr(template, '__call__'):  # callable passed -- invoke
            # noinspection PyCallingNonCallable
            template = template(item, templates=templates, **kwargs)
            if template is None:
                msg = 'Function for template "%s" returned None'
                log.warning(msg % key)
                rv = String(item)
            else:
                rv = template
        else:
            rv = template

        if not isinstance(rv, Element):
            rv = String(rv)

        if not isinstance(item, str):
            rv.features.update(deepcopy(item.features))

        return rv

    def items_as_element_list(self, items, features=None):
        """Flatten items into an ElementList, optionally updating features."""
        rv = ElementList(features=features)
        for item in items:
            if isinstance(item, ElementList):
                # TODO: do we really want to propagate the item features here?
                inner = self.items_as_element_list(item, features=item.features)
                rv.extend(inner)
            elif isinstance(item, Element):
                rv.append(item)
            else:
                raise Exception('Unexpected type "{}".'.format(type(item)))
        return rv
