import json
import unittest

from copy import copy, deepcopy

from nlglib.microplanning import *

from nlglib.features import DISCOURSE_FUNCTION, category


class TestElement(unittest.TestCase):
    def setUp(self):
        self.e = Element(features={'foo': 'bar'})

    def test_basics(self):
        """ Test ctor. """
        e = Element()
        self.assertFalse(bool(e))

    def test_copy(self):
        e2 = copy(self.e)
        self.assertEqual(self.e, e2)

    def test_deepcopy(self):
        e2 = deepcopy(self.e)
        self.assertEqual(self.e, e2)
        self.assertNotEqual(id(self.e.features), id(e2.features))

    def test_to_json(self):
        s = self.e.to_json()
        self.assertIn('<class \'nlglib.microplanning.struct.Element\'>', s)
        self.assertIn('"foo": "bar"', s)

    def test_from_json(self):
        s = self.e.to_json()
        e2 = Element.from_json(s)
        self.assertEqual(self.e, e2)

    def test_feature_lookup(self):
        self.assertEqual('bar', self.e['foo'].value)

    def test_feature_del(self):
        del self.e['foo']
        self.assertNotIn('foo', self.e)

    def test_feature_set(self):
        self.e['zzz'] = 'baz'
        self.assertIn('zzz', self.e.features)
        self.assertEqual('baz', self.e['zzz'].value)

    def test_add(self):
        self.assertEqual(Element(), Element() + Element())

    def test_arguments(self):
        """ Test retrieving arguments from an Element. """
        e = Element()
        args = list(e.arguments())
        self.assertEqual([], args)

    def test_set_argument(self):
        """ Test replacing an argument with a value (Element). """
        # does nothing on Element

    def test_features_to_xml_attributes(self):
        """ Test formatting features so that they can be put into XML. """
        e = Element()
        expected = ' TENSE="PAST" cat="ELEMENT"'
        e['TENSE'] = 'past'
        data = XmlVisitor.features_to_xml_attributes(e)
        self.assertEqual(expected, data)

        expected = ' PROGRESSIVE="true" TENSE="PAST" cat="ELEMENT"'
        e['ASPECT'] = 'progressive'
        data = XmlVisitor.features_to_xml_attributes(e)
        self.assertIn('TENSE="PAST"', data)
        self.assertIn('PROGRESSIVE="true"', data)
        self.assertEqual(expected, data)

    def test_eq(self):
        """ Test the test of equality :-) """
        e1 = Element()
        e2 = Element()
        self.assertEqual(e1, e2)

        e1['TENSE'] = 'future'
        self.assertNotEqual(e1, e2)

        e2['ASPECT'] = 'progressive'
        self.assertNotEqual(e1, e2)

        e1['ASPECT'] = 'progressive'
        e2['TENSE'] = 'future'
        self.assertEqual(e1, e2)


class TestElementList(unittest.TestCase):
    def setUp(self):
        self.e = ElementList(['happy', 'birthday'])

    def test_setitem(self):
        self.e[0] = 'merry'
        self.assertEqual(String('merry'), self.e[0])

    def test_concat(self):
        e2 = self.e + ['dude']
        for e in e2:
            with self.subTest(actual=e):
                self.assertTrue(isinstance(e, String))

    def test_add(self):
        el = ElementList()
        el += ['foo', 'bar']
        for e in el:
            with self.subTest(actual=e):
                self.assertTrue(isinstance(e, String))

    def test_copy(self):
        e2 = copy(self.e)
        self.assertEqual(self.e, e2)
        self.assertEqual(id(self.e[0]), id(e2[0]))
        self.assertEqual(id(self.e[1]), id(e2[1]))

    def test_deepcopy(self):
        e2 = deepcopy(self.e)
        self.assertEqual(self.e, e2)
        self.assertNotEqual(id(self.e[0]), id(e2[0]))
        self.assertNotEqual(id(self.e[1]), id(e2[1]))

    def test_to_json(self):
        s = self.e.to_json()
        self.assertIn('<class \'nlglib.microplanning.struct.ElementList\'>', s)

    def test_from_json(self):
        s = self.e.to_json()
        e2 = ElementList.from_json(s)
        self.assertEqual(self.e, e2)

    # noinspection PyTypeChecker
    def test_adding_elements(self):
        """ Test adding modifiers. """
        tmp = ElementList()
        tmp.append('yesterday')
        expected = [String('yesterday')]
        self.assertEqual(expected, tmp)

        tmp += ['late', Word('evening', 'NOUN')]
        expected.append(String('late'))
        expected.append(Word('evening', 'NOUN'))
        self.assertEqual(expected, tmp)

    def test_deleting_elements(self):
        """ Test deleting modifiers. """
        tmp = ElementList(['to', 'the', 'little', 'shop'])
        expected = [String(x) for x in ('to', 'the', 'little', 'shop')]
        self.assertEqual(expected, tmp)
        self.assertIn('little', tmp)
        tmp.remove('little')
        expected = expected[:2] + expected[3:]
        self.assertEqual(expected, tmp)


