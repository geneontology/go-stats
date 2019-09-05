import requests
import json
import sys, getopt, os

import go_stats
import go_ontology_changes
import go_annotation_changes


def merge_dict(dict_total, dict_diff):
    new_dict = { }
    for key, val in dict_total.items():
        if type(val) == str:
            new_dict[key] = val
        elif type(val) == int or type(val) == float:
            if val == 0:
                diff_val = dict_diff[key] if key in dict_diff else 0
                new_dict[key] = str(diff_val) + " / " + str(val) + " (0%) "
            else:
                diff_val = dict_diff[key] if key in dict_diff else 0
                new_dict[key] = str(diff_val) + " / " + str(val) + " (" + str(round(100 * diff_val / val, 2)) + "%) "
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


def print_help():
    print('Usage: python go_reports.py -g <golr_url> -s <previous_stats_url> -n <previous_stats_no_pb_url> -c <current_obo_url> -p <previous_obo_url> -o <output_rep>\n')


def main(argv):
    golr_url = ''
    previous_stats_url = ''
    previous_stats_no_pb_url = ''
    current_obo_url = ''
    previous_obo_url = ''    
    output_rep = ''

    if len(argv) < 3:
        print_help()
        sys.exit(2)

    try:
        opts, argv = getopt.getopt(argv,"g:s:n:c:p:o:",["golrurl=", "pstats=", "pnstats=", "cobo=", "pobo=", "orep="])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print_help()
            sys.exit()
        elif opt in ("-g", "--golrurl"):
            golr_url = arg
        elif opt in ("-s", "--pstats"):
            previous_stats_url = arg
        elif opt in ("-n", "--pnstats"):
            previous_stats_no_pb_url = arg
        elif opt in ("-c", "--cobo"):
            current_obo_url = arg
        elif opt in ("-p", "--pobo"):
            previous_obo_url = arg
        elif opt in ("-o", "--orep"):
            output_rep = arg

    if not output_rep.endswith("/"):
        output_rep += "/"

    if not os.path.exists(output_rep):
        os.mkdir(output_rep)


    # 1 - Executing go_stats script
    print("\n\n1a - EXECUTING GO_STATS SCRIPT (INCLUDING PROTEIN BINDING)...\n")
    json_stats = go_stats.compute_stats(golr_url)
    # with open('newstats/2019-06/go-stats.json', 'r') as myfile:
    #     data=myfile.read()
    # json_stats = json.loads(data)
    
    print("DONE.")

    print("\n\n1b - EXECUTING GO_STATS SCRIPT (EXCLUDING PROTEIN BINDING)...\n")
    json_stats_no_pb = go_stats.compute_stats(golr_url, True)
    # with open('newstats/2019-06/go-stats-no-pb.json', 'r') as myfile:
    #     data=myfile.read()
    # json_stats_no_pb = json.loads(data)
    # print("DONE.")


    # 2 - Executing go_ontology_changes script
    print("\n\n2 - EXECUTING GO_ONTOLOGY_CHANGES SCRIPT...\n")
    json_onto_changes = go_ontology_changes.compute_changes(current_obo_url, previous_obo_url)
    go_annotation_changes.write_json(output_rep + "go-ontology-changes.json", json_onto_changes)

    tsv_onto_changes = go_ontology_changes.create_text_report(json_onto_changes) 
    go_annotation_changes.write_text(output_rep + "go-ontology-changes.tsv", tsv_onto_changes)

    # with open('newstats/2019-06/go-ontology-changes.json', 'r') as myfile:
    #     data=myfile.read()
    # json_onto_changes = json.loads(data)
    print("DONE.")


    # 3 - Executing go_annotation_changes script
    print("\n\n3a - EXECUTING GO_ANNOTATION_CHANGES SCRIPT (INCLUDING PROTEIN BINDING)...\n")
    previous_stats = requests.get(previous_stats_url).json()    
    json_annot_changes = go_annotation_changes.compute_changes(json_stats, previous_stats)
    print("DONE.")
    
    print("\n\n3b - EXECUTING GO_ANNOTATION_CHANGES SCRIPT (EXCLUDING PROTEIN BINDING)...\n")
    previous_stats_no_pb = requests.get(previous_stats_no_pb_url).json()    # WE STILL NEED TO CORRECT THAT: 1 FILE OR SEVERAL FILE ? IF SEVERAL, ONE MORE PARAMETER
    json_annot_no_pb_changes = go_annotation_changes.compute_changes(json_stats_no_pb, previous_stats_no_pb)
    print("DONE.")

    # 4 - Refining go-stats with ontology stats
    print("\n\n4 - EXECUTING GO_REFINE_STATS SCRIPT...\n")

    # print("JSON STATS: ", json_stats)
    # print("JSON_ANNOT_CHANGES: ", json_annot_changes)
    merged_annotations_diff = merge_dict(json_stats, json_annot_changes)
    go_stats.write_json(output_rep + "go-merged-annotations-diff.json", merged_annotations_diff)
    json_annot_changes = merged_annotations_diff



