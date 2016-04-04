import unittest

from nlglib.structures import *


class TestRhetRep(unittest.TestCase):

    expected1 = """\
  <rhetrep name="elaboration">
    <marker>and</marker>
    <semrep>
      This is the nucleus
    </semrep>
    <semrep>
      this is the satelite
    </semrep>
  </rhetrep>
"""

    expected2 = """\
  <rhetrep name="elaboration">
    <marker>and</marker>
    <semrep>
      This is the nucleus
    </semrep>
    <rhetrep name="concession">
      <marker>however</marker>
      <semrep>
        this is another nucleus
      </semrep>
      <semrep>
        this is the satelite
      </semrep>
    </rhetrep>
  </rhetrep>
"""

    def test_init(self):
        nucleus = SemRep('This is the nucleus')
        satelite = SemRep('this is the satelite')
        r = RhetRep('elaboration', nucleus, satelite, 'and')
        self.assertEqual(self.expected1, r.to_xml(1))
        nucleus2 = SemRep('this is another nucleus')
        r2 = RhetRep('concession', nucleus2, satelite, 'however')
        r = RhetRep('elaboration', nucleus, r2, 'and')
        self.assertEqual(self.expected2, r.to_xml(1))


class DummyMessage(MsgSpec):
    """ A dummy message specification for testing. """

    def __init__(self, name):
        super().__init__(name)

    def foo(self):
        """ A simple method that is acting as a kye and returns value 'bar' """
        return 'bar'


class TestMessageSpec(unittest.TestCase):

    def test_str(self):
        tm = DummyMessage('nice_name')
        descr = str(tm)
        self.assertEqual('nice_name', descr)

    def test_repr(self):
        tm = DummyMessage('nice_name')
        descr = repr(tm)
        self.assertEqual('MsgSpec: nice_name', descr)

    def test_value_for(self):
        tm = DummyMessage('some_name')
        self.assertEqual('bar', tm.value_for('foo'))
        self.assertRaises(ValueError, tm.value_for, 'baz')


class TestMessage(unittest.TestCase):

    def test_str(self):
        expected = 'foo bar baz'
        m = Message('Elaboration', 'foo', 'bar', 'baz')
        descr = str(m)
        self.assertEqual(expected, descr)

        expected = 'foo bar baz bar baz'
        m2 = Message('Contrast', m, 'bar', 'baz')
        descr = str(m2)
        self.assertEqual(expected, descr)

    def test_repr(self):
        expected = "Message (Elaboration): 'foo' 'bar' 'baz'"
        m = Message('Elaboration', 'foo', 'bar', 'baz')
        descr = repr(m)
        self.assertEqual(expected, descr)

        expected = ("Message (Contrast): Message (Elaboration): 'foo' 'bar' 'baz' 'bar' 'baz'")
        m2 = Message('Contrast', m, 'bar', 'baz')
        descr = repr(m2)
        self.assertEqual(expected, descr)


class TestParagraph(unittest.TestCase):

    def test_str(self):
        expected = '\tfoo bar'
        m = Message('Elaboration', 'foo', 'bar')
        p = Paragraph(m)
        descr = str(p)
        self.assertEqual(expected, descr)

        expected = '\tfoo bar bar baz'
        m2 = Message('Contrast', m, 'bar', 'baz')
        p = Paragraph(m2)
        descr = str(p)
        self.assertEqual(expected, descr)

        expected = '\tfoo bar bar baz; foobar'
        m3 = Message('Leaf', 'foobar')
        p = Paragraph(m2, m3)
        descr = str(p)
        self.assertEqual(expected, descr)

    def test_repr(self):
        expected = """Paragraph (1):
Message (Elaboration): 'foo' 'bar'"""
        m = Message('Elaboration', 'foo', 'bar')
        p = Paragraph(m)
        descr = repr(p)
        self.assertEqual(expected, descr)

        expected = """Paragraph (1):
Message (Contrast): Message (Elaboration): 'foo' 'bar' 'bar' 'baz'"""
        m2 = Message('Contrast', m, 'bar', 'baz')
        p = Paragraph(m2)
        descr = repr(p)
        self.assertEqual(expected, descr)

        expected ="""Paragraph (2):
Message (Contrast): Message (Elaboration): 'foo' 'bar' \
'bar' 'baz'; Message (Leaf): 'foobar'"""
        m3 = Message('Leaf', 'foobar')
        p = Paragraph(m2, m3)
        descr = repr(p)
        self.assertEqual(expected, descr)


