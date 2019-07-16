# go-stats python tool

Generate statistics for a GO release based on a GOLr instance

## Install
> pip install go-stats

## Usage
```
import go_stats

stats = go_stats.compute_stats('http://golr-aux.geneontology.io/solr/')

print(stats)

go_stats.write_json("stats.json", stats)
```


Note: current GOLr instance is [http://golr-aux.geneontology.io/solr/](http://golr-aux.geneontology.io/solr/)