#     json_stats["ontology"] = json_onto_changes["summary"]["current"]
#     del json_stats["ontology"]["release_date"]
#     del json_stats["terms"]
#     go_stats.write_json(output_rep + "go-stats.json", json_stats)

#     json_stats_no_pb["ontology"] = json_onto_changes["summary"]["current"]
#     del json_stats_no_pb["ontology"]["release_date"]
#     del json_stats_no_pb["terms"]
#     go_stats.write_json(output_rep + "go-stats-no-pb.json", json_stats_no_pb)

# #    tsv_stats = go_stats.create_text_report(json_stats)
# #    go_stats.write_text(output_rep + "go-stats.tsv", tsv_stats)

#     json_meta["ontology"] = json_onto_changes["summary"]["current"]
#     del json_meta["ontology"]["release_date"]
#     del json_meta["terms"]

#     json_meta["annotations"]["total_no_pb"] = json_stats_no_pb["annotations"]["total"]
#     json_meta["annotations"]["experimental_no_pb"] = json_stats_no_pb["annotations"]["experimental"]
#     json_meta["bioentities"]["total_no_pb"] = json_stats_no_pb["bioentities"]["total"]
#     json_meta["bioentities"]["by_type_no_pb"] = json_stats_no_pb["bioentities"]["by_type"]
#     json_meta["references_no_pb"] = json_stats_no_pb["references"]
#     json_meta["pmids_no_pb"] = json_stats_no_pb["pmids"]
#     go_stats.write_json(output_rep + "go-stats-summary.json", json_meta)


    ontology = json_onto_changes["summary"]["current"].copy()
    del ontology["release_date"]

    json_stats = {
        "release_date" : json_stats["release_date"],
        "ontology" : ontology,
        "annotations" : json_stats["annotations"]
    }
    go_stats.write_json(output_rep + "go-stats.json", json_stats)


    json_stats_no_pb = {
        "release_date" : json_stats_no_pb["release_date"],
        "ontology" : ontology,
        "annotations" : json_stats_no_pb["annotations"]
    }
    go_stats.write_json(output_rep + "go-stats-no-pb.json", json_stats_no_pb)


    annotations_by_reference_genome = { }
    for taxon in go_stats.reference_genomes_ids:
        key = go_stats.taxon_label(taxon)
        annotations_by_reference_genome[key] = json_stats["annotations"]["by_taxon"][key]

    bioentities_by_reference_genome = { }
    for taxon in go_stats.reference_genomes_ids:
        key = go_stats.taxon_label(taxon)
        bioentities_by_reference_genome[key] = json_stats["annotations"]["bioentities"]["by_taxon"]["cluster"][key]

    references_by_reference_genome = { }
    for taxon in go_stats.reference_genomes_ids:
        key = go_stats.taxon_label(taxon)
        references_by_reference_genome[key] = json_stats["annotations"]["references"]["all"]["by_taxon"][key]

    pmids_by_reference_genome = { }
    for taxon in go_stats.reference_genomes_ids:
        key = go_stats.taxon_label(taxon)
        pmids_by_reference_genome[key] = json_stats["annotations"]["references"]["pmids"]["by_taxon"][key]
        
    json_stats_summary = {
        "release_date" : json_stats["release_date"],
        "ontology" : ontology,
        "annotations" : {
            "total" : json_stats["annotations"]["total"],
            "total_no_pb" : json_stats_no_pb["annotations"]["total"],
            "by_evidence_cluster" : json_stats["annotations"]["by_evidence"]["cluster"],
            "by_evidence_cluster_no_pb" : json_stats_no_pb["annotations"]["by_evidence"]["cluster"],
            "by_reference_genome" : json_stats["annotations"]["by_reference_genome"]
        },
        "taxa" : {
            "total" : json_stats["annotations"]["taxa"]["total"],
            "filtered" : json_stats["annotations"]["taxa"]["filtered"],
        },
        "bioentities" : {
            "total" : json_stats["annotations"]["bioentities"]["total"],
            "total_no_pb" : json_stats_no_pb["annotations"]["bioentities"]["total"],
            "by_type_cluster" : json_stats["annotations"]["bioentities"]["by_type"]["cluster"],
            "by_type_cluster_no_pb" : json_stats_no_pb["annotations"]["bioentities"]["by_type"]["cluster"],
            "by_reference_genome" : bioentities_by_reference_genome
        },
        "references" : {
            "all" : {
                "total" : json_stats["annotations"]["references"]["all"]["total"],
                "total_no_pb" : json_stats_no_pb["annotations"]["references"]["all"]["total"],
                "by_reference_genome" : references_by_reference_genome
            }, 
            "pmids" : {
                "total" : json_stats["annotations"]["references"]["pmids"]["total"],
                "total_no_pb" : json_stats_no_pb["annotations"]["references"]["pmids"]["total"],
                "by_reference_genome" : pmids_by_reference_genome
            }
        },
    }
    go_stats.write_json(output_rep + "go-stats-summary.json", json_stats_summary)






    json_annot_changes = {
        "releases_compared" : {
            "current" : json_stats["release_date"],
            "previous" : previous_stats["release_date"]
        },
        "summary" : {
            "current" : {
                "annotations" : {
                    "total" : json_stats["annotations"]["total"],
                    "by_aspect" : json_stats["annotations"]["by_aspect"],
                    "by_evidence_cluster" : json_stats["annotations"]["by_evidence"]["cluster"],
                },
                "bioentities" : json_stats["annotations"]["bioentities"]["total"],
                "taxa" : json_stats["annotations"]["taxa"]["total"],
                "taxa_filtered" : json_stats["annotations"]["taxa"]["filtered"],
                "references" : json_stats["annotations"]["references"]["all"]["total"],
                "pmids" : json_stats["annotations"]["references"]["pmids"]["total"]
            },
            "previous" : {
                "annotations" : {
                    "total" : previous_stats["annotations"]["total"],
                    "by_aspect" : previous_stats["annotations"]["by_aspect"],
                    "by_evidence_cluster" : previous_stats["annotations"]["by_evidence"]["cluster"],
                },
                "bioentities" : previous_stats["annotations"]["bioentities"]["total"],
                "taxa" : previous_stats["annotations"]["taxa"]["total"],
                "taxa_filtered" : previous_stats["annotations"]["taxa"]["filtered"],
                "references" : previous_stats["annotations"]["references"]["all"]["total"],
                "pmids" : previous_stats["annotations"]["references"]["pmids"]["total"]
            },
            "changes" : {
                "annotations" : {
                    "total" : json_stats["annotations"]["total"] - previous_stats["annotations"]["total"],
                    "by_aspect" : minus_dict(json_stats["annotations"]["by_aspect"], previous_stats["annotations"]["by_aspect"]),
                    "by_evidence_cluster" : minus_dict(json_stats["annotations"]["by_evidence"]["cluster"], previous_stats["annotations"]["by_evidence"]["cluster"]),
                },
                "bioentities" : json_stats["annotations"]["bioentities"]["total"] - previous_stats["annotations"]["bioentities"]["total"],
                "taxa" : json_stats["annotations"]["taxa"]["total"] - previous_stats["annotations"]["taxa"]["total"],
                "taxa_filtered" : json_stats["annotations"]["taxa"]["filtered"] - previous_stats["annotations"]["taxa"]["filtered"],
                "references" : json_stats["annotations"]["references"]["all"]["total"] - previous_stats["annotations"]["references"]["all"]["total"],
                "pmids" : json_stats["annotations"]["references"]["pmids"]["total"] - previous_stats["annotations"]["references"]["pmids"]["total"]
            },
        },
        "detailed_changes" : json_annot_changes["annotations"] 
    }
    go_annotation_changes.write_json(output_rep + "go-annotation-changes.json", json_annot_changes)
    tsv_annot_changes = go_annotation_changes.create_text_report(json_annot_changes)
    go_annotation_changes.write_text(output_rep + "go-annotation-changes.tsv", tsv_annot_changes)


    json_annot_no_pb_changes = {
        "releases_compared" : {
            "current" : json_stats_no_pb["release_date"],
            "previous" : previous_stats_no_pb["release_date"]
        },
        "summary" : {
            "current" : {
                "annotations" : {
                    "total" : json_stats_no_pb["annotations"]["total"],
                    "by_aspect" : json_stats_no_pb["annotations"]["by_aspect"],
                    "by_evidence_cluster" : json_stats_no_pb["annotations"]["by_evidence"]["cluster"],
                },                
                "bioentities" : json_stats_no_pb["annotations"]["bioentities"]["total"],
                "taxa" : json_stats_no_pb["annotations"]["taxa"]["total"],
                "taxa_filtered" : json_stats_no_pb["annotations"]["taxa"]["filtered"],
                "references" : json_stats_no_pb["annotations"]["references"]["all"]["total"],
                "pmids" : json_stats_no_pb["annotations"]["references"]["pmids"]["total"]
            },
            "previous" : {
                "annotations" : {
                    "total" : previous_stats_no_pb["annotations"]["total"],
                    "by_aspect" : previous_stats_no_pb["annotations"]["by_aspect"],
                    "by_evidence_cluster" : previous_stats_no_pb["annotations"]["by_evidence"]["cluster"],
                },
                "bioentities" : previous_stats_no_pb["annotations"]["bioentities"]["total"],
                "taxa" : previous_stats_no_pb["annotations"]["taxa"]["total"],
                "taxa_filtered" : previous_stats_no_pb["annotations"]["taxa"]["filtered"],
                "references" : previous_stats_no_pb["annotations"]["references"]["all"]["total"],
                "pmids" : previous_stats_no_pb["annotations"]["references"]["pmids"]["total"]
            },
            "changes" : {
                "annotations" : {
                    "total" : json_stats_no_pb["annotations"]["total"] - previous_stats_no_pb["annotations"]["total"],
                    "by_aspect" : minus_dict(json_stats_no_pb["annotations"]["by_aspect"], previous_stats_no_pb["annotations"]["by_aspect"]),
                    "by_evidence_cluster" : minus_dict(json_stats_no_pb["annotations"]["by_evidence"]["cluster"], previous_stats_no_pb["annotations"]["by_evidence"]["cluster"]),
                },
                "bioentities" : json_stats_no_pb["annotations"]["bioentities"]["total"] - previous_stats_no_pb["annotations"]["bioentities"]["total"],
                "taxa" : json_stats_no_pb["annotations"]["taxa"]["total"] - previous_stats_no_pb["annotations"]["taxa"]["total"],
                "taxa_filtered" : json_stats_no_pb["annotations"]["taxa"]["filtered"] - previous_stats_no_pb["annotations"]["taxa"]["filtered"],
                "references" : json_stats_no_pb["annotations"]["references"]["all"]["total"] - previous_stats_no_pb["annotations"]["references"]["all"]["total"],
                "pmids" : json_stats_no_pb["annotations"]["references"]["pmids"]["total"] - previous_stats_no_pb["annotations"]["references"]["pmids"]["total"]
            }
        },
        "detailed_changes" : json_annot_no_pb_changes["annotations"] 
    }
    go_annotation_changes.write_json(output_rep + "go-annotation-changes_no_pb.json", json_annot_no_pb_changes)
    tsv_annot_changes_no_pb = go_annotation_changes.create_text_report(json_annot_no_pb_changes)
    go_annotation_changes.write_text(output_rep + "go-annotation-changes_no_pb.tsv", tsv_annot_changes_no_pb)


    print("SUCCESS.")




if __name__ == "__main__":
   main(sys.argv[1:])
   