class TestSection(unittest.TestCase):

    def test_str(self):
        expected = 'One\n\tfoo bar'
        m = Message('Elaboration', 'foo', 'bar')
        s = Section('One', Paragraph(m))
        descr = str(s)
        self.assertEqual(expected, descr)

        expected = 'One\n\tfoo bar\n\tbaz bar'
        m2 = Message('Contrast', 'baz', 'bar')
        s = Section('One', Paragraph(m), Paragraph(m2))
        descr = str(s)
        self.assertEqual(expected, descr)

    def test_repr(self):
        expected = """Section:
title: 'One'
Paragraph (1):
Message (Elaboration): 'foo' 'bar'"""
        m = Message('Elaboration', 'foo', 'bar')
        s = Section('One', Paragraph(m))
        descr = repr(s)
        self.assertEqual(expected, descr)

        expected = """Section:
title: 'One'
Paragraph (1):
Message (Elaboration): 'foo' 'bar'
Paragraph (1):
Message (Contrast): 'baz' 'bar'"""
        m2 = Message('Contrast', 'baz', 'bar')
        s = Section('One', Paragraph(m), Paragraph(m2))
        descr = repr(s)
        self.assertEqual(expected, descr)


class TestDocument(unittest.TestCase):

    def test_str(self):
        expected = 'MyDoc\nOne\n\tfoo bar'
        m = Message('Elaboration', 'foo', 'bar')
        one = Section('One', Paragraph(m))
        d = Document('MyDoc', one)
        descr = str(d)
        self.assertEqual(expected, descr)

        expected = 'MyDoc\nOne\n\tfoo bar\n\nTwo\n\tbaz bar'
        m2 = Message('Contrast', 'baz', 'bar')
        two = Section('Two', Paragraph(m2))
        d = Document('MyDoc', one, two)
        descr = str(d)
        self.assertEqual(expected, descr)

    def test_repr(self):
        expected = """Document:
title: 'MyDoc'
Section:
title: 'One'
Paragraph (1):
Message (Elaboration): 'foo' 'bar'"""
        m = Message('Elaboration', 'foo', 'bar')
        one = Section('One', Paragraph(m))
        d = Document('MyDoc', one)
        descr = repr(d)
        self.assertEqual(expected, descr)

        expected = """Document:
title: 'MyDoc'
Section:
title: 'One'
Paragraph (1):
Message (Elaboration): 'foo' 'bar'

Section:
title: 'Two'
Paragraph (1):
Message (Contrast): 'baz' 'bar'"""
        m2 = Message('Contrast', 'baz', 'bar')
        two = Section('Two', Paragraph(m2))
        d = Document('MyDoc', one, two)
        descr = repr(d)
        self.assertEqual(expected, descr)


################################################################################
#                                                                              #
#                              microplanning                                   #
#                                                                              #
################################################################################


