# Changes in Gene Ontology Statistics

This document keeps track of the changes in the statistics files provided by the Gene Ontology in the release_stats/ folder.
Example: [http://current.geneontology.org/release_stats/index.html](http://current.geneontology.org/release_stats/index.html)

## Update June 2020

This update affects statistics files starting July 2020.

### go-stats, go-stats-no-pb and go-stats-summary
* added annotations.total_pb : the number of annotations to protein binding term
* annotations.by_qualifier : the number of annotations by qualifier (eg contributes_to, colocalizes_with, not)
* annotations.by_model_organism.{taxon}.by_qualifier: the number of annotations by qualifier for the given taxon

### List of PMID for each release
* file go-pmids.tsv with PMID | Nb annotations
* file GO.ui with only PMID without prefixes (used to update PubMed references to GO)

### go-annotation-changes



