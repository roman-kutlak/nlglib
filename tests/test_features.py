import unittest

from nlglib.features import Feature, FeatureGroup, FeatureSet


# noinspection PyUnresolvedReferences
class TestFeature(unittest.TestCase):
    def test_equal(self):
        singular = Feature('NUMBER', 'singular')
        plural = Feature('NUMBER', 'plural')
        number = FeatureGroup('NUMBER', 'singular', 'plural')
        self.assertEqual(number.singular, singular)
        self.assertEqual(number.plural, plural)
        self.assertEqual(number, singular)
        self.assertEqual(number, plural)
        self.assertNotEqual(number.singular, number.plural)
        self.assertNotEqual(singular, plural)

    def test_str(self):
        singular = Feature('NUMBER', 'singular')
        self.assertEqual('NUMBER: singular', str(singular))

    def test_repr(self):
        singular = Feature('NUMBER', 'singular')
        self.assertEqual('<Feature NUMBER: singular>', repr(singular))


# noinspection PyUnresolvedReferences
class TestFeatureGroup(unittest.TestCase):
    def test_equal(self):
        singular = Feature('NUMBER', 'singular')
        plural = Feature('NUMBER', 'plural')
        number = FeatureGroup('NUMBER', 'singular', 'plural')
        self.assertEqual(2, len(number))
        self.assertEqual(number.singular, singular)
        self.assertEqual(number.plural, plural)
        self.assertEqual(number, singular)
        self.assertEqual(number, plural)
        self.assertNotEqual(number.singular, number.plural)
        number2 = FeatureGroup('NUMBER', 'singular', 'plural')
        self.assertEqual(number, number2)
        number3 = FeatureGroup('NUMBER', 'plural', 'singular')
        self.assertNotEqual(number, number3)

    def test_str(self):
        singular = Feature('NUMBER', 'singular')
        self.assertEqual('NUMBER: singular', str(singular))

    def test_repr(self):
        singular = Feature('NUMBER', 'singular')
        self.assertEqual('<Feature NUMBER: singular>', repr(singular))

    def test_contains(self):
        singular = Feature('NUMBER', 'singular')
        plural = Feature('NUMBER', 'plural')
        dual = Feature('NUMBER', 'dual')
        number = FeatureGroup('NUMBER', 'singular', 'plural')
        self.assertIn(singular, number)
        self.assertIn(plural, number)
        self.assertNotIn(dual, number)
        self.assertIn('singular', number)
        fake = Feature('fake', 'plural')
        self.assertNotIn(fake, number)

    def test_eq(self):
        fg = FeatureGroup('NUMBER', 'singular', 'plural')
        sg = Feature('NUMBER', 'singular')
        pl = Feature('NUMBER', 'plural')
        self.assertEqual(fg, sg)
        self.assertEqual(fg, pl)
        self.assertNotEqual(sg, pl)


# noinspection PyUnresolvedReferences
class TestFeatureSet(unittest.TestCase):

    number = FeatureGroup('NUMBER', 'singular', 'plural')
    tense = FeatureGroup('TENSE', 'present', 'past', 'future')
    person = FeatureGroup('PERSON', 'first', 'second', 'third')

    def test_contains(self):
        fs = FeatureSet([self.number.singular, self.person.first])
        self.assertEqual(2, len(fs))
        self.assertIn(self.number.singular, fs)
        self.assertNotIn(self.number.plural, fs)
        self.assertIn(self.number, fs)
        self.assertEqual(Feature('number', 'plural'), Feature('NUMBER', 'plural'))
        self.assertNotEqual(Feature('number', 'plural'), Feature('number', 'PLURAL'))

    def test_add(self):
        fs = FeatureSet()
        fs.add(self.number.singular)
        self.assertEqual(1, len(fs))
        fs.add(self.number.singular)
        self.assertEqual(1, len(fs))
        fs.add(self.number.plural)
        self.assertEqual(2, len(fs))

    def test_remove_feature(self):
        fs = FeatureSet([self.number.singular, self.person.first])
        fs.remove(self.number.singular)
        self.assertNotIn(self.number.singular, fs)
        self.assertIn(self.person.first, fs)

    def test_replace(self):
        fs = FeatureSet()
        fs.replace(self.number.singular)
        self.assertEqual(FeatureSet([self.number.singular]), fs)
        fs.replace(self.number.singular)
        self.assertEqual(FeatureSet([self.number.singular]), fs)
        fs.replace(self.number.plural)
        self.assertEqual(FeatureSet([self.number.plural]), fs)

    def test_remove_feature_group(self):
        fs = FeatureSet([self.number.singular, self.person.first])
        fs.remove(self.number)
        self.assertNotIn(self.number.singular, fs)
        self.assertIn(self.person.first, fs)

    def test_equals(self):
        fs1 = FeatureSet([self.number.singular, self.person.first])
        fs2 = FeatureSet()
        fs2.add(self.number.singular)
        fs2.add(self.person.first)
        self.assertEqual(fs1, fs2)

    def test_not_equals(self):
        fs1 = FeatureSet([self.number.singular, self.person.first])
        fs2 = FeatureSet()
        fs2.add(self.number.plural)
        fs2.add(self.person.first)
        self.assertNotEqual(fs1, fs2)

    def test_getitem(self):
        fs = FeatureSet([self.number.singular, self.person.first])
        self.assertEqual(self.number.singular, fs[self.number])
        self.assertIsNone(fs[self.tense])

    def test_get(self):
        fs = FeatureSet([self.number.singular, self.person.first])
        self.assertEqual(self.number.singular, fs.get(self.number))
        self.assertEqual(None, fs.get(self.tense))
        self.assertEqual(self.tense.future, fs.get(self.tense, self.tense.future))

    def test_setitem(self):
        fs = FeatureSet([self.number.singular, self.person.first])
        fs[self.number] = self.number.plural
        expected = FeatureSet([self.number.plural, self.person.first])
        self.assertEqual(expected, fs)


if __name__ == '__main__':
    unittest.main()