class TestElement(unittest.TestCase):
    """ Test the functionality of the base class of NLG elements. """

    def test_basics(self):
        """ Test ctor. """
        e = Element()
        self.assertIsNotNone(e)
        e = Element(ELEMENT)
        self.assertEqual('visit_element', e._visitor_name)

    def test_features(self):
        """ Test handeling features. """
        e = Element(ELEMENT)
        self.assertEqual('visit_element', e._visitor_name)
        self.assertEqual(False, e.has_feature('TENSE'))
        self.assertEqual(None, e.feature('TENSE'))
        self.assertRaises(KeyError, e.get_feature, 'TENSE')
        e.set_feature('TENSE', 'PAST')
        self.assertEqual('PAST', e._features['TENSE'])
        self.assertEqual(True, e.has_feature('TENSE'))
        self.assertEqual('PAST', e.feature('TENSE'))
        self.assertEqual('PAST', e.get_feature('TENSE'))

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
        expected = ' tense="past"'
        e.set_feature('tense', 'past')
        data = e.features_to_xml_attributes()
        self.assertEqual(expected, data)

        expected = ' tense="past" aspect="progressive"'
        e.set_feature('aspect', 'progressive')
        data = e.features_to_xml_attributes()
        self.assertEqual(True, 'tense="past"' in data)
        self.assertEqual(True, 'aspect="progressive"' in data)

    def test_eq(self):
        """ Test the test of equality :-) """
        e1 = Element()
        e2 = Element()
        self.assertEqual(e1, e2)

        e1.set_feature('tense', 'future')
        self.assertNotEqual(e1, e2)

        e2.set_feature('aspect', 'progressive')
        self.assertNotEqual(e1, e2)

        e1.set_feature('aspect', 'progressive')
        e2.set_feature('tense', 'future')
        self.assertEqual(e1, e2)

    def test_str_to_elt(self):
        """ Test converting strings to Strings. """
        expected = [String('late'), Word('evening', 'NOUN')]
        actual = list(str_to_elt('late', Word('evening', 'NOUN')))
        self.assertEqual(expected, actual)

    def test_adding_mods(self):
        """ Test adding modifiers. """
        tmp = list()
        Element._add_to_list(tmp, 'yesterday')
        expected = [String('yesterday')]
        self.assertEqual(expected, tmp)

        expected.append(String('late'))
        expected.append(Word('evening', 'NOUN'))
        Element._add_to_list(tmp, 'late', Word('evening', 'NOUN'))
        self.assertEqual(expected, tmp)

    def test_deleting_mods(self):
        """ Test deleting modifiers. """
        tmp = list()
        Element._add_to_list(tmp, 'to', 'the', 'little', 'shop')
        expected = list(map(lambda x: String(x),
                            ['to', 'the', 'little', 'shop']))
        self.assertEqual(expected, tmp)

        Element._del_from_list(tmp, 'little')
        expected = list(map(lambda x: String(x), ['to', 'the', 'shop']))
        self.assertEqual(expected, tmp)


class TestString(unittest.TestCase):
    """ Tests for a string element. """

    def test_eq(self):
        """ Test equality. """
        s1 = String()
        s2 = String()
        self.assertEqual(s1, s2)

        s1 = String('hello')
        s2 = String('word')
        self.assertNotEqual(s1, s2)

        s1.set_feature('type', 'greeting')
        s2 = String('hello')
        self.assertNotEqual(s1, s2)

        s2.set_feature('type', 'greeting')
        self.assertEqual(s1, s2)

class TestWord(unittest.TestCase):
    """ Tests for a word element. """

#    def test_str(self):
#        """ Test basic printing. """
#        w = Word('foo', 'NOUN')
#        expected = 'foo'
#        self.assertEqual(expected, str(w))
#
#        w.set_feature('countable', 'yes')
#        self.assertEqual(expected, str(w))

    # def test_repr(self):
    #     """ Test debug printing. """
    #
    #     w = Word('foo', 'NOUN')
    #     expected = 'Word(foo, NOUN) {}'
    #     self.assertEqual(expected, repr(w))
    #
    #     expected = "Word(foo, NOUN) {'countable': 'yes'}"
    #     w.set_feature('countable', 'yes')
    #     self.assertEqual(expected, repr(w))

    def test_eq(self):
        """ Test equality. """
        w1 = Word('foo', 'NOUN')
        w2 = Word('foo', 'VERB')
        self.assertNotEqual(w1, w2)

        w2.pos = 'NOUN'
        self.assertEqual(w1, w2)

        w2.set_feature('role', 'subject')
        self.assertNotEqual(w1, w2)

        w2.del_feature('role', 'subject')
        self.assertEqual(w1, w2)

        w1.set_feature('role', 'subject')
        w2.set_feature('role', 'object')
        self.assertNotEqual(w1, w2)

        w2.set_feature('role', 'subject')
        self.assertEqual(w1, w2)


