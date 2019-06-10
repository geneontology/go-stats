# UpdateGoCAMs

import requests
import json
import datetime
from dateutil.parser import parse

import boto3
import botocore

from gzip import GzipFile
from io import BytesIO


s3_resource = boto3.resource('s3')

go_s3_bucket = s3_resource.Bucket(name="geneontology-public")
gocam_models_url = "https://api.geneontology.cloud/models"
gocam_gps_url = "https://api.geneontology.cloud/models/gp"
gocam_gos_url = "https://api.geneontology.cloud/models/go"
gocam_pmids_url = "https://api.geneontology.cloud/models/pmid"

gocam_models_key = "gocam-models.json"
gocam_gps_key = "gocam-gps.json"
gocam_gos_key = "gocam-goterms.json"
gocam_pmids_key = "gocam-pmids.json"

go_pipeline_release_url = "http://current.geneontology.org/metadata/release-date.json"

causal_count_url = "https://s3.amazonaws.com/geneontology-public/gocam/gocam-causal-count.txt"

release_date = "N/A"


def lambda_handler(event, context):
    global release_date
    release_date = get_release_date()
    
    r = requests.get(gocam_models_url)
    store_json("gocam/" + gocam_models_key, r.json())
    store_json("gocam/archive/" + release_date + "_" + gocam_models_key, r.json())

    r = requests.get(gocam_gps_url)
    store_json("gocam/" + gocam_gps_key, r.json())
    store_json("gocam/archive/" + release_date + "_" + gocam_gps_key, r.json())

    r = requests.get(gocam_gos_url)
    store_json("gocam/" + gocam_gos_key, r.json())
    store_json("gocam/archive/" + release_date + "_" + gocam_gos_key, r.json())

    r = requests.get(gocam_pmids_url)
    store_json("gocam/" + gocam_pmids_key, r.json())
    store_json("gocam/archive/" + release_date + "_" + gocam_pmids_key, r.json())

#    temporary()

    return 'success'
    
def temporary():
    r = requests.get(gocam_models_url)
    model_json = r.json()

    new_model_json = []
    
    r = requests.get(causal_count_url)
    for line in r.text.split("\n"):
        if len(line) == 0:
            continue
        key = line.split("\t")[0]
        key = key[0 : key.index(".ttl")]

        for elt in model_json:
            if key in elt['gocam']:
                new_model_json.append(elt)
                break
        
    print("Control: " , str(len(model_json)) , str(len(new_model_json)))
    store_json("gocam/gocam-models-reordered.json", new_model_json)
    
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