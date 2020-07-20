import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from enum import Enum

# This is a hard coded list of evidence, better organized for readability
ev_all = ['EXP', 'IDA', 'IMP', 'IGI',  'IPI', 'IEP', 'IGC', 'RCA', 'IBA', 'IKR', 'IC', 'NAS', 'ND', 'TAS', 'HDA', 'HEP', 'HGI', 'HMP', 'ISA', 'ISM', 'ISO', 'ISS', 'IEA']


class CLOSURE_LABELS(Enum):
   ISA = "isa_closure"
   ISA_PARTOF = "isa_partof_closure"
   REGULATES = "regulates_closure"

# This is a hard coded list of reference genomes that should always be present in a GO release
REFERENCE_GENOME_IDS = [
    "NCBITaxon:9606",
    "NCBITaxon:10116",
    "NCBITaxon:10090",
    "NCBITaxon:3702",
    "NCBITaxon:7955",
    "NCBITaxon:6239",
    "NCBITaxon:559292",
    "NCBITaxon:7227",
    "NCBITaxon:44689",
    "NCBITaxon:4896",
    "NCBITaxon:83333"
]

BP_TERM_ID = "GO:0008150"
MF_TERM_ID = "GO:0003674"
CC_TERM_ID = "GO:0005575"

# useful grouping of evidences as discussed with Pascale
EVIDENCE_GROUPS = {
    "EXP": ["EXP", "IDA", "IEP", "IGI", "IMP", "IPI"],
    "HTP": ["HDA", "HEP", "HGI", "HMP", "HTP"],
    "PHYLO": ["IBA", "IRD", "IKR", "IMR"],
    "IEA": ["IEA"],
    "ND": ["ND"],
    "OTHER": ["IC", "IGC", "ISA", "ISM", "ISO", "ISS", "NAS", "RCA", "TAS"]
}

EVIDENCE_MIN_GROUPS = {
    "EXPERIMENTAL" : EVIDENCE_GROUPS["EXP"] + EVIDENCE_GROUPS["HTP"],
    "COMPUTATIONAL" : EVIDENCE_GROUPS["PHYLO"] + EVIDENCE_GROUPS["IEA"] + EVIDENCE_GROUPS["OTHER"]
}

def is_experimental(evidence_type):
    return evidence_type in EVIDENCE_MIN_GROUPS["EXPERIMENTAL"]

def is_computational(evidence_type):
    return evidence_type in EVIDENCE_MIN_GROUPS["COMPUTATIONAL"]

def get_evidence_min_group(evidence_type):
    for group, codes in EVIDENCE_MIN_GROUPS.items():
        if evidence_type in codes:
            return group
    return "ND"

def aspect_from_source(source):
    if source == "molecular_function":
        return "MF"
    elif source == "biological_process":
        return "BP"
    elif source == "cellular_component":
        return "CC"
    return "UNK"


global_session = None

