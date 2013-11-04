from copy import deepcopy
import re

from nlg.structures import *
from nlg.aggregation import *
from nlg.lexicalisation import SentenceTemplates, lexicalise
import nlg.realisation as realisation
import nlg.format as format


class LanguageGen:
    """LanguageGen class represents the NLG module used for realising plans."""
    
    def __init__(self):
        self.nlg = Nlg()

    def realise_plan(self, plan):
        return self.nlg.realise_plan(plan)

    def realise_world(self, world, state):
        faulty = 0
        for sensor, reading in world.items():
            if reading > 5:
                faulty += 1

        if 0 < faulty:
            text = '{} of the sensors report high vibrations in section a.\n'.format(faulty)
        else:
            text = 'All sensors report nominal values.\n'

        return text


class Context:
    def __init__(self, ontology=None):
        self.ontology = ontology
        self.referents = dict()
        self.last_referent = None


class REG:
    def __init__(self):
        pass

    def gre(self, referent, context):
        # can we use a pronoun?
        # actually, using a pronoun for the last ref can still be ambiguous :-)
#        if referent == context.last_referent:
#            return NP(Word('it', 'PRONOUN'))

        result = None

        if referent in context.referents:
            result = self._do_repeated_reference(referent, context)
        else:
            result = self._do_initial_reference(referent, context)
        return result

    def _do_initial_reference(self, referent, context):
        result = None

        # do we have information about the referent?
        try:
            onto = context.ontology
            if onto is None: print('GRE does not have ontology!')

            entity_type = onto.best_entity_type(':' + referent)
            result = NP(Word(entity_type, 'NOUN'))
            print('\t%s: type "%s"' % (referent, entity_type))
            # if the object is the only one in the domain, add 'the'
            distractors = onto.entities_of_type(':' + entity_type)
            print('\tdistractors: %s' % str(distractors))
            count = len(distractors)

            if count == 1:
                # save the RE without the determiner
                context.referents[referent] = (True, deepcopy(result))
                # this should really be done by simpleNLG...
                if entity_type[0] in "aeiouy":
                    result.spec = Word('an', 'DETERMINER')
                else:
                    result.spec = Word('a', 'DETERMINER')
            else:
                context.referents[referent] = (False, result)
                # else add the number to distinguish from others
                number = None
                tmp = re.search(r"([^0-9]+)([0-9]+)$", referent)
                if (tmp is not None):
                    number = tmp.group(2)

                if (number is not None):
                    result.add_complement(Word(number))
        except Exception as msg:
            # if we have no info, assume referent is not unique
            result = NP(Word(referent, 'NOUN'))
            context.referents[referent] = (False, result)
            print('GRE for "%s" failed : "%s"' % (referent, str(msg)))

        context.last_referent = referent
        return result

    def _do_repeated_reference(self, referent, context):
        result = None

        is_unique, re = context.referents[referent]
        if is_unique:
            result = deepcopy(re)
            result.spec = Word('the', 'DETERMINER')
        else:
            result = re
        return result

    def _count_type_instances(self, entity_type, object_map):
        count = 0
        for k, v in object_map.items():
            if v == entity_type: count += 1
        return count


class Nlg:
    def __init__(self):
        self.templates = SentenceTemplates()
        self.reg = REG()

    def realise_plan(self, plan):
        plan_list = list()
        for action_idx in plan.sequence:
            action = plan.actions[action_idx]
            num_params = len(action.signature)
            params = list()
            for p in action.signature:
                params.append(p[0]) # get the name of the parameter

            key = "{0}{1}".format(action.name, num_params)
            sent = self.templates.template(key)
            if None != sent:
                print("sent: %s \n\tparams %s" % (sent, params))
                plan_list.append(sent.format(*params))
            else:
                print("Key %s not found\n" % key)

        sentences = list()
        for s in plan_list:
            words = s.split()
            words[0] = words[0].capitalize()
            sentences.append(" ".join(words))

        text = ". ".join(sentences)
        if text != "":
            text += "."

        return text

    def document_to_text(self, doc):
        summary = lexicalise(doc)
