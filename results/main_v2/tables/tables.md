# Results tables

Generated from `results\main_v2`.

## gift_cards  (147 items)

### cost

| family     | reranker  | repeats | ndcg   | recall | exposure_parity | cpu_once  | cpu_per_request | spread_once | spread_per_request | cpu_train | cpu_rerank_setup | cpu_retrieve_score | cpu_retrieve_select | cpu_rerank |
|------------|-----------|---------|--------|--------|-----------------|-----------|-----------------|-------------|--------------------|-----------|------------------|--------------------|---------------------|------------|
| popularity | none      | 5       | 0.0729 | 0.1450 | 1.5000          | 8.457e-05 | 6.293e-05       | 3.1%        | 12.3%              | 8.457e-05 | 0.000e+00        | 1.042e-02          | 2.185e-03           | 0.000e+00  |
| itemknn    | none      | 5       | 0.1733 | 0.3550 | 1.3595          | 1.871e-03 | 6.392e-05       | 18.4%       | 8.6%               | 1.871e-03 | 0.000e+00        | 1.042e-02          | 2.367e-03           | 0.000e+00  |
| als        | none      | 5       | 0.0585 | 0.1400 | 0.4820          | 6.562e-01 | 6.773e-05       | 9.5%        | 9.7%               | 6.562e-01 | 0.000e+00        | 1.116e-02          | 2.385e-03           | 0.000e+00  |
| popularity | quota_mmr | 5       | 0.0534 | 0.0800 | 0.3000          | 5.687e-04 | 1.626e-03       | 2.5%        | 19.6%              | 8.198e-05 | 4.875e-04        | 1.008e-02          | 2.201e-03           | 3.125e-01  |
| itemknn    | quota_mmr | 5       | 0.1277 | 0.2250 | 0.2840          | 2.378e-03 | 1.704e-03       | 10.2%       | 18.5%              | 1.894e-03 | 4.890e-04        | 1.042e-02          | 2.350e-03           | 3.281e-01  |
| als        | quota_mmr | 5       | 0.0569 | 0.1450 | 0.2565          | 6.724e-01 | 2.018e-03       | 16.3%       | 14.9%              | 6.719e-01 | 5.008e-04        | 1.078e-02          | 2.385e-03           | 3.906e-01  |

### breakeven

| a                    | b                    | n_requests | lo      | hi        | replicates_crossing | repeats | stable | cheaper_below        | cheaper_above        |
|----------------------|----------------------|------------|---------|-----------|---------------------|---------|--------|----------------------|----------------------|
| popularity           | popularity+quota_mmr | --         | --      | --        | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | itemknn              | 636        | 347     | 723       | 30.2%               | 5       | no     | popularity           | itemknn              |
| popularity           | itemknn+quota_mmr    | --         | --      | --        | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | als                  | 770,247    | 202,160 | 1,438,705 | 14.6%               | 5       | no     | popularity           | als                  |
| popularity           | als+quota_mmr        | --         | --      | --        | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity+quota_mmr | itemknn              | 0.834      | 0.718   | 1         | 100.0%              | 5       | yes    | popularity+quota_mmr | itemknn              |
| popularity+quota_mmr | itemknn+quota_mmr    | 24         | 11      | 24        | 30.2%               | 5       | no     | popularity+quota_mmr | itemknn+quota_mmr    |
| popularity+quota_mmr | als                  | 421        | 365     | 450       | 100.0%              | 5       | yes    | popularity+quota_mmr | als                  |
| popularity+quota_mmr | als+quota_mmr        | --         | --      | --        | 0.0%                | 5       | no     | popularity+quota_mmr | popularity+quota_mmr |
| itemknn              | itemknn+quota_mmr    | --         | --      | --        | 0.0%                | 5       | no     | itemknn              | itemknn              |
| itemknn              | als                  | 458,257    | 189,185 | 1,194,967 | 5.5%                | 5       | no     | itemknn              | als                  |
| itemknn              | als+quota_mmr        | --         | --      | --        | 0.0%                | 5       | no     | itemknn              | itemknn              |
| itemknn+quota_mmr    | als                  | 399        | 349     | 428       | 100.0%              | 5       | yes    | itemknn+quota_mmr    | als                  |
| itemknn+quota_mmr    | als+quota_mmr        | --         | --      | --        | 0.0%                | 5       | no     | itemknn+quota_mmr    | itemknn+quota_mmr    |
| als                  | als+quota_mmr        | 7          | 7       | 28        | 6.4%                | 5       | no     | als+quota_mmr        | als                  |

### rerank_share

| family     | reranker  | cpu_rerank | cpu_serving_total | rerank_share_of_serving | cpu_rerank_setup | serving_multiplier |
|------------|-----------|------------|-------------------|-------------------------|------------------|--------------------|
| popularity | quota_mmr | 3.125e-01  | 3.251e-01         | 96.1%                   | 4.875e-04        | 25.7977            |
| itemknn    | quota_mmr | 3.281e-01  | 3.409e-01         | 96.3%                   | 4.890e-04        | 26.7025            |
| als        | quota_mmr | 3.906e-01  | 4.037e-01         | 96.8%                   | 5.008e-04        | 30.9551            |

### rerankers

| family     | reranker  | repeats | cpu_rerank_per_request | cpu_serving_per_request | rerank_share | ndcg   | exposure_parity | recall | time_bounded | cost_vs_cheapest |
|------------|-----------|---------|------------------------|-------------------------|--------------|--------|-----------------|--------|--------------|------------------|
| als        | quota_mmr | 5       | 1.953e-03              | 2.018e-03               | 96.8%        | 0.0569 | 0.2565          | 0.1450 | no           | 1.0000           |
| itemknn    | quota_mmr | 5       | 1.641e-03              | 1.704e-03               | 96.3%        | 0.1277 | 0.2840          | 0.2250 | no           | 1.0000           |
| popularity | quota_mmr | 5       | 1.563e-03              | 1.626e-03               | 96.1%        | 0.0534 | 0.3000          | 0.0800 | no           | 1.0000           |

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
| 1          | popularity | 1.475e-04 | cpu_seconds | 0.000148        | 0.00219                   | 0.00194      | 0.00408                | 0.656    | 0.674              |
| 10         | popularity | 7.139e-04 | cpu_seconds | 0.000714        | 0.0168                    | 0.00251      | 0.0194                 | 0.657    | 0.693              |
| 100        | popularity | 6.378e-03 | cpu_seconds | 0.00638         | 0.163                     | 0.00826      | 0.173                  | 0.663    | 0.874              |
| 1,000      | popularity | 6.302e-02 | cpu_seconds | 0.063           | 2                         | 0.0658       | 2                      | 0.724    | 3                  |
| 10,000     | popularity | 6.294e-01 | cpu_seconds | 0.629           | 16                        | 0.641        | 17                     | 1        | 21                 |
| 100,000    | popularity | 6.293e+00 | cpu_seconds | 6               | 163                       | 6            | 170                    | 7        | 203                |
| 1,000,000  | popularity | 6.293e+01 | cpu_seconds | 63              | 1,626                     | 64           | 1,704                  | 68       | 2,019              |

