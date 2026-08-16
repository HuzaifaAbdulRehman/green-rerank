# Results tables

Generated from `results\energy`.

## gift_cards  (147 items)

### cost

| family     | reranker  | repeats | ndcg   | recall | exposure_parity | cpu_once  | cpu_per_request | spread_once | spread_per_request | cpu_train | cpu_rerank_setup | cpu_retrieve_score | cpu_retrieve_select | cpu_rerank |
|------------|-----------|---------|--------|--------|-----------------|-----------|-----------------|-------------|--------------------|-----------|------------------|--------------------|---------------------|------------|
| popularity | none      | 3       | 0.0626 | 0.1250 | 1.5000          | 8.552e-05 | 6.581e-05       | 3.3%        | 7.5%               | 8.552e-05 | 0.000e+00        | 1.042e-02          | 2.385e-03           | 0.000e+00  |
| itemknn    | none      | 3       | 0.1622 | 0.3550 | 1.3625          | 1.953e-03 | 6.690e-05       | 2.5%        | 3.5%               | 1.953e-03 | 0.000e+00        | 1.078e-02          | 2.520e-03           | 0.000e+00  |
| als        | none      | 3       | 0.0593 | 0.1350 | 0.4890          | 6.250e-01 | 7.250e-05       | 15.0%       | 37.0%              | 6.250e-01 | 0.000e+00        | 1.202e-02          | 2.480e-03           | 0.000e+00  |
| popularity | quota_mmr | 3       | 0.0525 | 0.0900 | 0.2995          | 5.803e-04 | 1.710e-03       | 2.3%        | 14.1%              | 8.423e-05 | 4.968e-04        | 1.078e-02          | 2.422e-03           | 3.281e-01  |
| itemknn    | quota_mmr | 3       | 0.1095 | 0.2050 | 0.2670          | 2.458e-03 | 1.863e-03       | 2.1%        | 8.8%               | 1.929e-03 | 5.148e-04        | 1.078e-02          | 2.385e-03           | 3.594e-01  |
| als        | quota_mmr | 3       | 0.0546 | 0.1200 | 0.2610          | 6.256e-01 | 2.122e-03       | 5.0%        | 11.4%              | 6.250e-01 | 5.182e-04        | 1.250e-02          | 2.583e-03           | 4.062e-01  |

### breakeven

| a                    | b                    | n_requests | lo        | hi        | replicates_crossing | repeats | stable | cheaper_below        | cheaper_above        |
|----------------------|----------------------|------------|-----------|-----------|---------------------|---------|--------|----------------------|----------------------|
| popularity           | popularity+quota_mmr | --         | --        | --        | 0.0%                | 3       | no     | popularity           | popularity           |
| popularity           | itemknn              | 1,281      | 827       | 1,281     | 18.6%               | 3       | no     | popularity           | itemknn              |
| popularity           | itemknn+quota_mmr    | --         | --        | --        | 0.0%                | 3       | no     | popularity           | popularity           |
| popularity           | als                  | 1,409,370  | 1,409,370 | 1,409,370 | 6.6%                | 3       | no     | popularity           | als                  |
| popularity           | als+quota_mmr        | --         | --        | --        | 0.0%                | 3       | no     | popularity           | popularity           |
| popularity+quota_mmr | itemknn              | 0.836      | 0.736     | 0.888     | 100.0%              | 3       | yes    | popularity+quota_mmr | itemknn              |
| popularity+quota_mmr | itemknn+quota_mmr    | 356        | 337       | 359       | 18.6%               | 3       | no     | popularity+quota_mmr | itemknn+quota_mmr    |
| popularity+quota_mmr | als                  | 387        | 347       | 462       | 100.0%              | 3       | yes    | popularity+quota_mmr | als                  |
| popularity+quota_mmr | als+quota_mmr        | --         | --        | --        | 0.0%                | 3       | no     | popularity+quota_mmr | popularity+quota_mmr |
| itemknn              | itemknn+quota_mmr    | --         | --        | --        | 0.0%                | 3       | no     | itemknn              | itemknn              |
| itemknn              | als                  | 1,275,755  | 1,275,755 | 1,275,755 | 6.6%                | 3       | no     | itemknn              | als                  |
| itemknn              | als+quota_mmr        | --         | --        | --        | 0.0%                | 3       | no     | itemknn              | itemknn              |
| itemknn+quota_mmr    | als                  | 348        | 318       | 400       | 100.0%              | 3       | yes    | itemknn+quota_mmr    | als                  |
| itemknn+quota_mmr    | als+quota_mmr        | 125,802    | 125,802   | 125,802   | 6.6%                | 3       | no     | itemknn+quota_mmr    | als+quota_mmr        |
| als                  | als+quota_mmr        | 43         | 32        | 45        | 25.2%               | 3       | no     | als+quota_mmr        | als                  |

