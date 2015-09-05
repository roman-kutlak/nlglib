import unittest
from copy import deepcopy


from nlg.structures import *
from nlg.aggregation import *
from nlg.realisation import simple_realisation


class TestAggregation(unittest.TestCase):
    
    def setUp(self):
        the = Word('the', 'DETERMINER')
        truck = Word("truck", "NOUN")
        the_truck = NounPhrase(head=truck, spec=the)
        into = Word("into", "PREPOSITION")
        pp = PrepositionalPhrase(head=into)
        pp.complements.append(the_truck)
        
        put = Word("put", "VERB")
        vp = VerbPhrase(head=put)
        
        piano = Word("piano", "NOUN")
        drum = Word("drum", "NOUN")
        vp.complements.append(pp)
        
        obj1 = NounPhrase(piano, the)
        obj1._features["discourseFunction"] = 'OBJECT'
        obj2 = NounPhrase(drum, the)
        obj2._features["discourseFunction"] = 'OBJECT'
        
        vp2 = deepcopy(vp)
        vp.complements.insert(0, obj1)
        vp2.complements.insert(0, obj2)
        
        self.c1 = Clause(vp=vp)
        self.c1._features['FORM'] = "IMPERATIVE"
        
        self.c2 = Clause(vp=vp2)
        self.c2._features['FORM'] = "IMPERATIVE"
        
        self.john = NounPhrase(Word('John'))
        self.a = Word('a', 'DETERNIMER')
        self.boy = NounPhrase(Word('boy', 'NOUN'), self.a)
        self.tall = AdjectivePhrase(Word('tall'))
    
    
    def tearDown(self):
        pass

    def test_aggr(self):
        """ Note that we miss out one of the 'the's during the aggregation."""
        re = simple_realisation
        self.assertEqual('put the piano into the truck', re(self.c1))
        self.assertEqual('put the drum into the truck', re(self.c2))
        c3 = try_to_aggregate(self.c1, self.c2)
        self.assertEqual('put the piano and drum into the truck', re(c3))
        c3 = try_to_aggregate(self.c1, self.c2)
        self.assertEqual('put the piano and drum into the truck', re(c3))

    def test_s_try_aggr(self):
        re = simple_realisation
        vp1 = VerbPhrase(Word('is'), self.boy)
        vp2 = VerbPhrase(Word('is'), self.tall)
        
        c1 = Clause(self.john, vp1)
        c2 = Clause(self.john, vp2)
        self.assertEqual('John is a boy', re(c1))
        self.assertEqual('John is tall', re(c2))
        
        c3 = try_to_aggregate(c1, c2)
        self.assertEqual('John is a boy and tall', re(c3))

        article = NounPhrase(Word('article'), Word('an'))
        vp = VerbPhrase(Word('wrote'), article)
        c1 = Clause(self.john, deepcopy(vp))
        c2 = Clause(NounPhrase(Word('Mary')), vp)
        self.assertEqual('John wrote an article', re(c1))
        self.assertEqual('Mary wrote an article', re(c2))
        c3 = try_to_aggregate(c1, c2)
        self.assertEqual('John and Mary wrote an article', re(c3))








# main
if __name__ == '__main__':
    unittest.main()