### retraining

| retrain_every | n_requests | cheapest   | training_events | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|---------------|------------|------------|-----------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| never         | 100,000    | popularity | 1               | 6               | 163                       | 6            | 170                    | 7        | 203                |
| 1,000,000     | 100,000    | popularity | 1               | 6               | 163                       | 6            | 170                    | 7        | 203                |
| 100,000       | 100,000    | popularity | 2               | 6               | 163                       | 6            | 170                    | 8        | 203                |
| 10,000        | 100,000    | popularity | 11              | 6               | 163                       | 6            | 170                    | 14       | 209                |
| 1,000         | 100,000    | popularity | 101             | 6               | 163                       | 7            | 171                    | 73       | 270                |
| 100           | 100,000    | popularity | 1,001           | 6               | 163                       | 8            | 173                    | 664      | 875                |

## software  (727 items)

### cost

| family     | reranker  | repeats | ndcg   | recall | exposure_parity | cpu_once  | cpu_per_request | spread_once | spread_per_request | cpu_train | cpu_rerank_setup | cpu_retrieve_score | cpu_retrieve_select | cpu_rerank |
|------------|-----------|---------|--------|--------|-----------------|-----------|-----------------|-------------|--------------------|-----------|------------------|--------------------|---------------------|------------|
| popularity | none      | 5       | 0.0048 | 0.0150 | 1.5000          | 1.030e-04 | 8.336e-05       | 6.4%        | 6.8%               | 1.030e-04 | 0.000e+00        | 1.078e-02          | 6.010e-03           | 0.000e+00  |
| als        | none      | 5       | 0.0823 | 0.1550 | 0.6335          | 2.703e+00 | 9.184e-05       | 6.4%        | 30.7%              | 2.703e+00 | 0.000e+00        | 1.157e-02          | 6.793e-03           | 0.000e+00  |
| itemknn    | none      | 5       | 0.0836 | 0.1550 | 0.9085          | 2.232e-02 | 9.482e-05       | 0.0%        | 4.2%               | 2.232e-02 | 0.000e+00        | 1.202e-02          | 6.944e-03           | 0.000e+00  |
| popularity | quota_mmr | 5       | 0.0019 | 0.0050 | 1.0000          | 9.032e-03 | 2.274e-03       | 5.6%        | 10.5%              | 1.034e-04 | 8.929e-03        | 1.078e-02          | 6.127e-03           | 4.375e-01  |
| itemknn    | quota_mmr | 5       | 0.0828 | 0.1550 | 0.2655          | 3.151e-02 | 3.144e-03       | 7.4%        | 5.0%               | 2.232e-02 | 9.191e-03        | 1.202e-02          | 7.102e-03           | 6.094e-01  |
| als        | quota_mmr | 5       | 0.0760 | 0.1450 | 0.2625          | 2.743e+00 | 3.451e-03       | 2.9%        | 7.2%               | 2.734e+00 | 8.929e-03        | 1.157e-02          | 6.793e-03           | 6.719e-01  |

### breakeven

| a                    | b                    | n_requests | lo      | hi        | replicates_crossing | repeats | stable | cheaper_below        | cheaper_above        |
|----------------------|----------------------|------------|---------|-----------|---------------------|---------|--------|----------------------|----------------------|
| popularity           | popularity+quota_mmr | --         | --      | --        | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | itemknn              | --         | --      | --        | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | itemknn+quota_mmr    | --         | --      | --        | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | als                  | --         | --      | --        | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | als+quota_mmr        | --         | --      | --        | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity+quota_mmr | itemknn              | 6          | 5       | 6         | 100.0%              | 5       | yes    | popularity+quota_mmr | itemknn              |
| popularity+quota_mmr | itemknn+quota_mmr    | --         | --      | --        | 0.0%                | 5       | no     | popularity+quota_mmr | popularity+quota_mmr |
| popularity+quota_mmr | als                  | 1,235      | 1,115   | 1,320     | 100.0%              | 5       | yes    | popularity+quota_mmr | als                  |
| popularity+quota_mmr | als+quota_mmr        | --         | --      | --        | 0.0%                | 5       | no     | popularity+quota_mmr | popularity+quota_mmr |
| itemknn              | itemknn+quota_mmr    | --         | --      | --        | 0.0%                | 5       | no     | itemknn              | itemknn              |
| itemknn              | als                  | 899,413    | 434,237 | 1,239,531 | 69.2%               | 5       | no     | itemknn              | als                  |
| itemknn              | als+quota_mmr        | --         | --      | --        | 0.0%                | 5       | no     | itemknn              | itemknn              |
| itemknn+quota_mmr    | als                  | 876        | 833     | 933       | 100.0%              | 5       | yes    | itemknn+quota_mmr    | als                  |
| itemknn+quota_mmr    | als+quota_mmr        | --         | --      | --        | 0.0%                | 5       | no     | itemknn+quota_mmr    | itemknn+quota_mmr    |
| als                  | als+quota_mmr        | 11         | 2       | 39        | 36.0%               | 5       | no     | als+quota_mmr        | als                  |

### rerank_share

| family     | reranker  | cpu_rerank | cpu_serving_total | rerank_share_of_serving | cpu_rerank_setup | serving_multiplier |
|------------|-----------|------------|-------------------|-------------------------|------------------|--------------------|
| popularity | quota_mmr | 4.375e-01  | 4.548e-01         | 96.4%                   | 8.929e-03        | 27.6341            |
| itemknn    | quota_mmr | 6.094e-01  | 6.288e-01         | 97.0%                   | 9.191e-03        | 33.3917            |
| als        | quota_mmr | 6.719e-01  | 6.902e-01         | 97.3%                   | 8.929e-03        | 36.4375            |

### rerankers

