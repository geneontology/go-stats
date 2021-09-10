# Changes in Gene Ontology Statistics

This document keeps track of the changes in the statistics files provided by the Gene Ontology in the release_stats/ folder.
Example: [http://current.geneontology.org/release_stats/index.html](http://current.geneontology.org/release_stats/index.html)

## Update July 2020

This update affects statistics files starting August 2020.

### go-stats, go-stats-no-pb and go-stats-summary
* added annotations.total_pb : the number of annotations to protein binding term (only in go-stats-summary as requiring both go-stats and go-stats-no-pb)
* annotations.by_qualifier : the number of annotations by qualifier (eg contributes_to, colocalizes_with, not)
* annotations.by_model_organism.{taxon}.by_qualifier: the number of annotations by qualifier for the given taxon

### List of PMID for each release
* go-references.tsv : table of REFERENCES | Nb annotations
* go-pmids.tsv : table of PMID | Nb annotations
* GO.ui : table containing only PMIDs without their prefixes (used to update PubMed references to GO)

### go-annotation-changes
* summary.changes.pmids.added/removed : show the number of pmids added / removed (in previous releases, those values were set to 0)
* detailed_changes.references.all.added : detail the list of references newly annotated (they were not used in previous release)
* detailed_changes.references.all.removed : detail the list of references present in the previous release but not in the new/current release
* detailed_changes.references.pmids.added : detail the list of publications newly annotated (were not used in previous release)
* detailed_changes.references.pmids.removed : detail the list of publications present in the previous release but not present in the new/current release

Note: go-annotation-changes.tsv should also reflect those changes that primarily occurs in go-annotation-changes.json

## Update September 2021

This update affects statistics files starting October 2021.

### go-stats, go-stats-no-pb, go-stats-summary and go-annotation-changes
* gocams.all : the number of all GO-CAM models in RDF triplestore
* gocams.causal : the number of all GO-CAM models having at least 3 activities connected through causal relationships in RDF triplestore