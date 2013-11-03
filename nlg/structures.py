from copy import deepcopy

""" Data structures used by other packages. """

# macroplanning level structures
#   for content determination and content structuring

def enum(*sequential, **named):
    """ This functions declares a new type 'enum' that acts as an enum. """
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.items())
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)


""" Rhetorical Structure Theory relations """
RST = enum( 'Elaboration', 'Exemplification',
            'Contrast', 'Exception',
            'Sequence', 'Set',
            'Leaf'
          )


class Document:
    def __init__(self, title, *sections):
        self.title = title
        self.sections = [s for s in sections if s is not None]

    def __repr__(self):
        return 'Document:\ntitle: %s' % str(self)

    def __str__(self):
        descr = (str(self.title) + '\n'
                + '\n\n'.join([str(s) for s in self.sections if s is not None]))
        return descr

    def constituents(self):
        """ Return a generator to iterate through the elements. """
        yield self.title
        for x in self.sections: yield from x.constituents()


class Section:
    def __init__(self, title, *paragraphs):
        self.title = title
        self.paragraphs = [p for p in paragraphs if p is not None]

    def __repr__(self):
        return 'Section:\ntitle: %s' % str(self)

    def __str__(self):
        descr = (str(self.title) + '\n'
                + '\n'.join([str(p) for p in self.paragraphs if p is not None]))
        return descr

    def constituents(self):
        """ Return a generator to iterate through the elements. """
        yield self.title
        for x in self.paragraphs: yield from x.constituents()



class Paragraph:
    def __init__(self, *messages):
        self.messages = [m for m in messages if m is not None]

    def __repr__(self):
        return 'Paragraph (%d):\n%s' % (len(self.messages), str(self))

    def __str__(self):
        descr = ('\t'
                 + '; '.join([str(m) for m in self.messages if m is not None]))
        return descr

    def constituents(self):
        """ Return a generator to iterate through the elements. """
        for x in self.messages: yield from x.constituents()


class Message:
    def __init__(self, rel, nucleus, *satelites):
        self.rst = rel
        self.nucleus = nucleus
        self.satelites = [s for s in satelites if s is not None]

    def __repr__(self):
        return 'Message (%s): %s' % (self.rst, str(self))

    def __str__(self):
        descr = ' '.join( [str(x) for x in
            ([self.nucleus] + self.satelites) if x is not None ] )
        return (descr.strip() if descr is not None else '')

    def constituents(self):
        """ Return a generator to iterate through the elements. """
        if self.nucleus is not None: yield from self.nucleus.constituents()
        for x in self.satelites: yield from x.constituents()


class MsgSpec:
    """ MsgSpec specifies an interface for various message specifications.
    Because the specifications are domain dependent, this is just a convenience 
    interface that allows the rest of the library to operate on the messages.
    
    The name of the message is used during lexicalisation where the name is 
    looked up in an ontology to find corresponding syntactic frame. To populate
    the frame, the lexicaliser finds all variables and uses their names 
    as a key to look up the values in the corresponding message. For example,
    if the syntactic structure in the domain ontology specifies a variable
    named 'foo', the lexicaliser will call msg.value_for('foo'), which
    in turn calls self.foo(). This should return the value for the key 'foo'.
    
    """
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'MsgSpec: %s' % str(self)

    def __str__(self):
        return str(self.name)

    def value_for(self, data_member):
        """ Return a value for an argument using introspection. """
        if not hasattr(self, data_member):
            raise ValueError('Error: cannot find value for key: %s' %
                                data_member)
        m = getattr(self, data_member)
        if not hasattr(m, '__call__'):
            raise ValueError('Error: cannot call the method "%s"' %
                                data_member)
        return m()

    @classmethod
    def instantiate(Klass, data):
        return None



# microplanning level structures