| family     | reranker  | repeats | cpu_rerank_per_request | cpu_serving_per_request | rerank_share | ndcg   | exposure_parity | recall | time_bounded | cost_vs_cheapest |
|------------|-----------|---------|------------------------|-------------------------|--------------|--------|-----------------|--------|--------------|------------------|
| als        | quota_mmr | 5       | 3.359e-03              | 3.451e-03               | 97.3%        | 0.0760 | 0.2625          | 0.1450 | no           | 1.0000           |
| itemknn    | quota_mmr | 5       | 3.047e-03              | 3.144e-03               | 97.0%        | 0.0828 | 0.2655          | 0.1550 | no           | 1.0000           |
| popularity | quota_mmr | 5       | 2.188e-03              | 2.274e-03               | 96.4%        | 0.0019 | 1.0000          | 0.0050 | no           | 1.0000           |

### frontier

| n_requests | frontier                 | dominated                                                   | cheapest   | most_accurate |
|------------|--------------------------|-------------------------------------------------------------|------------|---------------|
| 1          | popularity, itemknn      | als+quota_mmr, als, itemknn+quota_mmr, popularity+quota_mmr | popularity | itemknn       |
| 10         | popularity, itemknn      | als+quota_mmr, als, itemknn+quota_mmr, popularity+quota_mmr | popularity | itemknn       |
| 100        | popularity, itemknn      | als+quota_mmr, als, itemknn+quota_mmr, popularity+quota_mmr | popularity | itemknn       |
| 1,000      | popularity, itemknn      | als+quota_mmr, itemknn+quota_mmr, als, popularity+quota_mmr | popularity | itemknn       |
| 10,000     | popularity, itemknn      | als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr, als | popularity | itemknn       |
| 100,000    | popularity, itemknn      | als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr, als | popularity | itemknn       |
| 1,000,000  | popularity, als, itemknn | als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr      | popularity | itemknn       |

### regimes

| n_requests | cheapest   | cost      | unit        | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|------------|------------|-----------|-------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| 1          | popularity | 1.864e-04 | cpu_seconds | 0.000186        | 0.0113                    | 0.0224       | 0.0347                 | 3        | 3                  |
| 10         | popularity | 9.366e-04 | cpu_seconds | 0.000937        | 0.0318                    | 0.0233       | 0.063                  | 3        | 3                  |
| 100        | popularity | 8.439e-03 | cpu_seconds | 0.00844         | 0.236                     | 0.0318       | 0.346                  | 3        | 3                  |
| 1,000      | popularity | 8.346e-02 | cpu_seconds | 0.0835          | 2                         | 0.117        | 3                      | 3        | 6                  |
| 10,000     | popularity | 8.337e-01 | cpu_seconds | 0.834           | 23                        | 0.971        | 31                     | 4        | 37                 |
| 100,000    | popularity | 8.336e+00 | cpu_seconds | 8               | 227                       | 10           | 314                    | 12       | 348                |
| 1,000,000  | popularity | 8.336e+01 | cpu_seconds | 83              | 2,274                     | 95           | 3,144                  | 95       | 3,454              |

### retraining

| retrain_every | n_requests | cheapest   | training_events | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|---------------|------------|------------|-----------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| never         | 100,000    | popularity | 1               | 8               | 227                       | 10           | 314                    | 12       | 348                |
| 1,000,000     | 100,000    | popularity | 1               | 8               | 227                       | 10           | 314                    | 12       | 348                |
| 100,000       | 100,000    | popularity | 2               | 8               | 227                       | 10           | 314                    | 15       | 351                |
| 10,000        | 100,000    | popularity | 11              | 8               | 227                       | 10           | 315                    | 39       | 375                |
| 1,000         | 100,000    | popularity | 101             | 8               | 228                       | 12           | 318                    | 282      | 622                |
| 100           | 100,000    | popularity | 1,001           | 8               | 236                       | 32           | 346                    | 2,715    | 3,091              |

## ml100k  (1,349 items)

### cost

| family     | reranker  | repeats | ndcg   | recall | exposure_parity | cpu_once  | cpu_per_request | spread_once | spread_per_request | cpu_train | cpu_rerank_setup | cpu_retrieve_score | cpu_retrieve_select | cpu_rerank |
|------------|-----------|---------|--------|--------|-----------------|-----------|-----------------|-------------|--------------------|-----------|------------------|--------------------|---------------------|------------|
| popularity | none      | 5       | 0.0527 | 0.1050 | 1.1855          | 1.581e-04 | 1.046e-04       | 10.9%       | 4.5%               | 1.581e-04 | 0.000e+00        | 1.116e-02          | 9.766e-03           | 0.000e+00  |
| als        | none      | 5       | 0.0685 | 0.1550 | 0.8280          | 5.781e+00 | 1.515e-04       | 7.6%        | 57.4%              | 5.781e+00 | 0.000e+00        | 2.083e-02          | 9.766e-03           | 0.000e+00  |
| itemknn    | none      | 5       | 0.0471 | 0.1000 | 1.1425          | 1.953e-01 | 1.776e-04       | 12.0%       | 9.3%               | 1.953e-01 | 0.000e+00        | 2.604e-02          | 9.470e-03           | 0.000e+00  |
| multvae    | none      | 5       | 0.0448 | 0.1000 | 0.9745          | 3.688e+00 | 5.729e-04       | 50.0%       | 20.1%              | 3.688e+00 | 0.000e+00        | 6.250e-02          | 4.464e-02           | 0.000e+00  |
| gru4rec    | none      | 5       | 0.0995 | 0.1850 | 0.9025          | 4.179e+02 | 1.042e-03       | 15.2%       | 22.5%              | 4.179e+02 | 0.000e+00        | 1.562e-01          | 5.208e-02           | 0.000e+00  |
| popularity | quota_mmr | 5       | 0.0517 | 0.0950 | 0.2505          | 8.609e-02 | 2.607e-03       | 9.1%        | 9.3%               | 1.579e-04 | 8.594e-02        | 1.202e-02          | 9.470e-03           | 5.000e-01  |
| itemknn    | quota_mmr | 5       | 0.0529 | 0.1050 | 0.2480          | 2.852e-01 | 2.759e-03       | 2.7%        | 11.7%              | 1.953e-01 | 8.984e-02        | 2.604e-02          | 9.470e-03           | 5.156e-01  |
| als        | quota_mmr | 5       | 0.0490 | 0.1050 | 0.2575          | 5.887e+00 | 3.192e-03       | 4.9%        | 5.2%               | 5.797e+00 | 8.984e-02        | 1.786e-02          | 9.766e-03           | 6.094e-01  |
| multvae    | quota_mmr | 5       | 0.0489 | 0.1000 | 0.2460          | 4.141e+00 | 5.067e-03       | 19.6%       | 3.1%               | 3.766e+00 | 3.750e-01        | 7.812e-02          | 4.464e-02           | 8.906e-01  |
| gru4rec    | quota_mmr | 5       | 0.0860 | 0.1600 | 0.2620          | 4.334e+02 | 5.938e-03       | 3.7%        | 5.9%               | 4.330e+02 | 4.375e-01        | 1.562e-01          | 5.208e-02           | 9.688e-01  |

