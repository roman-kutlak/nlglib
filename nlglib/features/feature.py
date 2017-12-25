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

    def __init__(self, name, *values, transform=None):
        """Create a feature group with given values as Feature instances.

        The values are accessible as instance attributes. The values are
        also stored in an instance variable (list) `values`.

        Note that the order of values matters! (intentionally)

        :param str name: the name of the group (eg number or tense)
        :param str values: the individual feature values (eg first, second or present, past)
        :param str transform: string transformation for given values ('lower', 'upper' or None)

        >>> number = FeatureGroup('number', 'singular', 'plural')
        >>> number.singular
        <Feature number: singular>

        """
        def ident(x):
            return x
        fn = ident
        if transform:
            fn = getattr(str, transform)
        self.transform = fn
        self.name = fn(name)
        self.values = list(values)
        for v in values:
            setattr(self, fn(v), Feature(fn(name), fn(v)))

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

    def __getattr__(self, item):
        item = self.transform(item)
        return super(FeatureGroup, self).__getattribute__(item)


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
        self.discard(value)
        self.add(value)

    def discard(self, value):
        """Discard a given value from the set (doesn't raise KeyError if not found)

        >>> fs = FeatureSet([Feature('number', 'singular')])
        >>> fs.discard(Feature('number', 'plural'))
        >>> repr(fs)
        '<FeatureSet {<Feature number: singular>}>'
        >>> fs.discard(FeatureGroup('number'))
        >>> repr(fs)
        '<FeatureSet set()>'

        """
        to_del = (x for x in self.feature_set if x.name == value.name)
        self.feature_set -= set(to_del)

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
        """Return the value of the corresponding feature group (eg number or tense) or None

        >>> fs = FeatureSet([Feature('number', 'plural')])
        >>> fs[FeatureGroup('number')]
        <Feature number: plural>

        """
        for f in self.feature_set:
            if f.name == feature.name:
                return f
        return None

    def __setitem__(self, key, value):
        """Add the given `value` using `self.replace`; `key` is used only if `value` is a string.

        >>> number = FeatureGroup('number', 'singular', 'plural')
        >>> fs = FeatureSet([number.singular])
        >>> fs[number] = number.plural
        >>> repr(fs)
        '<FeatureSet {<Feature number: plural>}>'
        >>> fs[number] = 'singular'

        """
        if isinstance(value, str):
            value = Feature(str(key), value)
        self.replace(value)

    def get(self, feature, default=None):
        """Get the value of a given feature group or return `default` if it is not present

        >>> fs = FeatureSet([Feature('number', 'plural')])
        >>> fs.get(FeatureGroup('number'))
        <Feature number: plural>
        >>> fs.get(FeatureGroup('tense'), 'some-default')
        'some-default'

        """
        return self[feature] if self[feature] is not None else default

    def __repr__(self):
        return '<FeatureSet {0}>'.format(str(self.feature_set))

    def as_dict(self):
        """Return given feature set as a dictionary;

        The method is assuming that each feature belongs to a different group.

        """
        return {f.name: f.value for f in self.feature_set}

    def keys(self):
        for f in self.feature_set:
            yield f.name

    def values(self):
        for f in self.feature_set:
            yield f.value

    def items(self):
        for f in self.feature_set:
            yield (f.name, f.value)

    def update(self, other):
        if isinstance(other, dict):
            for k, v in other.items():
                self.replace(Feature(k, v))
        elif isinstance(other, FeatureSet):
            self.feature_set |= other.feature_set
        else:
            msg = 'FeatureSet does not know how to update from "{}".'
            raise TypeError(msg.format(type(other)))