class Element:
    def __init__(self, vname='visit_element'):
        self.id = 0 # this is useful for replacing elements
        self._visitor_name = vname
        self._features = dict()
        self.realisation = ""

    def __eq__(self, other):
        if (not isinstance(other, Element)):
            return False
        # disregard realisation as that is only a cached value
        return (self.id == other.id and
                self._visitor_name == other._visitor_name and
                self._features == other._features)

    def to_str(self):
        return ""
    
    def __repr__(self):
        text = 'Element (%s): ' % self._visitor_name
        text += str(self._features)
        if '' != self.realisation:
            text += ' realisation:' + self.realisation
        return text

    def __str__(self):
        v = StrVisitor()
        self.accept(v)
        return v.to_str()
        
    def accept(self, visitor, element='child'):
        """Implementation of the Visitor pattern."""
        if self._visitor_name == None:
            raise ValueError('Error: visit method of uninitialized visitor '
                             'called!')
        # get the appropriate method of the visitor instance
        m = getattr(visitor, self._visitor_name)
        # ensure that the method is callable
        if not hasattr(m, '__call__'):
            raise ValueError('Error: cannot call undefined method: %s on '
                             'visitor' % self._visitor_name)
        # and finally call the callback
        m(self, element)

    def features_to_xml_attributes(self):
        features = ""
        for (k, v) in self._features.items():
            features += '%s="%s" ' % (k, v)
        return features

    def add_feature(self, feature, value):
        """ Add a feature to the feature set.
        If the feature exists, overwrite the old value.
        
        """
        self._features[feature] = value

    def has_feature(self, feature):
        """ Return True if the element has the given feature. """
        return (feature in self._features)

    def get_feature(self, feature):
        """ Return value for given feature or raise KeyError. """
        return self._features[feature]

    def feature(self, feat):
        """ Return value for given feature or None. """
        if feat in self._features: return self._features[feat]
        else: return None

    def del_feature(self, feat, val=None):
        """ Delete a feature, if the element has it else do nothing.
        If val is None, delete whathever value is assigned to the feature.
        Otherwise only delete the feature if it has matching value.

        """
        if feat in self._features:
            if val is not None: del self._features[feat]
            elif val == self._features[feat]: del self._features[feat]

    def constituents(self):
        """ Return a generator representing constituents of an element. """
        return []

    def arguments(self):
        """ Return any arguments (placeholders) from the elemen as a generator.
        
        """
        return filter(lambda x: isinstance(x, PlaceHolder), self.constituents())

    def replace(self, one, another):
        """ Replace first occurance of one with another.
        Return True if successful.
        
        """
        return False # basic implementation does nothing

    def replace_argument(self, arg_id, repl):
        """ Replace an argument with given id by repl if such argumen exists."""
        for a in self.arguments():
            if a.id == arg_id:
                return self.replace(a, repl)
        return False

    def replace_arguments(self, *args, **kwargs):
        """ Replace arguments with ids in the kwargs by the corresponding
        values.
        Replacements can be passed as a single dictionary or a kwarg list
        (e.g., arg1=x, arg2=y, ...)
        
        """
        if len(args) > 0 and len(args) > 1:
            raise ValueError('too many parameters')
        elif len(args) > 0:
            for k, v in args[0]:
                self.replace_argument(k, v)
        else:
            for k, v in kwargs.items():
                self.replace_argument(k, v)

    @staticmethod
    def _strings_to_elements(*params):
        """ Check that all params are Elements and convert
        and any strings to String.
        
        """
        fn = lambda x: String(x) if isinstance(x, str) else x
        return map(fn, params)

    @staticmethod
    def _add_to_list(lst, *mods):
        """ Add modifiers to the given list. Convert any strings to String. """
        for p in Element._strings_to_elements(*mods):
            if p not in lst: lst.append(p)

    @staticmethod
    def _del_from_list(lst, *mods):
        """ Delete elements from a list. Convert any strings to String. """
        for p in Element._strings_to_elements(*mods):
            if p in lst: lst.remove(p)