### breakeven

| a                    | b                    | n_requests | lo      | hi         | replicates_crossing | repeats | stable | cheaper_below        | cheaper_above        |
|----------------------|----------------------|------------|---------|------------|---------------------|---------|--------|----------------------|----------------------|
| popularity           | popularity+quota_mmr | --         | --      | --         | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | itemknn              | --         | --      | --         | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | itemknn+quota_mmr    | --         | --      | --         | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | als                  | --         | --      | --         | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | als+quota_mmr        | --         | --      | --         | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | multvae              | --         | --      | --         | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | multvae+quota_mmr    | --         | --      | --         | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | gru4rec              | --         | --      | --         | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | gru4rec+quota_mmr    | --         | --      | --         | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity+quota_mmr | itemknn              | 45         | 41      | 52         | 100.0%              | 5       | yes    | popularity+quota_mmr | itemknn              |
| popularity+quota_mmr | itemknn+quota_mmr    | 16,985     | 2,106   | 16,985     | 3.8%                | 5       | no     | popularity+quota_mmr | itemknn+quota_mmr    |
| popularity+quota_mmr | als                  | 2,322      | 2,173   | 2,437      | 100.0%              | 5       | yes    | popularity+quota_mmr | als                  |
| popularity+quota_mmr | als+quota_mmr        | --         | --      | --         | 0.0%                | 5       | no     | popularity+quota_mmr | popularity+quota_mmr |
| popularity+quota_mmr | multvae              | 1,772      | 1,637   | 2,630      | 100.0%              | 5       | yes    | popularity+quota_mmr | multvae              |
| popularity+quota_mmr | multvae+quota_mmr    | --         | --      | --         | 0.0%                | 5       | no     | popularity+quota_mmr | popularity+quota_mmr |
| popularity+quota_mmr | gru4rec              | 266,193    | 240,566 | 339,060    | 100.0%              | 5       | yes    | popularity+quota_mmr | gru4rec              |
| popularity+quota_mmr | gru4rec+quota_mmr    | --         | --      | --         | 0.0%                | 5       | no     | popularity+quota_mmr | popularity+quota_mmr |
| itemknn              | itemknn+quota_mmr    | --         | --      | --         | 0.0%                | 5       | no     | itemknn              | itemknn              |
| itemknn              | als                  | 213,900    | 121,712 | 14,968,800 | 94.3%               | 5       | yes    | itemknn              | als                  |
| itemknn              | als+quota_mmr        | --         | --      | --         | 0.0%                | 5       | no     | itemknn              | itemknn              |
| itemknn              | multvae              | --         | --      | --         | 0.0%                | 5       | no     | itemknn              | itemknn              |
| itemknn              | multvae+quota_mmr    | --         | --      | --         | 0.0%                | 5       | no     | itemknn              | itemknn              |
| itemknn              | gru4rec              | --         | --      | --         | 0.0%                | 5       | no     | itemknn              | itemknn              |
| itemknn              | gru4rec+quota_mmr    | --         | --      | --         | 0.0%                | 5       | no     | itemknn              | itemknn              |
| itemknn+quota_mmr    | als                  | 2,110      | 1,928   | 2,242      | 100.0%              | 5       | yes    | itemknn+quota_mmr    | als                  |
| itemknn+quota_mmr    | als+quota_mmr        | --         | --      | --         | 0.0%                | 5       | no     | itemknn+quota_mmr    | itemknn+quota_mmr    |
| itemknn+quota_mmr    | multvae              | 1,585      | 1,400   | 2,357      | 100.0%              | 5       | yes    | itemknn+quota_mmr    | multvae              |
| itemknn+quota_mmr    | multvae+quota_mmr    | --         | --      | --         | 0.0%                | 5       | no     | itemknn+quota_mmr    | itemknn+quota_mmr    |
| itemknn+quota_mmr    | gru4rec              | 243,623    | 212,279 | 306,067    | 100.0%              | 5       | yes    | itemknn+quota_mmr    | gru4rec              |
| itemknn+quota_mmr    | gru4rec+quota_mmr    | --         | --      | --         | 0.0%                | 5       | no     | itemknn+quota_mmr    | itemknn+quota_mmr    |
| als                  | als+quota_mmr        | 6          | 1       | 17         | 22.1%               | 5       | no     | als+quota_mmr        | als                  |
| als                  | multvae              | 4,969      | 816     | 6,345      | 100.0%              | 5       | yes    | multvae              | als                  |
| als                  | multvae+quota_mmr    | 340        | 210     | 391        | 100.0%              | 5       | yes    | multvae+quota_mmr    | als                  |
| als                  | gru4rec              | --         | --      | --         | 0.0%                | 5       | no     | als                  | als                  |
| als                  | gru4rec+quota_mmr    | --         | --      | --         | 0.0%                | 5       | no     | als                  | als                  |
| als+quota_mmr        | multvae              | --         | --      | --         | 0.0%                | 5       | no     | multvae              | multvae              |
| als+quota_mmr        | multvae+quota_mmr    | 968        | 606     | 1,088      | 100.0%              | 5       | yes    | multvae+quota_mmr    | als+quota_mmr        |
| als+quota_mmr        | gru4rec              | 190,710    | 178,596 | 236,787    | 100.0%              | 5       | yes    | als+quota_mmr        | gru4rec              |
| als+quota_mmr        | gru4rec+quota_mmr    | --         | --      | --         | 0.0%                | 5       | no     | als+quota_mmr        | als+quota_mmr        |
| multvae              | multvae+quota_mmr    | 289        | 153     | 331        | 5.9%                | 5       | no     | multvae+quota_mmr    | multvae              |
| multvae              | gru4rec              | --         | --      | --         | 0.0%                | 5       | no     | multvae              | multvae              |
| multvae              | gru4rec+quota_mmr    | --         | --      | --         | 0.0%                | 5       | no     | multvae              | multvae              |
| multvae+quota_mmr    | gru4rec              | 102,298    | 99,943  | 122,474    | 100.0%              | 5       | yes    | multvae+quota_mmr    | gru4rec              |
| multvae+quota_mmr    | gru4rec+quota_mmr    | --         | --      | --         | 0.0%                | 5       | no     | multvae+quota_mmr    | multvae+quota_mmr    |
| gru4rec              | gru4rec+quota_mmr    | 9,510      | 7,965   | 12,123     | 5.9%                | 5       | no     | gru4rec+quota_mmr    | gru4rec              |