def requests_retry(retries = 3, backoff = 0.3, session = None):
    session = session or requests.Session()
    retry = Retry(
        total = retries,
        read = retries,
        connect = retries,
        backoff_factor = backoff,
        status_forcelist = (429, 500, 502, 503, 504)
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def fetch(url):
    """
    Error proof method to get data from HTTP request
    If an error occured, return None
    """
    global global_session
    global_session = requests_retry(global_session)
    try:
        r = global_session.get(url)
        return r
    except Exception as x:
        print("Query GET " , url , " failed: ", x)
        return None

def post(url, params):
    global global_session
    global_session = requests_retry(global_session)
    try:
        r = global_session.post(url, data = params)
        return r  
    except Exception as x:
        print("Query POST " , url , " failed: ", x)
        return None
    

def golr_fetch(golr_base_url, select_query):
    """
    Error proof method to get data from GOLr
    If an HTTP error occurs, return None, otherwise return the json object
    """
    r = fetch(golr_base_url + select_query)
    if r is None:
        return None
    response = r.json()
    return response

def golr_fetch_by_taxon(golr_base_url, select_query, taxon):
    return golr_fetch(golr_base_url, select_query + "&fq=taxon:\"" + taxon + "\"")

def golr_fetch_by_taxa(golr_base_url, select_query, taxa):
    tmp = ""
    if isinstance(taxa, list):
        tmp = "&fq=taxon:(\"" + taxa.join("\" ") + "\")"
    else:
        tmp = "&fq=taxon:\"" + taxa + "\""
    print("*** ", golr_base_url + select_query + tmp)
    return golr_fetch(golr_base_url, select_query + tmp)

# utility function to build a list from a solr/golr facet array
def build_list(items_list, min_size = None):
    ls = []
    for i in range(0, len(items_list), 2):
        if min_size is None or items_list[i + 1] > min_size:
            ls.append(items_list[i])
    return ls

# utility function to transform a list [A, 1, B, 2] into a map {A: 1, B: 2}
def build_map(items_list, min_size = None):
    map = {}
    for i in range(0, len(items_list), 2):
        if min_size is None or items_list[i + 1] > min_size:
            map[items_list[i]] = items_list[i + 1]
    return map

# utility function to build a reverse map: { "a": 1, "b": 1, "c": 2 } -> {1: ["a", "b"], 2: ["c"]}
def build_reverse_map(map):
    reverse_map = { }
    for key, val in map.items():
        ls = []
        if val in reverse_map:
            ls = reverse_map[val]
        else:
            reverse_map[val] = ls
        ls.append(key)
    return reverse_map

# utility function to cluster elements of an input map based on another map of synonyms
def cluster_map(input_map, synonyms):
    cluster = { }
    for key, val in input_map.items():
        temp = synonyms[key]
        if temp in cluster:
            val_cluster = cluster[temp]
            cluster[temp] = val_cluster + val
        else:
            cluster[temp] = val
    return cluster

# similar as above but the value of each key is also a map
def cluster_complex_map(input_map, synonyms):
    cluster = { }
    for key, val in input_map.items():
        temp = synonyms[key]
        # print("working on : " , key , val)
        if temp in cluster:
            temp_cluster = cluster[temp]
            # print("cluster already found : ", temp , temp_cluster)
            for key_cluster, val_cluster in temp_cluster.items():
                temp_cluster[key_cluster] = val_cluster + val[key_cluster]
        else:
            cluster[temp] = val
    return cluster


# reorder map (python 3.6 keeps order in which items are inserted in map: https://stackoverflow.com/questions/613183/how-do-i-sort-a-dictionary-by-value)
def ordered_map(map):
    ordered_map = { }
    for w in sorted(map, key=map.get, reverse=True):
        ordered_map[w] = map[w]
    return ordered_map
    
def extract_map(map, key_str):
    extracted = { }
    for key, val in map.items():
        if key_str in key:
            extracted[key] = val
    return extracted


def merge_dict(dict_total, dict_diff):
    new_dict = { }
    for key, val in dict_total.items():
        if type(val) == str:
            new_dict[key] = val
        elif type(val) == int or type(val) == float:
            if val == 0:
                diff_val = dict_diff[key] if key in dict_diff else 0
                new_dict[key] = str(diff_val) + " / " + str(val) + "\t0%"
            else:
                diff_val = dict_diff[key] if key in dict_diff else 0
                new_dict[key] = str(diff_val) + " / " + str(val) + "\t" + str(round(100 * diff_val / val, 2)) + "%"
        elif type(val) == dict:
            diff_val = dict_diff[key] if key in dict_diff else { }
            new_dict[key] = merge_dict(val, diff_val)
        else:
            print("should not happened ! " , val , type(val))
    return new_dict

def minus_dict(dict1, dict2):
    new_dict = { }
    for key, val in dict1.items():
        if type(val) == str:
            new_dict[key] = val
        elif type(val) == int or type(val) == float:
                diff_val = dict2[key] if key in dict2 else 0
                new_dict[key] = val - diff_val
        elif type(val) == dict:
            diff_val = dict2[key] if key in dict2 else { }
            new_dict[key] = merge_dict(val, diff_val)
        else:
            print("should not happened ! " , val , type(val))
    return new_dict    

def has_taxon(stats, taxon_id):
    for taxon in stats["annotations"]["by_taxon"]:
        if taxon_id in taxon:
            return True
    return False
    
def added_removed_species(current_stats, previous_stats):
    results = {
        "added" : { },
        "removed" : { }
    }

    for taxon in current_stats["annotations"]["by_taxon"]:
        taxon_id = taxon.split("|")[0]
        if not has_taxon(previous_stats, taxon_id):
            results["added"][taxon] = current_stats["annotations"]["by_taxon"][taxon]

    for taxon in previous_stats["annotations"]["by_taxon"]:
        taxon_id = taxon.split("|")[0]
        if not has_taxon(current_stats, taxon_id):
            results["removed"][taxon] = previous_stats["annotations"]["by_taxon"][taxon]
        
    return results    


def bioentity_type(str_type):
    """
    In a nutshell, collapse all RNA related types into RNA
    """
    if "RNA" in str_type or "ribozyme" in str_type or "transcript" in str_type:
        return "RNA_cluster"
    return str_type

def sum_map_values(map):
    """
    Utility function to sum up the values of a map. Assume the map values are all numbers
    """
    total = 0
    for key, val in map.items():
        total += val
    return total

def write_json(key, content):
    with open(key, 'w') as outfile:
        try:
            json.dump(content, outfile, indent=2)
        finally:
            outfile.close()
 
def write_text(key, content):
    with open(key, 'w') as outfile:
        try:
            outfile.write(content)
        finally:
            outfile.close()

