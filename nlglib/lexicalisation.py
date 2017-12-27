import numbers

from nlglib.microplanning import *
from nlglib.macroplanning import *
from nlglib.features import element_type

default_logger = logging.getLogger(__name__)

# **************************************************************************** #


class Lexicaliser(object):
    """Lexicaliser performs lexicalisation of objects.
    
    The default implementation can lexicalise `Element`, `MsgSpec`, 
    `RhetRel` and `Document` instances.
    
    Lexical templates are (partially) lexicalised syntactic trees (LST)
    or callable objects that return LST.
    
    """

    default_templates = {
        'string_message_spec': Clause(subject=Var('val'))
    }

    def __init__(self, **kwargs):
        """Create a new lexicaliser.
        
        :param logger: a custom logger to use, otherwise the default module
        logger is used
        :param templates: a dict with templates for lexicalising elements
        
        """
        self.logger = kwargs.get('logger', default_logger)
        self.templates = self.default_templates.copy()
        self.templates.update(kwargs.get('templates', {}))

    def __call__(self, msg, **kwargs):
        """ Perform lexicalisation on the message depending on the type. """
        if msg is None:
            return None
        elif isinstance(msg, numbers.Number):
            return Numeral(msg)
        elif isinstance(msg, str):
            return String(msg)
        elif isinstance(msg, (list, tuple)):
            return [self(x, **kwargs) for x in msg]
        elif isinstance(msg, Element):
            return self.element(msg, **kwargs)
        elif isinstance(msg, MsgSpec):
            return self.msg_spec(msg, **kwargs)
        elif isinstance(msg, RhetRel):
            return self.rhet_rel(msg, **kwargs)
        elif isinstance(msg, Document):
            return self.document(msg, **kwargs)
        else:
            raise TypeError('"%s" is neither a Message nor a MsgInstance' % msg)

    def element_list(self, element, **kwargs):
        self.logger.warning('This should not be called???')
        self.logger.debug('Lexicalising ElementList: {0}'.format(repr(element)))
        return ElementList([self(x, **kwargs) for x in element])

    def element(self, element, **kwargs):
        """Return a deep copy of `element` with variables replaced.
        
        The replacement is looked up in self.templates and kwargs['templates']
        using the `key` of the argument (`Var` instance).
        
        """
        self.logger.debug('Lexicalising Element: {0}'.format(repr(element)))
        rv = deepcopy(element)
        # find arguments
        args = rv.arguments()
        # if there are any variables, replace them by values from templates
        for arg in args:
            template = self.get_template(arg, **kwargs)
            if template is None:
                continue
            self.logger.info('Replacing\n{0} in \n{1} by \n{2}.'
                             .format(repr(arg), repr(rv), repr(template)))
            # avoid infinite recursion of lexicalising args (Var instances)?
            if rv == arg:
                return template
            else:
                # allow nested templates
                lexicalised_arg = self.__call__(template, **kwargs)
                rv.replace(arg, lexicalised_arg)
        return rv

    def msg_spec(self, msg, **kwargs):
        """Return Element corresponding to given message specification.
    
        If the lexicaliser can not find correct lexicalisation, it returns 
        String(msg) and logs the error.
        
        :param msg: MsgSpec instance
        :param kwargs: extra lexicalisation args (e.g., templates)
        :return lexicalised message specification
        :rtype: Element

        """
        self.logger.debug('Lexicalising message specs: {0}'.format(repr(msg)))
        if msg is None:
            return None
        template = None
        try:
            template = self.get_template(msg, **kwargs)
            args = template.arguments()
            # if there are any arguments, replace them by values from the msg
            for arg in args:
                self.logger.info('Replacing argument\n{0} in \n{1}.'
                                 .format(str(arg), repr(template)))
                val = msg.value_for(arg.id)
                # check if value is a template and if so, look it up
                if isinstance(val, str):
                    val = self.get_template(String(val), **kwargs)
                lex_val = self(val, **kwargs)
                log_msg = 'Replacement value for {0}: {1}'
                self.logger.info(log_msg.format(str(arg), repr(lex_val)))
                template.replace(arg, lex_val)
            return template
        except Exception as e:
            self.logger.exception('Error in lexicalising MsgSpec: %s', e)
            self.logger.info('\tmsg: ' + repr(msg))
            self.logger.info('\ttemplate: ' + repr(template))
        return String(msg)

    def rhet_rel(self, rel, **kwargs):
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
        self.logger.debug('Lexicalising RhetRel {0}'.format(rel))
        if rel is None:
            return None

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
            self.logger.debug('RST Implication: ' + repr(rel))
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
            objekt = satellite
            features[element_type] = element_type.negated
            result.predicate(VP('is', objekt, features=features))
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
            # In case of CC, modify the first coordinate
            if result.category == COORDINATION:
                result.coords[0].add_front_modifier(String(front_mod), pos=0)
            else:
                result.premodifiers.insert(0, String(front_mod))
            self.logger.debug('Result:\n' + repr(result))
        elif relation == 'negation':
            result = Clause(Pronoun('it'), VP('is', NP('the', 'case'),
                                              features=(element_type.negated, )))
            cl = raise_to_phrase(nucleus)
            cl['COMPLEMENTISER'] = 'that'
            result.vp.complements.append(cl)
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
        self.logger.debug('Lexicalising document.')
        if doc is None:
            return None
        title = self(doc.title, **kwargs)
        sections = [self(x, **kwargs) for x in doc.sections]
        return Document(*sections, title=title)

    def get_template(self, item, **kwargs):
        """Return the template for given `element`.
        
        The looked templates are `self.templates` and `kwargs['templates']`.
        
        If the template under given key is a callable object, 
        it will be passed `element` and **kwargs and should return a template.
        
        :param item: str or something with `key` attribute for lookup
        :param kwargs: optional arguments from the pipeline
        :return: a template or String(str(element))
        :rtype: Element
        
        """
        # TODO: maybe do this in call and call dispatch everywhere else?
        available_templates = self.templates.copy()
        available_templates.update(kwargs.get('templates', {}))

        key = item if isinstance(item, str) else item.id
        template = deepcopy(available_templates.get(key))
        if template is None:
            self.logger.warning('No template for "%s"' % key)
            rv = String(item)
        elif hasattr(template, '__call__'):  # callable passed -- invoke
            # noinspection PyCallingNonCallable
            template = template(item, **kwargs)
            if template is None:
                msg = 'Function for template "%s" returned None'
                self.logger.warning(msg % key)
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
