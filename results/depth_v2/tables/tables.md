# Results tables

Generated from `results\depth_v2`.

## ml100k  (1,349 items)

### cost

| family     | reranker  | repeats | ndcg   | recall | exposure_parity | cpu_once  | cpu_per_request | spread_once | spread_per_request | cpu_train | cpu_rerank_setup | cpu_retrieve_score | cpu_retrieve_select | cpu_rerank |
|------------|-----------|---------|--------|--------|-----------------|-----------|-----------------|-------------|--------------------|-----------|------------------|--------------------|---------------------|------------|
| popularity | none      | 15      | 0.0527 | 0.1050 | 1.1855          | 1.634e-04 | 1.097e-04       | 19.1%       | 61.5%              | 1.634e-04 | 0.000e+00        | 1.116e-02          | 1.078e-02           | 0.000e+00  |
| als        | none      | 15      | 0.0526 | 0.1150 | 0.8280          | 5.781e+00 | 1.580e-04       | 9.2%        | 103.8%             | 5.781e+00 | 0.000e+00        | 1.953e-02          | 1.008e-02           | 0.000e+00  |
| itemknn    | none      | 15      | 0.0448 | 0.1000 | 1.1535          | 1.953e-01 | 1.841e-04       | 8.0%        | 40.6%              | 1.953e-01 | 0.000e+00        | 2.734e-02          | 1.042e-02           | 0.000e+00  |
| popularity | quota_mmr | 15      | 0.0551 | 0.1150 | 0.2475          | 8.610e-02 | 2.769e-03       | 4.6%        | 642.9%             | 1.634e-04 | 8.594e-02        | 1.202e-02          | 1.078e-02           | 5.312e-01  |
| itemknn    | quota_mmr | 15      | 0.0529 | 0.1200 | 0.2465          | 2.852e-01 | 2.850e-03       | 6.8%        | 619.5%             | 1.953e-01 | 8.984e-02        | 2.734e-02          | 1.042e-02           | 5.312e-01  |
| als        | quota_mmr | 15      | 0.0477 | 0.1050 | 0.2560          | 5.949e+00 | 3.397e-03       | 7.4%        | 570.1%             | 5.859e+00 | 8.984e-02        | 1.786e-02          | 1.008e-02           | 6.562e-01  |

### breakeven

| a                    | b                    | n_requests | lo        | hi         | replicates_crossing | repeats | stable | cheaper_below        | cheaper_above     |
|----------------------|----------------------|------------|-----------|------------|---------------------|---------|--------|----------------------|-------------------|
| popularity           | popularity+quota_mmr | --         | --        | --         | 0.0%                | 15      | no     | popularity           | popularity        |
| popularity           | itemknn              | --         | --        | --         | 0.0%                | 15      | no     | popularity           | popularity        |
| popularity           | itemknn+quota_mmr    | --         | --        | --         | 0.0%                | 15      | no     | popularity           | popularity        |
| popularity           | als                  | 18,942,592 | 1,238,013 | 19,037,055 | 0.2%                | 15      | no     | popularity           | als               |
| popularity           | als+quota_mmr        | --         | --        | --         | 0.0%                | 15      | no     | popularity           | popularity        |
| popularity+quota_mmr | itemknn              | 42         | 16        | 104        | 100.0%              | 15      | yes    | popularity+quota_mmr | itemknn           |
| popularity+quota_mmr | itemknn+quota_mmr    | 50         | 35        | 154        | 29.1%               | 15      | no     | popularity+quota_mmr | itemknn+quota_mmr |
| popularity+quota_mmr | als                  | 2,211      | 826       | 5,388      | 100.0%              | 15      | yes    | popularity+quota_mmr | als               |
| popularity+quota_mmr | als+quota_mmr        | 1,828      | 1,106     | 6,215      | 29.1%               | 15      | no     | popularity+quota_mmr | als+quota_mmr     |
| itemknn              | itemknn+quota_mmr    | --         | --        | --         | 0.0%                | 15      | no     | itemknn              | itemknn           |
| itemknn              | als                  | 191,761    | 80,974    | 1,259,771  | 98.0%               | 15      | yes    | itemknn              | als               |
| itemknn              | als+quota_mmr        | --         | --        | --         | 0.0%                | 15      | no     | itemknn              | itemknn           |
| itemknn+quota_mmr    | als                  | 2,047      | 778       | 4,854      | 100.0%              | 15      | yes    | itemknn+quota_mmr    | als               |
| itemknn+quota_mmr    | als+quota_mmr        | 1,663      | 1,027     | 4,818      | 29.1%               | 15      | no     | itemknn+quota_mmr    | als+quota_mmr     |
| als                  | als+quota_mmr        | 5          | 1         | 23         | 2.5%                | 15      | no     | als+quota_mmr        | als               |

### rerank_share

