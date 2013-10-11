import rdflib
import rdflib.plugins.sparql as sparql
from rdflib.namespace import RDF


class Ontology:
    """ The class Ontology represents an interface to the underlying RDF 
    ontology. It allows querying the ontology for things such as entity
    types.
    """

    def __init__(self, path, format='n3', nsMappings=None):
        """ Parse an rdf graph and construct the ontology. No inference done.
        path - string indicating the path of the file
        format - string indicationg the format of the file; default 'n3'
        nsMappings - dictionary with namespace mappings. If set, all queries
        make use of the currently set mapping. The expected format is a string
        to string mapping (e.g., {'foaf': 'http://xmlns.com/foaf/0.1/'})

        """
        self.graph = rdflib.Graph()
        self.graph.parse(path, format=format)
        self.ns = nsMappings if nsMappings is not None else (
            dict(self.graph.namespace_manager.namespaces()))

    def entity_types(self, entity_name):
        qres = self._entity_types(entity_name)
        result = [str(x.type) for x in qres]
        result = [self._remove_prefix(x) for x in result]
        return result

    def best_entity_type(self, entity_name):
        types = self.entity_types(entity_name)
        print('ontology types for "%s": %s' % (entity_name, str(types)))
        for t in types:
            if t.startswith(':'):
                return t.replace(':', '')
        return entity_name

    def entities_of_type(self, entity_type):
        qres = self._entities_of_type(entity_type)
        result = [str(x.entity) for x in qres]
        result = [self._remove_prefix(x) for x in result]

        return result

    def _entity_types(self, entity_name):
        """ Return the entity types as URIRef instances """
        query_text = """
SELECT DISTINCT ?type
WHERE {
    ?entity rdf:type ?type.
}"""
        query = sparql.prepareQuery(query_text)

        entity_name = self._apply_prefix(entity_name)
        entity = rdflib.URIRef(entity_name)

        qres = self.graph.query(query, initBindings={'entity': entity})
        return qres

    def _entities_of_type(self, entity_type):
        query_text = """
SELECT ?entity
WHERE {
  ?entity rdf:type ?cls.
}"""
        query = sparql.prepareQuery(query_text)

        entity_type = self._apply_prefix(entity_type)
        cls = rdflib.URIRef(entity_type)

        qres = self.graph.query(query, initBindings={'cls': cls})
        return qres

    def _apply_prefix(self, entity_name):
        if self.ns is None: return entity_name

        tmp = entity_name.split(':')
        if len(tmp) > 1:
            prefix = tmp[0]
            if prefix in self.ns:
                entity_name = entity_name.replace(prefix + ':', self.ns[prefix])
        return entity_name

    def _remove_prefix(self, result):
        if self.ns is None: return result
        for k, v in self.ns.items():
            if result.startswith(v):
                return result.replace(v, k + ':')
        return result









#select all instances of a class (including subclasses)
#http://stackoverflow.com/questions/9209577/
#sparql-get-all-the-entities-of-subclasses-of-a-certain-class

#SELECT ?entity
#WHERE {
#  ?entity rdf:type ?type.
#  ?type rdfs:subClassOf* :C.
#}

