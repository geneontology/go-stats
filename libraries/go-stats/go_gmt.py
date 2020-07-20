# This script is experimental and is used to produce GMT files out of GO terms

import sys, getopt, os, json
import go_stats_utils as utils
from obo_parser import OBO_Parser, TermState

max_rows = 10000000



select_ontology = "select?fq=document_category:\"ontology_class\"&q=*:*&rows=" + str(max_rows) + "&wt=json&fq=idspace:\"GO\"&fq=is_obsolete:false&fl=annotation_class,annotation_class_label,source,regulates_closure,isa_closure,isa_partof_closure,regulates_closure"
select_annotations = "select?fq=document_category:\"annotation\"&q=*:*&rows=" + str(max_rows) + "&wt=json&fq=type:\"protein\"&fl=bioentity,annotation_class,evidence_type"

ASPECTS = {
    "GO:0003674" : "MF",
    "GO:0008150" : "BP",
    "GO:0005575" : "CC"
}


def create_ontology_map(golr_base_url):
    ontology = utils.golr_fetch(golr_base_url, select_ontology)
    ontology = ontology['response']['docs']
    map={}
    for item in ontology:
        map[item['annotation_class']] = item
    return map

def create_go_annotation_map(golr_base_url, taxa):
    """
    Create a Map { GO-Term -> [ annotations ] } using the direct annotation to the term (annotation_class)
    """
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

def remap_go_annotation_map(go_annotation_map, ontology_map, closure):
    """
    Remap an existing go annotation map using a certain closure (see CLOSURE_LABELS)
    """
    new_map = {}
    for term in go_annotation_map:
        new_map[term] = []
        closure_terms = ontology_map[term][closure]

        for closure_term in closure_terms:
            # continue only if there is an annotation for that closure term
            if closure_term not in go_annotation_map:
                continue
            # discard annotation to root terms
            if closure_term in ASPECTS:
                continue
            new_map[term] = new_map[term] + go_annotation_map[closure_term]

    return new_map

def format_id(id):
    return id.replace("MGI:MGI:", "MGI:")
    # return id.replace("UniProtKB:", "")


def gmt(ontology_map, golr_base_url, taxa):
    print("\nCreating term annotation map for taxa ", taxa , " ...")
    go_annotation_map = create_go_annotation_map(golr_base_url, taxa)
    print("Term annotation map created with ", len(go_annotation_map) , " terms")

    closure = utils.CLOSURE_LABELS.REGULATES.value
    print("\nRemapping annotations using closure ", closure)
    go_annotation_map = remap_go_annotation_map(go_annotation_map, ontology_map, closure)
    print("Term annotation remapped using closure ", closure , " with ", len(go_annotation_map) , " terms")

    evidence_groups = [ "ALL", "EXPERIMENTAL", "INFERRED" ]
    aspect_lists = [ "ALL", "BP", "MF", "CC" ]

    report = { }
    for aspect in aspect_lists:
        report[aspect] = { }

    count = 0

    for term_id, value in go_annotation_map.items():
        # do not consider aspect level terms (irrelevant: a gene supposedly always have at least 1 MF, 1 BP and 1 CC)
        if term_id in ASPECTS:
            continue

        term_label = ontology_map[term_id]['annotation_class_label']
        term_aspect = utils.aspect_from_source(ontology_map[term_id]['source'])


        # for each annotated term, we'll keep a list of all the genes associated based on their evidence groups
        id_sets = { }
        for evgroup in evidence_groups:
            id_set = set()
            id_sets[evgroup] = id_set

        # going through each annotation for the term considered
        for annot in value:
            # Add all annotations (don't filter by evidence)
            id_sets["ALL"].add(format_id(annot['bioentity']))
            
            et = annot['evidence_type']
            evgroup = utils.get_evidence_min_group(et)
            if(evgroup == "ND"):
                continue

            # Add the annotation for the specific group of evidence
            id_sets[evgroup].add(format_id(annot['bioentity']))


        # Building the report for that term; will add only the term to an evidence group report IF the term has at least one gene
        for evgroup in evidence_groups:
            id_set = id_sets[evgroup]
            if len(id_set) == 0:
                continue
            
            if evgroup not in report["ALL"]:
                report["ALL"][evgroup] = ""                
            report["ALL"][evgroup] += term_label + "%" + term_aspect + "%" + term_id + "\t" + "\t".join(id_set) + "\n"

            if evgroup not in report[term_aspect]:
                report[term_aspect][evgroup] = ""
            report[term_aspect][evgroup] += term_label + "%" + term_aspect + "%" + term_id + "\t" + "\t".join(id_set) + "\n"

        count += 1

        if count % 5000 == 0:
            print(str(count) + " terms map created...")
    print(str(count) + " terms map created...")

    return report


def filter_slim(report, terms):
    gmt_slim = { }
    for aspect in report:
        gmt_slim[aspect] = { }
        for evgroup in report[aspect]:
            gmt_aspect = report[aspect][evgroup]
            lines = gmt_aspect.split("\n")
            for line in lines:
                # test if the line contains any terms of the slim
                res = any(ele in line for ele in terms)
                if res:
                    if evgroup not in gmt_slim[aspect]:
                        gmt_slim[aspect][evgroup] = ""    
                    gmt_slim[aspect][evgroup] += line + "\n"
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
    print("Slims loaded: ", len(slim_obos))



    # taxa = utils.REFERENCE_GENOME_IDS
    taxa = [ "NCBITaxon:9606", "NCBITaxon:10090" ]
    print("\n3 - Creating the GMTs for " , len(taxa) , " taxa")
    for taxon in taxa:
        taxon_id = taxon.split(":")[1]
        gmt_taxon = gmt(ontology_map, golr_base_url, taxon)

        output = output_rep + taxon_id

        for aspect in gmt_taxon:
            for evgroup in gmt_taxon[aspect]:
                if len(gmt_taxon[aspect][evgroup]) > 0:
                    utils.write_text(output + "-" + aspect.lower() + "-" + evgroup.lower() + ".gmt", gmt_taxon[aspect][evgroup])

        for slim_obo in slim_obos:
            oterms = slim_obos[slim_obo].get_terms(TermState.VALID)
            terms = oterms.keys()
            gmt_taxon_slim = filter_slim(gmt_taxon, terms)
            slim_key = slim_obo.replace(".obo", "")

            for aspect in gmt_taxon_slim:
                for evgroup in gmt_taxon_slim[aspect]:
                    if len(gmt_taxon_slim[aspect][evgroup]) > 0:
                        utils.write_text(output + "-" + slim_key + "-" + aspect.lower() + "-" + evgroup.lower() + ".gmt", gmt_taxon_slim[aspect][evgroup])



if __name__ == "__main__":
   main(sys.argv[1:])