class TestVar(unittest.TestCase):
    def setUp(self):
        self.e = Var('x', features={'foo': 'bar'})

    def test_copy(self):
        e2 = copy(self.e)
        self.assertEqual(self.e, e2)
        self.assertEqual(self.e.value, e2.value)

    def test_deepcopy(self):
        e2 = deepcopy(self.e)
        self.assertEqual(self.e, e2)
        self.assertEqual(self.e.value, e2.value)
        self.assertNotEqual(id(self.e.features), id(e2.features))

    def test_to_json(self):
        s = self.e.to_json()
        self.assertIn('<class \'nlglib.microplanning.struct.Var\'>', s)
        self.assertIn('"foo": "bar"', s)
        self.assertIn('"id": "x"', s)

    def test_from_json(self):
        s = self.e.to_json()
        e2 = Element.from_json(s)
        self.assertEqual(self.e, e2)

    def test_eq(self):
        """ Test equality. """
        self.assertEqual(Var(), Var())

        p1 = Var('arg1')
        p2 = Var('arg2')
        self.assertNotEqual(p1, p2)

        p2 = Var('arg1')
        self.assertEqual(p1, p2)

        p1['countable'] = 'no'
        self.assertNotEqual(p1, p2)

        p2['countable'] = 'no'
        self.assertEqual(p1, p2)

        p1 = Var('arg1', 'drum')
        p1['countable'] = 'no'
        self.assertNotEqual(p1, p2)

        p2.set_value('drum')
        self.assertEqual(p1, p2)

    def test_repr(self):
        """ Test debug printing. """
        expected = "Var('obj1', Word('obj1', 'NOUN'))"
        p = Var('obj1')
        self.assertEqual(expected, repr(p))

        expected = "Var('obj1', Word('obj1', 'NOUN'), features={'countable': 'yes'})"
        p['countable'] = 'yes'
        self.assertEqual(expected, repr(p))


class TestString(unittest.TestCase):
    def setUp(self):
        self.e = String('happiness', features={'foo': 'bar'})

    def test_eq(self):
        """ Test equality. """
        s1 = String()
        s2 = String()
        self.assertEqual(s1, s2)

        s1 = String('hello')
        s2 = String('word')
        self.assertNotEqual(s1, s2)

        s1['type'] = 'greeting'
        s2 = String('hello')
        self.assertNotEqual(s1, s2)

        s2['type'] = 'greeting'
        self.assertEqual(s1, s2)

        self.assertEqual(String('please'), raise_to_element('please'))

        np = NP('my', 'house')
        expected = [Word('my', 'DETERMINER'), Word('house', 'NOUN')]
        self.assertEqual(expected, list(np.elements()))

    def test_copy(self):
        e2 = copy(self.e)
        self.assertEqual(self.e, e2)
        self.assertEqual(self.e.value, e2.value)

    def test_deepcopy(self):
        e2 = deepcopy(self.e)
        self.assertEqual(self.e, e2)
        self.assertEqual(self.e.value, e2.value)
        self.assertNotEqual(id(self.e.features), id(e2.features))

    def test_to_json(self):
        s = self.e.to_json()
        self.assertIn('<class \'nlglib.microplanning.struct.String\'>', s)
        self.assertIn('"foo": "bar"', s)
        self.assertIn('"value": "happiness"', s)

    def test_from_json(self):
        s = self.e.to_json()
        e2 = Element.from_json(s)
        self.assertEqual(self.e, e2)


