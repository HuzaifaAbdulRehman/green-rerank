# Results tables

Generated from `results\depth`.

## ml100k  (1,349 items)

### cost

| family     | reranker  | repeats | ndcg   | recall | exposure_parity | cpu_once  | cpu_per_request | spread_once | spread_per_request | cpu_train | cpu_rerank_setup | cpu_retrieve_score | cpu_retrieve_select | cpu_rerank |
|------------|-----------|---------|--------|--------|-----------------|-----------|-----------------|-------------|--------------------|-----------|------------------|--------------------|---------------------|------------|
| popularity | none      | 15      | 0.0527 | 0.1050 | 1.1855          | 1.593e-04 | 1.083e-04       | 6.7%        | 68.5%              | 1.593e-04 | 0.000e+00        | 1.157e-02          | 1.008e-02           | 0.000e+00  |
| als        | none      | 15      | 0.0526 | 0.1150 | 0.8280          | 5.625e+00 | 1.411e-04       | 12.8%       | 114.2%             | 5.625e+00 | 0.000e+00        | 1.953e-02          | 9.766e-03           | 0.000e+00  |
| itemknn    | none      | 15      | 0.0448 | 0.1000 | 1.1535          | 1.953e-01 | 1.839e-04       | 8.0%        | 34.2%              | 1.953e-01 | 0.000e+00        | 2.734e-02          | 9.766e-03           | 0.000e+00  |
| popularity | quota_mmr | 15      | 0.0531 | 0.1050 | 0.2565          | 8.610e-02 | 2.614e-03       | 4.5%        | 639.3%             | 1.599e-04 | 8.594e-02        | 1.202e-02          | 9.766e-03           | 5.000e-01  |
| itemknn    | quota_mmr | 15      | 0.0511 | 0.1050 | 0.2470          | 2.812e-01 | 2.843e-03       | 6.9%        | 623.9%             | 1.953e-01 | 8.984e-02        | 2.604e-02          | 9.766e-03           | 5.312e-01  |
| als        | quota_mmr | 15      | 0.0454 | 0.0950 | 0.2565          | 5.605e+00 | 3.193e-03       | 16.5%       | 579.2%             | 5.516e+00 | 8.984e-02        | 1.838e-02          | 1.008e-02           | 6.094e-01  |

### breakeven

| a                    | b                    | n_requests | lo      | hi        | replicates_crossing | repeats | stable | cheaper_below        | cheaper_above     |
|----------------------|----------------------|------------|---------|-----------|---------------------|---------|--------|----------------------|-------------------|
| popularity           | popularity+quota_mmr | --         | --      | --        | 0.0%                | 15      | no     | popularity           | popularity        |
| popularity           | itemknn              | --         | --      | --        | 0.0%                | 15      | no     | popularity           | popularity        |
| popularity           | itemknn+quota_mmr    | --         | --      | --        | 0.0%                | 15      | no     | popularity           | popularity        |
| popularity           | als                  | 845,039    | 257,462 | 1,871,822 | 2.9%                | 15      | no     | popularity           | als               |
| popularity           | als+quota_mmr        | --         | --      | --        | 0.0%                | 15      | no     | popularity           | popularity        |
| popularity+quota_mmr | itemknn              | 44         | 15      | 106       | 100.0%              | 15      | yes    | popularity+quota_mmr | itemknn           |
| popularity+quota_mmr | itemknn+quota_mmr    | 51         | 34      | 157       | 29.4%               | 15      | no     | popularity+quota_mmr | itemknn+quota_mmr |
| popularity+quota_mmr | als                  | 2,231      | 807     | 5,282     | 100.0%              | 15      | yes    | popularity+quota_mmr | als               |
| popularity+quota_mmr | als+quota_mmr        | 1,569      | 1,000   | 5,432     | 29.1%               | 15      | no     | popularity+quota_mmr | als+quota_mmr     |
| itemknn              | itemknn+quota_mmr    | --         | --      | --        | 0.0%                | 15      | no     | itemknn              | itemknn           |
| itemknn              | als                  | 126,066    | 67,175  | 3,399,412 | 88.5%               | 15      | no     | itemknn              | als               |
| itemknn              | als+quota_mmr        | --         | --      | --        | 0.0%                | 15      | no     | itemknn              | itemknn           |
| itemknn+quota_mmr    | als                  | 1,971      | 745     | 4,626     | 100.0%              | 15      | yes    | itemknn+quota_mmr    | als               |
| itemknn+quota_mmr    | als+quota_mmr        | 1,389      | 926     | 4,295     | 29.1%               | 15      | no     | itemknn+quota_mmr    | als+quota_mmr     |
| als                  | als+quota_mmr        | 12         | 1       | 56        | 61.9%               | 15      | no     | als+quota_mmr        | als               |

