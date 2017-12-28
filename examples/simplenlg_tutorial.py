import logging

from nlglib.realisation.simplenlg.realisation import Realiser
from nlglib.microplanning import *


realise = Realiser(host='roman.kutlak.info')


def main():
    c = Clause('Mary', 'chase', 'the monkey')
    print(realise(c))
    tense()
    negation()
    interrogative()
    complements()
    modifiers()
    coordinations()
    prepositional_phrase()
    coordinated_clause()
    subordinate_clause()


def tense():
    c = Clause('Mary', 'chase', 'the monkey')
    c['TENSE'] = 'PAST'
    print(realise(c))
    c['TENSE'] = 'FUTURE'
    print(realise(c))


def negation():
    c = Clause('Mary', 'chase', 'the monkey')
    c['NEGATED'] = 'true'
    print(realise(c))


def interrogative():
    c = Clause('Mary', 'chase', 'the monkey')
    c['INTERROGATIVE_TYPE'] = 'YES_NO'
    print(realise(c))
    c['INTERROGATIVE_TYPE'] = 'WHO_OBJECT'
    print(realise(c))


def complements():
    c = Clause('Mary', 'chase', 'the monkey',
               complements=['very quickly', 'despite her exhaustion'])
    print(realise(c))


def modifiers():
    subject = NP('Mary')
    verb = VP('chase')
    objekt = NP('the', 'monkey')
    subject += Adjective('fast')
    c = Clause()
    c.subject = subject
    c.predicate = verb
    c.object = objekt
    print(realise(c))
    verb += Adverb('quickly')
    c = Clause(subject, verb, objekt)
    print(realise(c))


def coordinations():
    subject1 = NP('Mary')
    subject2 = NP('your', 'giraffe')  # BUG
    subj1 = Coordination(subject1, subject2)
    subj2 = CC(subject1, subject2)
    assert subj1 == subj2
    c = Clause(subj1, VP('chase'), NP('the', 'monkey'))
    print(realise(c))
    subject1 = NP('Mary')
    subject2 = NP('your giraffe')
    subj = subject1 + subject2
    obj = NP('the monkey') + NP('George')
    obj += NP('Martha')
    c = Clause(subj, VP('chase'), obj)
    print(realise(c))
    obj.conj = 'or'
    print(realise(c))


def prepositional_phrase():
    c = Clause('Mary', 'chase', 'the monkey')
    c.complements += PP('in', 'the park')
    print(realise(c))
    c = Clause('Mary', 'chase', 'the monkey')
    c.complements += PP('in', NP('the', 'park'))
    print(realise(c))


def coordinated_clause():
    s1 = Clause('my cat', 'like', 'fish', features={'TENSE': 'PAST'})
    s2 = Clause('my dog', 'like', 'big bones', features={'TENSE': 'PRESENT'})
    s3 = Clause('my horse', 'like', 'grass', features={'TENSE': 'FUTURE'})
    c = s1 + s2 + s3
    c = CC(s1, s2, s3)
    print(realise(s1))
    print(realise(s2))
    print(realise(s3))
    print(realise(s1 + s2))
    print(realise(c))


def subordinate_clause():
    p = Clause("I", "be", "happy")
    q = Clause("I", "eat", "fish")
    q['COMPLEMENTISER'] = "because"
    q['TENSE'] = 'PAST'
    p.complements += q
    print(realise(p))


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    main()
