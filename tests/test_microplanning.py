import unittest

from nlglib.microplanning import *
from nlglib.lexicon import *


class TestXmlFormatting(unittest.TestCase):

    def test_string(self):
        v = XmlVisitor()
        s = String('hello')
        expected = ('<child xsi:type="StringElement">\n'
                    '  <val>hello</val>\n'
                    '</child>\n')
        s.accept(v)
        actual = v.xml
        self.assertEqual(expected, actual)

    def test_word(self):
        v = XmlVisitor()
        s = Word('house', 'NOUN')
        expected = ('<child xsi:type="WordElement" cat="NOUN">\n'
                    '  <base>house</base>\n'
                    '</child>\n')
        s.accept(v)
        actual = v.xml
        self.assertEqual(expected, actual)

    def test_var(self):
        v = XmlVisitor()
        s = Var(0, 'truck')
        expected = ('<child xsi:type="StringElement">\n'
                    '  <val>0</val>\n'
                    '</child>\n')
        s.accept(v)
        actual = v.xml
        self.assertEqual(expected, actual)

    def test_NP(self):
        v = XmlVisitor()
        s = NP(Noun('truck'), Determiner('the'))
        expected = """\
<child xsi:type="NPPhraseSpec">
  <spec xsi:type="WordElement" cat="DETERMINER">
    <base>the</base>
  </spec>
  <head xsi:type="WordElement" cat="NOUN">
    <base>truck</base>
  </head>
</child>
"""
        s.accept(v)
        actual = v.xml
        self.assertEqual(expected, actual)

    def test_vp(self):
        v = XmlVisitor()
        s = VP(Verb('drive'), Noun('truck'))
        expected = """\
<child xsi:type="VPPhraseSpec">
  <head xsi:type="WordElement" cat="VERB">
    <base>drive</base>
  </head>
  <compl xsi:type="WordElement" cat="NOUN">
    <base>truck</base>
  </compl>
</child>
"""
        s.accept(v)
        actual = v.xml
        self.assertEqual(expected, actual)

    def test_pp(self):
        v = XmlVisitor()
        s = PP(Preposition('in'), NP(Noun('office'), Determiner('the')))
        expected = """\
<child xsi:type="PPPhraseSpec">
  <head xsi:type="WordElement" cat="PREPOSITION">
    <base>in</base>
  </head>
  <compl xsi:type="NPPhraseSpec">
    <spec xsi:type="WordElement" cat="DETERMINER">
      <base>the</base>
    </spec>
    <head xsi:type="WordElement" cat="NOUN">
      <base>office</base>
    </head>
  </compl>
</child>
"""
        s.accept(v)
        actual = v.xml
        self.assertEqual(expected, actual)
    
    def test_adjp(self):
        v = XmlVisitor()
        s = AdjP(Adjective('large'), Noun('office'))
        expected = """\
<child xsi:type="AdjPhraseSpec">
  <head xsi:type="WordElement" cat="ADJECTIVE">
    <base>large</base>
  </head>
  <compl xsi:type="WordElement" cat="NOUN">
    <base>office</base>
  </compl>
</child>
"""
        s.accept(v)
        actual = v.xml
        self.assertEqual(expected, actual)
    
    def test_advp(self):
        v = XmlVisitor()
        s = AdvP(Adverb('quickly'), VP(Verb('run')))
        expected = """\
<child xsi:type="AdvPhraseSpec">
  <head xsi:type="WordElement" cat="ADVERB">
    <base>quickly</base>
  </head>
  <compl xsi:type="VPPhraseSpec">
    <head xsi:type="WordElement" cat="VERB">
      <base>run</base>
    </head>
  </compl>
</child>
"""
        s.accept(v)
        actual = v.xml
        self.assertEqual(expected, actual)

    def test_clause(self):
        v = XmlVisitor()
        s = Clause(NP(Noun('Arthur')), VP(Verb('smiled'),
                   features={'TENSE': 'PAST'}))
        expected = """\
<child xsi:type="SPhraseSpec">
  <subj xsi:type="NPPhraseSpec">
    <head xsi:type="WordElement" cat="NOUN">
      <base>Arthur</base>
    </head>
  </subj>
  <vp xsi:type="VPPhraseSpec" TENSE="PAST">
    <head xsi:type="WordElement" cat="VERB">
      <base>smiled</base>
    </head>
  </vp>
</child>
"""
        s.accept(v)
        actual = v.xml
        self.assertEqual(expected, actual)

    def test_coordination(self):
        v = XmlVisitor()
        s = Coordination(Noun('truck'), Noun('car'), Noun('train'), conj='and')
        expected = """\
<child xsi:type="CoordinatedPhraseElement" conj="and">
  <coord xsi:type="WordElement" cat="NOUN">
    <base>truck</base>
  </coord>
  <coord xsi:type="WordElement" cat="NOUN">
    <base>car</base>
  </coord>
  <coord xsi:type="WordElement" cat="NOUN">
    <base>train</base>
  </coord>
</child>
"""
        s.accept(v)
        actual = v.xml
        self.assertEqual(expected, actual)

    def test_format(self):
        v = XmlVisitor(depth=1, indent='    ')
        s = Clause(NP(Noun('Arthur')), VP(Verb('smiled'),
                   features={'TENSE': 'PAST'}))
        expected = """\
    <child xsi:type="SPhraseSpec">
        <subj xsi:type="NPPhraseSpec">
            <head xsi:type="WordElement" cat="NOUN">
                <base>Arthur</base>
            </head>
        </subj>
        <vp xsi:type="VPPhraseSpec" TENSE="PAST">
            <head xsi:type="WordElement" cat="VERB">
                <base>smiled</base>
            </head>
        </vp>
    </child>
"""
        s.accept(v)
        actual = v.xml
        self.assertEqual(expected, actual)
        
        v = XmlVisitor(indent='', sep='')
        s = Clause(NP(Noun('Arthur')), VP(Verb('smiled'),
                   features={'TENSE': 'PAST'}))
        expected = ('<child xsi:type="SPhraseSpec">'
                    '<subj xsi:type="NPPhraseSpec">'
                    '<head xsi:type="WordElement" cat="NOUN">'
                    '<base>Arthur</base>'
                    '</head>'
                    '</subj>'
                    '<vp xsi:type="VPPhraseSpec" TENSE="PAST">'
                    '<head xsi:type="WordElement" cat="VERB">'
                    '<base>smiled</base>'
                    '</head>'
                    '</vp>'
                    '</child>')
        s.accept(v)
        actual = v.xml
        self.assertEqual(expected, actual)