class String(Element):
    def __init__(self, val=""):
        super().__init__('visit_string')
        self.val = val
    
    def to_xml(self, element):
        text = ('<%s xsi:type="StringElement">'
                '\n\t<val>%s</val>\n</%s>\n'
                % (element, self.val, element))
        return text
    
    def to_str(self):
        return self.val
    
    def __eq__(self, other):
        if (not isinstance(other, String)):
            return False
        return (self.val == other.val and
                super().__eq__(other))

    def __str__(self):
        return self.val if self.val is not None else ''

    def __repr__(self):
        return ('String(%s)' % self.val)
        
    def constituents(self):
        return [self]


class Word(Element):
    def __init__(self, word=None, pos=None):
        super().__init__('visit_word')
        self.word = word
        self.pos = pos

    def to_xml(self, element):
        text = ('<%s xsi:type="WordElement" cat="%s">'
                '\n\t<base>%s</base>\n</%s>\n'
                % (element, self.pos, self.word, element))
        return text
    
    def to_str(self):
        return self.word if word is not None else ''
    
    def __eq__(self, other):
        if (not isinstance(other, Word)):
            return False
        return (self.word == other.word and
                self.pos == other.pos and
                super().__eq__(other))

    def __str__(self):
        return self.word if self.word is not None else ''

    def __repr__(self):
        text = 'Word: %s (%s) %s' % (str(self.word),
                                     str(self.pos),
                                     str(self._features))
        return text

    def constituents(self):
        return [self]


class PlaceHolder(Element):
    def __init__(self, id=None, obj=None):
        super().__init__('visit_placeholder')
        self.id = id
        self.set_value(obj)

    def to_xml(self, element):
        text = ('<%s xsi:type="StringElement">'
                '\n\t<val>%s</val>\n</%s>\n'
                % (element, str(self.id), element))
        return text

    def to_str(self):
        if (self.value):
            return str(self.value)
        return self.id

    def __eq__(self, other):
        if (not isinstance(other, PlaceHolder)):
            return False
        else:
            return (self.id == other.id and
                    self.value == other.value and
                    super().__eq__(other))

    def __repr__(self):
        return ('PlaceHolder: id=%s value=%s %s' %
                (str(self.id), str(self.value), str(self._features)))

    def __str__(self):
        return self.to_str()

    def constituents(self):
        return [self]

    def set_value(self, val):
        self.value = String(val) if isinstance(val, str) else val


