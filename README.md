# GO-stats for the GO release pipeline
Compute statistics and changes for both the GO ontology and annotations at every release and snapshot.

The following details each folder of this repository:

## libraries

### go-stats
This is the python package that is used to compute statistics over go annotations. You can [read more here](libraries/go-stats/README.md).

## General GO stats file access for the current release
* [go-stats-summary.json](http://current.geneontology.org/release_stats/go-stats-summary.json): summary statistics
* [aggregated-go-stats-summaries.json](http://current.geneontology.org/release_stats/aggregated-go-stats-summaries.json): summary statistics for all [GO releases stored in Zenodo](https://zenodo.org/record/3477535)
* [go-stats.json](http://current.geneontology.org/release_stats/go-stats.json): detailed statistics
* [go-stats-no-pb.json](http://current.geneontology.org/release_stats/go-stats-no-pb.json): detailed statistics (excluding direct annotation to *p*rotein *b*inding)
* [go-ontology-changes.json](http://current.geneontology.org/release_stats/go-ontology-changes.json): changes in the ontology since the last release
* [go-ontology-changes.tsv](http://current.geneontology.org/release_stats/go-ontology-changes.tsv)
* [go-annotation-changes.json](http://current.geneontology.org/release_stats/go-annotation-changes.json): changes in the annotations since the last release
* [go-annotation-changes.tsv](http://current.geneontology.org/release_stats/go-annotation-changes.tsv)

## General GO-CAM files for the current release
* [gocam-models.json](https://geneontology-public.s3.amazonaws.com/gocam/gocam-models.json): detailed list of models
* [gocam-pmids.json](https://geneontology-public.s3.amazonaws.com/gocam/gocam-pmids.json): list of articles/references per model
* [gocam-gps.json](https://geneontology-public.s3.amazonaws.com/gocam/gocam-gps.json): list of gene products permodel
* [gocam-goterms](https://geneontology-public.s3.amazonaws.com/gocam/gocam-goterms.json): list of GO terms per model

# GO-stats for the experimental AWS pipeline
## GO Notification System
The code checks the release date in the main pipeline (http://current.geneontology.org/metadata/release-date.json) and when the date changes, it triggers a secondary pipeline by publishing a message in a specific topic (SNS) and update the release date on the secondary pipeline

## GO Store Changes
The code loads the GO obo file (http://purl.obolibrary.org/obo/go.obo) and compare the terms of the new release to the previous most recent release.

## GO Update Statistics
The code send queries to GOLr to fetch statistics about the GO annotations (e.g. per aspect, per species, per group etc)

## GO Update GO-CAMs
The code compute a number of views over the GO-CAMs data (e.g. models, gene products, go terms, etc) using the GO SPARQL endpoint.
