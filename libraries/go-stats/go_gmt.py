import sys, getopt, os, json
import go_stats_utils as utils

max_rows = 10000000

select_ontology = "select?fq=document_category:\"ontology_class\"&q=*:*&rows=" + str(max_rows) + "&wt=json&fq=idspace:\"GO\"&fq=is_obsolete:false&fl=annotation_class,annotation_class_label,source"
select_annotations = "select?fq=document_category:\"annotation\"&q=*:*&rows=" + str(max_rows) + "&wt=json&fq=taxon:\"NCBITaxon:9606\"&fq=type:\"protein\"&fl=bioentity,aspect,annotation_class"
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

def aspect_from_source(source):
    if source == "molecular_function":
        return "MF"
    elif source == "biological_process":
        return "BP"
    elif source == "cellular_component":
        return "CC"
    return "UNK"

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
        term_aspect = aspect_from_source(ontology_map[term_id]['source'])

        report_direct["ALL"] += term_label + "%" + term_aspect + "%" + term_id
        report_direct[term_aspect] += term_label + "%" + term_aspect + "%" + term_id

        for annot in value:
            report_direct["ALL"] += "\t" + format_id(annot['bioentity'])
            report_direct[term_aspect] += "\t" + format_id(annot['bioentity'])

        report_direct["ALL"] += "\n"
        report_direct[term_aspect] += "\n"
        count += 1

        if count % 100 == 0:
            print(str(count) + " terms map created...")

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


    print("\nCreating ontology map...")
    ontology_map = create_ontology_map(golr_base_url)
    print("Ontology map created with ", len(ontology_map) , " terms")


    taxa = ["NCBITaxon:9606"]
    for taxon in taxa:
        taxon_id = taxon.split(":")[1]
        data = gmt(ontology_map, golr_base_url, taxon)

        output = output_rep + taxon_id
        utils.write_text(output + "-all.gmt", data["ALL"])
        utils.write_text(output + "-bp.gmt", data["BP"])
        utils.write_text(output + "-mf.gmt", data["MF"])
        utils.write_text(output + "-cc.gmt", data["CC"])

        if len(data["UNK"]) > 0:
            utils.write_text(output + "-unk.gmt", data["UNK"])
            print("WARNING: terms with invalid aspect can be found in ", output + "-unk.gmt")


if __name__ == "__main__":
   main(sys.argv[1:])