### rerank_share

| family     | reranker  | cpu_rerank | cpu_serving_total | rerank_share_of_serving | cpu_rerank_setup | serving_multiplier |
|------------|-----------|------------|-------------------|-------------------------|------------------|--------------------|
| popularity | quota_mmr | 3.281e-01  | 3.420e-01         | 96.1%                   | 4.968e-04        | 25.3396            |
| itemknn    | quota_mmr | 3.594e-01  | 3.725e-01         | 96.5%                   | 5.148e-04        | 28.3053            |
| als        | quota_mmr | 4.062e-01  | 4.245e-01         | 96.6%                   | 5.182e-04        | 29.7580            |

### frontier

| n_requests | frontier            | dominated                                                   | cheapest   | most_accurate |
|------------|---------------------|-------------------------------------------------------------|------------|---------------|
| 1          | popularity, itemknn | als+quota_mmr, als, itemknn+quota_mmr, popularity+quota_mmr | popularity | itemknn       |
| 10         | popularity, itemknn | als+quota_mmr, als, itemknn+quota_mmr, popularity+quota_mmr | popularity | itemknn       |
| 100        | popularity, itemknn | als+quota_mmr, als, itemknn+quota_mmr, popularity+quota_mmr | popularity | itemknn       |
| 1,000      | popularity, itemknn | als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr, als | popularity | itemknn       |
| 10,000     | popularity, itemknn | als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr, als | popularity | itemknn       |
| 100,000    | popularity, itemknn | als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr, als | popularity | itemknn       |
| 1,000,000  | popularity, itemknn | als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr, als | popularity | itemknn       |

### regimes

| n_requests | cheapest   | cost      | unit        | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|------------|------------|-----------|-------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| 1          | popularity | 1.513e-04 | cpu_seconds | 0.000151        | 0.00229                   | 0.00202      | 0.00432                | 0.625    | 0.628              |
| 10         | popularity | 7.436e-04 | cpu_seconds | 0.000744        | 0.0177                    | 0.00262      | 0.0211                 | 0.626    | 0.647              |
| 100        | popularity | 6.666e-03 | cpu_seconds | 0.00667         | 0.172                     | 0.00864      | 0.189                  | 0.632    | 0.838              |
| 1,000      | popularity | 6.589e-02 | cpu_seconds | 0.0659          | 2                         | 0.0689       | 2                      | 0.697    | 3                  |
| 10,000     | popularity | 6.582e-01 | cpu_seconds | 0.658           | 17                        | 0.671        | 19                     | 1        | 22                 |
| 100,000    | popularity | 6.581e+00 | cpu_seconds | 7               | 171                       | 7            | 186                    | 8        | 213                |
| 1,000,000  | popularity | 6.581e+01 | cpu_seconds | 66              | 1,710                     | 67           | 1,863                  | 73       | 2,123              |

### retraining

