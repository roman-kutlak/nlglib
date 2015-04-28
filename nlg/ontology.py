import rdflib
import rdflib.plugins.sparql as sparql
import logging


logging.getLogger(__name__).addHandler(logging.NullHandler())

def get_log():
    return logging.getLogger(__name__)


# this is using rdflib; check out owllib

class Ontology:
    """ The class Ontology represents an interface to the underlying RDF
    ontology. It allows querying the ontology for things such as entity
    types.
    """

    def __init__(self, path, format='n3', nsMappings=None):
        """ Parse an rdf graph and construct the ontology. No inference done.
        path - string indicating the path of the file
        format - string indicating the format of the file; default 'n3'
        nsMappings - dictionary with namespace mappings. If set, all queries
        make use of the currently set mapping. The expected format is a string
        to string mapping (e.g., {'foaf': 'http://xmlns.com/foaf/0.1/'})

        """
        self.graph = rdflib.Graph()
        self.graph.parse(path, format=format)
        self.ns = nsMappings if nsMappings is not None else (
            dict(self.graph.namespace_manager.namespaces()))
        self.cache = dict()

    def entity_types(self, entity_name):
        result = self.types(entity_name)
        return result

    def best_entity_type(self, entity_name):
        """ Return the most specific type of the entity.
        An object can belong to multiple hierarchies (multiple inheritance).
        The function assumes that the longest hierarchy path is the best one
        and it returns the most specific type from the longest hierarchy.
        If two or more hierarchies have the same length, the function takes
        the first one (i.e. undefined order between the two).

        """
        types = list(self.entity_types(entity_name))
        get_log().debug('ontology types for "%s": %s' % (entity_name, str(types)))
        if types == []: return None
        elif len(types) == 1: return types[0]
        part = self.partition(types)
        # since the list was non-empty, there is at least one partition
        partition = part[0]
        partition = subsume_sort(partition, self)
        get_log().debug(partition)
        return partition[0]

    def entities(self):
        """ Return a set of all individuals in the ontology. """
        query_text = """
            SELECT DISTINCT ?ind
            WHERE {
                ?ind rdf:type owl:NamedIndividual .
            }
        """
        result = self._exec_query(query_text, {})
        return result

    def entities_of_type(self, entity_type):
        result = self.individuals(entity_type)
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
            }
        """
        result = self._exec_query(query_text, {'a': a})
        return result

    def superclasses(self, a):
        """ Return the set of superclasses of a. """
        query_text = """
            SELECT ?x
            WHERE {
              ?a rdfs:subClassOf* ?x.
            }
        """
        result = self._exec_query(query_text, {'a': a})
        return result

    def individuals(self, cls):
        """ Return a set of individuals of a given class (incl subclasses). """
        query_text = """
            SELECT DISTINCT ?x
            WHERE {
              ?x rdf:type ?type.
              ?type rdfs:subClassOf* ?cls.
            }
        """
        result = self._exec_query(query_text, {'cls': cls})
        return result

    def types(self, object):
        """ Return the types which apply to the object. """
        query_text = """
            SELECT DISTINCT ?x
            WHERE {
                ?object rdf:type ?x.
            }
        """
        result = self._exec_query(query_text, {'object': object})
        return result

    def properties(self, entity):
        """Return a list of pairs of properties of the given object. """
        query_text = """
            SELECT ?predicate ?object
            WHERE {
                ?subject ?predicate ?object.
            }
        """
        result = self._exec_query(query_text, {'subject': entity})
        return result
    

    def sort(self, classes):
        """ Sort the classes according to a hierarchy. """
        return subsume_sort(classes, self)

    def partition(self, classes):
        """ Partition classes according to subsumption hierarchy and return
        the partitions in a list sorted by size of partition from largest down.

        """
        partitions = subsume_partition(classes, self)
        partitions = sorted(partitions, key=lambda x: len(x), reverse=True)
        return partitions

##############################   Private methods   #############################

    def _exec_query(self, query_text, params):
        """ Take a sparql query and a parameter and run the query.
        The function applies prefixes before the query and strips them 
        in the result.
        
        """
        key = (query_text, tuple(params.items()))
        if key in self.cache: return self.cache[key]
        bindings = dict()
        for k, p in params.items():
            bindings[k] = rdflib.URIRef(self._apply_prefix(p))
#            bindings[k] = self.graph.namespace_manager.absolutize(p)
        query = sparql.prepareQuery(query_text, initNs=self.ns)
        qres = self.graph.query(query, initBindings=bindings)
        normalise = self.graph.namespace_manager.normalizeUri
        if len(qres.vars) == 1:
            result = [normalise(r[0]) for r in qres]
        else:
            result = [tuple([normalise(str(x)) for x in r])
                        for r in qres]
        self.cache[key] = result
        return set(result)

    def _apply_prefix(self, entity_name):
        if self.ns is None: return entity_name

        tmp = entity_name.rsplit(':')
        if len(tmp) > 1:
            prefix = tmp[0]
            if prefix in self.ns:
                entity_name = entity_name.replace(prefix + ':', self.ns[prefix])
        return entity_name


def subsume_sort(list, ontology):
    """Quicksort list of classes. Assume classes are on the same hierarchy. """
    if list == []:
        return []
    else:
        pivot = list[0]
        lower_part = [x for x in list[1:] if not ontology.subsumes(x, pivot)]
        upper_part = [x for x in list[1:] if ontology.subsumes(x, pivot)]
        lesser = subsume_sort(lower_part, ontology)
        greater = subsume_sort(upper_part, ontology)
        return lesser + [pivot] + greater

def subsume_partition(classes, ontology):
    """ Partition the list of classes according to ontology hierarchy. """
    partitions = []
    tmp = list(classes)
    current_len = -1
    while (len([x for p in partitions for x in p]) != current_len or
           len(tmp) > 0):
        current_len = len([x for p in partitions for x in p])
        if len(tmp) == 0: break
        elt = tmp.pop()
        consumed = False
        for partition in partitions:
            all_in = True
            if elt in partition:
                consumed = True
                continue
            for element in partition:
                if not (ontology.subsumes(elt, element) or
                        ontology.subsumes(element, elt)):
                    all_in = False
                    break
            if all_in: # all elements are from the same hierarchy
                partition.add(elt)
                consumed = True
                tmp = list(classes)
        if not consumed: partitions.append({elt})

    return [list(x) for x in partitions]



#select all instances of a class (including subclasses)
#http://stackoverflow.com/questions/9209577/
#sparql-get-all-the-entities-of-subclasses-of-a-certain-class

#SELECT ?entity
#WHERE {
#  ?entity rdf:type ?type.
#  ?type rdfs:subClassOf* :C.
#}


# works if we assume single inheritance
#def subsume_partition(classes, ontology):
#    """ Partition the list of classes according to ontology hierarchy.
#    Assume that the classes are either from one hierarchy or disjoint.
#    This means that owl:thing is not part of the class list.
#
#    """
#    partitions = []
#    tmp = list(classes)
#    while len(tmp) > 0:
#        elt = tmp.pop()
#        consumed = False
#        for partition in partitions:
#            all_in = True
#            for element in partition:
#                if (ontology.subsumes(elt, element) or
#                    ontology.subsumes(element, elt)):
#                    partition.append(elt)
#                    consumed = True
#                    break
#            if consumed: break
#        if not consumed: partitions.append([elt])
#    return partitions
#


#############################################################################
##
## Copyright (C) 2013 Roman Kutlak, University of Aberdeen.
## All rights reserved.
##
## This file is part of SAsSy NLG library.
##
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of University of Aberdeen nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
##
#############################################################################
