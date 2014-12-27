import unittest

from nlg.microplanning import *
from nlg.lexicon import *

class TestStringRealisation(unittest.TestCase):

    def test_string(self):
        v = RealisationVisitor()
        s = String('hello')
        expected = 'hello'
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_word(self):
        v = RealisationVisitor()
        s = Word('house', 'NOUN')
        expected = 'house'
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

        v = RealisationVisitor()
        s = Word('house', 'NOUN', {'NUMBER': 'PLURAL'})
        expected = 'houses'
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_placeholder(self):
        v = RealisationVisitor()
        s = PlaceHolder(0, 'truck1')
        expected = 'truck1'
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_coordination(self):
        w1 = Word('truck', 'NOUN')
        w2 = Word('car', 'NOUN')
        w3 = Word('motorbike', 'NOUN')

        v = RealisationVisitor()
        expected = ''
        s = Coordination()
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

        v = RealisationVisitor()
        expected = 'truck'
        s = Coordination(w1)
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

        v = RealisationVisitor()
        expected = 'truck and car'
        s = Coordination(w1, w2)
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)
        
        v = RealisationVisitor()
        expected = 'truck, car and motorbike'
        s = Coordination(w1, w2, w3)
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_clause(self):
        v = RealisationVisitor()
        c = Clause(Word('Peter', 'NOUN'),
                   Word('run', 'VERB'))
        expected = 'Peter run'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

        v = RealisationVisitor()
        c = Clause(Word('Peter', 'NOUN'),
                   Word('run', 'VERB'),
                   pre_modifiers=[String('yesterday')])
        expected = 'yesterday Peter run'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)
        
        v = RealisationVisitor()
        c = Clause(Word('Peter', 'NOUN'),
                   Word('run', 'VERB'),
                   pre_modifiers=[String('yesterday')],
                   post_modifiers=[String('abundantly')])
        expected = 'yesterday Peter run abundantly'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)
        
        v = RealisationVisitor()
        c = Clause(Word('Peter', 'NOUN'),
                   Word('run', 'VERB'),
                   pre_modifiers=['yesterday'],
                   post_modifiers=['abundantly'])
        expected = 'yesterday Peter run abundantly'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_np(self):
        v = RealisationVisitor()
        c = NP(Word('house', 'NOUN'),
               Word('this', 'DETERMINER'))
        expected = 'this house'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)
        
        v = RealisationVisitor()
        c = NP(Word('house', 'NOUN'),
               Word('this', 'DETERMINER'),
               pre_modifiers=['tall', 'yellow'],
               post_modifiers=['that we lived in'])
        expected = 'this tall yellow house that we lived in'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_vp(self):
        v = RealisationVisitor()
        c = VP(Word('hit', 'VERB'),
               String('the ball'),
               String('with the bat'))
        expected = 'hit the ball with the bat'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)
        
        v = RealisationVisitor()
        c = VP(Word('hit', 'VERB'),
               NP(Word('ball', 'NOUN'), 'the'),
               String('with the bat'))
        expected = 'hit the ball with the bat'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_pp(self):
        v = RealisationVisitor()
        c = PP(Word('in', 'PREPOSITION'),
               String('the house'))
        expected = 'in the house'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)
        
        v = RealisationVisitor()
        c = PP(Word('in', 'PREPOSITION'),
               NP(Word('house', 'NOUN'), Word('the', 'DETERMINER')))
        expected = 'in the house'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_adjp(self):
        v = RealisationVisitor()
        c = AdjP(Word('green', 'ADJECTIVE'))
        expected = 'green'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_advp(self):
        v = RealisationVisitor()
        c = AdvP(Word('rarely', 'ADVERB'))
        expected = 'rarely'
        c.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_complex(self):
        house = NP('house', 'the')
        shopping = NP('shopping', 'the')
        put = VP('put', shopping, PP('in', house))
        s = Clause(NP('Peter'), put)
        expected = 'Peter put the shopping in the house'
        v = RealisationVisitor()
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)


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

    def test_placeholder(self):
        v = XmlVisitor()
        s = PlaceHolder(0, 'truck')
        expected = ('<child xsi:type="StringElement">\n'
                    '  <val>0</val>\n'
                    '</child>\n')
        s.accept(v)
        actual = v.xml
        self.assertEqual(expected, actual)

    def test_np(self):
        v = XmlVisitor()
        s = NP(noun('truck'), determiner('the'))
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
        s = VP(verb('drive'), noun('truck'))
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
        s = PP(preposition('in'), NP(noun('office'), determiner('the')))
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
        s = AdjP(adjective('large'), noun('office'))
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
        s = AdvP(adverb('quickly'), VP(verb('run')))
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
        s = Clause(NP(noun('Arthur')), VP(verb('smiled'),
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
        s = Coordination(noun('truck'), noun('car'), noun('train'), conj='and')
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
        s = Clause(NP(noun('Arthur')), VP(verb('smiled'),
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
        s = Clause(NP(noun('Arthur')), VP(verb('smiled'),
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
        s = noun('truck')
        expected = "Word('truck', 'NOUN')"
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)
        
        v = ReprVisitor()
        s = noun('truck')
        s.add_feature('NUMBER', 'PLURAL')
        expected = "Word('truck', 'NOUN', {'NUMBER': 'PLURAL'})"
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_placeholder(self):
        v = ReprVisitor()
        s = PlaceHolder(0, 'truck')
        expected = "PlaceHolder(0, String('truck'))"
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)

    def test_clause(self):
        v = ReprVisitor()
        s = Clause(NP(noun('Python')), VP(verb('rocks')))
        expected = ("Clause(NP(Word('Python', 'NOUN')),\n"
                    "       VP(Word('rocks', 'VERB')))")
        s.accept(v)
        actual = str(v)
        self.assertEqual(expected, actual)
        self.assertEqual(s, eval(actual))
        
        v = ReprVisitor()
        s = Clause(NP(noun('Python')), VP(verb('rocks')))
        s.pre_modifiers.append(adverb('today'))
        s.add_feature('foo', 'bar')
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
        s = VP(verb('put'), np('the', 'bat'), PP('on', np('the', 'mat')))
        expected = ("VP(Word('put', 'VERB'),\n"
                    "   NP(Word('bat', 'NOUN'), Word('the', 'DETERMINER')),\n"
                    "   PP(String('on'),\n"
                    "      NP(Word('mat', 'NOUN'), Word('the', 'DETERMINER'))))")
        s.accept(v)
        actual = str(v)
        self.assertEqual(s, eval(actual))
        self.assertEqual(expected, actual)

    def test_np(self):
        v = ReprVisitor()
        s = np('the', 'war')
        expected = ("NP(Word('war', 'NOUN'), Word('the', 'DETERMINER'))")
        s.accept(v)
        actual = str(v)
        self.assertEqual(s, eval(actual))
        self.assertEqual(expected, actual)
        
        v = ReprVisitor()
        s = np('the', 'war')
        s.post_modifiers.append(PP('of',
                                   np('the', 'worlds',
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
        s = PP('on', np('the', 'mat'))
        expected = ("PP(String('on'),\n"
                    "   NP(Word('mat', 'NOUN'), Word('the', 'DETERMINER')))")
        s.accept(v)
        actual = str(v)
        self.assertEqual(s, eval(actual))
        self.assertEqual(expected, actual)
        
    def test_coordination(self):
        v = ReprVisitor()
        s = Coordination(noun('truck'), noun('bike'))
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
        s = nnp('Arthur Dent')
        expected = [s]
        s.accept(v)
        actual = v.elements
        self.assertEqual(expected, actual)
    
    def test_placeholder(self):
        v = ElementVisitor()
        s = PlaceHolder(0, 'Arthur Dent')
        expected = [s]
        s.accept(v)
        actual = v.elements
        self.assertEqual(expected, actual)

    def test_np(self):
        v = ElementVisitor()
        s = np('the', 'life')
        expected = [Word('the', 'DETERMINER'), Word('life', 'NOUN')]
        s.accept(v)
        actual = v.elements
        self.assertEqual(expected, actual)

    def test_vp(self):
        v = ElementVisitor()
        s = VP(verb('run'), PP(preposition('for'), np('your', 'life')))
        expected = [Word('run', 'VERB'),
                    Word('for', 'PREPOSITION'),
                    Word('your', 'DETERMINER'),
                    Word('life', 'NOUN')]
        s.accept(v)
        actual = v.elements
        self.assertEqual(expected, actual)

    def test_pp(self):
        v = ElementVisitor()
        s = PP(preposition('for'), np('your', 'life'))
        expected = [Word('for', 'PREPOSITION'),
                    Word('your', 'DETERMINER'),
                    Word('life', 'NOUN')]
        s.accept(v)
        actual = v.elements
        self.assertEqual(expected, actual)

    def test_adjp(self):
        v = ElementVisitor()
        s = AdjP(adjective('happy'), noun('life'))
        expected = [Word('happy', 'ADJECTIVE'),
                    Word('life', 'NOUN')]
        s.accept(v)
        actual = v.elements
        self.assertEqual(expected, actual)
    
    def test_advp(self):
        v = ElementVisitor()
        s = AdjP(adverb('gently'), verb('run'))
        expected = [Word('gently', 'ADVERB'),
                    Word('run', 'VERB')]
        s.accept(v)
        actual = v.elements
        self.assertEqual(expected, actual)

    def test_coordination(self):
        v = ElementVisitor()
        s = AdjP(adverb('gently'), verb('run'))
        expected = [Word('gently', 'ADVERB'),
                    Word('run', 'VERB')]
        s.accept(v)
        actual = v.elements
        self.assertEqual(expected, actual)






















if __name__ == '__main__':
    unittest.main()