| retrain_every | n_requests | cheapest   | training_events | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|---------------|------------|------------|-----------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| never         | 100,000    | popularity | 1               | 7               | 171                       | 7            | 186                    | 8        | 213                |
| 1,000,000     | 100,000    | popularity | 1               | 7               | 171                       | 7            | 186                    | 8        | 213                |
| 100,000       | 100,000    | popularity | 2               | 7               | 171                       | 7            | 186                    | 8        | 213                |
| 10,000        | 100,000    | popularity | 11              | 7               | 171                       | 7            | 186                    | 14       | 219                |
| 1,000         | 100,000    | popularity | 101             | 7               | 171                       | 7            | 187                    | 70       | 275                |
| 100           | 100,000    | popularity | 1,001           | 7               | 172                       | 9            | 189                    | 633      | 838                |

## ml100k  (1,349 items)

### cost

| family     | reranker  | repeats | ndcg   | recall | exposure_parity | cpu_once  | cpu_per_request | spread_once | spread_per_request | cpu_train | cpu_rerank_setup | cpu_retrieve_score | cpu_retrieve_select | cpu_rerank |
|------------|-----------|---------|--------|--------|-----------------|-----------|-----------------|-------------|--------------------|-----------|------------------|--------------------|---------------------|------------|
| popularity | none      | 3       | 0.0527 | 0.1050 | 1.1855          | 1.554e-04 | 1.083e-04       | 4.8%        | 4.7%               | 1.554e-04 | 0.000e+00        | 1.157e-02          | 1.008e-02           | 0.000e+00  |
| als        | none      | 3       | 0.0526 | 0.1150 | 0.8280          | 5.875e+00 | 1.357e-04       | 0.8%        | 24.0%              | 5.875e+00 | 0.000e+00        | 1.766e-02          | 1.008e-02           | 0.000e+00  |
| itemknn    | none      | 3       | 0.0448 | 0.1000 | 1.1535          | 1.953e-01 | 1.841e-04       | 4.0%        | 2.7%               | 1.953e-01 | 0.000e+00        | 2.734e-02          | 9.766e-03           | 0.000e+00  |
| popularity | quota_mmr | 3       | 0.0541 | 0.1100 | 0.2570          | 8.610e-02 | 2.685e-03       | 0.0%        | 2.8%               | 1.594e-04 | 8.594e-02        | 1.157e-02          | 1.008e-02           | 5.156e-01  |
| itemknn    | quota_mmr | 3       | 0.0518 | 0.1100 | 0.2465          | 2.852e-01 | 2.913e-03       | 4.1%        | 7.7%               | 1.953e-01 | 8.984e-02        | 2.734e-02          | 9.766e-03           | 5.469e-01  |
| als        | quota_mmr | 3       | 0.0471 | 0.0950 | 0.2600          | 5.914e+00 | 3.356e-03       | 6.3%        | 5.8%               | 5.828e+00 | 8.594e-02        | 2.083e-02          | 9.766e-03           | 6.406e-01  |

### breakeven