### rerank_share

| family     | reranker  | cpu_rerank | cpu_serving_total | rerank_share_of_serving | cpu_rerank_setup | serving_multiplier |
|------------|-----------|------------|-------------------|-------------------------|------------------|--------------------|
| popularity | quota_mmr | 5.000e-01  | 5.215e-01         | 95.9%                   | 8.594e-02        | 24.2678            |
| itemknn    | quota_mmr | 5.156e-01  | 5.517e-01         | 93.5%                   | 8.984e-02        | 15.2744            |
| als        | quota_mmr | 6.094e-01  | 6.384e-01         | 95.7%                   | 8.984e-02        | 23.0606            |
| multvae    | quota_mmr | 8.906e-01  | 1.013e+00         | 87.9%                   | 3.750e-01        | 8.2545             |
| gru4rec    | quota_mmr | 9.688e-01  | 1.188e+00         | 81.6%                   | 4.375e-01        | 5.4286             |

### rerankers

| family     | reranker  | repeats | cpu_rerank_per_request | cpu_serving_per_request | rerank_share | ndcg   | exposure_parity | recall | time_bounded | cost_vs_cheapest |
|------------|-----------|---------|------------------------|-------------------------|--------------|--------|-----------------|--------|--------------|------------------|
| als        | quota_mmr | 5       | 3.047e-03              | 3.192e-03               | 95.7%        | 0.0490 | 0.2575          | 0.1050 | no           | 1.0000           |
| gru4rec    | quota_mmr | 5       | 4.844e-03              | 5.938e-03               | 81.6%        | 0.0860 | 0.2620          | 0.1600 | no           | 1.0000           |
| itemknn    | quota_mmr | 5       | 2.578e-03              | 2.759e-03               | 93.5%        | 0.0529 | 0.2480          | 0.1050 | no           | 1.0000           |
| multvae    | quota_mmr | 5       | 4.453e-03              | 5.067e-03               | 87.9%        | 0.0489 | 0.2460          | 0.1000 | no           | 1.0000           |
| popularity | quota_mmr | 5       | 2.500e-03              | 2.607e-03               | 95.9%        | 0.0517 | 0.2505          | 0.0950 | no           | 1.0000           |

### frontier

| n_requests | frontier                                    | dominated                                                                                                      | cheapest   | most_accurate |
|------------|---------------------------------------------|----------------------------------------------------------------------------------------------------------------|------------|---------------|
| 1          | popularity, itemknn+quota_mmr, als, gru4rec | gru4rec+quota_mmr, als+quota_mmr, multvae+quota_mmr, multvae, itemknn, popularity+quota_mmr                    | popularity | gru4rec       |
| 10         | popularity, itemknn+quota_mmr, als, gru4rec | gru4rec+quota_mmr, als+quota_mmr, multvae+quota_mmr, multvae, itemknn, popularity+quota_mmr                    | popularity | gru4rec       |
| 100        | popularity, itemknn+quota_mmr, als, gru4rec | gru4rec+quota_mmr, als+quota_mmr, multvae+quota_mmr, multvae, popularity+quota_mmr, itemknn                    | popularity | gru4rec       |
| 1,000      | popularity, itemknn+quota_mmr, als, gru4rec | gru4rec+quota_mmr, multvae+quota_mmr, als+quota_mmr, multvae, popularity+quota_mmr, itemknn                    | popularity | gru4rec       |
| 10,000     | popularity, als, gru4rec                    | gru4rec+quota_mmr, multvae+quota_mmr, als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr, multvae, itemknn | popularity | gru4rec       |
| 100,000    | popularity, als, gru4rec                    | gru4rec+quota_mmr, multvae+quota_mmr, als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr, multvae, itemknn | popularity | gru4rec       |
| 1,000,000  | popularity, als, gru4rec                    | gru4rec+quota_mmr, multvae+quota_mmr, als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr, multvae, itemknn | popularity | gru4rec       |

### regimes

| n_requests | cheapest   | cost      | unit        | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr | cost.multvae | cost.multvae+quota_mmr | cost.gru4rec | cost.gru4rec+quota_mmr |
|------------|------------|-----------|-------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|--------------|------------------------|--------------|------------------------|
| 1          | popularity | 2.628e-04 | cpu_seconds | 0.000263        | 0.0887                    | 0.195        | 0.288                  | 6        | 6                  | 4            | 4                      | 418          | 433                    |
| 10         | popularity | 1.204e-03 | cpu_seconds | 0.0012          | 0.112                     | 0.197        | 0.313                  | 6        | 6                  | 4            | 4                      | 418          | 433                    |
| 100        | popularity | 1.062e-02 | cpu_seconds | 0.0106          | 0.347                     | 0.213        | 0.561                  | 6        | 6                  | 4            | 5                      | 418          | 434                    |
| 1,000      | popularity | 1.048e-01 | cpu_seconds | 0.105           | 3                         | 0.373        | 3                      | 6        | 9                  | 4            | 9                      | 419          | 439                    |
| 10,000     | popularity | 1.046e+00 | cpu_seconds | 1               | 26                        | 2            | 28                     | 7        | 38                 | 9            | 55                     | 428          | 493                    |
| 100,000    | popularity | 1.046e+01 | cpu_seconds | 10              | 261                       | 18           | 276                    | 21       | 325                | 61           | 511                    | 522          | 1,027                  |
| 1,000,000  | popularity | 1.046e+02 | cpu_seconds | 105             | 2,608                     | 178          | 2,759                  | 157      | 3,198              | 577          | 5,071                  | 1,460        | 6,371                  |

### retraining

| retrain_every | n_requests | cheapest   | training_events | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr | cost.multvae | cost.multvae+quota_mmr | cost.gru4rec | cost.gru4rec+quota_mmr |
|---------------|------------|------------|-----------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|--------------|------------------------|--------------|------------------------|
| never         | 100,000    | popularity | 1               | 10              | 261                       | 18           | 276                    | 21       | 325                | 61           | 511                    | 522          | 1,027                  |
| 1,000,000     | 100,000    | popularity | 1               | 10              | 261                       | 18           | 276                    | 21       | 325                | 61           | 511                    | 522          | 1,027                  |
| 100,000       | 100,000    | popularity | 2               | 10              | 261                       | 18           | 276                    | 27       | 331                | 65           | 515                    | 940          | 1,461                  |
| 10,000        | 100,000    | popularity | 11              | 10              | 262                       | 20           | 279                    | 79       | 384                | 98           | 552                    | 4,701        | 5,361                  |
| 1,000         | 100,000    | popularity | 101             | 10              | 269                       | 37           | 305                    | 599      | 914                | 430          | 925                    | 42,308       | 44,369                 |
| 100           | 100,000    | popularity | 1,001           | 11              | 347                       | 213          | 561                    | 5,802    | 6,212              | 3,748        | 4,651                  | 418,381      | 434,449                |