class Phrase(Element):
    def __init__(self, type=None, discourse_fn=None, vname='visit_phrase'):
        super().__init__(vname)
        self.type = type
        self.discourse_fn = discourse_fn
        self.front_modifier = list()
        self.pre_modifier = list()
        self.head = None
        self.complement = list()
        self.post_modifier = list()

    def __eq__(self, other):
        if (not isinstance(other, Phrase)):
            return False
        return (self.type == other.type and
                self.discourse_fn == other.discourse_fn and
                self.front_modifier == other.front_modifier and
                self.pre_modifier == other.pre_modifier and
                self.head == other.head and
                self.complement == other.complement and
                self.post_modifier == other.post_modifier and
                super().__eq__(other))

    def __str__(self):
        data = [' '.join([str(o) for o in self.front_modifier]),
                 ' '.join([str(o) for o in self.pre_modifier]),
                 str(self.head) if self.head is not None else '',
                 ' '.join([str(o) for o in self.complement]),
                 ' '.join([str(o) for o in self.post_modifier])]
        # remove empty strings
        data = filter(lambda x: x != '', data)
        return (' '.join(data))

    def __repr__(self):
        return ('(Phrase %s %s: "%s" %s)' %
                (self.type, self.discourse_fn, str(self), str(self._features)))

    def set_front_modifiers(self, *mods):
        """ Set front-modifiers to the passed parameters. """
        self.front_modifier = list(self._strings_to_elements(*mods))

    def add_front_modifier(self, *mods):
        """ Add one or more front-modifiers. """
        self._add_to_list(self.front_modifier, *mods)

    def del_front_modifier(self, *mods):
        """ Remove one or more front-modifiers if present. """
        self._del_from_list(self.front_modifier, *mods)

    def set_pre_modifiers(self, *mods):
        """ Set pre-modifiers to the passed parameters. """
        self.pre_modifier = list(self._strings_to_elements(*mods))

    def add_pre_modifier(self, *mods):
        """ Add one or more pre-modifiers. """
        self._add_to_list(self.pre_modifier, *mods)

    def del_pre_modifier(self, *mods):
        """ Delete one or more pre-modifiers if present. """
        self._del_from_list(self.pre_modifier, *mods)

    def set_complements(self, *mods):
        """ Set complemets to the given ones. """
        self.complement = list(self._strings_to_elements(*mods))

    def add_complement(self, *mods):
        """ Add one or more complements. """
        self._add_to_list(self.complement, *mods)

    def del_complement(self, *mods):
        """ Delete one or more complements if present. """
        self._del_from_list(self.complement, *mods)

    def set_post_modifiers(self, *mods):
        """ Set post-modifiers to the given parameters. """
        self.post_modifier = list(self._strings_to_elements(*mods))

    def add_post_modifier(self, *mods):
        """ Add one or more post-modifiers. """
        self._add_to_list(self.post_modifier, *mods)

    def del_post_modifier(self, *mods):
        """ Delete one or more post-modifiers if present. """
        self._del_from_list(self.post_modifier, *mods)

    def set_head(self, elt):
        """ Set head of the phrase to the given element. """
        self.head = String(elt) if isinstance(elt, str) else elt

    def yield_front_modifiers(self):
        """ Iterate through front modifiers. """
        for o in self.front_modifier:
            for x in o.constituents():
                yield x

    def yield_pre_modifiers(self):
        """ Iterate through pre-modifiers. """
        for o in self.pre_modifier:
            for x in o.constituents():
                yield x

    def yield_head(self):
        """ Iterate through the elements composing the head. """
        if self.head is not None:
            for x in self.head.constituents():
                yield x

    def yield_complements(self):
        """ Iterate through complements. """
        for o in self.complement:
            for x in o.constituents():
                yield x

    def yield_post_modifiers(self):
        """ Iterate throught post-modifiers. """
        for o in self.post_modifier:
            for x in o.constituents():
                yield x

    def constituents(self):
        """ Return a generator to iterate through constituents. """
        yield from self.yield_front_modifiers()
        yield from self.yield_pre_modifiers()
        yield from self.yield_head()
        yield from self.yield_complements()
        yield from self.yield_post_modifiers()

    # TODO: consider spliting the code below similarly to 'constituents()'
    def replace(self, one, another):
        """ Replace first occurance of one with another.
        Return True if successful.
        
        """
        for i, o in enumerate(self.front_modifier):
            if o == one:
                if another is None:
                    del sent.front_modifier[i]
                else:
                    self.front_modifier[i] = another
                return True
            else:
                if o.replace(one, another):
                    return True

        for i, o in enumerate(self.pre_modifier):
            if o == one:
                if another is None:
                    del sent.pre_modifier[i]
                else:
                    self.pre_modifier[i] = another
                return True
            else:
                if o.replace(one, another):
                    return True

        if self.head == one:
            self.head = another
            return True
        elif self.head is not None:
            if self.head.replace(one, another):
                return True

        for i, o in enumerate(self.complement):
            if o == one:
                if another is None:
                    del sent.complement[i]
                else:
                    self.complement[i] = another
                return True
            else:
                if o.replace(one, another):
                    return True

        for i, o in enumerate(self.post_modifier):
            if o == one:
                if another is None:
                    del sent.front_modifier[i]
                else:
                    self.front_modifier[i] = another
                return True
            else:
                if o.replace(one, another):
                    return True
        return False


