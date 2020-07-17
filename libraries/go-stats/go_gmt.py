import sys, getopt, os, json
import go_stats_utils as utils

max_rows = 10000000

select_ontology = "select?fq=document_category:\"ontology_class\"&q=*:*&rows=" + str(max_rows) + "&wt=json&fq=idspace:\"GO\"&fq=is_obsolete:false&fl=annotation_class,annotation_class_label,source"

select_annotations = "select?fq=document_category:%22annotation%22&q=*:*&rows=" + str(max_rows) + "&wt=json&fq=taxon:%22NCBITaxon:9606%22&fq=type:%22protein%22&fl=bioentity,aspect,annotation_class,evidence_type,isa_partof_closure,regulates_closure"

def create_ontology_map(golr_base_url):
    ontology = utils.golr_fetch(golr_base_url, select_ontology)
    ontology = ontology['response']['docs']
    map={}
    for item in ontology:
        map[item['annotation_class']] = item
    return map

def create_go_annotation_map(golr_base_url):
    annots = utils.golr_fetch(golr_base_url, select_annotations)
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

def aspect(source):
    if source == "molecular_function":
        return "MF"
    elif source == "biological_proces":
        return "BP"
    elif source == "cellular_component":
        return "CC"
    return "UNK"


def gmt(golr_base_url, taxon):
    ontology_map = create_ontology_map(golr_base_url)
    go_annotation_map = create_go_annotation_map(golr_base_url)

    report_direct = { "ALL" : "", "BP" : "", "MF" : "", "CC" : "" }
    for term_id, value in go_annotation_map.items():  
        term_label = ontology_map[term_id]['annotation_class_label']
        term_aspect = aspect(ontology_map[term_id]['source'])

        report_direct["ALL"] += term_label + "%" + term_aspect + "%" + term_id
        report_direct[term_aspect] += term_label + "%" + term_aspect + "%" + term_id

        for annot in value:
            report_direct["ALL"] += "\t" + format_id(annot['bioentity'])
            report_direct[term_aspect] += "\t" + format_id(annot['bioentity'])

        report_direct["ALL"] + "\n"
        report_direct[term_aspect] + "\n"

    return report_direct

def print_help():
    print('\nUsage: python go_gmt.py -g <golr_base_url> -o <output_rep>\n')


def main(argv):
    golr_base_url = ''
    output_rep = ''

    if len(argv) < 4:
        print_help()
        sys.exit(2)

    try:
        opts, argv = getopt.getopt(argv,"g:o:",["golrurl=","orep="])
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

    if not output_rep.endswith("/"):
        output_rep += "/"

    if not os.path.exists(output_rep):
        os.mkdir(output_rep)

    human_taxon = "NCBITaxon:9606"
    taxon = human_taxon
    # gmt(golr_base_url, taxon, output_rep + taxon.split(":")[1])
    # ontology = create_ontology_map(golr_base_url)
    # print(ontology)

    # annots = create_go_annotation_map(golr_base_url)
    # print(annots)
    
    taxon_id = taxon.split(":")[1]
    data = gmt(golr_base_url, taxon)

    output = output_rep + taxon_id
    utils.write_text(output + "-" + taxon_id + "-all.gmt", data["ALL"])
    utils.write_text(output + "-" + taxon_id + "-bp.gmt", data["BP"])
    utils.write_text(output + "-" + taxon_id + "-mf.gmt", data["MF"])
    utils.write_text(output + "-" + taxon_id + "-cc.gmt", data["CC"])


if __name__ == "__main__":
   main(sys.argv[1:])