| family     | reranker  | cpu_rerank | cpu_serving_total | rerank_share_of_serving | cpu_rerank_setup | serving_multiplier |
|------------|-----------|------------|-------------------|-------------------------|------------------|--------------------|
| popularity | quota_mmr | 5.312e-01  | 5.538e-01         | 95.8%                   | 8.594e-02        | 23.9185            |
| itemknn    | quota_mmr | 5.312e-01  | 5.701e-01         | 93.2%                   | 8.984e-02        | 14.6829            |
| als        | quota_mmr | 6.562e-01  | 6.794e-01         | 96.4%                   | 8.984e-02        | 28.0676            |

### rerankers

| family     | reranker  | repeats | cpu_rerank_per_request | cpu_serving_per_request | rerank_share | ndcg   | exposure_parity | recall | time_bounded | cost_vs_cheapest |
|------------|-----------|---------|------------------------|-------------------------|--------------|--------|-----------------|--------|--------------|------------------|
| als        | quota_mmr | 15      | 3.281e-03              | 3.397e-03               | 96.4%        | 0.0477 | 0.2560          | 0.1050 | no           | 1.0000           |
| itemknn    | quota_mmr | 15      | 2.656e-03              | 2.850e-03               | 93.2%        | 0.0529 | 0.2465          | 0.1200 | no           | 1.0000           |
| popularity | quota_mmr | 15      | 2.656e-03              | 2.769e-03               | 95.8%        | 0.0551 | 0.2475          | 0.1150 | no           | 1.0000           |

### frontier

| n_requests | frontier                         | dominated                                      | cheapest   | most_accurate        |
|------------|----------------------------------|------------------------------------------------|------------|----------------------|
| 1          | popularity, popularity+quota_mmr | als+quota_mmr, als, itemknn+quota_mmr, itemknn | popularity | popularity+quota_mmr |
| 10         | popularity, popularity+quota_mmr | als+quota_mmr, als, itemknn+quota_mmr, itemknn | popularity | popularity+quota_mmr |
| 100        | popularity, popularity+quota_mmr | als+quota_mmr, als, itemknn+quota_mmr, itemknn | popularity | popularity+quota_mmr |
| 1,000      | popularity, popularity+quota_mmr | als+quota_mmr, als, itemknn+quota_mmr, itemknn | popularity | popularity+quota_mmr |
| 10,000     | popularity, popularity+quota_mmr | als+quota_mmr, itemknn+quota_mmr, als, itemknn | popularity | popularity+quota_mmr |
| 100,000    | popularity, popularity+quota_mmr | als+quota_mmr, itemknn+quota_mmr, als, itemknn | popularity | popularity+quota_mmr |
| 1,000,000  | popularity, popularity+quota_mmr | als+quota_mmr, itemknn+quota_mmr, itemknn, als | popularity | popularity+quota_mmr |

### regimes

| n_requests | cheapest   | cost      | unit        | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|------------|------------|-----------|-------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| 1          | popularity | 2.731e-04 | cpu_seconds | 0.000273        | 0.0889                    | 0.195        | 0.288                  | 6        | 6                  |
| 10         | popularity | 1.260e-03 | cpu_seconds | 0.00126         | 0.114                     | 0.197        | 0.314                  | 6        | 6                  |
| 100        | popularity | 1.113e-02 | cpu_seconds | 0.0111          | 0.363                     | 0.214        | 0.57                   | 6        | 6                  |
| 1,000      | popularity | 1.098e-01 | cpu_seconds | 0.11            | 3                         | 0.379        | 3                      | 6        | 9                  |
| 10,000     | popularity | 1.097e+00 | cpu_seconds | 1               | 28                        | 2            | 29                     | 7        | 40                 |
| 100,000    | popularity | 1.097e+01 | cpu_seconds | 11              | 277                       | 19           | 285                    | 22       | 346                |
| 1,000,000  | popularity | 1.097e+02 | cpu_seconds | 110             | 2,769                     | 184          | 2,851                  | 164      | 3,403              |

### retraining

| retrain_every | n_requests | cheapest   | training_events | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|---------------|------------|------------|-----------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| never         | 100,000    | popularity | 1               | 11              | 277                       | 19           | 285                    | 22       | 346                |
| 1,000,000     | 100,000    | popularity | 1               | 11              | 277                       | 19           | 285                    | 22       | 346                |
| 100,000       | 100,000    | popularity | 2               | 11              | 277                       | 19           | 286                    | 27       | 352                |
| 10,000        | 100,000    | popularity | 11              | 11              | 278                       | 21           | 288                    | 79       | 405                |
| 1,000         | 100,000    | popularity | 101             | 11              | 286                       | 38           | 314                    | 600      | 941                |
| 100           | 100,000    | popularity | 1,001           | 11              | 363                       | 214          | 570                    | 5,803    | 6,295              |