class TestRepresentation(unittest.TestCase):

    def test_string(self):
        v = ReprVisitor()
        s = String('hello')
        expected = "String('hello')"
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)
        
    def test_word(self):
        v = ReprVisitor()
        s = Noun('truck')
        expected = "Word('truck', 'NOUN')"
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)
        
        v = ReprVisitor()
        s = Noun('truck')
        s.set_feature('NUMBER', 'PLURAL')
        expected = "Word('truck', 'NOUN', {'NUMBER': 'PLURAL'})"
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_var(self):
        v = ReprVisitor()
        s = Var(0, 'truck')
        expected = "Var(0, String('truck'))"
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_clause(self):
        v = ReprVisitor()
        s = Clause(NP(Noun('Python')), VP(Verb('rocks')))
        expected = ("Clause(NP(Word('Python', 'NOUN')),\n"
                    "       VP(Word('rocks', 'VERB')))")
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)
        self.assertEqual(s, eval(actual))
        
        v = ReprVisitor()
        s = Clause(NP(Noun('Python')), VP(Verb('rocks')))
        s.pre_modifiers.append(Adverb('today'))
        s.set_feature('foo', 'bar')
        expected = ("Clause(NP(Word('Python', 'NOUN')),\n"
                    "       VP(Word('rocks', 'VERB')),\n"
                    "       {'foo': 'bar'},\n"
                    "       pre_modifiers=[Word('today', 'ADVERB')])")
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)
        self.assertEqual(s, eval(actual))
        
    def test_vp(self):
        v = ReprVisitor()
        s = VP(Verb('put'), NP('the', 'bat'), PP('on', NP('the', 'mat')))
        expected = ("VP(Word('put', 'VERB'),\n"
                    "   NP(Word('bat', 'NOUN'), Word('the', 'DETERMINER')),\n"
                    "   PP(String('on'),\n"
                    "      NP(Word('mat', 'NOUN'), Word('the', 'DETERMINER'))))")
        s.accept(v)
        actual = str(v)
        self.assertEqual(s, eval(actual))
        self.assertEqual(expected, actual)

    def test_NP(self):
        v = ReprVisitor()
        s = NP('the', 'war')
        expected = ("NP(Word('war', 'NOUN'), Word('the', 'DETERMINER'))")
        s.accept(v)
        actual = str(v)
        self.assertEqual(s, eval(actual))
        self.assertEqual(expected, actual)
        
        v = ReprVisitor()
        s = NP('the', 'war')
        s.post_modifiers.append(PP('of',
                                   NP('the', 'worlds',
                                      features={'NUMBER': 'PLURAL'})))
        expected = ("NP(Word('war', 'NOUN'), Word('the', 'DETERMINER'),\n"
                    "   post_modifiers=[PP(String('of'),\n"
                    "                      NP(Word('worlds', 'NOUN'), "\
                    "Word('the', 'DETERMINER'), "\
                    "features={'NUMBER': 'PLURAL'}))])")
        s.accept(v)
        actual = str(v)
        self.assertEqual(s, eval(actual))
        self.assertEqual(expected, actual)

    def test_pp(self):
        v = ReprVisitor()
        s = PP('on', NP('the', 'mat'))
        expected = ("PP(String('on'),\n"
                    "   NP(Word('mat', 'NOUN'), Word('the', 'DETERMINER')))")
        s.accept(v)
        actual = str(v)
        self.assertEqual(s, eval(actual))
        self.assertEqual(expected, actual)
        
    def test_coordination(self):
        v = ReprVisitor()
        s = Coordination(Noun('truck'), Noun('bike'))
        expected = ("Coordination(Word('truck', 'NOUN'),\n"
                    "             Word('bike', 'NOUN'),\n"
                    "             conj='and',\n"
                    "             features={'conj': 'and'})")
        s.accept(v)
        actual = str(v)
        self.assertEqual(s, eval(actual))
        self.assertEqual(expected, actual)


