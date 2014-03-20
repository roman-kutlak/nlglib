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

    def entities_of_type2(self, entity_type):
        qres = self._entities_of_type2(entity_type)
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
        entity_name = self._apply_prefix(entity_name)
        entity = rdflib.URIRef(entity_name)

        query = sparql.prepareQuery(query_text)
        qres = self.graph.query(query, initBindings={'entity': entity})
        return qres

    def _entities_of_type(self, entity_type):
        query_text = """
SELECT DISTINCT ?entity
WHERE {
  ?entity rdf:type ?type.
  ?type rdfs:subClassOf* ?cls.
}"""
        entity_type = self._apply_prefix(entity_type)
        cls = rdflib.URIRef(entity_type)

        query = sparql.prepareQuery(query_text)
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

    def subsumes(self, a, b):
        """ Return true if a subsumes b. """
        subclasses = self.subclasses(a)
        return (b in subclasses)

    def subclasses(self, a):
        """ Return the set of subclasses of a. """
        query_text = """
SELECT DISTINCT ?x
WHERE {
  ?x rdfs:subClassOf* ?a.
}"""
        a = self._apply_prefix(a)
        cls = rdflib.URIRef(a)

        query = sparql.prepareQuery(query_text)
        qres = self.graph.query(query, initBindings={'a': cls})
        result = [str(r.x) for r in qres]
        result = [self._remove_prefix(x) for x in result]
        return set(result)

    def superclasses(self, a):
        """ Return the set of superclasses of a. """
        query_text = """
SELECT ?x
WHERE {
  ?a rdfs:subClassOf* ?x.
}"""
        a = self._apply_prefix(a)
        cls = rdflib.URIRef(a)

        query = sparql.prepareQuery(query_text)
        qres = self.graph.query(query, initBindings={'a': cls})
        result = [str(r.x) for r in qres]
        result = [self._remove_prefix(x) for x in result]
        return set(result)

    def individuals(self, cls):
        """ Return a set of individuals of a given class. """
        pass

    def _exec_query(self, query_text, params):
        """ Take a sparql query and a parameter and run the query.
        The function only supports query with one varaible in the result
        and this variable has to be called x.
        Params is a dict of parameters to bind in the query.
        """
        bindings = dict()
        for k, p in params.items():
            bindings[k] = rdflib.URIRef(self._apply_prefix(p))

        query = sparql.prepareQuery(query_text)
        qres = self.graph.query(query, initBindings=bindings)
        result = [str(r.x) for r in qres]
        result = [self._remove_prefix(x) for x in result]
        return set(result)




#select all instances of a class (including subclasses)
#http://stackoverflow.com/questions/9209577/
#sparql-get-all-the-entities-of-subclasses-of-a-certain-class

#SELECT ?entity
#WHERE {
#  ?entity rdf:type ?type.
#  ?type rdfs:subClassOf* :C.
#}