| a                    | b                    | n_requests | lo     | hi      | replicates_crossing | repeats | stable | cheaper_below        | cheaper_above        |
|----------------------|----------------------|------------|--------|---------|---------------------|---------|--------|----------------------|----------------------|
| popularity           | popularity+quota_mmr | --         | --     | --      | 0.0%                | 3       | no     | popularity           | popularity           |
| popularity           | itemknn              | --         | --     | --      | 0.0%                | 3       | no     | popularity           | popularity           |
| popularity           | itemknn+quota_mmr    | --         | --     | --      | 0.0%                | 3       | no     | popularity           | popularity           |
| popularity           | als                  | --         | --     | --      | 0.0%                | 3       | no     | popularity           | popularity           |
| popularity           | als+quota_mmr        | --         | --     | --      | 0.0%                | 3       | no     | popularity           | popularity           |
| popularity+quota_mmr | itemknn              | 44         | 41     | 45      | 100.0%              | 3       | yes    | popularity+quota_mmr | itemknn              |
| popularity+quota_mmr | itemknn+quota_mmr    | --         | --     | --      | 0.0%                | 3       | no     | popularity+quota_mmr | popularity+quota_mmr |
| popularity+quota_mmr | als                  | 2,271      | 2,251  | 2,351   | 100.0%              | 3       | yes    | popularity+quota_mmr | als                  |
| popularity+quota_mmr | als+quota_mmr        | --         | --     | --      | 0.0%                | 3       | no     | popularity+quota_mmr | popularity+quota_mmr |
| itemknn              | itemknn+quota_mmr    | --         | --     | --      | 0.0%                | 3       | no     | itemknn              | itemknn              |
| itemknn              | als                  | 116,372    | 81,204 | 174,480 | 100.0%              | 3       | yes    | itemknn              | als                  |
| itemknn              | als+quota_mmr        | --         | --     | --      | 0.0%                | 3       | no     | itemknn              | itemknn              |
| itemknn+quota_mmr    | als                  | 1,998      | 1,887  | 2,064   | 100.0%              | 3       | yes    | itemknn+quota_mmr    | als                  |
| itemknn+quota_mmr    | als+quota_mmr        | --         | --     | --      | 0.0%                | 3       | no     | itemknn+quota_mmr    | itemknn+quota_mmr    |
| als                  | als+quota_mmr        | 60         | 46     | 61      | 25.1%               | 3       | no     | als+quota_mmr        | als                  |

### rerank_share

| family     | reranker  | cpu_rerank | cpu_serving_total | rerank_share_of_serving | cpu_rerank_setup | serving_multiplier |
|------------|-----------|------------|-------------------|-------------------------|------------------|--------------------|
| popularity | quota_mmr | 5.156e-01  | 5.370e-01         | 96.0%                   | 8.594e-02        | 24.8112            |
| itemknn    | quota_mmr | 5.469e-01  | 5.827e-01         | 93.9%                   | 8.984e-02        | 16.2727            |
| als        | quota_mmr | 6.406e-01  | 6.712e-01         | 95.4%                   | 8.594e-02        | 21.9362            |

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
| 1          | popularity | 2.637e-04 | cpu_seconds | 0.000264        | 0.0888                    | 0.195        | 0.288                  | 6        | 6                  |
| 10         | popularity | 1.238e-03 | cpu_seconds | 0.00124         | 0.113                     | 0.197        | 0.314                  | 6        | 6                  |
| 100        | popularity | 1.098e-02 | cpu_seconds | 0.011           | 0.355                     | 0.214        | 0.576                  | 6        | 6                  |
| 1,000      | popularity | 1.084e-01 | cpu_seconds | 0.108           | 3                         | 0.379        | 3                      | 6        | 9                  |
| 10,000     | popularity | 1.083e+00 | cpu_seconds | 1               | 27                        | 2            | 29                     | 7        | 39                 |
| 100,000    | popularity | 1.083e+01 | cpu_seconds | 11              | 269                       | 19           | 292                    | 19       | 342                |
| 1,000,000  | popularity | 1.083e+02 | cpu_seconds | 108             | 2,685                     | 184          | 2,914                  | 142      | 3,362              |

### retraining

| retrain_every | n_requests | cheapest   | training_events | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|---------------|------------|------------|-----------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| never         | 100,000    | popularity | 1               | 11              | 269                       | 19           | 292                    | 19       | 342                |
| 1,000,000     | 100,000    | popularity | 1               | 11              | 269                       | 19           | 292                    | 19       | 342                |
| 100,000       | 100,000    | popularity | 2               | 11              | 269                       | 19           | 292                    | 25       | 347                |
| 10,000        | 100,000    | popularity | 11              | 11              | 269                       | 21           | 294                    | 78       | 401                |
| 1,000         | 100,000    | popularity | 101             | 11              | 277                       | 38           | 320                    | 607      | 933                |
| 100           | 100,000    | popularity | 1,001           | 11              | 355                       | 214          | 577                    | 5,894    | 6,256              |