### rerank_share

| family     | reranker  | cpu_rerank | cpu_serving_total | rerank_share_of_serving | cpu_rerank_setup | serving_multiplier |
|------------|-----------|------------|-------------------|-------------------------|------------------|--------------------|
| popularity | quota_mmr | 5.000e-01  | 5.228e-01         | 95.8%                   | 8.594e-02        | 23.9517            |
| itemknn    | quota_mmr | 5.312e-01  | 5.687e-01         | 93.7%                   | 8.984e-02        | 15.8364            |
| als        | quota_mmr | 6.094e-01  | 6.385e-01         | 95.4%                   | 8.984e-02        | 21.8989            |

### frontier

| n_requests | frontier                         | dominated                                      | cheapest   | most_accurate        |
|------------|----------------------------------|------------------------------------------------|------------|----------------------|
| 1          | popularity, popularity+quota_mmr | als, als+quota_mmr, itemknn+quota_mmr, itemknn | popularity | popularity+quota_mmr |
| 10         | popularity, popularity+quota_mmr | als+quota_mmr, als, itemknn+quota_mmr, itemknn | popularity | popularity+quota_mmr |
| 100        | popularity, popularity+quota_mmr | als+quota_mmr, als, itemknn+quota_mmr, itemknn | popularity | popularity+quota_mmr |
| 1,000      | popularity, popularity+quota_mmr | als+quota_mmr, als, itemknn+quota_mmr, itemknn | popularity | popularity+quota_mmr |
| 10,000     | popularity, popularity+quota_mmr | als+quota_mmr, itemknn+quota_mmr, als, itemknn | popularity | popularity+quota_mmr |
| 100,000    | popularity, popularity+quota_mmr | als+quota_mmr, itemknn+quota_mmr, als, itemknn | popularity | popularity+quota_mmr |
| 1,000,000  | popularity, popularity+quota_mmr | als+quota_mmr, itemknn+quota_mmr, itemknn, als | popularity | popularity+quota_mmr |

### regimes

| n_requests | cheapest   | cost      | unit        | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|------------|------------|-----------|-------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| 1          | popularity | 2.675e-04 | cpu_seconds | 0.000268        | 0.0887                    | 0.195        | 0.284                  | 6        | 6                  |
| 10         | popularity | 1.242e-03 | cpu_seconds | 0.00124         | 0.112                     | 0.197        | 0.31                   | 6        | 6                  |
| 100        | popularity | 1.099e-02 | cpu_seconds | 0.011           | 0.347                     | 0.214        | 0.566                  | 6        | 6                  |
| 1,000      | popularity | 1.084e-01 | cpu_seconds | 0.108           | 3                         | 0.379        | 3                      | 6        | 9                  |
| 10,000     | popularity | 1.083e+00 | cpu_seconds | 1               | 26                        | 2            | 29                     | 7        | 38                 |
| 100,000    | popularity | 1.083e+01 | cpu_seconds | 11              | 261                       | 19           | 285                    | 20       | 325                |
| 1,000,000  | popularity | 1.083e+02 | cpu_seconds | 108             | 2,614                     | 184          | 2,844                  | 147      | 3,198              |

### retraining

| retrain_every | n_requests | cheapest   | training_events | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|---------------|------------|------------|-----------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| never         | 100,000    | popularity | 1               | 11              | 261                       | 19           | 285                    | 20       | 325                |
| 1,000,000     | 100,000    | popularity | 1               | 11              | 261                       | 19           | 285                    | 20       | 325                |
| 100,000       | 100,000    | popularity | 2               | 11              | 262                       | 19           | 285                    | 25       | 330                |
| 10,000        | 100,000    | popularity | 11              | 11              | 262                       | 21           | 287                    | 76       | 381                |
| 1,000         | 100,000    | popularity | 101             | 11              | 270                       | 38           | 313                    | 582      | 885                |
| 100           | 100,000    | popularity | 1,001           | 11              | 348                       | 214          | 566                    | 5,645    | 5,930              |
