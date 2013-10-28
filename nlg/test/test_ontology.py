import unittest

import sys

folder = '../src'

if folder not in sys.path:
    sys.path.append(folder)


from nlg.ontology import Ontology
import rdflib
import rdflib.plugins.sparql as sparql


path = '/Users/roman/Work/Sassy/data/Logistics1.sassy/domain.ttl'
format = 'n3'


class TestOntology(unittest.TestCase):

    def test_ctor(self):
        ontology = Ontology(path, format)
        self.assertIsNotNone(ontology)

    def test_entity_type(self):
        ontology = Ontology(path, format)
        entity = 'http://www.scrutable-systems.org/ontology/Logistics#obj11'
        res = ontology.entity_types(entity)
        self.assertEqual(len(res), 2)
        entity = ':obj11'
        res = ontology.entity_types(entity)
        self.assertEqual(len(res), 2)

    def test_entity_type_fail(self):
        ontology = Ontology(path, format)
        entity = 'sassy:obj11'
        res = ontology.entity_types(entity)
        self.assertEqual(len(res), 0)

    def test_best_entity_type(self):
        ontology = Ontology(path, format)
        entity = ':obj11'
        res = ontology.best_entity_type(entity)
        self.assertEqual('drum', res)

    def test_entities_of_type(self):
        ontology = Ontology(path, format)
        type_ = ':drum'
        res = ontology.entities_of_type(type_)
        self.assertGreater(len(res), 0)




#ns = rdflib.namespace.Namespace('http://www.scrutable-systems.org/ontology/Logistics#')
#
##mapping = {'sassy': 'http://www.scrutable-systems.org/ontology/Logistics#'}
#mapping = {'sassy': ns}
#
ontology = Ontology(path)
#
entity_name = ':obj11'
#
#query_text = """
#SELECT ?type
#WHERE { ?entity rdf:type ?type.}
#"""
#
#query = sparql.prepareQuery(query_text)
#
#result = ontology.graph.query(query, initBindings={'entity': ns[entity_name]})
#
#print('Results for %s:' % entity_name)
#for row in result:
#    print("%s has type %s" % (entity_name,
#                              ontology.graph.qname(row.type)) )
#
#ontology.entity_types(':obj11')
#
#ontology.entity_types('http://www.scrutable-systems.org/ontology/Logistics#obj11')
#
#ontology._entities_of_type(':drum')
#
#ontology.entities_of_type(':drum')



# if the module is loaded on its own, run the test
if __name__ == '__main__':
    unittest.main()


#from rdflib import Namespace, Graph, URIRef
#g = Graph()
#g.load("http://www.wikier.org/foaf.rdf")
#for result in g.query("SELECT ?person WHERE { ?person a ?type }",
#    initNs={ "foaf" : Namespace("http://xmlns.com/foaf/0.1/") },
#    initBindings={'type': URIRef("http://xmlns.com/foaf/0.1/Person")}): #<-- OK
#    initBindings={'type': URIRef("foaf:Person")}): # <-- not working
#    print (result)













