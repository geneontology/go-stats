# go-stats python tool

Generate statistics for a GO release based on a GOLr instance

## Install
> pip install -r requirements.txt

## Usage
```
import go_stats

stats = go_stats.compute_stats('http://golr-aux.geneontology.io/solr/')
print(stats)
```


Note: current GOLr instance is [http://golr-aux.geneontology.io/solr/](http://golr-aux.geneontology.io/solr/)