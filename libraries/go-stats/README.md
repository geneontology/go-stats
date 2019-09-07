# go-stats python tool

Generate statistics for a GO release based on a GOLr instance

## Install
> pip install go-stats

## Content
This package contains several scripts used to compute both statistics and changes of Gene Ontology releases.

* go_stats.py: compute the stats for a given release
* go_ontology_changes.py: compute the changes for two releases (using OBO files)
* go_annotation_changes.py: compute the changes for two releases (using 1 GOLr instance and previously computed stats)
* go_refine_stats.py: used to compute the first stats, including ontology stats
* go_reports.py: used to compute all stats and changes between two releases

## Usage
```
import go_stats

release_date = '2019-09-01'
include_protein_binding = False

json_stats = go_stats.compute_stats('http://golr-aux.geneontology.io/solr/', release_date, include_protein_binding)
go_stats.write_json("stats.json", json_stats)

tsv_stats = go_stats.create_text_report(json_stats)
go_stats.write_text("stats.tsv", tsv_stats)

json_meta = go_stats.create_meta(json_stats)
go_stats.write_json("meta.json", json_meta)
```


## Notes
* current GOLr instance is [http://golr-aux.geneontology.io/solr/](http://golr-aux.geneontology.io/solr/)
* older GOLr archives are stored in zenodo both as [full archive](https://zenodo.org/record/3267438#.XXN5spNKg4M) and [reference archive](https://zenodo.org/record/3267437#.XXN5spNKg4M) which can be used with [bdbags](https://geneontology.github.io/docs/tools-guide/#programmatic-download-bdbag) to retrieve only the golr database dump (golr-index-contents.tgz)
* several scripts will be refactored and simplified (e.g. go_refine_stats.py is used to compute the first set of stats files, then for the next releases one can use go_reports.py)