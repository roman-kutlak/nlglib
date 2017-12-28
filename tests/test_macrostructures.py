import unittest

from nlglib.macroplanning import Document, RhetRel, MsgSpec
from nlglib.microplanning import *

Paragraph = Document


class Section(Document):
    def __init__(self, title, *paragraphs):
        super().__init__(*paragraphs, title=title)


class DummyMessage(MsgSpec):
    """ A dummy RhetRel specification for testing. """

    def __init__(self, name):
        super().__init__(name)

    @staticmethod
    def foo():
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


class TestRhetRel(unittest.TestCase):
    expected1 = """\
  <RhetRel name="elaboration">
    <marker>and</marker>
    <nuclei>
      <nucleus>
        This is the nuclei
      </nucleus>
    </nuclei>
    <satellite>
      this is the satellite
    </satellite>
  </RhetRel>
"""

    expected2 = """\
  <RhetRel name="elaboration">
    <marker>and</marker>
    <semrep>
      This is the nuclei
    </semrep>
    <RhetRel name="concession">
      <marker>however</marker>
      <semrep>
        this is another nuclei
      </semrep>
      <semrep>
        this is the satellite
      </semrep>
    </RhetRel>
  </RhetRel>
"""

    def test_init(self):
        nucleus = 'This is the nucleus'
        satellite = 'this is the satellite'
        r = RhetRel('elaboration', nucleus, satellite=satellite, marker='and')
        self.assertEqual(self.expected1, r.to_xml(1))
        nucleus2 = 'this is another nucleus'
        r2 = RhetRel('concession', nucleus2, satellite=satellite, marker='however')
        r = RhetRel('elaboration', nucleus, satellite=r2, marker='and')
        self.assertEqual(self.expected2, r.to_xml(1))

    def test_str(self):
        expected = 'foo bar baz'
        m = RhetRel('Elaboration', 'foo', 'bar', 'baz')
        descr = str(m)
        self.assertEqual(expected, descr)

        expected = 'foo bar baz bar baz'
        m2 = RhetRel('Contrast', m, 'bar', 'baz')
        descr = str(m2)
        self.assertEqual(expected, descr)

    def test_repr(self):
        expected = "RhetRel (Elaboration): 'foo' 'bar' 'baz'"
        m = RhetRel('Elaboration', 'foo', 'bar', 'baz')
        descr = repr(m)
        self.assertEqual(expected, descr)

        expected = "RhetRel (Contrast): RhetRel (Elaboration): 'foo' 'bar' 'baz' 'bar' 'baz'"
        m2 = RhetRel('Contrast', m, 'bar', 'baz')
        descr = repr(m2)
        self.assertEqual(expected, descr)


class TestParagraph(unittest.TestCase):
    def test_str(self):
        expected = '\tfoo bar'
        m = RhetRel('Elaboration', 'foo', 'bar')
        p = Paragraph(m)
        descr = str(p)
        self.assertEqual(expected, descr)

        expected = '\tfoo bar bar baz'
        m2 = RhetRel('Contrast', m, 'bar', 'baz')
        p = Paragraph(m2)
        descr = str(p)
        self.assertEqual(expected, descr)

        expected = '\tfoo bar bar baz; foobar'
        m3 = RhetRel('Leaf', 'foobar')
        p = Paragraph(m2, m3)
        descr = str(p)
        self.assertEqual(expected, descr)

    def test_repr(self):
        expected = """Paragraph (1):
RhetRel (Elaboration): 'foo' 'bar'"""
        m = RhetRel('Elaboration', 'foo', 'bar')
        p = Paragraph(m)
        descr = repr(p)
        self.assertEqual(expected, descr)

        expected = """Paragraph (1):
RhetRel (Contrast): RhetRel (Elaboration): 'foo' 'bar' 'bar' 'baz'"""
        m2 = RhetRel('Contrast', m, 'bar', 'baz')
        p = Paragraph(m2)
        descr = repr(p)
        self.assertEqual(expected, descr)

        expected = """Paragraph (2):
RhetRel (Contrast): RhetRel (Elaboration): 'foo' 'bar' \
'bar' 'baz'; RhetRel (Leaf): 'foobar'"""
        m3 = RhetRel('Leaf', 'foobar')
        p = Paragraph(m2, m3)
        descr = repr(p)
        self.assertEqual(expected, descr)


class TestSection(unittest.TestCase):
    def test_str(self):
        expected = 'One\n\tfoo bar'
        m = RhetRel('Elaboration', 'foo', 'bar')
        s = Section('One', Paragraph(m))
        descr = str(s)
        self.assertEqual(expected, descr)

        expected = 'One\n\tfoo bar\n\tbaz bar'
        m2 = RhetRel('Contrast', 'baz', 'bar')
        s = Section('One', Paragraph(m), Paragraph(m2))
        descr = str(s)
        self.assertEqual(expected, descr)

    def test_repr(self):
        expected = """Section:
title: 'One'
Paragraph (1):
RhetRel (Elaboration): 'foo' 'bar'"""
        m = RhetRel('Elaboration', 'foo', 'bar')
        s = Section('One', Paragraph(m))
        descr = repr(s)
        self.assertEqual(expected, descr)

        expected = """Section:
title: 'One'
Paragraph (1):
RhetRel (Elaboration): 'foo' 'bar'
Paragraph (1):
RhetRel (Contrast): 'baz' 'bar'"""
        m2 = RhetRel('Contrast', 'baz', 'bar')
        s = Section('One', Paragraph(m), Paragraph(m2))
        descr = repr(s)
        self.assertEqual(expected, descr)


class TestDocument(unittest.TestCase):
    def test_str(self):
        expected = 'MyDoc\nOne\n\tfoo bar'
        m = RhetRel('Elaboration', 'foo', 'bar')
        one = Section('One', Paragraph(m))
        d = Document('MyDoc', one)
        descr = str(d)
        self.assertEqual(expected, descr)

        expected = 'MyDoc\nOne\n\tfoo bar\n\nTwo\n\tbaz bar'
        m2 = RhetRel('Contrast', 'baz', 'bar')
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
RhetRel (Elaboration): 'foo' 'bar'"""
        m = RhetRel('Elaboration', 'foo', 'bar')
        one = Section('One', Paragraph(m))
        d = Document('MyDoc', one)
        descr = repr(d)
        self.assertEqual(expected, descr)

        expected = """Document:
title: 'MyDoc'
Section:
title: 'One'
Paragraph (1):
RhetRel (Elaboration): 'foo' 'bar'

Section:
title: 'Two'
Paragraph (1):
RhetRel (Contrast): 'baz' 'bar'"""
        m2 = RhetRel('Contrast', 'baz', 'bar')
        two = Section('Two', Paragraph(m2))
        d = Document('MyDoc', one, two)
        descr = repr(d)
        self.assertEqual(expected, descr)


if __name__ == '__main__':
    unittest.main()