class TestWord(unittest.TestCase):
    def setUp(self):
        self.e = Word('happiness', 'NOUN', features={'foo': 'bar'})

    def test_copy(self):
        e2 = copy(self.e)
        self.assertEqual(self.e, e2)
        self.assertEqual(self.e.word, e2.word)

    def test_deepcopy(self):
        e2 = deepcopy(self.e)
        self.assertEqual(self.e, e2)
        self.assertEqual(self.e.word, e2.word)
        self.assertNotEqual(id(self.e.features), id(e2.features))

    def test_to_json(self):
        s = self.e.to_json()
        self.assertIn('<class \'nlglib.microplanning.struct.Word\'>', s)
        self.assertIn('"pos": "NOUN"', s)
        self.assertIn('"foo": "bar"', s)
        self.assertIn('"word": "happiness"', s)

    def test_from_json(self):
        s = self.e.to_json()
        e2 = Element.from_json(s)
        self.assertEqual(self.e, e2)

    def test_str(self):
        """ Test basic printing. """
        w = Word('foo', 'NOUN')
        expected = 'foo'
        self.assertEqual(expected, str(w))

        w['countable'] = 'yes'
        self.assertEqual(expected, str(w))

    def test_repr(self):
        """ Test debug printing. """

        w = Word('foo', 'NOUN')
        expected = "Word('foo', 'NOUN')"
        self.assertEqual(expected, repr(w))

        expected = "Word('foo', 'NOUN', features={'countable': 'yes'})"
        w['countable'] = 'yes'
        self.assertEqual(expected, repr(w))

    def test_eq(self):
        """ Test equality. """
        w1 = Word('foo', 'NOUN')
        w2 = Word('foo', 'VERB')
        self.assertNotEqual(w1, w2)

        w2.pos = 'NOUN'
        self.assertEqual(w1, w2)

        w2['role'] = 'subject'
        self.assertNotEqual(w1, w2)

        del w2['role']
        self.assertEqual(w1, w2)

        w1['role'] = 'subject'
        w2['role'] = 'object'
        self.assertNotEqual(w1, w2)

        w2['role'] = 'subject'
        self.assertEqual(w1, w2)


class TestCoordination(unittest.TestCase):
    def setUp(self):
        self.e = Coordination('big', 'fat')

    def test_copy(self):
        e2 = copy(self.e)
        self.assertEqual(self.e, e2)
        self.assertEqual(self.e.coords, e2.coords)

    def test_deepcopy(self):
        e2 = deepcopy(self.e)
        self.assertEqual(self.e, e2)
        self.assertEqual(self.e.coords, e2.coords)
        self.assertNotEqual(id(self.e.features), id(e2.features))
        self.assertNotEqual(id(self.e.coords), id(e2.coords))
        cs = list(self.e.elements())
        cs2 = list(e2.elements())
        self.assertEqual(cs, cs2)
        for c1, c2 in zip(cs, cs2):
            with self.subTest(actual=(c1, c2)):
                self.assertNotEqual(id(c1), id(c2))

    def test_to_json(self):
        s = self.e.to_json()
        self.assertIn('<class \'nlglib.microplanning.struct.Coordination\'>', s)
        self.assertIn('"conj":', s)

    def test_from_json_basic(self):
        s = self.e.to_json()
        e2 = Element.from_json(s)
        self.assertEqual(self.e, e2)

    def test_from_json_complex(self):
        c1 = Coordination('bar', 'baz')
        c2 = Coordination('foo', c1)
        s = c2.to_json()
        c3 = Element.from_json(s)
        self.assertEqual(c2, c3)
        self.assertEqual(c1.parent, c2)
        self.assertEqual(c3.coords[1].parent, c3)

    def test_replace(self):
        """ Test replacing an element. """
        self.assertTrue(self.e.replace('fat', 'fluffy'))
        self.assertFalse(self.e.replace('fat', 'fluffy'))
        self.assertEqual(['big', 'fluffy'], [x.string for x in self.e.coords])

        p = Coordination('apple', 'banana', 'pear', conj='')
        expected = [String('apple'), String('banana'), String('pear')]
        self.assertEqual(expected, list(p.elements()))

        p.replace(String('banana'), String('potato'))
        expected = [String('apple'), String('potato'), String('pear')]
        self.assertEqual(expected, list(p.elements()))

    def test_elements(self):
        """ Test iterating through constituents. """
        p = Coordination('apple', 'banana', 'pear')
        expected = [String('apple'), String('banana'), String('and'), String('pear')]
        self.assertEqual(expected, list(p.elements()))


