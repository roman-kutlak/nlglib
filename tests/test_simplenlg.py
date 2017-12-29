import logging
import unittest

from nlglib.microplanning import Clause, CC, PP
import realisation.simplenlg.client as snlg


class TestSimplenlgClient(unittest.TestCase):

    simplenlg_server = None
    client = None

    @classmethod
    def setUpClass(cls):
        jp = '../simplenlg/build/jar/simplenlg.jar'
        port = '50007'
        cls.test_result = 'Put the piano and the drum into the truck.'
        cls.simplenlg_server = snlg.SimpleNLGServer(jp, port)
        cls.simplenlg_server.start()
        cls.simplenlg_server.wait_for_init()
        cls.client = snlg.SimplenlgClient('localhost', port)

    @classmethod
    def tearDownClass(cls):
        # signal that we would like to shut the server down
        if cls.simplenlg_server:
            cls.simplenlg_server.shutdown()

    def test_socket(self):
        self.assertIsNotNone(self.simplenlg_server)
        self.simplenlg_server.wait_for_init()
        mysocket = snlg.Socket('', 50007)
        with mysocket as sock:
            n = sock.send_string(test_data)
            self.assertEqual(n, len(test_data))
            msg = sock.recv_string()
            self.assertEqual(self.test_result, msg)

        with mysocket as sock:
            n = sock.send_string(test_data)
            self.assertEqual(n, len(test_data))
            msg = sock.recv_string()
            self.assertEqual(self.test_result, msg)

    def test_snlg_1(self):
        expected = self.test_result
        realisation = self.client.xml_request(test_data)
        self.assertEqual(expected, realisation)

    def test_snlg_2(self):
        expected = 'Is indicated by transfusion of whole blood.'
        realisation = self.client.xml_request(test_data2)
        self.assertEqual(expected, realisation)

    def test_snlg_3(self):
        expected = 'Roman is not in the office.'
        realisation = self.client.xml_request(test_data3)
        self.assertEqual(expected, realisation)

    def test_snlg_4(self):
        expected = 'Roman is not at work.'
        realisation = self.client.xml_request(test_data4)
        self.assertEqual(expected, realisation)

    def test_snlg_5(self):
        expected = 'If p then q.'
        realisation = self.client.xml_request(test_data5)
        self.assertEqual(expected, realisation)

    def test_snlg_6(self):
        expected = 'There exists X such that p.'
        realisation = self.client.xml_request(test_data6)
        print(realisation)
        self.assertEqual(expected, realisation)

    def test_snlg_7(self):
        # FIXME: simplenlg realiser seems to have problem with coordinated elements
        #   - missing upper CASE and period
        expected = 'if x equals y and p is at location x then p is not at location y'
        realisation = self.client.xml_request(test_data7)
        self.assertEqual(expected, realisation)

    def test_complex_sentence(self):
        c1 = Clause('x', 'equal', 'y', front_modifiers=['if'])
        c2 = Clause('p', 'be', PP('at', 'location x'),
                    features={'COMPLEMENTISER': 'and'})
        c3 = Clause('p', 'be', PP('at', 'location y'),
                    features={'NEGATED': 'true', 'COMPLEMENTISER': 'then'})
        c2.complements.append(c3)
        c1.complements.append(c2)
        expected = 'If x equals y and p is at location x then p is not at location y.'
        actual = self.client.xml_request(c1.to_xml(headers=True))
        self.assertEqual(expected, actual)

    def test_coordination(self):
        c1 = Clause('x', 'equal', 'y', front_modifiers=['if'])
        c2 = Clause('p', 'be', PP('at', 'location x'))
        c3 = Clause('p', 'be', PP('at', 'location y'),
                    features={'NEGATED': 'true', 'COMPLEMENTISER': 'then'})
        c2.complements.append(c3)
        c = CC(c1, c2)
        expected = 'if x equals y and p is at location x then p is not at location y'
        actual = self.client.xml_request(c.to_xml(headers=True))
        self.assertEqual(expected, actual)


