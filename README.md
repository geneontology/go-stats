# GO-Stats
Compute statistics and changes for both the GO ontology and annotations at every release.

## GO Notification System
The code checks the release date in the main pipeline (http://current.geneontology.org/metadata/release-date.json) and when the date changes, it triggers a secondary pipeline by publishing a message in a specific topic (SNS) and update the release date on the secondary pipeline

## GO Store Changes
The code loads the GO obo file and compare the terms of the new release to the previously most recent release.

## GO Update Statistics
The code send queries to GOLr to fetch statistics about the GO annotations (e.g. per aspect, per species, per group etc)