class TestPhrase(unittest.TestCase):
    def setUp(self):
        self.phrase = Phrase(features={'foo': 'bar'},
                             head='say',
                             premodifiers=['please'],
                             complements=['hello', 'world'],
                             postmodifiers=['dude'])

    def test_init(self):
        p = self.phrase
        self.assertEqual(String('say'), p.head)
        self.assertIn(String('please'), p.premodifiers)
        self.assertIn(String('hello'), p.complements)
        self.assertIn(String('world'), p.complements)
        self.assertIn(String('dude'), p.postmodifiers)

    def test_copy(self):
        p2 = copy(self.phrase)
        self.assertEqual(self.phrase, p2)

    def test_deepcopy(self):
        p = self.phrase
        p2 = deepcopy(p)
        self.assertEqual(self.phrase, p2)
        self.assertNotEqual(id(p.head), id(p2.head))
        self.assertEqual(p, p.head.parent)
        self.assertEqual(p2, p2.head.parent)

    def test_deepcopy_2(self):
        """Test deepcopy on nested phrases."""
        p = Phrase(head=self.phrase, complements=['that', 'stands', 'tall'])
        p2 = deepcopy(p)
        self.assertEqual(self.phrase, p.head)
        self.assertEqual(self.phrase, p2.head)
        self.assertNotEqual(id(self.phrase), id(p2.head))
        self.assertEqual(p2.head.parent, p2)
        self.assertEqual(p2.head.head.parent, p2.head)

    def test_modifier_addition(self):
        """Test that adjective is added as a premodifier."""
        mod = Word('happy', pos=category.ADJECTIVE)
        self.phrase += mod
        self.assertIn(mod, self.phrase.premodifiers)

    def test_modifier_addition2(self):
        """Test that adverb is added as a premodifier."""
        mod = Word('happily', pos=category.ADVERB)
        self.phrase += mod
        self.assertIn(mod, self.phrase.premodifiers)

    def test_modifier_addition3(self):
        """Test that preposition is added as a complement."""
        mod = Word('over', pos=category.PREPOSITION)
        self.phrase += mod
        self.assertIn(mod, self.phrase.complements)

    def test_set_head(self):
        head = Word('shout', pos=category.VERB)
        self.phrase.head = head
        self.assertEqual(head, self.phrase.head)

    def test_set_empty_head(self):
        self.phrase.head = None
        self.assertEqual(Element(), self.phrase.head)

    def test_elements(self):
        p = self.phrase
        for c in p.elements():
            with self.subTest(actual=c):
                self.assertTrue(isinstance(c, (Phrase, String)))
        self.assertEqual(p, list(p.elements(itself='first'))[0])

    def test_elements2(self):
        """ Test iterating through elements. """
        p = Phrase()
        self.assertEqual([], list(p.elements()))

        p.head = Word('head', 'NOUN')
        self.assertEqual([Word('head', 'NOUN')], list(p.elements()))

        p2 = Phrase()
        p2.head = Word('forward', 'ADVERB')
        p.complements.append(p2)
        expected = [Word('head', 'NOUN'), Phrase(head=Word('forward', 'ADVERB'))]
        self.assertEqual(expected, list(p.elements()))
        expected = [Word('head', 'NOUN'), Word('forward', 'ADVERB')]
        self.assertEqual(expected, list(p.elements(recursive=True)))

    def test_replace(self):
        p = self.phrase
        self.assertFalse(p.replace('worlds', 'universe'))
        self.assertTrue(p.replace('world', 'universe'))
        self.assertNotIn(String('world'), p.complements)
        self.assertIn(String('universe'), p.complements)

    def test_replace2(self):
        """ Test replacing a constituent. """
        p = Phrase()
        hi = Word('hi', 'EXCLAMATION')
        hello = Word('hello', 'EXCLAMATION')
        self.assertEqual(False, p.replace(hi, hello))
        ph = Var('arg_name')
        p.head = hi
        p.complements.append(ph)
        self.assertEqual(True, p.replace(hi, hello))
        self.assertEqual(hello, p.head)

        ph2 = Var('arg_place')
        p2 = Phrase()
        p2.head = ph2
        p.postmodifiers.append(p2)

        p.replace(Var('arg_place'), Word('Aberdeen', 'NOUN'))
        self.assertEqual(False, Var('arg_place') in list(p.elements()))

    def test_replace_using_key(self):
        p = Phrase(features={'foo': 'bar'},
                   head='say',
                   premodifiers=['please'],
                   complements=['hello', String('world', id=1)],
                   postmodifiers=['dude'])
        self.assertFalse(p.replace(String('worlds', id=2), 'universe',
                                   key=lambda x: x.id))
        self.assertTrue(p.replace(String('worlds', id=1), 'universe',
                                  key=lambda x: x.id))
        self.assertNotIn(String('world'), p.complements)
        self.assertIn(String('universe'), p.complements)

    def test_to_json(self):
        s = self.phrase.to_json()
        self.assertIn('<class \'nlglib.microplanning.struct.Phrase\'>', s)
        self.assertIn('please', s)
        self.assertIn('say', s)
        self.assertIn('hello', s)

    def test_from_json(self):
        s = self.phrase.to_json()
        p2 = json.loads(s, cls=ElementDecoder)
        self.assertEqual(self.phrase, p2)
        self.assertEqual(p2, p2.head.parent)

    def test_str(self):
        """ Test basic printing. """
        p = Phrase()
        expected = ''
        self.assertEqual(expected, str(p))

        p.head = 'went'
        expected = 'went'
        self.assertEqual(expected, str(p))

        p.premodifiers.append('Peter')
        expected = 'Peter went'
        self.assertEqual(expected, str(p))

        p.complements.append('to')
        expected = 'Peter went to'
        self.assertEqual(expected, str(p))

        p.postmodifiers.append('Russia')
        expected = 'Peter went to Russia'
        self.assertEqual(expected, str(p))

        p['TENSE'] = 'past'
        expected = 'Peter went to Russia'
        self.assertEqual(expected, str(p))

    def test_repr(self):
        """ Test debug printing. """
        p = Phrase()
        expected = 'Phrase()'
        self.assertEqual(expected, repr(p))

        p.head = 'went'
        expected = "Phrase(String('went'))"
        self.assertEqual(expected, repr(p))

        p.premodifiers.append('Peter')
        expected = "Phrase(String('went'),\n       premodifiers=[String('Peter')])"
        self.assertEqual(expected, repr(p))

        p.complements.append('to')
        expected = """\
Phrase(String('went'),
       String('to'),
       premodifiers=[String('Peter')])"""
        self.assertEqual(expected, repr(p))

        p.postmodifiers.append('Russia')
        expected = """\
Phrase(String('went'),
       String('to'),
       premodifiers=[String('Peter')],
       postmodifiers=[String('Russia')])"""
        self.assertEqual(expected, repr(p))

        p['TENSE'] = 'past'
        expected = """\
Phrase(String('went'),
       String('to'),
       features={'TENSE': 'past'},
       premodifiers=[String('Peter')],
       postmodifiers=[String('Russia')])"""
        self.assertEqual(expected, repr(p))

    def test_eq(self):
        """ Test equality. """
        p1 = Phrase()
        p2 = Phrase()
        self.assertEqual(p1, p2)

        p1.head = Word('went', 'VERB', {'TENSE': 'PAST'})
        self.assertNotEqual(p1, p2)

        p2.head = Word('went', 'VERB', {'TENSE': 'PAST'})
        self.assertEqual(p1, p2)

        p1.premodifiers.append('Peter')
        self.assertNotEqual(p1, p2)

        p2.premodifiers.append('Peter')
        self.assertEqual(p1, p2)

        p1.complements.append('to')
        self.assertNotEqual(p1, p2)

        p2.complements.append('to')
        self.assertEqual(p1, p2)

        p1.postmodifiers.append('Russia')
        self.assertNotEqual(p1, p2)

        p2.postmodifiers.append('Russia')
        self.assertEqual(p1, p2)

        p1['TENSE'] = 'past'
        self.assertNotEqual(p1, p2)

        p2['TENSE'] = 'past'
        self.assertEqual(p1, p2)


    def test_arguments(self):
        """ Test getting arguments. """
        p = Phrase()
        self.assertEqual([], list(p.arguments()))
        ph = Var('arg_name')
        p.head = Word('ask', 'VERB')
        p.complements.append(ph)
        self.assertEqual([ph], list(p.arguments()))

        ph2 = Var('arg_place')
        p2 = Phrase()
        p2.head = ph2
        p.postmodifiers.append(p2)
        args = list(p.arguments())
        self.assertEqual(ph, args[0])
        self.assertEqual(ph2, args[1])


