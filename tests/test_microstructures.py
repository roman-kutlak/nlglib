import json
import unittest

from copy import copy, deepcopy

from nlglib.structures.microplanning import Element, ElementList, Var, String, Word, Coordination


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




if __name__ == '__main__':
    unittest.main()
