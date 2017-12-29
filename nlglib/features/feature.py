"""This module contains the Feature and FeatureGroup structures
for representing features such as number and gender.

In general, the features will depend on the language
that you are generating as some languages have features
not found in others.

"""

import copy
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
            return self.name.lower() == other.name.lower() and self.value == other.value
        elif isinstance(other, FeatureGroup):
            return self.name.lower() == other.name.lower()
        else:
            return False

    def __hash__(self):
        # hash uses only the name so that we can compare with FeatureGroup
        return hash(self.name)


class FeatureGroup(object):
    """Represents a group of features such as NUMBER or TENSE. """
    # TODO: consider using metaclasses and __slots__

    def __init__(self, name, *values, transform=None):
        """Create a feature group with given values as Feature instances.

        The values are accessible as instance attributes. The values are
        also stored in an instance variable (list) `values`.

        Note that the order of values matters! (intentionally)

        :param str name: the name of the group (eg NUMBER or TENSE)
        :param str values: the individual feature values (eg first, second or present, past)
        :param str transform: string transformation for given values ('lower', 'upper' or None)

        >>> NUMBER = FeatureGroup('NUMBER', 'singular', 'plural')
        >>> NUMBER.singular
        <Feature NUMBER: singular>

        """
        def ident(x):
            return x
        fn = ident
        if transform:
            fn = getattr(str, transform)
        self.transform = fn
        self.name = name
        self.values = list(values)
        for v in values:
            setattr(self, fn(v), Feature(name, fn(v)))

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
    __slots__ = ['__s']
    
    def __init__(self, seq=()):
        self.__s = set(seq)

    def __repr__(self):
        return '<FeatureSet {0}>'.format(str(self.__s))

    def __str__(self):
        features = sorted(self.__s, key=lambda f: (f.name, f.value))
        return '{' + ', '.join('{k}: {v}'.format(k=repr(f.name), v=repr(f.value)) for f in features) + '}'

    def __len__(self):
        return len(self.__s)

    def __iter__(self):
        return iter(self.__s)

    def __contains__(self, x):
        """Return True if the feature set contains either given feature or given feature group

        This function relies on the fact that FeatureGroup and Feature compare as equal
        if their names match. This is to allow, for example, NUMBER.plural == NUMBER return True.

        >>> NUMBER = FeatureGroup('NUMBER', 'singular', 'plural')
        >>> fs = FeatureSet([NUMBER.plural])
        >>> NUMBER in fs
        True
        >>> NUMBER.singular in fs
        False
        >>> NUMBER.plural in fs
        True

        """
        if isinstance(x, str):
            x = FeatureGroup(x)
        return x in self.__s

    def __getitem__(self, feature):
        """Return the value of the corresponding feature group (eg NUMBER or TENSE) or None

        >>> fs = FeatureSet([Feature('NUMBER', 'plural')])
        >>> fs[FeatureGroup('NUMBER')]
        <Feature NUMBER: plural>

        """
        name = feature if isinstance(feature, str) else feature.name
        for f in self.__s:
            if name == f.name:
                return f
        return None

    def __setitem__(self, key, value):
        """Add the given `value` using `self.replace`; `key` is used only if `value` is a string.

        >>> NUMBER = FeatureGroup('NUMBER', 'singular', 'plural')
        >>> fs = FeatureSet([NUMBER.singular])
        >>> fs[NUMBER] = NUMBER.plural
        >>> repr(fs)
        '<FeatureSet {<Feature NUMBER: plural>}>'
        >>> fs[NUMBER] = 'singular'

        """
        if isinstance(value, str):
            value = Feature(str(key), value)
        self.replace(value)

    def __delitem__(self, item):
        self.discard(item)

    def add(self, value):
        """Add a feature into the set
        >>> fs = FeatureSet([Feature('NUMBER', 'singular')])
        >>> fs.add(Feature('NUMBER', 'plural'))
        >>> repr(fs)
        '<FeatureSet {<Feature NUMBER: plural>, <Feature NUMBER: singular>}>'

        """
        self.__s.add(value)

    def replace(self, value):
        """Add a feature into the set, replacing other feature(s) of the same group

        >>> fs = FeatureSet([Feature('NUMBER', 'singular')])
        >>> fs.replace(Feature('NUMBER', 'plural'))
        >>> repr(fs)
        '<FeatureSet {<Feature NUMBER: plural>}>'

        """
        if not value:
            return
        self.discard(value)
        self.add(value)

    def discard(self, value):
        """Discard a given value from the set (doesn't raise KeyError if not found)

        >>> fs = FeatureSet([Feature('NUMBER', 'singular')])
        >>> fs.discard(Feature('NUMBER', 'plural'))
        {<Feature NUMBER: singular>}
        >>> repr(fs)
        '<FeatureSet {<Feature NUMBER: singular>}>'
        >>> fs.discard(FeatureGroup('NUMBER'))
        >>> repr(fs)
        '<FeatureSet set()>'

        """
        feature = value if isinstance(value, str) else value.name
        to_del = set(x for x in self.__s if x.name == feature)
        self.__s -= to_del
        return to_del

    def get(self, feature, default=None):
        """Get the value of a given feature group or return `default` if it is not present

        >>> fs = FeatureSet([Feature('number', 'plural')])
        >>> fs.get(FeatureGroup('number'))
        <Feature number: plural>
        >>> fs.get(FeatureGroup('tense'), 'some-default')
        'some-default'

        """
        return self[feature] if self[feature] is not None else default

    def as_dict(self):
        """Return given feature set as a dictionary;

        The method is assuming that each feature belongs to a different group.

        """
        return {f.name: f.value for f in self.__s}

    def keys(self):
        for f in self.__s:
            yield f.name

    def values(self):
        for f in self.__s:
            yield f.value

    def items(self):
        for f in self.__s:
            yield (f.name, f.value)

    def update(self, other):
        if not other:
            return
        if isinstance(other, dict):
            for k, v in other.items():
                self.replace(Feature(k, v))
        elif isinstance(other, FeatureSet):
            for f in other.__s:
                self.replace(f)
        elif isinstance(other, (list, tuple, set)):
            for x in other:
                if isinstance(x, Feature):
                    self.replace(x)
                else:
                    msg = 'FeatureSet does not know how to update with "{}".'
                    raise TypeError(msg.format(type(x)))
        else:
            msg = 'FeatureSet does not know how to update from "{}".'
            raise TypeError(msg.format(type(other)))

    def copy(self):
        rv = FeatureSet()
        rv.__s = copy.copy(self.__s)
        return rv
