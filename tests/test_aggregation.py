import unittest

from nlglib.microplanning import *
from nlglib.aggregation import SentenceAggregator


class TestAggregation(unittest.TestCase):
    aggregator = SentenceAggregator()

    def test_add_elements_1(self):
        res = self.aggregator.add_elements(
            NP('the', 'small', 'child'),
            NP('the', 'happy', 'child'),
        )
        expected = CC(
            NP('the', 'small', 'child'),
            NP('the', 'happy', 'child'),
            features={'NUMBER': 'plural'}
        )
        self.assertEqual(expected, res)

    def test_aggr(self):
        """ Note that we miss out one of the 'the's during the aggregation."""
        c1 = Clause(None, VP('put', NP('the', 'piano'), PP('into', NP('the', 'truck'))))
        c2 = Clause(None, VP('put', NP('the', 'drum'), PP('into', NP('the', 'truck'))))
        c3 = self.aggregator.try_to_aggregate(c1, c2)
        plural = {'NUMBER': 'plural'}
        expected = Clause(NounPhrase(Element()),
                          VP('put',
                             NP('the', CC(Noun('piano'),
                                          Noun('drum'),
                                          features=plural),
                                features=plural),
                             PP('into', NP('the', 'truck'))))
        self.assertEqual(expected, c3)

    def test_s_try_aggr(self):
        c1 = Clause(Male('John'), VP('is', NP('a', 'boy')))
        c2 = Clause(Male('John'), VP('is', AdjP('tall')))
        c3 = self.aggregator.try_to_aggregate(c1, c2)
        expected = Clause(
            Male('John'),
            VP('is', CC(NP('a', 'boy'), AdjP('tall'),
                        features={'NUMBER': 'plural'}
                        ))
        )
        self.assertEqual(expected, c3)

        c1 = Clause(Male('John'), VP('wrote', NP('an', 'article')))
        c2 = Clause(Female('Marry'), VP('wrote', NP('an', 'article')))
        c3 = self.aggregator.try_to_aggregate(c1, c2)
        expected = Clause(
            CC(Male('John'), Female('Marry'),
               features={'NUMBER': 'plural'}),
            VP('wrote', NP('an', 'article')))
        self.assertEqual(expected, c3)


if __name__ == '__main__':
    unittest.main()
