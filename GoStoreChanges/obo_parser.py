import networkx as nx
import re

from enum import Enum
class TermState:
    ANY = 1
    VALID = 2
    OBSOLETE = 3

def value(var):
    return var if var is not None else "N/A"

class Term:
    
    def __init__(self):
        self.id = None
        self.alt_ids = None
        self.is_obsolete = False
        self.is_a = None
        self.namespace = None
        self.name = None
        self.comment = None
        self.synonyms = None
        self.definition = None
        self.created_by = None
        self.creation_date = None
        self.subsets = None
        self.xrefs = None
        
    def add_is_a(self, is_a):
        if self.is_a is None:
            self.is_a = []
        self.is_a.append(is_a)
        
    def add_alternate_id(self, alt_id):
        if self.alt_ids is None:
            self.alt_ids = []
        self.alt_ids.append(alt_id)
        
    def add_synonym(self, synonym):
        if self.synonyms is None:
            self.synonyms = []
        self.synonyms.append(synonym)
        
    def add_subset(self, subset):
        if self.subsets is None:
            self.subsets = []
        self.subsets.append(subset)
        
    def add_xref(self, xref):
        if self.xrefs is None:
            self.xrefs = []
        self.xrefs.append(xref)

    def equals(self, other):
        return self.id == other.id and self.is_obsolete == other.is_obsolete and self.alt_ids == other.alt_ids and self.name == other.name and self.is_a == other.is_a and self.namespace == other.namespace and self.definition == other.definition and self.comment == other.comment and self.synonyms == other.synonyms and self.subsets == other.subsets and self.xrefs == other.xrefs

    def explain_differences(self, other):
        reasons = {}
        if self.id != other.id:
            reasons["id"] = {"current": value(self.id), "previous": value(other.id) }
        if self.is_obsolete != other.is_obsolete:
            reasons["is_obsolete"] = {"current": value(self.is_obsolete), "previous": value(other.is_obsolete) }
        if self.alt_ids != other.alt_ids:
            reasons["alt_ids"] = {"current": value(self.alt_ids), "previous": value(other.alt_ids) }
        if self.name != other.name:
            reasons["name"] = {"current": value(self.name), "previous": value(other.name) }
        if self.namespace != other.namespace:
            reasons["namespace"] = {"current": value(self.namespace), "previous": value(other.namespace) }
        if self.definition != other.definition:
            reasons["definition"] = {"current": value(self.definition), "previous": value(other.definition) }
        if self.comment != other.comment:
            reasons["comment"] = {"current": value(self.comment), "previous": value(other.comment) }
        if self.synonyms != other.synonyms:
            reasons["synonyms"] = {"current": value(self.synonyms), "previous": value(other.synonyms) }
        if self.subsets != other.subsets:
            reasons["subsets"] = {"current": value(self.subsets), "previous": value(other.subsets) }
        if self.xrefs != other.xrefs:
            reasons["xrefs"] = {"current": value(self.xrefs), "previous": value(other.xrefs) }
        if self.is_a != other.is_a:
            reasons["is_a"] = {"current": value(self.is_a), "previous": value(other.is_a) }
        return reasons
        
    def __str__(self):
        return self.id + "\t" + self.name
        
class Relation:
    
    def __init__(self):
        id = None
        name = None
        namespace = None
        xref = None
        is_transitive = False
        
    def __str__(self):
        return self.id + "\t" + self.name

# TODO: I have to add the is_a: term_id ! term_name but I have to add it in the edges of the graph
# TODO: I can also add the consider (who link to other term_ids)
# TODO: Other relations: intersection_of, relationship
class OBO_Parser:
    
    term_key = "[Term]"
    type_def_key = "[Typedef]"
    header = None
    obo_graph = None
    relation_graph = None
    
    def __init__(self, content):
        self.content = content
        self.obo_graph = nx.Graph()
        self.relation_graph = nx.Graph()
        self.header = { }
        self._parseHeader()
        self._parseTerms()
        self._parseRelations()
        print("oboparser: ", len(self.obo_graph) , " terms")
            
            
    def _parseHeader(self):
        lines = self.content.split(self.term_key)[0].split("\n")
        for line in lines:
            if len(line) == 0:
                continue
            kv = re.split(":(?=\s)", line)
#            print("line: " , line , " kv: ", kv)
            self.header[kv[0].strip()] = kv[1].strip()
        print(self.header)


    def _parseTerms(self):
        terms = self.content.split(self.term_key)
        for i in range(1, len(terms)):
            term = Term()

            for line in terms[i].split("\n"):
                if len(line) == 0:
                    continue
                
                if line.startswith(self.type_def_key):
                    break
                
                value = re.split(":(?=\s)", line)[1].strip()
                if line.startswith("id"):
                    term.id = value
                elif line.startswith("alt_id"):
                    term.add_alternate_id(value)
                elif line.startswith("namespace"):
                    term.namespace = value
                elif line.startswith("name"):
                    term.name = value
                elif line.startswith("comment"):
                    term.comment = value
                elif line.startswith("def"):
                    term.definition = value
                elif line.startswith("synonym"):
                    term.add_synonym(value)
                elif line.startswith("subset"):
                    term.add_subset(value)
                elif line.startswith("is_obsolete"):
                    term.is_obsolete = value
                elif line.startswith("xref"):
                    term.add_xref(value)
                elif line.startswith("is_a"):
                    term.add_is_a(value.split(" ! ")[0].strip())

            self.obo_graph.add_node(term.id, object=term)
            

    def _parseRelations(self):
        relations = self.content.split(self.type_def_key)

        for i in range(1, len(relations)):
            relation = Relation()

            for line in relations[i].split("\n"):
                if len(line) == 0:
                    continue
                
                value = line.split(":")[1].strip()
                if line.startswith("id"):
                    relation.id = value
                elif line.startswith("name"):
                    relation.name = value
                elif line.startswith("namespace"):
                    relation.namespace = value
                elif line.startswith("xref"):
                    relation.xref = value
                elif line.startswith("is_transitive"):
                    relation.is_transitive = value

            self.relation_graph.add_node(relation.id, object=relation)
            
            
    def get_nodes(self):
        return self.obo_graph.nodes(data=True)


    def get_terms(self, term_state = TermState.VALID):
        map = { }
        for id, data in self.obo_graph.nodes(data=True):
            if term_state == TermState.ANY or (term_state == TermState.OBSOLETE and data['object'].is_obsolete) or (term_state == TermState.VALID and not data['object'].is_obsolete):
                map[id] = data['object']
        return map
        
        
    def has_term(self, query):
        return self.obo_graph.has_node(query)


    def get_term(self, query):
        if not self.has_term(query):
            return None
        return self.obo_graph.nodes[query]['object']