import copy
import numbers

from nlglib import realisation
from nlglib.aggregation import *
from nlglib.lexicon import *
from nlglib.microplanning import *
from nlglib.structures import is_clause_t
from nlglib.structures import microplanning as microstruct
from nlglib.logic.fol import Expr

def get_log():
    return logging.getLogger(__name__)

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
        'string_message_spec': Clause(predicate=Var('val'))
    }

    def __init__(self, **kwargs):
        """Create a new lexicaliser.
        
        :param logger: a custom logger to use, otherwise the default module
        logger is used
        :param templates: a dict with templates for lexicalising elements
        
        """
        self.logger = kwargs.get('logger', default_logger)
        self.templates = kwargs.get('templates', self.default_templates)

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
                lexicalised_arg = self(template, **kwargs)
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
        # noinspection PyBroadException
        try:
            template = self.get_template(msg, **kwargs)
            args = template.arguments()
            # if there are any arguments, replace them by values from the msg
            for arg in args:
                self.logger.info('Replacing argument\n{0} in \n{1}.'
                                 .format(str(arg), repr(template)))
                val = msg.value_for(arg.key)
                # check if value is a template and if so, look it up
                if isinstance(val, (str, Expr)):
                    val = self.get_template(String(val), **kwargs)
                lex_val = self(val, **kwargs)
                log_msg = 'Replacement value for {0}: {1}'
                self.logger.info(log_msg.format(str(arg), repr(lex_val)))
                template.replace(arg, lex_val)
            return template
        except:
            self.logger.exception('Error in lexicalising MsgSpec')
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
            subj = self.promote_to_phrase(nucleus)
            compl = self.promote_to_phrase(satellite)
            compl['COMPLEMENTISER'] = 'then'
            result = Clause(subj)
            result.complements.append(compl)
            result.front_modifiers.append('if')
        elif relation == 'equivalent':
            result = self.promote_to_phrase(nucleus)
            compl = self.promote_to_phrase(satellite)
            compl['COMPLEMENTISER'] = 'if and only if'
            result.complements.append(compl)
        elif relation == 'impliedBy':
            result = self.promote_to_phrase(nucleus)
            compl = self.promote_to_phrase(satellite)
            compl['COMPLEMENTISER'] = 'if'
            result.complements.append(compl)
        elif relation == 'unless':
            result = self.promote_to_phrase(nucleus)
            compl = self.promote_to_phrase(satellite)
            compl['COMPLEMENTISER'] = 'unless'
            result.complements.append(compl)
        elif relation == 'equality':
            result = Clause()
            result.subject = nucleus
            tmp_vp = VerbPhrase('is', object=satellite, features=features)
            result.predicate = tmp_vp
        elif relation == 'inequality':
            result = Clause()
            result.set_subj(nucleus)
            object = satellite
            features['NEGATED'] = 'true'
            result.set_vp(VP('is', object, features=features))
        elif relation == 'quantifier':
            # quantifiers have multiple nuclei (variables)
            quant = rel.marker
            cc = Coordination(*nuclei, conj='and')
            np = NounPhrase(cc, String(quant))

            if quant.startswith('there exist'):
                np['COMPLEMENTISER'] = String('such that')
            else:
                np['COMPLEMENTISER'] = String(',')

            result = self.promote_to_phrase(satellite)

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
                                              features={'NEGATED': 'true'}))
            cl = self.promote_to_phrase(nucleus)
            cl['COMPLEMENTISER'] = 'that'
            result.vp.add_complement(cl)
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
        return Document(title, *sections)

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

        key = item if isinstance(item, str) else item.key
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

    @staticmethod
    def promote_to_clause(e):
        """Convert `e` to a clause. If it is a clause, return it."""
        if is_clause_t(e): return e
        if is_phrase_t(e):
            if e.category == NOUN_PHRASE: return Clause(subject=e)
            if e.category == VERB_PHRASE: return Clause(predicate=e)
        return Clause(e)

    @staticmethod
    def promote_to_phrase(e):
        """Convert `e` to a phrase. If it is a phrase, return it. """
        if is_clause_t(e): return e
        if is_phrase_t(e): return e
        if e.category == STRING: return NounPhrase(e, features=e.features)
        if e.category == VAR: return NounPhrase(e, features=e.features)
        if e.category == WORD:
            if e.pos == POS_VERB: return VerbPhrase(e, features=e.features)
            if e.pos == POS_ADVERB: return VerbPhrase(e, features=e.features)
            return NounPhrase(e, features=e.features)
        if e.category == COORDINATION:
            return Coordination(*[promote_to_phrase(x) for x in e.coords],
                                conj=e.conj, features=e.features)
        return NounPhrase(e, features=e.features)


