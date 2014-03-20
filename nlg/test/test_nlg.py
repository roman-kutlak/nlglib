import unittest
import time
import sys

from nlg.nlg import *
from nlg.structures import *
import nlg.simplenlg as snlg
#from planning.planner import Planner
from nlg.utils import get_user_settings

action_sequence = """Logistics-0,0.01,20,(load-truck obj13 tru1 pos1),(load-truck obj11 tru1 pos1),(load-truck obj21 tru2 pos2),(load-truck obj23 tru2 pos2),(drive-truck tru2 pos2 apt2 cit2),(unload-truck obj23 tru2 apt2),(unload-truck obj21 tru2 apt2),(load-airplane obj23 apn1 apt2),(load-airplane obj21 apn1 apt2),(drive-truck tru1 pos1 apt1 cit1),(unload-truck obj13 tru1 apt1),(unload-truck obj11 tru1 apt1),(fly-airplane apn1 apt2 apt1),(unload-airplane obj23 apn1 apt1),(unload-airplane obj21 apn1 apt1),(load-truck obj21 tru1 apt1),(load-truck obj23 tru1 apt1),(drive-truck tru1 apt1 pos1 cit1),(unload-truck obj23 tru1 pos1),(unload-truck obj21 tru1 pos1)
"""


v = XmlVisitor()
the = Word('the', 'DETERMINER')
truck = Word("truck", "NOUN")
the_truck = NP(head=truck, spec=the)
into = Word("into", "PREPOSITION")
pp = PP(head=into)
pp.complement.append(the_truck)

put = Word("put", "VERB")
vp = VP(head=put)

piano = Word("piano", "NOUN")
drum = Word("drum", "NOUN")
vp.complement.append(pp)

obj1 = NP(piano, the)
obj1._features["discourseFunction"] = 'OBJECT'
obj2 = NP(drum, the)
obj2._features["discourseFunction"] = 'OBJECT'

vp2 = deepcopy(vp)
vp.complement.insert(0, obj1)
vp2.complement.insert(0, obj2)

c1 = Clause(vp=vp)
c1._features['FORM'] = "IMPERATIVE"

c2 = Clause(vp=vp2)
c2._features['FORM'] = "IMPERATIVE"

john = NP(Word('John'))
a = Word('a', 'DETERNIMER')
boy = NP(Word('boy', 'NOUN'), a)
tall = AdjP(Word('tall'))

truck2 = Word("truck", "NOUN")
np2 = NP(head=truck2, spec=the)

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
        obj.simplenlg_thread.do_shutdown()
#        obj.simplenlg_thread.join()

#    def setUp(self):
#        time.sleep(2)

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
        #print('calling test_snlg()')
        s = get_user_settings()
        host = s.get_setting('SimplenlgHost')
        port = s.get_setting('SimplenlgPort')
        print((host, port))
        client = snlg.SimplenlgClient(host, port)
        realisation = client.xml_request(test_data)
        self.assertEqual(self.test_result, realisation)


#class TestGre(unittest.TestCase):
#    def setUp(self):
##        self.p = Planner()
#        self.dom = self.p.get_domain('logistics')
#        self.prob = self.p.get_problem('logistics', 'logistics-1.pddl')
#        self.context = Context(self.dom, self.prob)
#        self.reg = REG()
#
#    def test_reg(self):
#        res = self.reg.gre('tru1', self.context)
#        self.assertEqual('truck 1', str(res))
#        res = self.reg.gre('obj12', self.context)
#        self.assertEqual('a drum', str(res))
#
#
#class TestNlg(unittest.TestCase):
#    
#    def setUp(self):
#        self.p = Planner()
#        self.plan = self.p.plan_for_goal('Logistics-1')
#        self.nlg = Nlg()
#    
#    def tearDown(self):
#        pass
#    
#    def test_setup(self):
#        self.assertNotEqual(None, self.plan)
#        self.assertNotEqual(None, self.nlg)
#    
#    def test_lexicalise(self):
#        pass


# if the module is loaded on its own, run the test
if __name__ == '__main__':
    unittest.main()