class Clause(Phrase):
    """ Clause - sentence.
    From simplenlg:
     * <UL>
     * <li>FrontModifier (eg, "Yesterday")
     * <LI>Subject (eg, "John")
     * <LI>PreModifier (eg, "reluctantly")
     * <LI>Verb (eg, "gave")
     * <LI>IndirectObject (eg, "Mary")
     * <LI>Object (eg, "an apple")
     * <LI>PostModifier (eg, "before school")
     * </UL>

    """

    def __init__(self, subj=None, vp=None):
        super().__init__(type='CLAUSE', vname='visit_clause')
        self.set_subj(subj)
        self.set_vp(vp)

    def to_xml(self, element):
        features = self.features_to_xml_attributes()
        text = '<%s xsi:type="SPhraseSpec" %s>\n' % (element, features)
        return text
    
    def __eq__(self, other):
        if (not isinstance(other, Clause)):
            return False
        return (self.subj == other.subj and
                self.vp == other.vp and
                super().__eq__(other))

    def __str__(self):
        return ' '.join([str(x) for x in
                        [self.subj, self.vp] if x is not None])

    def __repr__(self):
        return ('Clause: subj=%s vp=%s\n(%s)' %
                (str(self.subj), str(self.vp), super().__str__()))

    def set_subj(self, subj):
        """ Set the subject of the clause. """
        # convert str to String if necessary
        self.subj = String(subj) if isinstance(subj, str) else subj

    def set_vp(self, vp):
        """ Set the vp of the clause. """
        self.vp = String(vp) if isinstance(vp, str) else vp

    def constituents(self):
        """ Return a generator to iterate through constituents. """
        yield from self.yield_front_modifiers()
        if self.subj is not None:
            # TODO: can we use yield from here? I think so...
            for c in self.subj.constituents(): yield c
        yield from self.yield_pre_modifiers()
        if self.vp is not None:
            for c in self.vp.constituents(): yield c
        yield from self.yield_complements()
        yield from self.yield_post_modifiers()

    def replace(self, one, another):
        """ Replace first occurance of one with another.
        Return True if successful.
        
        """
        if self.subj == one:
            self.subj = another
            return True
        elif self.subj is not None:
            if self.subj.replace(one, another): return True

        if self.vp == one:
            self.vp = another
            return True
        elif self.vp is not None:
            if self.vp.replace(one, another): return True

        return super().replace(one, another)


class NP(Phrase):
    """
     * <UL>
     * <li>Specifier    (eg, "the")
     * <LI>PreModifier  (eg, "green")
     * <LI>Noun         (eg, "apple")
     * <LI>PostModifier (eg, "in the shop")
     * </UL>
     """
    def __init__(self, head=None, spec=None):
        super().__init__(type='NOUN_PHRASE', vname='visit_np')
        self.set_spec(spec)
        self.set_head(head)

    def __eq__(self, other):
        if (not isinstance(other, NP)):
            return False
        return (self.spec == other.spec and
                self.head == other.head and
                super().__eq__(other))

    def __str__(self):
        """ Return string representation of the class. """
        if self.spec is not None:
            return str(self.spec) + ' ' + super().__str__()
        else:
            return super().__str__()

    def to_xml(self, element):
        features = self.features_to_xml_attributes()
        text = '<%s xsi:type="NPPhraseSpec" %s>\n' % (element, features)
        return text

    def set_spec(self, spec):
        """ Set the specifier (e.g., determiner) of the NP. """
        # convert str to String if necessary
        self.spec = String(spec) if isinstance(spec, str) else spec

    def constituents(self):
        """ Return a generator to iterate through constituents. """
        if self.spec is not None:
            for c in self.spec.constituents(): yield c
        yield from self.yield_front_modifiers()
        yield from self.yield_pre_modifiers()
        yield from self.yield_head()
        yield from self.yield_complements()
        yield from self.yield_post_modifiers()

    def replace(self, one, another):
        """ Replace first occurance of one with another.
        Return True if successful.
        
        """
        if self.spec == one:
            self.spec = another
            return True
        elif self.spec is not None:
            if self.spec.replace(one, another): return True

        return super().replace(one, another)


