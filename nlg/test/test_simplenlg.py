import unittest
import time
import sys

#from nlg.nlg import *
from nlg.structures import *
import nlg.simplenlg as snlg
#from planning.planner import Planner
from nlg.utils import get_user_settings


test_data = """<?xml version="1.0" encoding="utf-8"?>
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


test_data2="""<?xml version="1.0" encoding="utf-8"?>
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


test_data3="""<?xml version="1.0" encoding="utf-8"?>
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


# FIXME: not working
class TestSimplenlgClient(unittest.TestCase):

    @classmethod
    def setUpClass(obj):
        #print('Setting up class TestSimplenlgClient')
        obj.test_result = 'Put the piano and the drum into the truck.'
        obj.simplenlg_thread = snlg.SimpleNLGServer(snlg.simplenlg_path)
        obj.simplenlg_thread.start()

    @classmethod
    def tearDownClass(obj):
        #print('Tearing down class TestSimplenlgClient')
        # signal that we would like to shut the server down
        obj.simplenlg_thread.shutdown()
#        obj.simplenlg_thread.join()

    def test_socket(self):
        #print('calling test_socket()')
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

    def test_snlg(self):
        """ Preconditions: Settings.get_user_settings() can find the file with 
            user settings and the settings file contains entries for 
            SimplenlgHost and SimplenlgPort.
            
        """
        print('calling test_snlg()')
        s = get_user_settings()
        host = s.get_setting('SimplenlgHost')
        port = s.get_setting('SimplenlgPort')
        print((host, port))
        client = snlg.SimplenlgClient(host, port)
        realisation = client.xml_request(test_data)
        self.assertEqual(self.test_result, realisation)

        expected = 'Roman is not in the office.'
        realisation = client.xml_request(test_data3)
        self.assertEqual(expected, realisation)