## luxury_beauty  (1,365 items)

### cost

| family     | reranker  | repeats | ndcg   | recall | exposure_parity | cpu_once  | cpu_per_request | spread_once | spread_per_request | cpu_train | cpu_rerank_setup | cpu_retrieve_score | cpu_retrieve_select | cpu_rerank |
|------------|-----------|---------|--------|--------|-----------------|-----------|-----------------|-------------|--------------------|-----------|------------------|--------------------|---------------------|------------|
| popularity | none      | 5       | 0.0080 | 0.0150 | 1.5000          | 1.315e-04 | 9.921e-05       | 4.1%        | 4.7%               | 1.315e-04 | 0.000e+00        | 1.116e-02          | 8.929e-03           | 0.000e+00  |
| itemknn    | none      | 5       | 0.2002 | 0.2550 | 1.0465          | 7.187e-02 | 1.209e-04       | 0.0%        | 2.9%               | 7.187e-02 | 0.000e+00        | 1.302e-02          | 1.078e-02           | 0.000e+00  |
| als        | none      | 5       | 0.1824 | 0.2350 | 0.8000          | 5.578e+00 | 1.407e-04       | 3.9%        | 27.0%              | 5.578e+00 | 0.000e+00        | 1.838e-02          | 9.766e-03           | 0.000e+00  |
| itemknn    | quota_mmr | 5       | 0.2029 | 0.2600 | 0.2975          | 1.066e-01 | 3.167e-03       | 7.3%        | 2.5%               | 7.187e-02 | 3.472e-02        | 1.302e-02          | 1.078e-02           | 6.094e-01  |
| als        | quota_mmr | 5       | 0.1766 | 0.2300 | 0.2760          | 5.516e+00 | 3.425e-03       | 1.7%        | 5.7%               | 5.484e+00 | 3.281e-02        | 1.953e-02          | 9.766e-03           | 6.562e-01  |
| popularity | quota_mmr | 5       | 0.0081 | 0.0150 | 1.5000          | 3.138e-02 | 4.246e-03       | 5.0%        | 5.6%               | 1.292e-04 | 3.125e-02        | 1.157e-02          | 9.191e-03           | 8.281e-01  |

### breakeven

| a                    | b                    | n_requests | lo      | hi      | replicates_crossing | repeats | stable | cheaper_below        | cheaper_above     |
|----------------------|----------------------|------------|---------|---------|---------------------|---------|--------|----------------------|-------------------|
| popularity           | popularity+quota_mmr | --         | --      | --      | 0.0%                | 5       | no     | popularity           | popularity        |
| popularity           | itemknn              | --         | --      | --      | 0.0%                | 5       | no     | popularity           | popularity        |
| popularity           | itemknn+quota_mmr    | --         | --      | --      | 0.0%                | 5       | no     | popularity           | popularity        |
| popularity           | als                  | --         | --      | --      | 0.0%                | 5       | no     | popularity           | popularity        |
| popularity           | als+quota_mmr        | --         | --      | --      | 0.0%                | 5       | no     | popularity           | popularity        |
| popularity+quota_mmr | itemknn              | 10         | 9       | 10      | 100.0%              | 5       | yes    | popularity+quota_mmr | itemknn           |
| popularity+quota_mmr | itemknn+quota_mmr    | 70         | 57      | 75      | 100.0%              | 5       | yes    | popularity+quota_mmr | itemknn+quota_mmr |
| popularity+quota_mmr | als                  | 1,351      | 1,279   | 1,364   | 100.0%              | 5       | yes    | popularity+quota_mmr | als               |
| popularity+quota_mmr | als+quota_mmr        | 6,680      | 5,203   | 7,522   | 100.0%              | 5       | yes    | popularity+quota_mmr | als+quota_mmr     |
| itemknn              | itemknn+quota_mmr    | --         | --      | --      | 0.0%                | 5       | no     | itemknn              | itemknn           |
| itemknn              | als                  | 565,002    | 405,182 | 782,320 | 31.1%               | 5       | no     | itemknn              | als               |
| itemknn              | als+quota_mmr        | --         | --      | --      | 0.0%                | 5       | no     | itemknn              | itemknn           |
| itemknn+quota_mmr    | als                  | 1,807      | 1,757   | 1,821   | 100.0%              | 5       | yes    | itemknn+quota_mmr    | als               |
| itemknn+quota_mmr    | als+quota_mmr        | --         | --      | --      | 0.0%                | 5       | no     | itemknn+quota_mmr    | itemknn+quota_mmr |
| als                  | als+quota_mmr        | 22         | 18      | 47      | 64.6%               | 5       | no     | als+quota_mmr        | als               |

### rerank_share

| family     | reranker  | cpu_rerank | cpu_serving_total | rerank_share_of_serving | cpu_rerank_setup | serving_multiplier |
|------------|-----------|------------|-------------------|-------------------------|------------------|--------------------|
| popularity | quota_mmr | 8.281e-01  | 8.492e-01         | 97.6%                   | 3.125e-02        | 41.3911            |
| itemknn    | quota_mmr | 6.094e-01  | 6.334e-01         | 96.2%                   | 3.472e-02        | 26.6075            |
| als        | quota_mmr | 6.562e-01  | 6.850e-01         | 95.8%                   | 3.281e-02        | 23.9333            |

### rerankers

| family     | reranker  | repeats | cpu_rerank_per_request | cpu_serving_per_request | rerank_share | ndcg   | exposure_parity | recall | time_bounded | cost_vs_cheapest |
|------------|-----------|---------|------------------------|-------------------------|--------------|--------|-----------------|--------|--------------|------------------|
| als        | quota_mmr | 5       | 3.281e-03              | 3.425e-03               | 95.8%        | 0.1766 | 0.2760          | 0.2300 | no           | 1.0000           |
| itemknn    | quota_mmr | 5       | 3.047e-03              | 3.167e-03               | 96.2%        | 0.2029 | 0.2975          | 0.2600 | no           | 1.0000           |
| popularity | quota_mmr | 5       | 4.141e-03              | 4.246e-03               | 97.6%        | 0.0081 | 1.5000          | 0.0150 | no           | 1.0000           |