class TestPlaceHolder(unittest.TestCase):
    """ Tests for the PlaceHolder class. """

    def test_eq(self):
        """ Test equality. """
        self.assertEqual(PlaceHolder(), PlaceHolder())

        p1 = PlaceHolder('arg1')
        p2 = PlaceHolder('arg2')
        self.assertNotEqual(p1, p2)

        p2 = PlaceHolder('arg1')
        self.assertEqual(p1, p2)

        p1.set_feature('countable', 'no')
        self.assertNotEqual(p1, p2)

        p2.set_feature('countable', 'no')
        self.assertEqual(p1, p2)

        p1 = PlaceHolder('arg1', 'drum')
        p1.set_feature('countable', 'no')
        self.assertNotEqual(p1, p2)

        p2.set_value('drum')
        self.assertEqual(p1, p2)

    # def test_repr(self):
    #     """ Test debug printing. """
    #     expected = "PlaceHolder: id='obj1' value=None {}"
    #     p = PlaceHolder('obj1')
    #     self.assertEqual(expected, repr(p))
    #
    #     expected = "PlaceHolder: id='obj1' value=None {'countable': 'yes'}"
    #     p.set_feature('countable', 'yes')
    #     self.assertEqual(expected, repr(p))


class TestPhrase(unittest.TestCase):
    """ Test harness for the Phrase base class. """