class TestNounPhrase(unittest.TestCase):

    def setUp(self):
        self.phrase = NounPhrase(head='man', specifier='the',
                                 premodifiers=['small', 'happy'])

    def test_init(self):
        self.assertEqual(String('the'), self.phrase.specifier)
        self.assertEqual(category.NOUN_PHRASE, self.phrase.category)

    def test_copy(self):
        p = self.phrase
        p2 = copy(p)
        self.assertEqual(p, p2)

    def test_deepcopy(self):
        p = self.phrase
        p2 = deepcopy(p)
        self.assertEqual(p, p2)
        self.assertNotEqual(id(p), id(p2))
        self.assertNotEqual(id(p.specifier), id(p2.specifier))

    def test_replace(self):
        """Test replacing specifier."""
        self.phrase.replace('the', 'a')
        self.assertEqual(String('a'), self.phrase.specifier)

    def test_replace2(self):
        """Test replacing an element."""
        self.phrase.replace('small', 'big')
        self.assertNotIn(String('small'), self.phrase.premodifiers)
        self.assertIn(String('big'), self.phrase.premodifiers)

    def test_replace3(self):
        """ Test replacing an element. """
        p = NounPhrase(specifier=String('my'), head='Simpsons')
        expected = [String('the'), String('Simpsons')]
        p.replace(String('my'), String('the'))
        self.assertEqual(expected, list(p.elements()))

    def test_to_json(self):
        s = self.phrase.to_json()
        self.assertIn('<class \'nlglib.microplanning.struct.NounPhrase\'>', s)
        self.assertIn('the', s)
        self.assertIn('small', s)
        self.assertIn('man', s)

    def test_from_json(self):
        s = self.phrase.to_json()
        p2 = json.loads(s, cls=ElementDecoder)
        self.assertEqual(self.phrase, p2)
        self.assertEqual(p2, p2.head.parent)
        self.assertEqual(p2, p2.specifier.parent)

    def test_elements(self):
        """ Test iterating through constituents. """
        p = NounPhrase(specifier='the', head='Simpsons')
        expected = [String('the'), String('Simpsons')]
        self.assertEqual(expected, list(p.elements()))