class VP(Phrase):
    """
    * <UL>
     * <LI>PreModifier      (eg, "reluctantly")
     * <LI>Verb             (eg, "gave")
     * <LI>IndirectObject   (eg, "Mary")
     * <LI>Object           (eg, "an apple")
     * <LI>PostModifier     (eg, "before school")
     * </UL>
     """
    def __init__(self, head=None, *compl):
        super().__init__(type='VERB_PHRASE', vname='visit_vp')
        self.set_head(head)
        self.add_complement(*compl)

    def get_object(self):
        for c in self.complement:
            if ('discourseFunction' in c.features and
                c.features['discourseFunction'] == 'OBJECT'):
                return c
        return None

    def remove_object(self):
        compls = list()
        for c in self.complement:
            if ('discourseFunction' in c.features and
                c.features['discourseFunction'] == 'OBJECT'):
                continue
            else:
                compls.append(c)
        self.complement = compls

    def set_object(self, obj):
        self.remove_object()
        if obj is not None:
            if isinstance(obj, str): obj = String(obj)
            obj.features['discourseFunction'] = 'OBJECT'
            self.complement.insert(0, obj)

    def to_xml(self, element):
        features = self.features_to_xml_attributes()
        text = '<%s xsi:type="VPPhraseSpec" %s>\n' % (element, features)
        return text


class PP(Phrase):
    def __init__(self, head=None, *compl):
        super().__init__(type='PREPOSITIONAL_PHRASE', vname='visit_pp')
        self.set_head(head)
        self.add_complement(*compl)
    
    def to_xml(self, element):
        features = self.features_to_xml_attributes()
        text = '<%s xsi:type="PPPhraseSpec" %s>\n' % (element, features)
        return text


class AdvP(Phrase):
    def __init__(self, head=None, compl=None):
        super().__init__(type='ADVERB_PHRASE', vname='visit_pp')
        self.set_head(head)
        self.add_complement(*compl)

    def to_xml(self, element):
        features = self.features_to_xml_attributes()
        text = '<%s xsi:type="AdvPhraseSpec" %s>\n' % (element, features)
        return text


class AdjP(Phrase):
    def __init__(self, head=None, compl=None):
        super().__init__(type='ADJECTIVE_PHRASE', vname='visit_pp')
        self.set_head(head)
        self.add_complement(*compl)
    
    def to_xml(self, element):
        features = self.features_to_xml_attributes()
        text = '<%s xsi:type="AdjPhraseSpec" %s>\n' % (element, features)
        return text


class CC(Element):
    """ Coordinated clause with a conjunction. """

    def __init__(self, *coords, conj='and'):
        super().__init__(vname='visit_cc')
        self.coords = list()
        self.add_coordinate(*coords)
        self.add_feature('conj', conj)

    def __eq__(self, other):
        if (not isinstance(other, CC)):
            return False
        else:
            return (self.coords == other.coords and
                    super().__eq__(other))

    def __str__(self):
        if self.coords is None: return ''
        return ' '.join(map(lambda x: str(x), self.coords))


    def to_xml(self, element):
        features = self.features_to_xml_attributes()
        text = ('<%s xsi:type="CoordinatedPhraseElement" %s>\n' %
                (element, features))
        return text

    def add_coordinate(self, *elts):
        """ Add one or more elements as a co-ordinate in the clause. """
        for e in self._strings_to_elements(*elts):
            if e not in self.coords: self.coords.append(e)

    def constituents(self):
        """ Return a generator to iterate through constituents. """
        if self.coords is not None:
            for c in self.coords:
                yield from c.constituents()

    def replace(self, one, another):
        """ Replace first occurance of one with another.
        Return True if successful.
        
        """
        for i, o in enumerate(self.coords):
            if o == one:
                if another is not None: self.coords[i] = another
                else: del self.coords[i]
                return True
        return False


class IVisitor:
    def visit_phrase(self, node, element=''):
        if node.front_modifier:
            for c in node.front_modifier:
                c.accept(self, 'frontMod')
        
        if node.pre_modifier:
            for c in node.pre_modifier:
                c.accept(self, 'preMod')
        
        if node.head:
            node.head.accept(self, 'head')

        if node.complement:
            for c in node.complement:
                c.accept(self, 'compl')

        if node.post_modifier:
            for c in node.post_modifier:
                c.accept(self, 'postMod')



