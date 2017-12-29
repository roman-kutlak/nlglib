import unittest

from nlglib.macroplanning import Document, RhetRel, MsgSpec, Paragraph


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
        self.assertEqual('MsgSpec(nice_name, {})', descr)

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
        <child xsi:type="WordElement" canned="true"  cat="ANY">
          <base>This+is+the+nucleus</base>
        </child>

      </nucleus>
      <satellite>
        <child xsi:type="WordElement" canned="true"  cat="ANY">
          <base>this+is+the+satellite</base>
        </child>
      </satellite>
  </RhetRel>
"""

    expected2 = """\
  <RhetRel name="elaboration">
    <marker>and</marker>
    <nuclei>
      <nucleus>
        <child xsi:type="WordElement" canned="true"  cat="ANY">
          <base>This+is+the+nucleus</base>
        </child>

      </nucleus>
      <satellite>
        <RhetRel name="concession">
          <marker>however</marker>
          <nuclei>
            <nucleus>
              <child xsi:type="WordElement" canned="true"  cat="ANY">
                <base>this+is+another+nucleus</base>
              </child>

            </nucleus>
            <satellite>
              <child xsi:type="WordElement" canned="true"  cat="ANY">
                <base>this+is+the+satellite</base>
              </child>
            </satellite>
        </RhetRel>
      </satellite>
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
        expected = "<RhetRel (Elaboration): String('foo') String('bar') String('baz')>"
        m = RhetRel('Elaboration', 'foo', 'bar', 'baz')
        descr = repr(m)
        self.assertEqual(expected, descr)

        expected = "<RhetRel (Contrast): <RhetRel (Elaboration): " \
                   "String('foo') String('bar') String('baz')> " \
                   "String('bar') String('baz')>"
        m2 = RhetRel('Contrast', m, 'bar', 'baz')
        descr = repr(m2)
        self.assertEqual(expected, descr)


class TestParagraph(unittest.TestCase):
    def test_str(self):
        expected = 'foo bar'
        m = RhetRel('Elaboration', 'foo', 'bar')
        p = Paragraph(m)
        descr = str(p)
        self.assertEqual(expected, descr)

        expected = 'foo bar bar baz'
        m2 = RhetRel('Contrast', m, 'bar', 'baz')
        p = Paragraph(m2)
        descr = str(p)
        self.assertEqual(expected, descr)

        expected = 'foo bar bar baz foobar'
        m3 = RhetRel('Leaf', 'foobar')
        p = Paragraph(m2, m3)
        descr = str(p)
        self.assertEqual(expected, descr)

    def test_repr(self):
        expected = "<Paragraph (1):\n\t" \
                   "<RhetRel (Elaboration): String('foo') String('bar')>>"
        m = RhetRel('Elaboration', 'foo', 'bar')
        p = Paragraph(m)
        descr = repr(p)
        self.assertEqual(expected, descr)

        expected = "<Paragraph (1):\n\t" \
                   "<RhetRel (Contrast): " \
                   "<RhetRel (Elaboration): String('foo') String('bar')> " \
                   "String('bar') String('baz')>>"
        m2 = RhetRel('Contrast', m, 'bar', 'baz')
        p = Paragraph(m2)
        descr = repr(p)
        self.assertEqual(expected, descr)

        expected = "<Paragraph (2):\n\t" \
                   "<RhetRel (Contrast): " \
                   "<RhetRel (Elaboration): String('foo') String('bar')> " \
                   "String('bar') String('baz')>" \
                   "\n\t<RhetRel (Leaf): String('foobar') String('')>>"
        m3 = RhetRel('Leaf', 'foobar')
        p = Paragraph(m2, m3)
        descr = repr(p)
        self.assertEqual(expected, descr)


class TestDocument(unittest.TestCase):
    def test_str(self):
        expected = "MyDoc\n\nOne\n\nfoo bar"
        m = RhetRel('Elaboration', 'foo', 'bar')
        one = Document('One', Paragraph(m))
        d = Document('MyDoc', one)
        descr = str(d)
        self.assertEqual(expected, descr)

        expected = "MyDoc\n\nOne\n\nfoo bar\n\nTwo\n\nbaz bar"
        m2 = RhetRel('Contrast', 'baz', 'bar')
        two = Document('Two', Paragraph(m2))
        d = Document('MyDoc', one, two)
        descr = str(d)
        self.assertEqual(expected, descr)

    def test_repr(self):
        expected = """\
<Document: (MyDoc)
<Document: (One)
String('foo bar')>>"""
        m = RhetRel('Elaboration', 'foo', 'bar')
        one = Document('One', Paragraph(m))
        d = Document('MyDoc', one)
        self.assertEqual(expected, repr(d))

        expected = """\
<Document: (MyDoc)
<Document: (One)
String('foo bar')>
<Document: (Two)
String('baz bar')>>"""
        m2 = RhetRel('Contrast', 'baz', 'bar')
        two = Document('Two', Paragraph(m2))
        d = Document('MyDoc', one, two)
        self.assertEqual(expected, repr(d))


if __name__ == '__main__':
    unittest.main()