### frontier

| n_requests | frontier                                                     | dominated                                | cheapest   | most_accurate     |
|------------|--------------------------------------------------------------|------------------------------------------|------------|-------------------|
| 1          | popularity, popularity+quota_mmr, itemknn, itemknn+quota_mmr | als, als+quota_mmr                       | popularity | itemknn+quota_mmr |
| 10         | popularity, itemknn, itemknn+quota_mmr                       | als, als+quota_mmr, popularity+quota_mmr | popularity | itemknn+quota_mmr |
| 100        | popularity, itemknn, itemknn+quota_mmr                       | als+quota_mmr, als, popularity+quota_mmr | popularity | itemknn+quota_mmr |
| 1,000      | popularity, itemknn, itemknn+quota_mmr                       | als+quota_mmr, als, popularity+quota_mmr | popularity | itemknn+quota_mmr |
| 10,000     | popularity, itemknn, itemknn+quota_mmr                       | popularity+quota_mmr, als+quota_mmr, als | popularity | itemknn+quota_mmr |
| 100,000    | popularity, itemknn, itemknn+quota_mmr                       | popularity+quota_mmr, als+quota_mmr, als | popularity | itemknn+quota_mmr |
| 1,000,000  | popularity, itemknn, itemknn+quota_mmr                       | popularity+quota_mmr, als+quota_mmr, als | popularity | itemknn+quota_mmr |

### regimes

| n_requests | cheapest   | cost      | unit        | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|------------|------------|-----------|-------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| 1          | popularity | 2.307e-04 | cpu_seconds | 0.000231        | 0.0356                    | 0.072        | 0.11                   | 6        | 6                  |
| 10         | popularity | 1.124e-03 | cpu_seconds | 0.00112         | 0.0738                    | 0.0731       | 0.138                  | 6        | 6                  |
| 100        | popularity | 1.005e-02 | cpu_seconds | 0.0101          | 0.456                     | 0.084        | 0.423                  | 6        | 6                  |
| 1,000      | popularity | 9.934e-02 | cpu_seconds | 0.0993          | 4                         | 0.193        | 3                      | 6        | 9                  |
| 10,000     | popularity | 9.922e-01 | cpu_seconds | 0.992           | 42                        | 1            | 32                     | 7        | 40                 |
| 100,000    | popularity | 9.921e+00 | cpu_seconds | 10              | 425                       | 12           | 317                    | 20       | 348                |
| 1,000,000  | popularity | 9.921e+01 | cpu_seconds | 99              | 4,246                     | 121          | 3,167                  | 146      | 3,430              |

### retraining

| retrain_every | n_requests | cheapest   | training_events | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|---------------|------------|------------|-----------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| never         | 100,000    | popularity | 1               | 10              | 425                       | 12           | 317                    | 20       | 348                |
| 1,000,000     | 100,000    | popularity | 1               | 10              | 425                       | 12           | 317                    | 20       | 348                |
| 100,000       | 100,000    | popularity | 2               | 10              | 425                       | 12           | 317                    | 25       | 354                |
| 10,000        | 100,000    | popularity | 11              | 10              | 425                       | 13           | 318                    | 75       | 403                |
| 1,000         | 100,000    | popularity | 101             | 10              | 428                       | 19           | 327                    | 577      | 900                |
| 100           | 100,000    | popularity | 1,001           | 10              | 456                       | 84           | 423                    | 5,598    | 5,864              |

## digital_music  (11,268 items)

### cost

| family     | reranker  | repeats | ndcg   | recall | exposure_parity | cpu_once  | cpu_per_request | spread_once | spread_per_request | cpu_train | cpu_rerank_setup | cpu_retrieve_score | cpu_retrieve_select | cpu_rerank |
|------------|-----------|---------|--------|--------|-----------------|-----------|-----------------|-------------|--------------------|-----------|------------------|--------------------|---------------------|------------|
| popularity | none      | 5       | 0.0049 | 0.0100 | 1.5000          | 3.144e-04 | 3.348e-04       | 2.4%        | 3.9%               | 3.144e-04 | 0.000e+00        | 1.488e-02          | 5.208e-02           | 0.000e+00  |
| itemknn    | none      | 5       | 0.0602 | 0.0850 | 1.1775          | 3.281e-01 | 3.971e-04       | 9.5%        | 10.3%              | 3.281e-01 | 0.000e+00        | 2.604e-02          | 5.208e-02           | 0.000e+00  |
| als        | none      | 5       | 0.0411 | 0.0650 | 1.4665          | 3.031e+01 | 5.283e-04       | 2.6%        | 30.2%              | 3.031e+01 | 0.000e+00        | 5.357e-02          | 5.208e-02           | 0.000e+00  |
| als        | quota_mmr | 5       | 0.0452 | 0.0700 | 0.4515          | 3.053e+01 | 3.307e-03       | 1.4%        | 5.2%               | 3.039e+01 | 1.354e-01        | 6.563e-02          | 5.469e-02           | 5.312e-01  |
| itemknn    | quota_mmr | 5       | 0.0602 | 0.0800 | 0.2670          | 4.844e-01 | 3.746e-03       | 4.3%        | 8.3%               | 3.438e-01 | 1.406e-01        | 2.604e-02          | 5.729e-02           | 6.719e-01  |
| popularity | quota_mmr | 5       | 0.0049 | 0.0100 | 1.5000          | 1.357e-01 | 6.051e-03       | 3.8%        | 2.5%               | 3.182e-04 | 1.354e-01        | 1.562e-02          | 5.469e-02           | 1.141e+00  |

### breakeven