class TestVerbPhrase(unittest.TestCase):

    def setUp(self):
        self.phrase = VerbPhrase('give', 'me', 'it')

    def test_init(self):
        self.assertIn(String('me'), self.phrase.complements)

    def test_object_property(self):
        phrase = VerbPhrase('give', indirect_object='me', object='it')
        obj = String('it')
        obj[DISCOURSE_FUNCTION] = DISCOURSE_FUNCTION.object
        self.assertEqual(obj, phrase.object)

    def test_indirect_object_property(self):
        phrase = VerbPhrase('give', indirect_object='me', object='it')
        obj = String('me')
        obj[DISCOURSE_FUNCTION] = DISCOURSE_FUNCTION.indirect_object
        self.assertEqual(obj, phrase.indirect_object)

    def test_elements(self):
        """ Test iterating through constituents. """
        p = VerbPhrase('give', 'the book', 'to the cook')
        expected = [String('give'), String('the book'), String('to the cook')]
        self.assertEqual(expected, list(p.elements()))

    def test_replace(self):
        """ Test replacing an element. """
        p = VerbPhrase('give', 'the book', 'to the cook')
        expected = [String('give'), String('the book'), String('to the cook')]
        self.assertEqual(expected, list(p.elements(recursive=True)))
        p.replace(String('to the cook'), String('to the chef'))
        expected = [String('give'), String('the book'), String('to the chef')]
        self.assertEqual(expected, list(p.elements(recursive=True)))

    def test_arguments(self):
        """ Test replacing arguments. """
        p = VerbPhrase('give', Var('arg_obj'),
                       PrepositionPhrase('to', Var('arg_rec')))
        expected = [Var('arg_obj'), Var('arg_rec')]
        self.assertEqual(expected, list(p.arguments()))

        obj = NounPhrase(specifier='the', head='candy')
        rec = NounPhrase(head='Roman')
        p.replace_arguments(arg_obj=obj, arg_rec=rec)
        self.assertEqual([], list(p.arguments()))
        expected = [String('give'),
                     NounPhrase(String('candy'), String('the')),
                     PrepositionPhrase(String('to'),
                                       NounPhrase(String('Roman')))]
        self.assertEqual(expected, list(p.elements()))