test_data = """\
<?xml version="1.0" encoding="utf-8"?>
<nlg:NLGSpec xmlns="http://simplenlg.googlecode.com/svn/trunk/res/xml"
  xmlns:nlg="http://simplenlg.googlecode.com/svn/trunk/res/xml"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://simplenlg.googlecode.com/svn/trunk/res/xml ">
  <nlg:Request>

    <Document cat="PARAGRAPH">
      <child xsi:type="SPhraseSpec" FORM="IMPERATIVE" >
        <vp xsi:type="VPPhraseSpec" >
          <head xsi:type="WordElement" cat="VERB">
            <base>put</base>
          </head>
          <compl xsi:type="CoordinatedPhraseElement" conj="and" discourseFunction="OBJECT" >
            <coord xsi:type="NPPhraseSpec" >
              <spec xsi:type="WordElement" cat="DETERMINER">
                <base>the</base>
              </spec>
              <head xsi:type="WordElement" cat="NOUN">
                <base>piano</base>
              </head>

            </coord>
            <coord xsi:type="NPPhraseSpec" >
              <spec xsi:type="WordElement" cat="DETERMINER">
                <base>the</base>
              </spec>
              <head xsi:type="WordElement" cat="NOUN">
                <base>drum</base>
              </head>

            </coord>

          </compl>
          <compl xsi:type="PPPhraseSpec" >
            <head xsi:type="WordElement" cat="PREPOSITION">
              <base>into</base>
            </head>
            <compl xsi:type="NPPhraseSpec" >
              <spec xsi:type="WordElement" cat="DETERMINER">
                <base>the</base>
              </spec>
              <head xsi:type="WordElement" cat="NOUN">
                <base>truck</base>
              </head>

            </compl>

          </compl>

        </vp>

      </child>

    </Document>
  </nlg:Request>
</nlg:NLGSpec>
    """

test_data2 = """\
<?xml version="1.0" encoding="utf-8"?>
<nlg:NLGSpec xmlns="http://simplenlg.googlecode.com/svn/trunk/res/xml"
xmlns:nlg="http://simplenlg.googlecode.com/svn/trunk/res/xml"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://simplenlg.googlecode.com/svn/trunk/res/xml ">
<nlg:Request>
<Document cat="PARAGRAPH">
<child xsi:type="SPhraseSpec">
    <subj xsi:type="NPPhraseSpec">
        <head xsi:type="WordElement" cat="NOUN">
            <base>transfusion of whole blood</base>
        </head>
    </subj>
    <vp xsi:type="VPPhraseSpec" PASSIVE="true" TENSE="PRESENT">
      <head cat="VERB">
        <base>indicate</base>
    </head>
    </vp>
</child>
</Document>
</nlg:Request>
</nlg:NLGSpec>
"""

test_data3 = """\
<?xml version="1.0" encoding="utf-8"?>
<nlg:NLGSpec xmlns="http://simplenlg.googlecode.com/svn/trunk/res/xml"
xmlns:nlg="http://simplenlg.googlecode.com/svn/trunk/res/xml"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://simplenlg.googlecode.com/svn/trunk/res/xml ">
<nlg:Request>
<Document cat="PARAGRAPH">
<child xsi:type="SPhraseSpec">
    <subj xsi:type="NPPhraseSpec">
        <head xsi:type="WordElement" cat="NOUN">
            <base>Roman</base>
        </head>
    </subj>
    <vp xsi:type="VPPhraseSpec" NEGATED="true">
        <head cat="VERB">
            <base>be</base>
        </head>
        <compl xsi:type="PPPhraseSpec" >
            <head xsi:type="WordElement" cat="PREPOSITION">
                <base>in</base>
            </head>
            <compl xsi:type="NPPhraseSpec" >
                <spec xsi:type="WordElement" cat="DETERMINER">
                    <base>the</base>
                </spec>
                <head xsi:type="WordElement" cat="NOUN">
                    <base>office</base>
                </head>
            </compl>
        </compl>
    </vp>
</child>
</Document>
</nlg:Request>
</nlg:NLGSpec>
"""

test_data4 = """\
<?xml version="1.0" encoding="utf-8"?>
<nlg:NLGSpec xmlns="http://simplenlg.googlecode.com/svn/trunk/res/xml"
xmlns:nlg="http://simplenlg.googlecode.com/svn/trunk/res/xml"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://simplenlg.googlecode.com/svn/trunk/res/xml ">
<nlg:Request>

<Document cat="PARAGRAPH">
<child xsi:type="SPhraseSpec" NEGATED="true">
  <subj xsi:type="WordElement" canned="true">
    <base>Roman</base>
  </subj>
  <vp xsi:type="VPPhraseSpec">
    <head xsi:type="WordElement" cat="VERB">
      <base>be</base>
    </head>
    <compl xsi:type="PPPhraseSpec">
      <head xsi:type="WordElement" cat="PREPOSITION">
        <base>at</base>
      </head>
      <compl xsi:type="WordElement" canned="true">
        <base>work</base>
      </compl>
    </compl>
  </vp>
</child>

</Document>
</nlg:Request>
</nlg:NLGSpec>
"""

