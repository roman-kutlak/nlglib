import unittest

from nlglib.macroplanning import expr, formula_to_rst, PredicateMsg, Document
from nlglib.microplanning import String


class TestPredicateMsg(unittest.TestCase):
    def test_simple_predicate(self):
        p = expr('Happy(john)')
        spec = formula_to_rst(p)
        self.assertEqual(PredicateMsg('Happy', 'john'), spec)


class TestDocument(unittest.TestCase):
    def setUp(self):
        self.doc = Document('Title',
                            Document('Section 1', 'para 1', 'para 2'),
                            Document('Section 2', 'para 3', 'para 4'))

    def test_init(self):
        self.assertTrue(isinstance(self.doc.title, String))
        self.assertTrue(isinstance(self.doc.sections[0].title, String))
        self.assertTrue(isinstance(self.doc.sections[1].title, String))

    def test_eq(self):
        d2 = Document('Title',
                      Document('Section 1', 'para 1', 'para 2'),
                      Document('Section 2', 'para 3', 'para 4'))
        self.assertEqual(self.doc, d2)
        self.assertEqual(hash(self.doc), hash(d2))

    def test_str(self):
        expected = ('Title\n\n'
                    'Section 1\n\npara 1\n\npara 2\n\n'
                    'Section 2\n\npara 3\n\npara 4')
        self.assertEqual(expected, str(self.doc))

    def test_repr(self):
        expected = """<Document: (Title)
<Document: (Section 1)
String('para 1')
String('para 2')>
<Document: (Section 2)
String('para 3')
String('para 4')>>"""
        self.assertEqual(expected, repr(self.doc))

    def test_elements(self):
        expected = [String('Title'),
                    Document('Section 1', 'para 1', 'para 2'),
                    Document('Section 2', 'para 3', 'para 4')]
        self.assertEqual(expected, list(self.doc.elements()))

    def test_to_xml(self):
        expected = '''\
<document>
  <title>
  <child xsi:type="WordElement" canned="true"  cat="ANY">
    <base>Title</base>
  </child>
  </title>
  <sections>
  <document>
    <title>
    <child xsi:type="WordElement" canned="true"  cat="ANY">
      <base>Section+1</base>
    </child>
    </title>
    <sections>
    <child xsi:type="WordElement" canned="true"  cat="ANY">
      <base>para+1</base>
    </child>
    <child xsi:type="WordElement" canned="true"  cat="ANY">
      <base>para+2</base>
    </child>
    </sections>
  </document>
  <document>
    <title>
    <child xsi:type="WordElement" canned="true"  cat="ANY">
      <base>Section+2</base>
    </child>
    </title>
    <sections>
    <child xsi:type="WordElement" canned="true"  cat="ANY">
      <base>para+3</base>
    </child>
    <child xsi:type="WordElement" canned="true"  cat="ANY">
      <base>para+4</base>
    </child>
    </sections>
  </document>
  </sections>
</document>
'''
        self.assertEqual(expected, self.doc.to_xml())


if __name__ == '__main__':
    unittest.main()