class XmlVisitor(IVisitor):
    def __init__(self):
        self.header = '''
<?xml version="1.0" encoding="utf-8"?>
<nlg:NLGSpec xmlns="http://simplenlg.googlecode.com/svn/trunk/res/xml"
xmlns:nlg="http://simplenlg.googlecode.com/svn/trunk/res/xml"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://simplenlg.googlecode.com/svn/trunk/res/xml ">
<nlg:Request>

<Document cat="PARAGRAPH">
'''
        self.xml = ''
        self.footer = '''
</Document>
</nlg:Request>
</nlg:NLGSpec>
'''

    def visit_word(self, node, element):
        if (node is not None):
            self.xml += node.to_xml(element)
    
    def visit_string(self, node, element):
        if (node is not None):
            self.xml += node.to_xml(element)
    
    def visit_placeholder(self, node, element):
        if (node is not None):
            self.xml += node.to_xml(element)

    def visit_clause(self, node, element):
        if (node is not None):
            self.xml += node.to_xml(element)
        if node.subj:
            node.subj.accept(self, 'subj')
        if node.vp:
            node.vp.accept(self, 'vp')
        self.xml += '\n</%s>\n' % element

    def visit_np(self, node, element):
        if (node is not None):
            self.xml += node.to_xml(element)
        if node.spec:
            node.spec.accept(self, 'spec')
        self.visit_phrase(node)
        self.xml += '\n</%s>\n' % element

    def visit_vp(self, node, element):
        if (node is not None):
            self.xml += node.to_xml(element)
        self.visit_phrase(node)
        self.xml += '\n</%s>\n' % element

    def visit_pp(self, node, element):
        if (node is not None):
            self.xml += node.to_xml(element)
        self.visit_phrase(node)
        self.xml += '\n</%s>\n' % element

    def visit_cc(self, node, element):
        if (node is not None):
            self.xml += node.to_xml(element)
        for c in node.coords:
            c.accept(self, 'coord')
        self.xml += '\n</%s>\n' % element

    def to_xml(self):
        return self.header + self.xml + self.footer
    
    def clear(self):
        self.xml = ''

    def __repr__(self):
        return ('[ XmlVisitor:\n%s]' % (self.header + self.xml + self.footer))



class StrVisitor(IVisitor):
    def __init__(self):
        self.text = ''

    def visit_element(self, node, element):
        # there is no text in Element
        pass
    
    def visit_word(self, node, element):
        if (node is not None):
            self.text += ' ' + node.to_str()
    
    def visit_string(self, node, element):
        if (node is not None):
            self.text += ' ' + node.to_str()
    
    def visit_placeholder(self, node, element):
        if (node is not None):
            self.text += ' ' + node.to_str()
    
    def visit_clause(self, node, element):
        if node.subj:
            node.subj.accept(self)
        if node.vp:
            node.vp.accept(self)
    
    def visit_np(self, node, element):
        if node.spec:
            node.spec.accept(self)
        self.visit_phrase(node)
    
    def visit_vp(self, node, element):
        self.visit_phrase(node)
    
    def visit_pp(self, node, element):
        self.visit_phrase(node)
    
    def visit_cc(self, node, element):
        if len(node.coords) > 2:
            for c in node.coords[:-1]:
                c.accept(self)
                self.text += ','
            self.text = self.text[:-1] # remove the last ", "
            self.text += ' and'
            node.coords[-1].accept(self)
    
        elif len(node.coords) > 1:
            node.coords[0].accept(self)
            self.text += ' and'
            node.coords[1].accept(self)

        elif len(node.coords) > 0:
            node.coords[0].accept(self)

    def to_str(self):
        return self.text.strip()
    
    def clear(self):
        self.text = ''
    
    def __repr__(self):
        return ('[ StrVisitor:\n%s]' % (self.text))