#        summary = aggregation.aggregate(summary)
#        summary = reg.generate(msgs, doc, Context(doc.ontology))
        summary = realisation.realise(summary)
        summary = format.to_text(summary)
        return summary

    def messages_to_text(self, messages):
        text = [str(x) for x in messages]
        text = map(lambda e: e[:1].upper() + e[1:], text)
        return ('.\n'.join(text))
    
    def lexicalise(self, document):
        """ Create a list of syntax trees representing the sequence of actions
        in a given plan.
        
        """
        tasks = list(map(lambda x: self.lexicalise_task(x, document),
                            document.workflow.tasks()))
        return tasks

    def lexicalise_task(self, task, document):
        """ Convert a task to a syntax tree with lexical items in it. """
#        print('Lexicalising task %s' % str(task))
        params = task.input_params[:]
        key = task.name if task.name != '' else task.id
        sent = deepcopy(self.templates.template(key))
        if None != sent:
            self._replace_placeholders_with_params(sent, params)
        else:
            print('Key "%s" or id "%s" not found' % (task.name, task.id))
        return sent

    def task_to_text(self, task, document, context):
        """ Convert a task to text by lexicalising and performing REG. """
        msgs = [self.lexicalise_task(task, document)]
#        print('Before aggregation: %s' % msgs)
        msgs = self.synt_aggregation(msgs)
#        print('Before gre: %s' % msgs)
        msgs = self.gre(msgs, document, context)
#        print('Before text: %s' % msgs)
        if msgs == [None]: text = task.id
        else: text = self.messages_to_text(msgs)
        return text + '.'

    def _replace_placeholders_with_params(self, template, params):
#        print('Replacing params in template:\n%s' % str(template))
#        print('Params: \n\t %s' % str(params))
        for c in sentence_iterator(template):
            if (isinstance(c, PlaceHolder)):
                id = c.id
                var = params[id]
                c.object = var
#                print('Replacing parameter %d with %s' % (id, var))

    def gre(self, msgs, document, context):
        """ Replace placeholders with NPs
        The placeholders should already have names in them, so just replace
        each of them by an NP.
        
        """
        if context is None: context = Context(document.ontology)

        messages = deepcopy(msgs)
        for m in messages:
            self._replace_placeholders_with_nps(m, context)
        return messages

    def _replace_placeholders_with_nps(self, message, context):
        for i in sentence_iterator(message):
            if (not isinstance(i, PlaceHolder)):
                continue
            
            refexp = self.reg.gre(i.object, context)
#            np = NP(Word(refexp))
            # replace the placeholder by an RE
            replace_element(message, i, refexp)

    def synt_aggregation(self, messages, max=3):
        """ Take a list of messages and combine messages that are sufficiently
        similar.
        
        messages - a list of messages to combine
        max      - a maximum number of messages to aggregate
        
        The algorithm relies on shared structure of the messages. If, for 
        example, two messages share the subject, combine the VPs into 
        a conjunction. Do not combine more than 'max' messages into each other.

        """
        if messages is None: return
        if len(messages) < 2: return messages

        aggregated = list()
        i = 0
        while i < len(messages) - 1:
            msg, increment = self._do_aggregate(messages, i, max)
            aggregated.append(msg)
            i += increment

        return aggregated

    def _do_aggregate(self, messages, i, max):
        lhs = messages[i]
        j = i + 1
        increment = 1
        while j < len(messages) and self._can_aggregate(lhs, max):
            print('LHS = %s' % lhs)
            rhs = messages[j]
            if self._can_aggregate(rhs, max):
                tmp = try_to_aggregate(lhs, rhs)
                if tmp is not None:
                    lhs = tmp
                    increment += 1
                    j += 1
                else:
                    break
            # cannot aggregate. can we skip it?
            elif self._can_skip(messages, j):
                j += 1
                increment += 1
            else:
                break
        return (lhs, increment)

    def _can_aggregate(self, message, max):
        """ Return true if this message can be aggregated.
        max - maximum number of coordinates in a coordingated clause
        If the message does not have a coordinated clause or if the number 
        of coordinates is less then 'max', return True.

        """
        if message is None: return False
        for part in sentence_iterator(message):
            if not isinstance(part, CC):
                continue
            else:
                return (len(part.coords) < max)
        # simple sentence - no coordinated clause
        return True

    def _can_skip(self, messages, j):
        """ Return true if this element can be skipped. """
        return (messages[j] is None)