#    def test_str(self):
#        """ Test basic printing. """
#        p = Phrase()
#        expected = ''
#        self.assertEqual(expected, str(p))
#
#        p.head = 'went'
#        expected = 'went'
#        self.assertEqual(expected, str(p))
#
#        p.front_modifiers.append('yesterday')
#        expected = 'yesterday went'
#        self.assertEqual(expected, str(p))
#
#        p.pre_modifiers.append('Peter')
#        expected = 'yesterday Peter went'
#        self.assertEqual(expected, str(p))
#
#        p.complements.append('to')
#        expected = 'yesterday Peter went to'
#        self.assertEqual(expected, str(p))
#
#        p.post_modifiers.append('Russia')
#        expected = 'yesterday Peter went to Russia'
#        self.assertEqual(expected, str(p))
#
#        p.set_feature('tense', 'past')
#        expected = 'yesterday Peter went to Russia'
#        self.assertEqual(expected, str(p))

    # def test_repr(self):
    #     """ Test debug printing. """
    #     p = Phrase()
    #     expected = '(Phrase None None: "" {})'
    #     self.assertEqual(expected, repr(p))
    #
    #     p.head = 'went'
    #     expected = '(Phrase None None: "went" {})'
    #     self.assertEqual(expected, repr(p))
    #
    #     p.front_modifiers.append('yesterday')
    #     expected = '(Phrase None None: "yesterday went" {})'
    #     self.assertEqual(expected, repr(p))
    #
    #     p.pre_modifiers.append('Peter')
    #     expected = '(Phrase None None: "yesterday Peter went" {})'
    #     self.assertEqual(expected, repr(p))
    #
    #     p.complements.append('to')
    #     expected = '(Phrase None None: "yesterday Peter went to" {})'
    #     self.assertEqual(expected, repr(p))
    #
    #     p.post_modifiers.append('Russia')
    #     expected = '(Phrase None None: "yesterday Peter went to Russia" {})'
    #     self.assertEqual(expected, repr(p))
    #
    #     p.set_feature('tense', 'past')
    #     expected = '(Phrase None None: "yesterday ' \
    #                 + 'Peter went to Russia" {\'tense\': \'past\'})'
    #     self.assertEqual(expected, repr(p))

    def test_eq(self):
        """ Test equality. """
        p1 = Phrase()
        p2 = Phrase()
        self.assertEqual(p1, p2)

        p1.head = Word('went', 'VERB', {'TENSE': 'PAST'})
        self.assertNotEqual(p1, p2)

        p2.head = Word('went', 'VERB', {'TENSE': 'PAST'})
        self.assertEqual(p1, p2)

        p1.front_modifiers.append('yesterday')
        self.assertNotEqual(p1, p2)

        p2.front_modifiers.append('yesterday')
        self.assertEqual(p1, p2)

        p1.pre_modifiers.append('Peter')
        self.assertNotEqual(p1, p2)

        p2.pre_modifiers.append('Peter')
        self.assertEqual(p1, p2)

        p1.complements.append('to')
        self.assertNotEqual(p1, p2)

        p2.complements.append('to')
        self.assertEqual(p1, p2)

        p1.post_modifiers.append('Russia')
        self.assertNotEqual(p1, p2)

        p2.post_modifiers.append('Russia')
        self.assertEqual(p1, p2)

        p1.set_feature('tense', 'past')
        self.assertNotEqual(p1, p2)

        p2.set_feature('tense', 'past')
        self.assertEqual(p1, p2)

        p1._type = PHRASE
        self.assertNotEqual(p1, p2)

        p2._type = PHRASE
        self.assertEqual(p1, p2)

    def test_constituents(self):
        """ Test iterating through constituents. """
        p = Phrase()
        self.assertEqual([], list(p.constituents()))

        p.head = Word('head', 'NOUN')
        self.assertEqual([Word('head', 'NOUN')], list(p.constituents()))

        p2 = Phrase()
        p2.head = Word('forward', 'ADVERB')
        p.complements.append(p2)
        expected = [Word('head', 'NOUN'), Word('forward', 'ADVERB')]
        self.assertEqual(expected, list(p.constituents()))

    def test_arguments(self):
        """ Test getting arguments. """
        p = Phrase()
        self.assertEqual([], list(p.arguments()))
        ph = PlaceHolder('arg_name')
        p.head = Word('ask', 'VERB')
        p.complements.append(ph)
        self.assertEqual([ph], list(p.arguments()))

        ph2 = PlaceHolder('arg_place')
        p2 = Phrase()
        p2.head = ph2
        p.post_modifiers.append(p2)
        args = list(p.arguments())
        self.assertEqual(ph, args[0])
        self.assertEqual(ph2, args[1])

    def test_replace(self):
        """ Test replacing a constituent. """
        p = Phrase()
        hi = Word('hi', 'EXCLAMATION')
        hello = Word('hello', 'EXCLAMATION')
        self.assertEqual(False, p.replace(hi, hello))
        ph = PlaceHolder('arg_name')
        p.head = hi
        p.complements.append(ph)
        self.assertEqual(True, p.replace(hi, hello))
        self.assertEqual(hello, p.head)

        ph2 = PlaceHolder('arg_place')
        p2 = Phrase()
        p2.head = ph2
        p.post_modifiers.append(p2)

        p.replace(PlaceHolder('arg_place'), Word('Aberdeen', 'NOUN'))
        self.assertEqual(False,
            PlaceHolder('arg_place') in list(p.constituents()))


class TestClause(unittest.TestCase):
    """ Tests for Clause. """

