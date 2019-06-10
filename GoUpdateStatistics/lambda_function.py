# GO Update Statistics

import requests
import json
import datetime
from dateutil.parser import parse

from gzip import GzipFile
from io import BytesIO

import boto3
import botocore

#now = datetime.datetime.now()
#formated_now = now.strftime("%Y-%m-%d")

s3_resource = boto3.resource('s3')

go_s3_bucket = s3_resource.Bucket(name="geneontology-public")
go_all_terms_key = "go-terms-aspect.json"
go_stats_key= "go-stats"
go_meta_key = "go-meta.json"
go_most_annotated_gps_key= "go-annotated-gps.json"

golr_fetch_all_go_classes_url = 'http://golr-aux.geneontology.io/solr/select?wt=json&fq=document_category:"ontology_class"&fq=id:GO\:*&fq=idspace:"GO"&fl=source,annotation_class,is_obsolete&rows=500000&q=*:*&facet=true&facet.field=source&facet.limit=1000000&facet.mincount=1'
golr_fetch_annotations_url = 'http://golr-aux.geneontology.io/solr/select?fq=document_category:"annotation"&q=*:*&start=0&rows=10&wt=json&facet=true&facet.field=taxon&facet.field=aspect&facet.field=evidence_type&facet.field=assigned_by&facet.field=bioentity&facet.limit=10000000&facet.mincount=1'

#go_doi_url = "https://zenodo.org/api/records/1205166"
go_pipeline_release_url = "http://current.geneontology.org/metadata/release-date.json"


release_date = "N/A"

def lambda_handler(event, context):
    global release_date
    release_date = get_release_date()

    r = requests.get(golr_fetch_all_go_classes_url)
    all_terms = r.json()
    
    r = requests.get(golr_fetch_annotations_url)
    all_annotations = r.json()
    
    save_stats(all_terms, all_annotations)
    save_terms_mapping(all_terms)
    
    return 'success'

def save_stats(all_terms, all_annotations):
    
    # 1 - SAVING STATS
    terms = 0
    obsoleted = 0
    for doc in all_terms['response']['docs']:
        if doc['is_obsolete'] == False:
            terms += 1
        else:
            obsoleted += 1

    annotations_taxon_count = { }
    facets = all_annotations['facet_counts']['facet_fields']['taxon']
    for i in range(0, len(facets), 2):
        annotations_taxon_count[facets[i]] = facets[i + 1]

    annotations_aspect_count = { }
    facets = all_annotations['facet_counts']['facet_fields']['aspect']
    for i in range(0, len(facets), 2):
        annotations_aspect_count[facets[i]] = facets[i + 1]

    annotations_evidence_count = { }
    facets = all_annotations['facet_counts']['facet_fields']['evidence_type']
    for i in range(0, len(facets), 2):
        annotations_evidence_count[facets[i]] = facets[i + 1]

    annotations_assigned_count = { }
    facets = all_annotations['facet_counts']['facet_fields']['assigned_by']
    for i in range(0, len(facets), 2):
        annotations_assigned_count[facets[i]] = facets[i + 1]

    annotations_bioentity_count = { }
    facets = all_annotations['facet_counts']['facet_fields']['bioentity']
    for i in range(0, len(facets), 2):
        annotations_bioentity_count[facets[i]] = facets[i + 1]

    go_stats = { 
        "release_date": release_date,
        "terms": {
            "all": terms + obsoleted, "valid": terms, "obsoleted": obsoleted
        },
        "annotations": {
            "all": all_annotations['response']['numFound'],
            "by_aspect": annotations_aspect_count,
            "by_evidence": annotations_evidence_count,
            "species": len(annotations_taxon_count),
            "by_species": annotations_taxon_count,
            "by_group": annotations_assigned_count,
            "geneproducts": len(annotations_bioentity_count)
        }
    }
    store_json(go_stats_key + ".json", go_stats)
    store_json("archive/" + release_date + "_" + go_stats_key + ".json", go_stats)
    
    txtreport = "GENE ONTOLOGY STATISTICS\nrelease_date\t" + release_date + "\ngeneproducts\t" + str(len(annotations_bioentity_count)) + "\nspecies\t" + str(len(annotations_taxon_count))

    txtreport += "\n\nTERMS\nall\t" + str(terms + obsoleted) + "\nvalid\t" + str(terms) + "\nobsoleted\t" + str(obsoleted) + "\n"

    txtreport += "\nANNOTATIONS\nall\t" + str(all_annotations['response']['numFound'])
    for key, value in annotations_aspect_count.items():
        txtreport += "\n" + key + "\t" + str(value)

    txtreport += "\n\nANNOTATIONS BY EVIDENCE"
    for key, value in annotations_evidence_count.items():
        txtreport += "\n" + key + "\t" + str(value)

    txtreport += "\n\nANNOTATIONS BY SPECIES"
    for key, value in annotations_taxon_count.items():
        txtreport += "\n" + key + "\t" + str(value)

    txtreport += "\n\nANNOTATIONS BY GROUP"
    for key, value in annotations_assigned_count.items():
        txtreport += "\n" + key + "\t" + str(value)
        
    store_text(go_stats_key + ".tsv", txtreport)
    store_text("archive/" + release_date + "_" + go_stats_key + ".tsv", txtreport)
    
    
    # 2 - SAVING META DATA
    go_meta = {
        "release_date": release_date,
        "terms": terms,
        "annotations": all_annotations['response']['numFound'],
        "species": len(annotations_taxon_count),
        "geneproducts": len(annotations_bioentity_count)
    }
    store_json(go_meta_key, go_meta)
    store_json("archive/" + release_date + "_" + go_meta_key, go_meta)
        
    print(go_meta)

    store_json(go_most_annotated_gps_key, annotations_bioentity_count)
    store_json("archive/" + release_date + "_" + go_most_annotated_gps_key, annotations_bioentity_count)

    
def save_terms_mapping(all_terms):
    for doc in all_terms['response']['docs']:
        doc.pop('is_obsolete', None)

    # creating the results divided by aspect        
    mapping = { }
    for term in all_terms['response']['docs']:
        if 'source' not in term: # often, obsoleted terms have no source
            print("Term " , term , " has no source !")
            continue
        if term['source'] not in mapping:
            mapping[term['source']] = []
        mapping[term['source']].append(term['annotation_class'])
    
    store_json(go_all_terms_key, mapping)
    store_json("archive/" + release_date + "_" + go_all_terms_key, mapping)
 

def store_text(key, content):
    # Storing a compressed version of the text file
    gz_body = BytesIO()
    gz = GzipFile(None, 'wb', 9, gz_body)
    gz.write(content.encode('utf-8'))
    gz.close()    

    go_s3_bucket.put_object(
        Key=key,  
        ContentType='text/plain', 
        ContentEncoding='gzip', 
        Body=gz_body.getvalue()
    )    
    
def store_json(key, content):
    # Storing a compressed version of the json file
    gz_body = BytesIO()
    gz = GzipFile(None, 'wb', 9, gz_body)
    gz.write(json.dumps(content).encode('utf-8'))
    gz.close()    

    go_s3_bucket.put_object(
        Key=key,  
        ContentType='application/json', 
        ContentEncoding='gzip', 
        Body=gz_body.getvalue()
    )    
 
def get_release_date():
    r = requests.get(go_pipeline_release_url)
    return r.json()['date']
