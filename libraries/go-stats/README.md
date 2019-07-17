# go-stats python tool

Generate statistics for a GO release based on a GOLr instance

## Install
> pip install go-stats

## Usage
```
import go_stats

json_stats = go_stats.compute_stats('http://golr-aux.geneontology.io/solr/')
go_stats.write_json("stats.json", json_stats)

tsv_stats = go_stats.create_text_report(json_stats)
go_stats.write_text("stats.tsv", tsv_stats)

json_meta = go_stats.create_meta(json_stats)
go_stats.write_json("meta.json", json_meta)
```


Note: current GOLr instance is [http://golr-aux.geneontology.io/solr/](http://golr-aux.geneontology.io/solr/)