class TestClause(unittest.TestCase):

    def setUp(self):
        self.clause = Clause('I', 'write', 'programs')

    def test_init(self):
        self.assertEqual(category.CLAUSE, self.clause.category)
        self.assertEqual('I', self.clause.subject.string)
        self.assertEqual('I', self.clause.subject.head.string)
        self.assertEqual('write', self.clause.predicate.string)
        self.assertEqual('write', self.clause.predicate.head.string)
        self.assertEqual('write', self.clause.verb.string)
        self.assertEqual('programs', self.clause.object.string)

    def test_copy(self):
        c2 = copy(self.clause)
        self.assertEqual(self.clause, c2)
        self.assertEqual(id(self.clause.subject), id(c2.subject))

    def test_deepcopy(self):
        c2 = deepcopy(self.clause)
        self.assertEqual(self.clause, c2)
        self.assertNotEqual(id(self.clause.subject), id(c2.subject))

    def test_front_modifiers(self):
        self.clause.front_modifiers.insert(0, 'luckily')
        self.assertIn(String('luckily'), self.clause.front_modifiers)

    def test_constituents(self):
        self.clause.front_modifiers.append('luckily')
        expected = ['luckily', 'I', 'write', 'programs']
        cs = list(self.clause.elements())
        for c in cs:
            with self.subTest(actual=c):
                if isinstance(c, String):
                    self.assertIn(c.string, expected)

    def test_replace_subject(self):
        self.assertTrue(self.clause.replace('I', 'you'))
        self.assertEqual('you', self.clause.subject.string)
        self.assertEqual(category.NOUN_PHRASE, self.clause.subject.category)

    def test_replace_subject2(self):
        self.assertTrue(self.clause.replace(NounPhrase(head='I'), 'you'))
        self.assertEqual('you', self.clause.subject.string)
        self.assertEqual(category.NOUN_PHRASE, self.clause.subject.category)

    def test_replace_predicate(self):
        self.assertTrue(self.clause.replace('write', 'compose'))
        self.assertEqual(String('compose'), self.clause.verb)

    def test_replace_predicate2(self):
        vp = VerbPhrase(head='write', object='programs')
        vp2 = VerbPhrase(head='compose', object='programs')
        self.assertTrue(self.clause.replace(vp, vp2))
        self.assertEqual(String('compose'), self.clause.verb)

    def test_replace_object(self):
        self.assertTrue(self.clause.replace('programs', 'software'))
        self.assertEqual(String('software'), self.clause.object)

    def test_set_indirect_object(self):
        self.assertIsNone(self.clause.indirect_object)
        self.clause.indirect_object = 'for fun'
        self.assertIn(String('for fun'), self.clause.predicate.complements)
        self.assertEqual(String('for fun'),
                         self.clause.predicate.indirect_object)

    def test_to_json(self):
        s = self.clause.to_json()
        self.assertIn('<class \'nlglib.microplanning.struct.Clause\'>', s)
        self.assertIn('I', s)
        self.assertIn('write', s)
        self.assertIn('programs', s)

    def test_from_json(self):
        s = self.clause.to_json()
        c2 = json.loads(s, cls=ElementDecoder)
        self.assertEqual(self.clause, c2)
        self.assertEqual(c2, c2.subject.parent)
        self.assertEqual(c2, c2.predicate.parent)
        self.assertEqual(c2.subject, c2.subject.head.parent)
        self.assertEqual(c2.predicate, c2.predicate.head.parent)

    def test_repr(self):
        s = repr(self.clause)
        self.assertIn('Clause(', s)
        self.assertIn('NounPhrase(String(\'I\'', s)
        self.assertIn('VerbPhrase(String(\'write\'', s)

    def test_xml(self):
        s = self.clause.to_xml(headers=True)
        expected = '''
<?xml version="1.0" encoding="utf-8"?>
<nlg:NLGSpec xmlns="http://simplenlg.googlecode.com/svn/trunk/res/xml"
xmlns:nlg="http://simplenlg.googlecode.com/svn/trunk/res/xml"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://simplenlg.googlecode.com/svn/trunk/res/xml ">
<nlg:Request>

<Document cat="PARAGRAPH">
<child xsi:type="SPhraseSpec" cat="CLAUSE">
  <subj xsi:type="NPPhraseSpec" cat="NOUN_PHRASE" discourseFunction="subject">
    <head xsi:type="WordElement" canned="true"  cat="ANY" discourseFunction="head">
      <base>I</base>
    </head>
  </subj>
  <vp xsi:type="VPPhraseSpec" cat="VERB_PHRASE" discourseFunction="predicate">
    <head xsi:type="WordElement" canned="true"  cat="ANY" discourseFunction="head">
      <base>write</base>
    </head>
    <compl xsi:type="WordElement" canned="true"  cat="ANY" discourseFunction="object">
      <base>programs</base>
    </compl>
  </vp>
</child>

</Document>
</nlg:Request>
</nlg:NLGSpec>
'''
        self.assertEqual(expected.strip(), s)

    def test_to_str(self):
        s = str(self.clause)
        self.assertEqual('I write programs', s)

    def test_replace_vars(self):
        c = Clause(Var(id='subj'), Var(id='predicate'))
        c.replace_arguments(subj=Word('I', pos='PRONOUN'),
                            predicate=VerbPhrase('am', 'happy'))
        self.assertEqual([], c.arguments())
        self.assertEqual(c.subject.string, 'I')
        self.assertEqual(c.predicate.string, 'am')
        self.assertEqual(c.predicate.complements[0].string, 'happy')

    def test_str(self):
        """ Test printing. """
        c = Clause()
        expected = ''
        self.assertEqual(expected, str(c))

        c = Clause('Roman')
        expected = 'Roman'
        self.assertEqual(expected, str(c))

        c = Clause('Roman', 'is slow!')
        expected = 'Roman is slow!'
        self.assertEqual(expected, str(c))

    def test_elements(self):
        """ Test iterating through constituents. """
        c = Clause('Roman', 'is slow!')
        expected = [NounPhrase(String('Roman')), VerbPhrase(String('is slow!'))]
        actual = list(c.elements())
        self.assertEqual(expected, actual)

        c.front_modifiers.append('Alas!')
        expected = [String('Alas!'), String('Roman'), String('is slow!')]
        actual = list(c.elements(recursive=True))
        self.assertEqual(expected, actual)

    def test_replace(self):
        """ Test replacing elements. """
        p = Clause()
        hi = Word('hi', 'EXCLAMATION')
        hello = Word('hello', 'EXCLAMATION')
        self.assertEqual(False, p.replace(hi, hello))
        ph = Var('arg_name')
        p.subject = hi
        p.postmodifiers.append(ph)
        self.assertEqual(True, p.replace(hi, hello))
        self.assertEqual(hello, p.subject.head)

        ph2 = Var('arg_place')
        p2 = Phrase()
        p2.head = ph2
        p.vp = p2

        p.replace(Var('arg_place'), Word('Aberdeen', 'NOUN'))
        self.assertEqual(False, Var('arg_place') in list(p.elements()))


class TestUtils(unittest.TestCase):

    def test_raise_to_element(self):
        """ Test converting strings to Strings. """
        expected = [String('late'), Word('evening', 'NOUN')]
        actual = [raise_to_element('late'), raise_to_element(Word('evening', 'NOUN'))]
        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