class TestElementVisitor(unittest.TestCase):

    def test_string(self):
        v = ElementVisitor()
        s = String('hello')
        expected = [s]
        s.accept(v)
        actual = v.elements
        self.assertEqual(expected, actual)

    def test_word(self):
        v = ElementVisitor()
        s = NNP('Arthur Dent')
        expected = [s]
        s.accept(v)
        actual = v.elements
        self.assertEqual(expected, actual)
    
    def test_var(self):
        v = ElementVisitor()
        s = Var(0, 'Arthur Dent')
        expected = [s]
        s.accept(v)
        actual = v.elements
        self.assertEqual(expected, actual)

    def test_NP(self):
        v = ElementVisitor()
        s = NP('the', 'life')
        expected = [Word('the', 'DETERMINER'), Word('life', 'NOUN')]
        s.accept(v)
        actual = v.elements
        self.assertEqual(expected, actual)

    def test_vp(self):
        v = ElementVisitor()
        s = VP(Verb('run'), PP(Preposition('for'), NP('your', 'life')))
        expected = [Word('run', 'VERB'),
                    Word('for', 'PREPOSITION'),
                    Word('your', 'DETERMINER'),
                    Word('life', 'NOUN')]
        s.accept(v)
        actual = v.elements
        self.assertEqual(expected, actual)

    def test_pp(self):
        v = ElementVisitor()
        s = PP(Preposition('for'), NP('your', 'life'))
        expected = [Word('for', 'PREPOSITION'),
                    Word('your', 'DETERMINER'),
                    Word('life', 'NOUN')]
        s.accept(v)
        actual = v.elements
        self.assertEqual(expected, actual)

    def test_adjp(self):
        v = ElementVisitor()
        s = AdjP(Adjective('happy'), Noun('life'))
        expected = [Word('happy', 'ADJECTIVE'),
                    Word('life', 'NOUN')]
        s.accept(v)
        actual = v.elements
        self.assertEqual(expected, actual)
    
    def test_advp(self):
        v = ElementVisitor()
        s = AdvP(Adverb('gently'), Verb('run'))
        expected = [Word('gently', 'ADVERB'),
                    Word('run', 'VERB')]
        s.accept(v)
        actual = v.elements
        self.assertEqual(expected, actual)

    def test_coordination(self):
        v = ElementVisitor()
        s = AdvP(Adverb('gently'), Verb('run'))
        expected = [Word('gently', 'ADVERB'),
                    Word('run', 'VERB')]
        s.accept(v)
        actual = v.elements
        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
