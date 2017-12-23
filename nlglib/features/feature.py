"""This module contains the Feature and FeatureGroup structures
for representing features such as number and gender.

In general, the features will depend on the language
that you are generating as some languages have features
not found in others.

"""

from collections import MutableSet


class Feature(object):
    """Represents individual features -- a pair of feature group name + value"""

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return '{0}: {1}'.format(self.name, self.value)

    def __repr__(self):
        return '<Feature {0}>'.format(str(self))

    def __eq__(self, other):
        """Return True if `other` is the same feature
        or if it is a `FeatureGroup` with the same name

        """
        if isinstance(other, Feature):
            return self.name == other.name and self.value == other.value
        elif isinstance(other, FeatureGroup):
            return self.name == other.name
        else:
            return False

    def __hash__(self):
        # hash uses only the name so that we can compare with FeatureGroup
        return hash(self.name)


class FeatureGroup(object):
    """Represents a group of features such as number or tense. """

    def __init__(self, name, *values):
        """Create a feature group with given values as Feature instances.

        The values are accessible as instance attributes. The values are
        also stored in an instance variable (list) `values`.

        Note that the order of values matters! (intentionally)

        >>> number = FeatureGroup('number', 'singular', 'plural')
        >>> number.singular
        <Feature number: singular>

        """
        self.name = name
        self.values = list(values)
        for v in values:
            setattr(self, v, Feature(name, v))

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<FeatureGroup {0}: {1}>'.format(self.name, ', '.join(self.values))

    def __len__(self):
        return len(self.values)

    def __getitem__(self, item):
        return self.values[item]

    def __contains__(self, item):
        if isinstance(item, str):
            return item in self.values
        elif isinstance(item, Feature):
            return item.name == self.name and item.value in self.values
        else:
            return False

    def __eq__(self, other):
        """Return True if `other` is the same FeatureGroup
        or if it is a `Feature` with the same name

        """
        if isinstance(other, FeatureGroup):
            return self.name == other.name and self.values == other.values
        elif isinstance(other, Feature):
            return self.name == other.name
        else:
            return False

    def __hash__(self):
        # hash uses only the name so that we can compare with Feature
        return hash(self.name)


class FeatureSet(MutableSet):
    """Represents a set of features"""

    def __init__(self, seq=()):
        self.feature_set = set(seq)

    def add(self, value):
        """Add a feature into the set
        >>> fs = FeatureSet([Feature('number', 'singular')])
        >>> fs.add(Feature('number', 'plural'))
        >>> repr(fs)
        '<FeatureSet {<Feature number: plural>, <Feature number: singular>}>'

        """
        self.feature_set.add(value)

    def replace(self, value):
        """Add a feature into the set, replacing other feature(s) of the same group

        >>> fs = FeatureSet([Feature('number', 'singular')])
        >>> fs.replace(Feature('number', 'plural'))
        >>> repr(fs)
        '<FeatureSet {<Feature number: plural>}>'

        """
        self.discard(value.name)
        self.add(value)

    def discard(self, value):
        """Discard a given value from the set (doesn't raise KeyError if not found)

        >>> fs = FeatureSet([Feature('number', 'singular')])
        >>> fs.discard(Feature('number', 'plural'))
        >>> repr(fs)
        '<FeatureSet {<Feature number: singular>}>'
        >>> fs.discard('number')
        >>> repr(fs)
        '<FeatureSet set()>'

        """
        if isinstance(value, (str, FeatureGroup)):
            group_name = str(value)
            to_del = (x for x in self.feature_set if x.name == group_name)
            self.feature_set -= set(to_del)
        else:
            self.feature_set.discard(value)

    def __len__(self):
        return len(self.feature_set)

    def __iter__(self):
        return iter(self.feature_set)

    def __contains__(self, x):
        """Return True if the feature set contains either given feature or given feature group

        This function relies on the fact that FeatureGroup and Feature compare as equal
        if their names match. This is to allow, for example, number.plural == number return True.

        >>> number = FeatureGroup('number', 'singular', 'plural')
        >>> fs = FeatureSet([number.plural])
        >>> number in fs
        True
        >>> number.singular in fs
        False
        >>> number.plural in fs
        True

        """
        return x in self.feature_set

    def __getitem__(self, feature):
        """Return the value of the corresponding feature group (eg number or tense)

        >>> fs = FeatureSet([Feature('number', 'plural')])
        >>> fs['number']
        <Feature number: plural>

        """
        feature = str(feature)
        for f in self.feature_set:
            if f.name == feature:
                return f
        raise KeyError('This element does not have feature "{}"'.format(feature))

    def __setitem__(self, key, value):
        """Add the given `value` using `self.replace`; `key` is redundant

        >>> number = FeatureGroup('number', 'singular', 'plural')
        >>> fs = FeatureSet([number.singular])
        >>> fs[number] = number.plural
        >>> repr(fs)
        '<FeatureSet {<Feature number: plural>}>'

        """
        self.replace(value)

    def get(self, feature, default=None):
        """Get the value of a given feature group or return `default` if it is not present

        >>> fs = FeatureSet([Feature('number', 'plural')])
        >>> fs.get('number')
        <Feature number: plural>
        >>> fs.get('tense', 'some-default')
        'some-default'

        """
        try:
            return self[feature]
        except KeyError:
            return default

    def __repr__(self):
        return '<FeatureSet {0}>'.format(str(self.feature_set))

    def as_dict(self):
        """Return given feature set as a dictionary;

        The method is assuming that each feature belongs to a different group.

        """
        return {f.name: f.value for f in self.feature_set}
