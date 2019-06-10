# GO-Stats
Compute statistics and changes for both the GO ontology and annotations at every release.

## GO Notification System
The code checks the release date in the main pipeline (http://current.geneontology.org/metadata/release-date.json) and when the date changes, it triggers a secondary pipeline by publishing a message in a specific topic (SNS) and update the release date on the secondary pipeline

## GO Store Changes
The code loads the GO obo file (http://purl.obolibrary.org/obo/go.obo) and compare the terms of the new release to the previous most recent release.

## GO Update Statistics
The code send queries to GOLr to fetch statistics about the GO annotations (e.g. per aspect, per species, per group etc)

## File Access
* [go-meta.json](https://geneontology-public.s3.amazonaws.com/go-meta.json): basic statistics
* [go-stats.json](https://geneontology-public.s3.amazonaws.com/go-stats.json): detailed statistics
* [go-last-changes.json](https://geneontology-public.s3.amazonaws.com/go-last-changes.json): changes in the ontology
* [go-terms-aspect.json](https://geneontology-public.s3.amazonaws.com/go-terms-aspect.json): terms per aspect (BP/MF/CC)
* [go-annotated-gps.json](https://geneontology-public.s3.amazonaws.com/go-annotated-gps.json): annotations per gene
