import unittest
from copy import deepcopy


from nlg.structures import *
from nlg.aggregation import *

class TestAggregation(unittest.TestCase):
    
    def setUp(self):
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
        
        self.c1 = Clause(vp=vp)
        self.c1._features['FORM'] = "IMPERATIVE"
        
        self.c2 = Clause(vp=vp2)
        self.c2._features['FORM'] = "IMPERATIVE"
        
        self.john = NP(Word('John'))
        self.a = Word('a', 'DETERNIMER')
        self.boy = NP(Word('boy', 'NOUN'), self.a)
        self.tall = AdjP(Word('tall'))
    
    
    def tearDown(self):
        pass
    
#    def test_do_aggr(self):
#        self.assertEqual('put the piano into the truck', str(self.c1))
#        self.assertEqual('put the drum into the truck', str(self.c2))
#        c3 = do_aggr(self.c1, self.c2)
#        self.assertEqual('put the piano and the drum into the truck', str(c3))
#    
#    def test_s_aggr(self):
#        vp1 = VP(Word('is'), self.boy)
#        vp2 = VP(Word('is'), self.tall)
#        
#        c1 = Clause(self.john, vp1)
#        c2 = Clause(self.john, vp2)
#        self.assertEqual('John is a boy', str(c1))
#        self.assertEqual('John is tall', str(c2))
#        
#        c3 = s_aggr(c1, c2)
#        self.assertEqual('John is a boy and is tall', str(c3))
#    
#    def test_pdo_aggr(self):
#        article = NP(Word('article'), Word('an'))
#        vp = VP(Word('wrote'), article)
#        c1 = Clause(self.john, deepcopy(vp))
#        c2 = Clause(NP(Word('Mary')), vp)
#        self.assertEqual('John wrote an article', str(c1))
#        self.assertEqual('Mary wrote an article', str(c2))
#        c3 = pdo_aggr(c1, c2)
#        self.assertEqual('John and Mary wrote an article', str(c3))

    def test_aggr(self):
        """ Note that we miss out one of the 'the's during the aggregation."""
        self.assertEqual('put the piano into the truck', str(self.c1))
        self.assertEqual('put the drum into the truck', str(self.c2))
        c3 = try_to_aggregate(self.c1, self.c2)
        self.assertEqual('put the piano and drum into the truck', str(c3))
        c3 = try_to_aggregate(self.c1, self.c2)
        self.assertEqual('put the piano and drum into the truck', str(c3))

    def test_s_try_aggr(self):
        vp1 = VP(Word('is'), self.boy)
        vp2 = VP(Word('is'), self.tall)
        
        c1 = Clause(self.john, vp1)
        c2 = Clause(self.john, vp2)
        self.assertEqual('John is a boy', str(c1))
        self.assertEqual('John is tall', str(c2))
        
        c3 = try_to_aggregate(c1, c2)
        self.assertEqual('John is a boy and tall', str(c3))

        article = NP(Word('article'), Word('an'))
        vp = VP(Word('wrote'), article)
        c1 = Clause(self.john, deepcopy(vp))
        c2 = Clause(NP(Word('Mary')), vp)
        self.assertEqual('John wrote an article', str(c1))
        self.assertEqual('Mary wrote an article', str(c2))
        c3 = try_to_aggregate(c1, c2)
        self.assertEqual('John and Mary wrote an article', str(c3))