#    def test_str(self):
#        """ Test printing. """
#        c = Clause()
#        expected = ''
#        self.assertEqual(expected, str(c))
#
#        c = Clause('Roman')
#        expected = 'Roman'
#        self.assertEqual(expected, str(c))
#
#        c = Clause('Roman', 'is slow!')
#        expected = 'Roman is slow!'
#        self.assertEqual(expected, str(c))

    def test_constituents(self):
        """ Test iterating through constituents. """
        c = Clause('Roman', 'is slow!')
        expected = [String('Roman'), String('is slow!')]
        actual = list(c.constituents())
        self.assertEqual(expected, actual)

        c.add_pre_modifier('Alas!')
        expected = [String('Alas!'), String('Roman'), String('is slow!')]
        actual = list(c.constituents())
        self.assertEqual(expected, actual)

    def test_replace(self):
        """ Test replacing elements. """
        p = Clause()
        hi = Word('hi', 'EXCLAMATION')
        hello = Word('hello', 'EXCLAMATION')
        self.assertEqual(False, p.replace(hi, hello))
        ph = PlaceHolder('arg_name')
        p.subj = hi
        p.post_modifiers.append(ph)
        self.assertEqual(True, p.replace(hi, hello))
        self.assertEqual(hello, p.subj)

        ph2 = PlaceHolder('arg_place')
        p2 = Phrase()
        p2.head = ph2
        p.vp = (p2)

        p.replace(PlaceHolder('arg_place'), Word('Aberdeen', 'NOUN'))
        self.assertEqual(False,
            PlaceHolder('arg_place') in list(p.constituents()))


class TestNP(unittest.TestCase):
    """ Tests for noun phrase class. """

    def test_constituents(self):
        """ Test iterating through constituents. """
        p = NounPhrase(spec='the', head='Simpsons')
        expected = [String('the'), String('Simpsons')]
        self.assertEqual(expected, list(p.constituents()))

    def test_replace(self):
        """ Test replacing an element. """
        p = NounPhrase(spec='', head='Simpsons')
        expected = [String('the'), String('Simpsons')]
        p.replace(String(''), String('the'))
        self.assertEqual(expected, list(p.constituents()))


class TestVP(unittest.TestCase):
    """ Tests for verb phrase class. """

    def test_constituents(self):
        """ Test iterating through constituents. """
        p = VerbPhrase('give', 'the book', 'to the cook')
        expected = [String('give'), String('the book'), String('to the cook')]
        self.assertEqual(expected, list(p.constituents()))

    def test_replace(self):
        """ Test replacing an element. """
        p = VerbPhrase('give', 'the book', 'to the cook')
        expected = [String('give'), String('the book'), String('to the cook')]
        self.assertEqual(expected, list(p.constituents()))
        p.replace(String('to the cook'), String('to the cheff'))
        expected = [String('give'), String('the book'), String('to the cheff')]
        self.assertEqual(expected, list(p.constituents()))

    def test_arguments(self):
        """ Test replacing arguments. """
        p = VerbPhrase('give', PlaceHolder('arg_obj'), PrepositionalPhrase('to', PlaceHolder('arg_rec')))
        expected = [PlaceHolder('arg_obj'), PlaceHolder('arg_rec')]
        self.assertEqual(expected, list(p.arguments()))

        obj = NounPhrase(spec='the', head='candy')
        rec = NounPhrase(head='Roman')
        p.replace_arguments(arg_obj=obj, arg_rec=rec)
        self.assertEqual([], list(p.arguments()))
        expected = [String('give'), String('the'), String('candy'),
                    String('to'), NounPhrase('Roman')]


class TestCC(unittest.TestCase):
    """ Tests for co-ordinated clause. """

    def test_constituents(self):
        """ Test iterating through constituents. """
        p = Coordination('apple', 'banana', 'pear')
        expected = [String('apple'), String('banana'), String('pear')]
        self.assertEqual(expected, list(p.constituents()))

    def test_replace(self):
        """ Test replacing an element. """
        p = Coordination('apple', 'banana', 'pear')
        expected = [String('apple'), String('banana'), String('pear')]
        self.assertEqual(expected, list(p.constituents()))

        p.replace(String('banana'), String('potato'))
        expected = [String('apple'), String('potato'), String('pear')]
        self.assertEqual(expected, list(p.constituents()))










# main
if __name__ == '__main__':
    unittest.main()
