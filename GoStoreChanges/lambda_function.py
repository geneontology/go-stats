# GO Store Changes
# sudo yum install python34-setuptools
# sudo yum install python34-devel
# pip3 install pyyaml -t .
# sudo python3 -m pip install pyyaml

from obo_parser import OBO_Parser, TermState

import requests
import json
import yaml
from datetime import date, time, datetime
from dateutil.parser import parse

from gzip import GzipFile
from io import BytesIO

import boto3
import botocore


go_s3_bucket_name = "geneontology-public"
go_obo_key = "go.obo"
go_obo_url = "http://purl.obolibrary.org/obo/go.obo"

#go_doi_url = "https://zenodo.org/api/records/1205166"
go_pipeline_release_url = "http://current.geneontology.org/metadata/release-date.json"

s3_resource = boto3.resource('s3')
go_s3_bucket = s3_resource.Bucket(name=go_s3_bucket_name)

release_date = "N/A"
last_obo = None
last_date = None

def lambda_handler(event, context):
    global release_date
    release_date = get_release_date()
    
    global last_obo
    last_obo = get_last_obo()
    
    store_current_go_obo()
    save_changes()
    
    return 'success'
    
def get_last_obo():
    global last_date
    last_date = datetime.min
    last_obo = None
    for obj in go_s3_bucket.objects.all():
        key = obj.key
        if "go.obo" not in key:
            continue
        date = obj.get()['LastModified'].replace(tzinfo=None)
        if date > last_date:
            last_date = date
            last_obo = key
            
    last_date = last_date.strftime("%Y-%m-%d")
    print("Last GO ontology detected: " , last_obo , " (" , last_date , ")")    
    return last_obo
    
def store_current_go_obo():
    r = requests.get(go_obo_url)
    content = r.text
    store_text("archive/" + release_date + "_" + go_obo_key, content)


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
    

def flattern(A):
    rt = []
    for i in A:
        if isinstance(i,list): rt.extend(flattern(i))
        else: rt.append(i)
    return rt

def save_changes():

    # The new published OBO archive
    print("Loading current GO ontology...")
    go_obo_url = "http://purl.obolibrary.org/obo/go.obo"
    newgo = OBO_Parser(requests.get(go_obo_url).text)

# TO OVERRIDE COMPARISON
#    last_date = "2019-02-01"
#    last_obo = "archive/" + last_date + "_go.obo"
    # The last published OBO archive
    print("Loading last GO ontology (" , last_obo , ") ...")
    old_go_obo_url = "https://s3.amazonaws.com/" + go_s3_bucket_name + "/" + last_obo
    oldgo = OBO_Parser(requests.get(old_go_obo_url).text)
    
    
    # New GO Terms
    added = { }
    added_count = 0
    for id, newterm in newgo.get_terms().items():                                                                                                                                                                                
        if not oldgo.has_term(id):
            if newterm.namespace not in added:
                added[newterm.namespace] = []
            added[newterm.namespace].append({ "id": id, "name": newterm.name})
            added_count += 1
            
    print(str(added_count) + " terms added since last revision")

    # Removed GO Terms
    removed = { }
    removed_count = 0
    for id, oldterm in oldgo.get_terms().items():                                                                                                                                                                                  
        if not newgo.has_term(id):
            if oldterm.namespace not in removed:
                removed[oldterm.namespace] = []
            removed[oldterm.namespace].append({ "id": id, "name": oldterm.name})
            removed_count += 1
    print(str(removed_count) + " terms removed since last revision")
    
    # Existing GO Terms that were modified
    changes = { }
    modified_count = 0
    for id, newterm in newgo.get_terms().items():
        if oldgo.has_term(id):                                                                                                                                                                            
            oldterm = oldgo.get_term(id)
            if not newterm.equals(oldterm):
                if newterm.namespace not in changes:
                    changes[newterm.namespace] = []
                    
                reasons = {}
                for key, reason in newterm.explain_differences(oldterm).items():
                    reasons[key] = { "current" : reason['current'], "previous" : reason['previous'] }
                changes[newterm.namespace].append({ "id" : id, "name": newterm.name , "changes": reasons })
                modified_count += 1
    print(str(modified_count) + " terms modified since last revision")
 
    report = { }
    report["releases"] = {
                "current" : { "date": release_date, "version" : newgo.header['data-version'], "format" : newgo.header['format-version'] },
                "previous" : { "date" : last_date, "version" : oldgo.header['data-version'], "format" : oldgo.header['format-version'] }
            }
    report["summary"] = {
        "added" : added_count,
        "removed" : removed_count,
        "modified" : modified_count
    }
    report["added"] = added
    report["removed"] = removed
    report["modified"] = changes
    store_json("go-last-changes.json", report)
    store_json("archive/" + release_date + "_changes.json", report)


    # Creating TSV version of the JSON report
    txtreport = "CHANGES IN GO BETWEEN " + report["releases"]["current"]["version"] + " (" + release_date + ") and " + report["releases"]["previous"]["version"] + " (" + last_date + ")\n"

    txtreport += "\nTERMS ADDED\t" + str(added_count) + "\n"
    for aspect in report["added"]:
        for term in report["added"][aspect]:
            txtreport += aspect + "\t" + term["id"] + "\t" + term["name"] + "\n"

    txtreport += "\nTERMS REMOVED\t" + str(removed_count) + "\n"
    for aspect in report["removed"]:
        for term in report["removed"][aspect]:
            txtreport += aspect + "\t" + term["id"] + "\t" + term["name"] + "\n"
        
    txtreport += "\nTERMS MODIFIED\t" + str(modified_count) + "\n"
    for aspect in report["modified"]:
        for term in report["modified"][aspect]:
            txtreport += aspect + "\t" + term["id"] + "\t" + term["name"]
            for change in term["changes"]:
                curr = term["changes"][change]["current"]
                if not isinstance(curr, str):
                    curr = ", ".join(map(str, curr))
                
                prev = term["changes"][change]["previous"]
                if not isinstance(prev, str):
                    prev = ", ".join(map(str, prev))
                txtreport += "\t" + change + " (current: " + curr + " previous: " + prev + ")"
            txtreport += "\n"

    store_text("go-last-changes.tsv", txtreport)
    store_text("archive/" + release_date + "_changes.tsv", txtreport)


def get_release_date():
    r = requests.get(go_pipeline_release_url)
    return r.json()['date']
    