| a                    | b                    | n_requests | lo     | hi     | replicates_crossing | repeats | stable | cheaper_below        | cheaper_above     |
|----------------------|----------------------|------------|--------|--------|---------------------|---------|--------|----------------------|-------------------|
| popularity           | popularity+quota_mmr | --         | --     | --     | 0.0%                | 5       | no     | popularity           | popularity        |
| popularity           | itemknn              | --         | --     | --     | 0.0%                | 5       | no     | popularity           | popularity        |
| popularity           | itemknn+quota_mmr    | --         | --     | --     | 0.0%                | 5       | no     | popularity           | popularity        |
| popularity           | als                  | --         | --     | --     | 0.0%                | 5       | no     | popularity           | popularity        |
| popularity           | als+quota_mmr        | --         | --     | --     | 0.0%                | 5       | no     | popularity           | popularity        |
| popularity+quota_mmr | itemknn              | 34         | 33     | 40     | 100.0%              | 5       | yes    | popularity+quota_mmr | itemknn           |
| popularity+quota_mmr | itemknn+quota_mmr    | 149        | 143    | 175    | 100.0%              | 5       | yes    | popularity+quota_mmr | itemknn+quota_mmr |
| popularity+quota_mmr | als                  | 5,464      | 5,387  | 5,657  | 100.0%              | 5       | yes    | popularity+quota_mmr | als               |
| popularity+quota_mmr | als+quota_mmr        | 11,025     | 10,525 | 11,333 | 100.0%              | 5       | yes    | popularity+quota_mmr | als+quota_mmr     |
| itemknn              | itemknn+quota_mmr    | --         | --     | --     | 0.0%                | 5       | no     | itemknn              | itemknn           |
| itemknn              | als                  | --         | --     | --     | 0.0%                | 5       | no     | itemknn              | itemknn           |
| itemknn              | als+quota_mmr        | --         | --     | --     | 0.0%                | 5       | no     | itemknn              | itemknn           |
| itemknn+quota_mmr    | als                  | 9,273      | 8,579  | 9,776  | 100.0%              | 5       | yes    | itemknn+quota_mmr    | als               |
| itemknn+quota_mmr    | als+quota_mmr        | 66,103     | 42,837 | 80,641 | 100.0%              | 5       | yes    | itemknn+quota_mmr    | als+quota_mmr     |
| als                  | als+quota_mmr        | 36         | 13     | 87     | 14.1%               | 5       | no     | als+quota_mmr        | als               |

### rerank_share

| family     | reranker  | cpu_rerank | cpu_serving_total | rerank_share_of_serving | cpu_rerank_setup | serving_multiplier |
|------------|-----------|------------|-------------------|-------------------------|------------------|--------------------|
| popularity | quota_mmr | 1.141e+00  | 1.210e+00         | 94.3%                   | 1.354e-01        | 17.3957            |
| itemknn    | quota_mmr | 6.719e-01  | 7.492e-01         | 88.9%                   | 1.406e-01        | 9.0000             |
| als        | quota_mmr | 5.312e-01  | 6.615e-01         | 81.9%                   | 1.354e-01        | 5.5333             |

### rerankers

| family     | reranker  | repeats | cpu_rerank_per_request | cpu_serving_per_request | rerank_share | ndcg   | exposure_parity | recall | time_bounded | cost_vs_cheapest |
|------------|-----------|---------|------------------------|-------------------------|--------------|--------|-----------------|--------|--------------|------------------|
| als        | quota_mmr | 5       | 2.656e-03              | 3.307e-03               | 81.9%        | 0.0452 | 0.4515          | 0.0700 | no           | 1.0000           |
| itemknn    | quota_mmr | 5       | 3.359e-03              | 3.746e-03               | 88.9%        | 0.0602 | 0.2670          | 0.0800 | no           | 1.0000           |
| popularity | quota_mmr | 5       | 5.703e-03              | 6.051e-03               | 94.3%        | 0.0049 | 1.5000          | 0.0100 | no           | 1.0000           |

### frontier

| n_requests | frontier                               | dominated                                | cheapest   | most_accurate     |
|------------|----------------------------------------|------------------------------------------|------------|-------------------|
| 1          | popularity, itemknn, itemknn+quota_mmr | als+quota_mmr, als, popularity+quota_mmr | popularity | itemknn+quota_mmr |
| 10         | popularity, itemknn, itemknn+quota_mmr | als+quota_mmr, als, popularity+quota_mmr | popularity | itemknn+quota_mmr |
| 100        | popularity, itemknn, itemknn+quota_mmr | als+quota_mmr, als, popularity+quota_mmr | popularity | itemknn+quota_mmr |
| 1,000      | popularity, itemknn, itemknn+quota_mmr | als+quota_mmr, als, popularity+quota_mmr | popularity | itemknn+quota_mmr |
| 10,000     | popularity, itemknn, itemknn+quota_mmr | als+quota_mmr, popularity+quota_mmr, als | popularity | itemknn+quota_mmr |
| 100,000    | popularity, itemknn, itemknn+quota_mmr | popularity+quota_mmr, als+quota_mmr, als | popularity | itemknn+quota_mmr |
| 1,000,000  | popularity, itemknn, itemknn+quota_mmr | popularity+quota_mmr, als+quota_mmr, als | popularity | itemknn+quota_mmr |

### regimes

| n_requests | cheapest   | cost      | unit        | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|------------|------------|-----------|-------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| 1          | popularity | 6.492e-04 | cpu_seconds | 0.000649        | 0.142                     | 0.329        | 0.488                  | 30       | 31                 |
| 10         | popularity | 3.663e-03 | cpu_seconds | 0.00366         | 0.196                     | 0.332        | 0.522                  | 30       | 31                 |
| 100        | popularity | 3.380e-02 | cpu_seconds | 0.0338          | 0.741                     | 0.368        | 0.859                  | 30       | 31                 |
| 1,000      | popularity | 3.351e-01 | cpu_seconds | 0.335           | 6                         | 0.725        | 4                      | 31       | 34                 |
| 10,000     | popularity | 3.349e+00 | cpu_seconds | 3               | 61                        | 4            | 38                     | 36       | 64                 |
| 100,000    | popularity | 3.348e+01 | cpu_seconds | 33              | 605                       | 40           | 375                    | 83       | 361                |
| 1,000,000  | popularity | 3.348e+02 | cpu_seconds | 335             | 6,051                     | 397          | 3,746                  | 559      | 3,338              |

### retraining

| retrain_every | n_requests | cheapest   | training_events | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|---------------|------------|------------|-----------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| never         | 100,000    | popularity | 1               | 33              | 605                       | 40           | 375                    | 83       | 361                |
| 1,000,000     | 100,000    | popularity | 1               | 33              | 605                       | 40           | 375                    | 83       | 361                |
| 100,000       | 100,000    | popularity | 2               | 33              | 605                       | 40           | 376                    | 113      | 392                |
| 10,000        | 100,000    | popularity | 11              | 33              | 607                       | 43           | 380                    | 386      | 667                |
| 1,000         | 100,000    | popularity | 101             | 34              | 619                       | 73           | 424                    | 3,114    | 3,414              |
| 100           | 100,000    | popularity | 1,001           | 34              | 741                       | 368          | 859                    | 30,396   | 30,887             |