test_data5 = """\
<?xml version="1.0" encoding="utf-8"?>
<nlg:NLGSpec xmlns="http://simplenlg.googlecode.com/svn/trunk/res/xml"
xmlns:nlg="http://simplenlg.googlecode.com/svn/trunk/res/xml"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://simplenlg.googlecode.com/svn/trunk/res/xml ">
<nlg:Request>

<Document cat="PARAGRAPH">
<child xsi:type="SPhraseSpec">
  <frontMod xsi:type="WordElement" canned="true">
    <base>if</base>
  </frontMod>
  <subj xsi:type="WordElement" canned="true">
    <base>p</base>
  </subj>
  <vp xsi:type="VPPhraseSpec">
    <head xsi:type="WordElement" cat="ADVERB">
      <base>then</base>
    </head>
    <compl xsi:type="WordElement" canned="true">
      <base>q</base>
    </compl>
  </vp>
</child>

</Document>
</nlg:Request>
</nlg:NLGSpec>
"""

test_data6 = """\
<?xml version="1.0" encoding="utf-8"?>
<nlg:NLGSpec xmlns="http://simplenlg.googlecode.com/svn/trunk/res/xml"
xmlns:nlg="http://simplenlg.googlecode.com/svn/trunk/res/xml"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://simplenlg.googlecode.com/svn/trunk/res/xml ">
<nlg:Request>
<Document cat="PARAGRAPH">
<child xsi:type="SPhraseSpec" PERSON="THIRD">
  <subj xsi:type="NPPhraseSpec">
    <head xsi:type="WordElement" canned="true" >
      <base>there</base>
    </head>
  </subj>
  <vp xsi:type="VPPhraseSpec">
    <head xsi:type="WordElement" canned="true" >
      <base>exist</base>
    </head>
    <compl xsi:type="WordElement" canned="true" >
      <base>X</base>
    </compl>
  </vp>
  <compl xsi:type="SPhraseSpec" COMPLEMENTISER="such+that">
    <subj xsi:type="NPPhraseSpec">
      <head xsi:type="WordElement" canned="true" >
        <base>p</base>
      </head>
    </subj>
  </compl>
</child>
</Document>
</nlg:Request>
</nlg:NLGSpec>
"""

test_data7 = """\
<?xml version="1.0" encoding="utf-8"?>
<nlg:NLGSpec xmlns="http://simplenlg.googlecode.com/svn/trunk/res/xml"
xmlns:nlg="http://simplenlg.googlecode.com/svn/trunk/res/xml"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://simplenlg.googlecode.com/svn/trunk/res/xml ">
<nlg:Request>
<Document cat="PARAGRAPH">
<child xsi:type="CoordinatedPhraseElement" conj="and">
  <coord xsi:type="SPhraseSpec">
    <frontMod xsi:type="WordElement" canned="true" >
      <base>if</base>
    </frontMod>
    <subj xsi:type="NPPhraseSpec">
      <head xsi:type="WordElement" canned="true" >
        <base>x</base>
      </head>
    </subj>
    <vp xsi:type="VPPhraseSpec">
      <head xsi:type="WordElement" canned="true" >
        <base>equal</base>
      </head>
      <compl xsi:type="WordElement" canned="true" >
        <base>y</base>
      </compl>
    </vp>
  </coord>
  <coord xsi:type="SPhraseSpec">
    <subj xsi:type="NPPhraseSpec">
      <head xsi:type="WordElement" canned="true" >
        <base>p</base>
      </head>
    </subj>
    <vp xsi:type="VPPhraseSpec">
      <head xsi:type="WordElement" canned="true" >
        <base>be</base>
      </head>
      <compl xsi:type="PPPhraseSpec">
        <head xsi:type="WordElement" cat="PREPOSITION">
          <base>at</base>
        </head>
        <compl xsi:type="WordElement" canned="true" >
          <base>location+x</base>
        </compl>
      </compl>
    </vp>
    <compl xsi:type="SPhraseSpec" NEGATED="true" COMPLEMENTISER="then">
      <subj xsi:type="NPPhraseSpec">
        <head xsi:type="WordElement" canned="true" >
          <base>p</base>
        </head>
      </subj>
      <vp xsi:type="VPPhraseSpec">
        <head xsi:type="WordElement" canned="true" >
          <base>be</base>
        </head>
        <compl xsi:type="PPPhraseSpec">
          <head xsi:type="WordElement" cat="PREPOSITION">
            <base>at</base>
          </head>
          <compl xsi:type="WordElement" canned="true" >
            <base>location+y</base>
          </compl>
        </compl>
      </vp>
    </compl>
  </coord>
</child>
</Document>
</nlg:Request>
</nlg:NLGSpec>
"""


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()