# **************************************************************************** #
#
#
# def lexicalise(msg, **kwargs):
#     """ Perform lexicalisation on the message depending on the type. """
#     if msg is None:
#         return None
#     elif isinstance(msg, numbers.Number):
#         return Numeral(msg)
#     elif isinstance(msg, str):
#         return String(msg)
#     elif isinstance(msg, (list, tuple)):
#         return [lexicalise(x, **kwargs) for x in msg]
#     elif isinstance(msg, Element):
#         return lexicalise_element(msg, **kwargs)
#     elif isinstance(msg, MsgSpec):
#         return lexicalise_message_spec(msg, **kwargs)
#     elif isinstance(msg, Message):
#         return lexicalise_message(msg, **kwargs)
#     elif isinstance(msg, Document):
#         return lexicalise_document(msg, **kwargs)
#     else:
#         raise TypeError('"%s" is neither a Message nor a MsgInstance' % msg)
#
#
# def lexicalise_element(elt, **kwargs):
#     """ See if element contains vars and if so, replace them
#     by templates.
#
#     """
#     get_log().debug('Lexicalising Element: {0}'.format(repr(elt)))
#     available_templates = kwargs.get('templates', templates)
#     # find arguments
#     args = elt.arguments()
#     # if there are any arguments, replace them by values
#     for arg in args:
#         result = available_templates.get(arg.id)
#         if result is None: continue
#         get_log().info('Replacing\n{0} in \n{1} by \n{2}.'
#                         .format(repr(arg), repr(elt), repr(result)))
#         if isinstance(result, str):
#             result = String(result)
#         result.features.update(elt.features)
#         if elt == arg:
#             return result
#         else:
#             elt.replace(arg, lexicalise(result, **kwargs))
#     return elt
#
#
# # each message should correspond to a clause
# def lexicalise_message_spec(msg, **kwargs):
#     """ Return Element corresponding to given message specification.
#     If the lexicaliser can not find correct lexicalisation, it returns None
#     and logs the error.
#
#     """
#     get_log().debug('Lexicalising message specs: {0}'.format(repr(msg)))
#     available_templates = kwargs.get('templates', templates)
#     template = None
#     try:
#         template = deepcopy(available_templates.get(msg.name))
#         # TODO: should MessageSpec correspond to a clause?
#         if template is None:
#             get_log().warning('No sentence template for "%s"' % msg.name)
#             result = String(str(msg))
#             result.features.update(msg.features)
#             return result
#         if hasattr(template, '__call__'):  # callable passed -- invoke
#             template = template(msg, **kwargs)
#         if isinstance(template, str):
#             result = String(template)
#             result.features.update(msg.features)
#             return result
#         template.features.update(msg.features)
#         if isinstance(template, Element) and not is_clause_t(template):
#             result = lexicalise(template)
#             return result  # return phrases and words
#         # find arguments
#         args = template.arguments()
#         # if there are any arguments, replace them by values
#         # TODO: check that features are propagated
#         for arg in args:
#             get_log().info('Replacing\n{0} in \n{1}.'
#                             .format(str(arg), repr(template)))
#             val = msg.value_for(arg.id)
#             # check if value is a template
#             if isinstance(val, (String, str)):
#                 t = templates.get(val.string if isinstance(val, String) else val)
#                 if t:
#                     val = t
#             val = lexicalise(val, **kwargs)
#             get_log().info('Replacement val = \n{0}'.format(repr(val)))
#             template.replace(arg, val)
#         return template
#     except Exception as e:
#         get_log().exception(str(e))
#         get_log().info('\tmessage: ' + repr(msg))
#         get_log().info('\ttemplate: ' + repr(template))
#
#
# # TODO: lexicalisation should replace Messages by {NLG Elements} and use
# # RST relations to connect the clauses when applicable.
# def lexicalise_message(msg, parenthesis=False, **kwargs):
#     """ Return a copy of Message with MsgSpecs replaced by NLG Elements. """
#     get_log().debug('Lexicalising message {0}'.format(msg))
#     if msg is None: return None
#     if isinstance(msg.nucleus, list):
#         nucleus = [lexicalise(x, **kwargs) for x in msg.nucleus if x is not None]
#     else:
#         nucleus = lexicalise(msg.nucleus, **kwargs)
#     satellites = [lexicalise(x, **kwargs) for x in msg.satellites if x is not None]
#
#     features = msg.features if hasattr(msg, 'features') else {}
#     # stick each message into a clause
#     result = None
#     if msg.rst == 'Conjunction' or msg.rst == 'Disjunction':
#         result = Coordination(*satellites, conj=msg.marker, features=features)
#     elif msg.rst == 'Imply':
#         get_log().debug('RST Implication: ' + repr(msg))
#         subj = promote_to_phrase(nucleus)
#         compl = promote_to_phrase(satellite)
#         compl.set_feature('COMPLEMENTISER', 'then')
#         result = subj
#         result.add_complement(compl)
#         result.add_front_modifier('if')
#     elif msg.rst == 'Equivalent':
#         result = promote_to_phrase(nucleus)
#         compl = promote_to_phrase(satellite)
#         compl.set_feature('COMPLEMENTISER', 'if and only if')
#         result.add_complement(compl)
#     elif msg.rst == 'ImpliedBy':
#         result = promote_to_phrase(nucleus)
#         compl = promote_to_phrase(satellite)
#         compl.set_feature('COMPLEMENTISER', 'if')
#         result.add_complement(compl)
#     elif msg.rst == 'Unless':
#         result = promote_to_phrase(nucleus)
#         compl = promote_to_phrase(satellite)
#         compl.set_feature('COMPLEMENTISER', 'unless')
#         result.add_complement(compl)
#     elif msg.rst == 'Equality':
#         result = Clause()
#         result.set_subj(nucleus)
#         object = satellite
#         tmp_vp = VP('is', object, features=features)
#         get_log().debug('Setting VP:\n' + repr(tmp_vp))
#         result.set_vp(tmp_vp)
#     elif msg.rst == 'Inequality':
#         result = Clause()
#         result.set_subj(nucleus)
#         object = satellite
#         features['NEGATED'] = 'true'
#         result.set_vp(VP('is', object, features=features))
#     elif msg.rst == 'Quantifier':
#         # quantifiers have multiple nuclei (variables)
#         quant = msg.marker
#         cc = Coordination(*nucleus, conj='and')
#         np = NounPhrase(cc, String(quant))
#
#         if quant.startswith('there exist'):
#             np.add_post_modifier(String('such that'))
#         else:
#             np.add_post_modifier(String(','))
#
#         result = promote_to_phrase(satellite)
#
#         front_mod = realisation.simple_realisation(np)
#         # remove period
#         if front_mod.endswith('.'): front_mod = front_mod[:-1]
#         # lower case the first letter
#         front_mod = front_mod[0].lower() + front_mod[1:]
#         # front_mod should go in front of existing front_mods
#         # In case of CC, modify the first coordinate
#         if result.type == COORDINATION:
#             result.coords[0].add_front_modifier(String(front_mod), pos=0)
#         else:
#             result.add_front_modifier(String(front_mod), pos=0)
#         get_log().debug('Result:\n' + repr(result))
#     elif msg.rst == 'Negation':
#         result = Clause(Pronoun('it'), VP('is', NP('the', 'case'),
#                                           features={'NEGATED': 'true'}))
#         cl = promote_to_phrase(nucleus)
#         cl.set_feature('COMPLEMENTISER', 'that')
#         if parenthesis:
#             cl.add_front_modifier('(')
#             cl.add_post_modifier(')')
#         result.vp.add_complement(cl)
#     else:
#         get_log().debug('RST relation: ' + repr(msg))
#         get_log().debug('RST nuclei:  ' + repr(nucleus))
#         get_log().debug('RST satellite: ' + repr(satellites))
#         result = Message(msg.rst, nucleus, *satellites)
#         result.marker = msg.marker
#         # TODO: decide how to handle features. Add to all? Drop?
#         # return ([nuclei] if nuclei else []) + [x for x in satellites]
#     result.features.update(features)
#     return result
#
#
# def lexicalise_document(doc, **kwargs):
#     """ Return a copy of a Document with MsgSpecs replaced by NLG Elements. """
#     get_log().debug('Lexicalising document.')
#     if doc is None: return None
#     title = lexicalise(doc.title, **kwargs)
#     sections = [lexicalise(x, **kwargs) for x in doc.sections if x is not None]
#     return Document(title, *sections)
#
#
# def create_template_from(string):
#     return eval(string)
#
#
# class SentenceTemplates:
#     """SentenceTemplates provides mapping from STRIPS operators to sentences.
#         The keys are actionN where N is the number of parameters. These
#         are mapped to string compatible with string.format().
#     """
#
#     def __init__(self, templates=None):
#         self.templates = templates if templates is not None else {}
#         self.templates['simple_message'] = Clause(None, Var('val'))
#         self.templates['string'] = Clause(None, VerbPhrase(Var('val')))
#
#     def get(self, key):
#         if key in self.templates:
#             return deepcopy(self.templates[key])
#         else:
#             return None
#
#     # for backwards compatibility
#     template = get
#
#
# templates = SentenceTemplates()
#
#
# def add_templates(newtemplates):
#     """ Add the given templates to the default SentenceTemplate instance. """
#     for k, v in newtemplates.items():
#         templates.templates[k] = v
#
#
# def add_template(k, v, replace=True):
#     if replace or (not k in templates.templates):
#         templates.templates[k] = v
#         return True
#     else:
#         return False
#
#
# def del_template(k, silent=True):
#     if silent and k not in templates.templates: return False
#     del templates.templates[k]
#
#
# def string_to_template(s):
#     return eval(s)
