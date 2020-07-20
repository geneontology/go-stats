# This script is experimental and is used to produce GMT files out of GO terms

import sys, getopt, os, json
import go_stats_utils as utils
from obo_parser import OBO_Parser, TermState

max_rows = 10000000

select_ontology = "select?fq=document_category:\"ontology_class\"&q=*:*&rows=" + str(max_rows) + "&wt=json&fq=idspace:\"GO\"&fq=is_obsolete:false&fl=annotation_class,annotation_class_label,source"
select_annotations = "select?fq=document_category:\"annotation\"&q=*:*&rows=" + str(max_rows) + "&wt=json&fq=taxon:\"NCBITaxon:9606\"&fq=type:\"protein\"&fl=bioentity,annotation_class"
# select_annotations = "select?fq=document_category:\"annotation\"&q=*:*&rows=" + str(max_rows) + "&wt=json&fq=taxon:\"NCBITaxon:9606\"&fq=type:\"protein\"&fl=bioentity,aspect,annotation_class,evidence_type,isa_partof_closure,regulates_closure"

def create_ontology_map(golr_base_url):
    ontology = utils.golr_fetch(golr_base_url, select_ontology)
    ontology = ontology['response']['docs']
    map={}
    for item in ontology:
        map[item['annotation_class']] = item
    return map

def create_go_annotation_map(golr_base_url, taxa):
    annots = utils.golr_fetch_by_taxa(golr_base_url, select_annotations, taxa)
    annots = annots['response']['docs']
    map={}
    for item in annots:
        iclass = item['annotation_class']
        iannots = []
        if iclass in map:
            iannots = map[iclass]
        else:
            map[iclass] = iannots
        iannots.append(item)
    return map

def format_id(id):
    return id.replace("UniProtKB:", "")



aspects = {
    "GO:0003674" : "MF",
    "GO:0008150" : "BP",
    "GO:0005575" : "CC"
}

def gmt(ontology_map, golr_base_url, taxa):
    print("\nCreating term annotation map...")
    go_annotation_map = create_go_annotation_map(golr_base_url, taxa)
    print("Term annotation map created with ", len(go_annotation_map) , " terms")

    report_direct = { "ALL" : "", "BP" : "", "MF" : "", "CC" : "", "UNK" : "" }
    count = 0

    for term_id, value in go_annotation_map.items():
        # do not consider aspect level terms (irrelevant: too many if not all genes)
        if term_id in aspects:
            continue

        term_label = ontology_map[term_id]['annotation_class_label']
        term_aspect = utils.aspect_from_source(ontology_map[term_id]['source'])

        report_direct["ALL"] += term_label + "%" + term_aspect + "%" + term_id
        report_direct[term_aspect] += term_label + "%" + term_aspect + "%" + term_id

        id_set = set()
        for annot in value:
            id_set.add(format_id(annot['bioentity']))

        report_direct["ALL"] += "\t" + "\t".join(id_set) + "\n"
        report_direct[term_aspect] += "\t" + "\t".join(id_set) + "\n"
        count += 1

        if count % 1000 == 0:
            print(str(count) + " terms map created...")

    return report_direct


def filter_slim(report, terms):
    gmt_slim = { }
    for aspect in report:
        gmt_aspect = report[aspect]
        gmt_slim[aspect] = ""
        lines = gmt_aspect.split("\n")
        for line in lines:
            # test if the line contains any terms of the slim
            res = any(ele in line for ele in terms)
            if res:
                gmt_slim[aspect] += line + "\n"
    return gmt_slim



def print_help():
    print('\nUsage: python go_gmt.py -g <golr_base_url> -o <output_rep> -s <slim_base_url>\n')


def main(argv):
    golr_base_url = ''
    output_rep = ''
    slim_base_url = ''


    if len(argv) < 6:
        print_help()
        sys.exit(2)

    try:
        opts, argv = getopt.getopt(argv,"g:o:s:",["golrurl=","orep=","slim="])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print_help()
            sys.exit()
        elif opt in ("-g", "--golrurl"):
            golr_base_url = arg
            if not golr_base_url.endswith("/"):
                golr_base_url = golr_base_url + "/"
        elif opt in ("-o", "--orep"):
            output_rep = arg
        elif opt in ("-s", "--slim"):
            slim_base_url = arg
            if not slim_base_url.endswith("/"):
                slim_base_url = slim_base_url + "/"

    if not output_rep.endswith("/"):
        output_rep += "/"

    if not os.path.exists(output_rep):
        os.mkdir(output_rep)



    print("\n1 - Creating ontology map...")
    ontology_map = create_ontology_map(golr_base_url)
    print("Ontology map created with ", len(ontology_map) , " terms")



    slims = [ "goslim_agr.obo", "goslim_generic.obo", "goslim_chembl.obo" ]
    print("\n2 - Loading ", len(slims), " slims to create the slim-specific GMTs...")
    slim_obos = { }

    for slim in slims:
        response = utils.fetch(slim_base_url + slim)
        obo = OBO_Parser(response.text)
        slim_obos[slim] = obo
        print(slim , obo)
        # with open(slim, 'r') as file:
        #     data = file.read()
        #     obo = OBO_Parser(data)
        #     slim_obos[slim] = obo
            # terms = obo.get_terms(TermState.VALID)
            # print("VALID TERMS: ", len(terms))
            # for term in terms:
            #     print("- ", term , terms[term].id , terms[term].name)
    print("Slims loaded: ", len(slim_obos))



    # taxa = utils.REFERENCE_GENOME_IDS
    taxa = [ "NCBITaxon:9606", "NCBITaxon:10116" ]
    print("\n3 - Creating the GMTs for " , len(taxa) , " ")
    for taxon in taxa:
        taxon_id = taxon.split(":")[1]
        data = gmt(ontology_map, golr_base_url, taxon)

        output = output_rep + taxon_id
        for aspect in data:
            if len(data[aspect]) > 0:
                utils.write_text(output + "-" + aspect.lower() + ".gmt", data[aspect])


if __name__ == "__main__":
   main(sys.argv[1:])
