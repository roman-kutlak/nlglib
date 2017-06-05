import json
import unittest

from copy import copy, deepcopy

from nlglib.structures import microplanning
from nlglib.structures.microplanning import (
    Element, ElementList, Var, String, Word, Coordination,
    Phrase, NounPhrase, VerbPhrase, AdjectivePhrase, AdverbPhrase
)


class TestElement(unittest.TestCase):
    def setUp(self):
        self.e = Element(features={'foo': 'bar'})

    def test_copy(self):
        e2 = copy(self.e)
        self.assertEqual(self.e, e2)
        self.assertEqual(id(self.e.features), id(e2.features))

    def test_deepcopy(self):
        e2 = deepcopy(self.e)
        self.assertEqual(self.e, e2)
        self.assertNotEqual(id(self.e.features), id(e2.features))

    def test_to_json(self):
        s = self.e.to_json()
        self.assertIn('<class \'nlglib.structures.microplanning.Element\'>', s)
        self.assertIn('"foo": "bar"', s)

    def test_from_json(self):
        s = self.e.to_json()
        e2 = Element.from_json(s)
        self.assertEqual(self.e, e2)

    def test_feature_lookup(self):
        self.assertEqual('bar', self.e.foo)

    def test_feature_del(self):
        del self.e['foo']
        self.assertNotIn('foo', self.e)

    def test_feature_set(self):
        self.e['zzz'] = 'baz'
        self.assertIn('zzz', self.e.features)
        self.assertEqual('baz', self.e.zzz)

    def test_add(self):
        self.assertEqual(Element(), Element() + Element())


class TestElementList(unittest.TestCase):
    def setUp(self):
        self.e = ElementList(['happy', 'birthday'])

    def test_setitem(self):
        self.e[0] = 'merry'
        self.assertEqual(String('merry'), self.e[0])

    def test_concat(self):
        e2 = self.e + ['dude']
        for e in e2:
            self.assertTrue(isinstance(e, String))

    def test_add(self):
        el = ElementList()
        el += ['foo', 'bar']
        for e in el:
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
        self.assertIn('<class \'nlglib.structures.microplanning.ElementList\'>', s)

    def test_from_json(self):
        s = self.e.to_json()
        e2 = ElementList.from_json(s)
        self.assertEqual(self.e, e2)


class TestVar(unittest.TestCase):
    def setUp(self):
        self.e = Var('x', features={'foo': 'bar'})

    def test_copy(self):
        e2 = copy(self.e)
        self.assertEqual(self.e, e2)
        self.assertEqual(self.e.value, e2.value)
        self.assertEqual(id(self.e.features), id(e2.features))

    def test_deepcopy(self):
        e2 = deepcopy(self.e)
        self.assertEqual(self.e, e2)
        self.assertEqual(self.e.value, e2.value)
        self.assertNotEqual(id(self.e.features), id(e2.features))

    def test_to_json(self):
        s = self.e.to_json()
        self.assertIn('<class \'nlglib.structures.microplanning.Var\'>', s)
        self.assertIn('"foo": "bar"', s)
        self.assertIn('"key": "x"', s)

    def test_from_json(self):
        s = self.e.to_json()
        e2 = Element.from_json(s)
        self.assertEqual(self.e, e2)


class TestString(unittest.TestCase):
    def setUp(self):
        self.e = String('happiness', features={'foo': 'bar'})

    def test_copy(self):
        e2 = copy(self.e)
        self.assertEqual(self.e, e2)
        self.assertEqual(self.e.value, e2.value)
        self.assertEqual(id(self.e.features), id(e2.features))

    def test_deepcopy(self):
        e2 = deepcopy(self.e)
        self.assertEqual(self.e, e2)
        self.assertEqual(self.e.value, e2.value)
        self.assertNotEqual(id(self.e.features), id(e2.features))

    def test_to_json(self):
        s = self.e.to_json()
        self.assertIn('<class \'nlglib.structures.microplanning.String\'>', s)
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
        self.assertEqual(id(self.e.features), id(e2.features))

    def test_deepcopy(self):
        e2 = deepcopy(self.e)
        self.assertEqual(self.e, e2)
        self.assertEqual(self.e.word, e2.word)
        self.assertNotEqual(id(self.e.features), id(e2.features))

    def test_to_json(self):
        s = self.e.to_json()
        self.assertIn('<class \'nlglib.structures.microplanning.Word\'>', s)
        self.assertIn('"cat": "NOUN"', s)
        self.assertIn('"foo": "bar"', s)
        self.assertIn('"word": "happiness"', s)

    def test_from_json(self):
        s = self.e.to_json()
        e2 = Element.from_json(s)
        self.assertEqual(self.e, e2)


