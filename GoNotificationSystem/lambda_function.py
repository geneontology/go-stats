# GO Notification System

import requests
import datetime
from dateutil.parser import parse

import boto3
import botocore

s3_resource = boto3.resource('s3')

go_s3_bucket = s3_resource.Bucket(name="geneontology-public")
go_last_release_date_key = "go-last-release-date"
#go_doi_url = "https://zenodo.org/api/records/1205166"
go_pipeline_release_url = "http://current.geneontology.org/metadata/release-date.json"

sns_go_release_topic = 'arn:aws:sns:us-east-1:828201240123:go-new-release'

def lambda_handler(event, context):
    gorelease = get_release_date()
    jsdate = gorelease
    s3date = current_date()

    print("release (json): ", jsdate)
    print("release (s3):   ", s3date)

    if s3date is None or jsdate != s3date:
        update_release_date(jsdate)
        trigger_new_release(jsdate)
        return "triggering new release"
    
    return "already up to date"
    
def transform_date_and_time(date):
    parsed_date = parse(date) 
    return parsed_date.strftime("%c")
    
def transform_date(date):
    parsed_date = parse(date) 
    return parsed_date.strftime("%m/%d/%Y")

def release_date(json):
    """
    Returns the date from the json content in argument
    """
    return json['updated']
    
def current_date():
    """
    Returns the date currently stored in S3
    """
    try:
        s3_object = go_s3_bucket.Object(go_last_release_date_key)
        body = s3_object.get()['Body']
        cd = body.read()
        return cd.decode("utf-8")
    except botocore.exceptions.ClientError as e:    
        print("Error: ", e)
        return None
    
def update_release_date(date):
    """
    Update the S3 object with the new release date
    """
    go_s3_bucket.put_object(Key=go_last_release_date_key, Body=date)



sns_client = boto3.client("sns")

def trigger_new_release(date):
    print("Triggering new release...")
    
    message = sns_client.publish(
        TopicArn=sns_go_release_topic,
        Message="Dear Subscriber,\n\nGene Ontology has published a new release on " + date + ":" + 
                                "\n- GO Ontology can be downloaded at http://purl.obolibrary.org/obo/go.obo" +
                                "\n- Changes in this release are available in both TSV format: https://s3.amazonaws.com/geneontology-public/go-last-changes.tsv and JSON format: https://s3.amazonaws.com/geneontology-public/go-last-changes.json" +
                                "\n- Statistics can also be viewed in both TSV format: https://s3.amazonaws.com/geneontology-public/go-stats.tsv and JSON format: https://s3.amazonaws.com/geneontology-public/go-stats.json\n" +
                                "\nVisit http://geneontology.org to learn more !\n\nThe GO Consortium",
        Subject= "Gene Ontology New Release (" + date + ")"
    )
    
    print("response: ", message)
    
def get_release_date():
    r = requests.get(go_pipeline_release_url)
    return r.json()['date']