class TestCoordination(unittest.TestCase):
    def setUp(self):
        self.e = Coordination('big', 'fat')

    def test_copy(self):
        e2 = copy(self.e)
        self.assertEqual(self.e, e2)
        self.assertEqual(self.e.coords, e2.coords)
        self.assertEqual(id(self.e.features), id(e2.features))

    def test_deepcopy(self):
        e2 = deepcopy(self.e)
        self.assertEqual(self.e, e2)
        self.assertEqual(self.e.coords, e2.coords)
        self.assertNotEqual(id(self.e.features), id(e2.features))
        self.assertNotEqual(id(self.e.coords), id(e2.coords))
        cs = list(self.e.constituents())
        cs2 = list(e2.constituents())
        self.assertEqual(cs, cs2)
        for c1, c2 in zip(cs, cs2):
            self.assertNotEqual(id(c1), id(c2))

    def test_to_json(self):
        s = self.e.to_json()
        self.assertIn('<class \'nlglib.structures.microplanning.Coordination\'>', s)
        self.assertIn('"conj": "and"', s)

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
        self.assertTrue(self.e.replace('fat', 'fluffy'))
        self.assertFalse(self.e.replace('fat', 'fluffy'))
        self.assertEqual(['big', 'fluffy'], [x.string for x in self.e.coords])


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
        mod = Word('happy', pos=microplanning.ADJECTIVE)
        self.phrase += mod
        self.assertIn(mod, self.phrase.premodifiers)

    def test_modifier_addition2(self):
        """Test that adverb is added as a premodifier."""
        mod = Word('happily', pos=microplanning.ADVERB)
        self.phrase += mod
        self.assertIn(mod, self.phrase.premodifiers)

    def test_modifier_addition3(self):
        """Test that preposition is added as a complement."""
        mod = Word('over', pos=microplanning.PREPOSITION)
        self.phrase += mod
        self.assertIn(mod, self.phrase.complements)

    def test_set_head(self):
        head = Word('shout', pos=microplanning.VERB)
        self.phrase.head = head
        self.assertEqual(head, self.phrase.head)

    def test_set_empty_head(self):
        self.phrase.head = None
        self.assertEqual(Element(), self.phrase.head)

    def test_constituents(self):
        p = self.phrase
        for c in p.constituents():
            self.assertTrue(isinstance(c, (Phrase, String)))
        self.assertEqual(p, list(p.constituents())[0])

    def test_replace(self):
        p = self.phrase
        self.assertFalse(p.replace('worlds', 'universe'))
        self.assertTrue(p.replace('world', 'universe'))
        self.assertNotIn(String('world'), p.complements)
        self.assertIn(String('universe'), p.complements)

    def test_replace_using_key(self):
        p = Phrase(features={'foo': 'bar'},
                   head='say',
                   premodifiers=['please'],
                   complements=['hello', String('world', key=1)],
                   postmodifiers=['dude'])
        self.assertFalse(p.replace(String('worlds', key=2), 'universe', key=lambda x: x.key))
        self.assertTrue(p.replace(String('worlds', key=1), 'universe', key=lambda x: x.key))
        self.assertNotIn(String('world'), p.complements)
        self.assertIn(String('universe'), p.complements)


class TestNounPhrase(unittest.TestCase):

    def setUp(self):
        self.phrase = NounPhrase(head='man', spec='the',
                                 premodifiers=['small', 'happy'])

    def test_init(self):
        self.assertEqual(String('the'), self.phrase.spec)

    def test_copy(self):
        p = self.phrase
        p2 = copy(p)
        self.assertEqual(p, p2)

    def test_deepcopy(self):
        p = self.phrase
        p2 = deepcopy(p)
        self.assertEqual(p, p2)
        self.assertNotEqual(id(p), id(p2))
        self.assertNotEqual(id(p.spec), id(p2.spec))

    def test_replace(self):
        """Test replacing specifier."""
        self.phrase.replace('the', 'a')
        self.assertEqual(String('a'), self.phrase.spec)

    def test_replace2(self):
        """Test replacing an element."""
        self.phrase.replace('small', 'big')
        self.assertNotIn(String('small'), self.phrase.premodifiers)
        self.assertIn(String('big'), self.phrase.premodifiers)


class TestVerbPhrase(unittest.TestCase):

    def setUp(self):
        self.phrase = VerbPhrase('give', 'me', 'it')

    def test_init(self):
        self.assertIn(String('me'), self.phrase.complements)

    def test_object_property(self):
        phrase = VerbPhrase('give', indirect_object='me', object='it')
        obj = String('it')
        obj['discourseFunction'] = 'OBJECT'
        self.assertEqual(obj, phrase.object)

    def test_direct_object_property(self):
        phrase = VerbPhrase('give', indirect_object='me', direct_object='it')
        obj = String('it')
        obj['discourseFunction'] = 'OBJECT'
        self.assertEqual(obj, phrase.direct_object)

    def test_indirect_object_property(self):
        phrase = VerbPhrase('give', indirect_object='me', object='it')
        obj = String('me')
        obj['discourseFunction'] = 'INDIRECT_OBJECT'
        self.assertEqual(obj, phrase.indirect_object)


if __name__ == '__main__':
    unittest.main()
