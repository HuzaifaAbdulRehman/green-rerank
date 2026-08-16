# Results tables

Generated from `results\main`.

## gift_cards  (147 items)

### cost

| family     | reranker  | repeats | ndcg   | recall | exposure_parity | cpu_once  | cpu_per_request | spread_once | spread_per_request | cpu_train | cpu_rerank_setup | cpu_retrieve_score | cpu_retrieve_select | cpu_rerank |
|------------|-----------|---------|--------|--------|-----------------|-----------|-----------------|-------------|--------------------|-----------|------------------|--------------------|---------------------|------------|
| itemknn    | none      | 5       | 0.1715 | 0.3550 | 1.3635          | 2.042e-03 | 6.532e-05       | 35.8%       | 25.0%              | 2.042e-03 | 0.000e+00        | 1.042e-02          | 2.648e-03           | 0.000e+00  |
| popularity | none      | 5       | 0.0729 | 0.1450 | 1.5000          | 8.376e-05 | 6.587e-05       | 51.1%       | 15.9%              | 8.376e-05 | 0.000e+00        | 1.042e-02          | 2.561e-03           | 0.000e+00  |
| als        | none      | 5       | 0.0593 | 0.1400 | 0.4890          | 7.188e-01 | 6.882e-05       | 15.2%       | 26.0%              | 7.188e-01 | 0.000e+00        | 1.116e-02          | 2.604e-03           | 0.000e+00  |
| popularity | quota_mmr | 5       | 0.0525 | 0.0900 | 0.2995          | 5.778e-04 | 1.862e-03       | 23.1%       | 20.0%              | 8.410e-05 | 4.937e-04        | 1.008e-02          | 2.790e-03           | 3.594e-01  |
| itemknn    | quota_mmr | 5       | 0.1123 | 0.2100 | 0.2660          | 2.516e-03 | 1.940e-03       | 49.3%       | 28.8%              | 2.029e-03 | 4.945e-04        | 1.042e-02          | 2.583e-03           | 3.750e-01  |
| als        | quota_mmr | 5       | 0.0546 | 0.1300 | 0.2610          | 7.192e-01 | 2.180e-03       | 36.9%       | 22.3%              | 7.188e-01 | 5.315e-04        | 1.157e-02          | 2.520e-03           | 4.219e-01  |

### breakeven

| a                    | b                    | n_requests | lo     | hi      | replicates_crossing | repeats | stable | cheaper_below        | cheaper_above        |
|----------------------|----------------------|------------|--------|---------|---------------------|---------|--------|----------------------|----------------------|
| popularity           | popularity+quota_mmr | --         | --     | --      | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | itemknn              | 947        | 192    | 3,576   | 48.0%               | 5       | no     | popularity           | itemknn              |
| popularity           | itemknn+quota_mmr    | --         | --     | --      | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | als                  | 160,850    | 75,202 | 430,750 | 24.3%               | 5       | no     | popularity           | als                  |
| popularity           | als+quota_mmr        | --         | --     | --      | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity+quota_mmr | itemknn              | 0.825      | 0.698  | 1       | 100.0%              | 5       | yes    | popularity+quota_mmr | itemknn              |
| popularity+quota_mmr | itemknn+quota_mmr    | 143        | 18     | 1,436   | 24.9%               | 5       | no     | popularity+quota_mmr | itemknn+quota_mmr    |
| popularity+quota_mmr | als                  | 401        | 354    | 474     | 100.0%              | 5       | yes    | popularity+quota_mmr | als                  |
| popularity+quota_mmr | als+quota_mmr        | --         | --     | --      | 0.0%                | 5       | no     | popularity+quota_mmr | popularity+quota_mmr |
| itemknn              | itemknn+quota_mmr    | 0.0712     | 0.0126 | 0.113   | 5.5%                | 5       | no     | itemknn+quota_mmr    | itemknn              |
| itemknn              | als                  | 137,892    | 54,601 | 680,519 | 24.3%               | 5       | no     | itemknn              | als                  |
| itemknn              | als+quota_mmr        | --         | --     | --      | 0.0%                | 5       | no     | itemknn              | itemknn              |
| itemknn+quota_mmr    | als                  | 365        | 287    | 420     | 100.0%              | 5       | yes    | itemknn+quota_mmr    | als                  |
| itemknn+quota_mmr    | als+quota_mmr        | 4,369      | 4,035  | 4,621   | 22.0%               | 5       | no     | itemknn+quota_mmr    | als+quota_mmr        |
| als                  | als+quota_mmr        | 29         | 7      | 44      | 34.2%               | 5       | no     | als+quota_mmr        | als                  |

### rerank_share

| family     | reranker  | cpu_rerank | cpu_serving_total | rerank_share_of_serving | cpu_rerank_setup | serving_multiplier |
|------------|-----------|------------|-------------------|-------------------------|------------------|--------------------|
| popularity | quota_mmr | 3.594e-01  | 3.724e-01         | 96.1%                   | 4.937e-04        | 25.7775            |
| itemknn    | quota_mmr | 3.750e-01  | 3.880e-01         | 96.6%                   | 4.945e-04        | 29.8477            |
| als        | quota_mmr | 4.219e-01  | 4.360e-01         | 96.8%                   | 5.315e-04        | 31.2212            |

### frontier

| n_requests | frontier            | dominated                                                               | cheapest   | most_accurate |
|------------|---------------------|-------------------------------------------------------------------------|------------|---------------|
| 1          | popularity, itemknn | als+quota_mmr, als, itemknn+quota_mmr, popularity+quota_mmr             | popularity | itemknn       |
| 10         | popularity, itemknn | als+quota_mmr, als, itemknn+quota_mmr, popularity+quota_mmr             | popularity | itemknn       |
| 100        | popularity, itemknn | als+quota_mmr, als, itemknn+quota_mmr, popularity+quota_mmr             | popularity | itemknn       |
| 1,000      | popularity, itemknn | als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr, als             | popularity | itemknn       |
| 10,000     | itemknn             | als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr, als, popularity | itemknn    | itemknn       |
| 100,000    | itemknn             | als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr, als, popularity | itemknn    | itemknn       |
| 1,000,000  | itemknn             | als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr, als, popularity | itemknn    | itemknn       |

### regimes

| n_requests | cheapest   | cost      | unit        | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|------------|------------|-----------|-------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| 1          | popularity | 1.496e-04 | cpu_seconds | 0.00015         | 0.00244                   | 0.00211      | 0.00446                | 0.719    | 0.721              |
| 10         | popularity | 7.425e-04 | cpu_seconds | 0.000742        | 0.0192                    | 0.0027       | 0.0219                 | 0.719    | 0.741              |
| 100        | popularity | 6.671e-03 | cpu_seconds | 0.00667         | 0.187                     | 0.00857      | 0.197                  | 0.726    | 0.937              |
| 1,000      | popularity | 6.596e-02 | cpu_seconds | 0.066           | 2                         | 0.0674       | 2                      | 0.788    | 3                  |
| 10,000     | itemknn    | 6.553e-01 | cpu_seconds | 0.659           | 19                        | 0.655        | 19                     | 1        | 23                 |
| 100,000    | itemknn    | 6.535e+00 | cpu_seconds | 7               | 186                       | 7            | 194                    | 8        | 219                |
| 1,000,000  | itemknn    | 6.533e+01 | cpu_seconds | 66              | 1,862                     | 65           | 1,940                  | 70       | 2,181              |

### retraining

| retrain_every | n_requests | cheapest   | training_events | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|---------------|------------|------------|-----------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| never         | 100,000    | itemknn    | 1               | 7               | 186                       | 7            | 194                    | 8        | 219                |
| 1,000,000     | 100,000    | itemknn    | 1               | 7               | 186                       | 7            | 194                    | 8        | 219                |
| 100,000       | 100,000    | itemknn    | 2               | 7               | 186                       | 7            | 194                    | 8        | 219                |
| 10,000        | 100,000    | itemknn    | 11              | 7               | 186                       | 7            | 194                    | 15       | 226                |
| 1,000         | 100,000    | popularity | 101             | 7               | 186                       | 7            | 194                    | 79       | 291                |
| 100           | 100,000    | popularity | 1,001           | 7               | 187                       | 9            | 197                    | 726      | 938                |

## software  (727 items)

### cost

| family     | reranker  | repeats | ndcg   | recall | exposure_parity | cpu_once  | cpu_per_request | spread_once | spread_per_request | cpu_train | cpu_rerank_setup | cpu_retrieve_score | cpu_retrieve_select | cpu_rerank |
|------------|-----------|---------|--------|--------|-----------------|-----------|-----------------|-------------|--------------------|-----------|------------------|--------------------|---------------------|------------|
| popularity | none      | 5       | 0.0034 | 0.0100 | 1.0000          | 1.030e-04 | 8.785e-05       | 33.2%       | 25.6%              | 1.030e-04 | 0.000e+00        | 1.078e-02          | 6.793e-03           | 0.000e+00  |
| als        | none      | 5       | 0.0868 | 0.1650 | 0.6500          | 2.828e+00 | 9.722e-05       | 24.3%       | 41.7%              | 2.828e+00 | 0.000e+00        | 1.250e-02          | 7.102e-03           | 0.000e+00  |
| itemknn    | none      | 5       | 0.0737 | 0.1450 | 0.9270          | 2.344e-02 | 9.730e-05       | 40.0%       | 24.0%              | 2.344e-02 | 0.000e+00        | 1.202e-02          | 7.440e-03           | 0.000e+00  |
| popularity | quota_mmr | 5       | 0.0046 | 0.0100 | 0.0000          | 9.577e-03 | 2.668e-03       | 14.8%       | 26.9%              | 1.078e-04 | 9.470e-03        | 1.202e-02          | 6.378e-03           | 5.156e-01  |
| itemknn    | quota_mmr | 5       | 0.0666 | 0.1200 | 0.2725          | 3.209e-02 | 3.378e-03       | 19.1%       | 32.5%              | 2.232e-02 | 9.766e-03        | 1.250e-02          | 7.267e-03           | 6.562e-01  |
| als        | quota_mmr | 5       | 0.0762 | 0.1300 | 0.2535          | 2.806e+00 | 3.551e-03       | 22.9%       | 23.5%              | 2.797e+00 | 9.470e-03        | 1.488e-02          | 6.944e-03           | 6.875e-01  |

### breakeven

| a                    | b                    | n_requests | lo      | hi         | replicates_crossing | repeats | stable | cheaper_below        | cheaper_above        |
|----------------------|----------------------|------------|---------|------------|---------------------|---------|--------|----------------------|----------------------|
| popularity           | popularity+quota_mmr | --         | --      | --         | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | itemknn              | 3,525      | 1,909   | 5,063      | 21.6%               | 5       | no     | popularity           | itemknn              |
| popularity           | itemknn+quota_mmr    | --         | --      | --         | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | als                  | 379,587    | 197,375 | 796,363    | 23.1%               | 5       | no     | popularity           | als                  |
| popularity           | als+quota_mmr        | --         | --      | --         | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity+quota_mmr | itemknn              | 5          | 4       | 9          | 100.0%              | 5       | yes    | popularity+quota_mmr | itemknn              |
| popularity+quota_mmr | itemknn+quota_mmr    | 27,453     | 9,012   | 27,453     | 1.7%                | 5       | no     | popularity+quota_mmr | itemknn+quota_mmr    |
| popularity+quota_mmr | als                  | 1,099      | 925     | 1,324      | 100.0%              | 5       | yes    | popularity+quota_mmr | als                  |
| popularity+quota_mmr | als+quota_mmr        | --         | --      | --         | 0.0%                | 5       | no     | popularity+quota_mmr | popularity+quota_mmr |
| itemknn              | itemknn+quota_mmr    | 0.0607     | 0.0607  | 0.0607     | 0.4%                | 5       | no     | itemknn+quota_mmr    | itemknn              |
| itemknn              | als                  | 492,917    | 115,859 | 42,076,125 | 64.5%               | 5       | no     | itemknn              | als                  |
| itemknn              | als+quota_mmr        | --         | --      | --         | 0.0%                | 5       | no     | itemknn              | itemknn              |
| itemknn+quota_mmr    | als                  | 852        | 648     | 1,054      | 100.0%              | 5       | yes    | itemknn+quota_mmr    | als                  |
| itemknn+quota_mmr    | als+quota_mmr        | 5,778      | 3,516   | 11,870     | 29.5%               | 5       | no     | itemknn+quota_mmr    | als+quota_mmr        |
| als                  | als+quota_mmr        | 107        | 1       | 192        | 57.9%               | 5       | no     | als+quota_mmr        | als                  |

### rerank_share

| family     | reranker  | cpu_rerank | cpu_serving_total | rerank_share_of_serving | cpu_rerank_setup | serving_multiplier |
|------------|-----------|------------|-------------------|-------------------------|------------------|--------------------|
| popularity | quota_mmr | 5.156e-01  | 5.336e-01         | 96.5%                   | 9.470e-03        | 28.8028            |
| itemknn    | quota_mmr | 6.562e-01  | 6.755e-01         | 97.1%                   | 9.766e-03        | 35.0261            |
| als        | quota_mmr | 6.875e-01  | 7.102e-01         | 97.1%                   | 9.470e-03        | 34.2021            |

### frontier

| n_requests | frontier                                                      | dominated                                              | cheapest   | most_accurate |
|------------|---------------------------------------------------------------|--------------------------------------------------------|------------|---------------|
| 1          | popularity, popularity+quota_mmr, itemknn, als+quota_mmr, als | itemknn+quota_mmr                                      | popularity | als           |
| 10         | popularity, itemknn, als                                      | als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr | popularity | als           |
| 100        | popularity, itemknn, als                                      | als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr | popularity | als           |
| 1,000      | popularity, itemknn, als                                      | als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr | popularity | als           |
| 10,000     | popularity, itemknn, als                                      | als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr | popularity | als           |
| 100,000    | popularity, itemknn, als                                      | als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr | popularity | als           |
| 1,000,000  | popularity, itemknn, als                                      | als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr | popularity | als           |

### regimes

| n_requests | cheapest   | cost      | unit        | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|------------|------------|-----------|-------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| 1          | popularity | 1.909e-04 | cpu_seconds | 0.000191        | 0.0122                    | 0.0235       | 0.0355                 | 3        | 3                  |
| 10         | popularity | 9.815e-04 | cpu_seconds | 0.000982        | 0.0363                    | 0.0244       | 0.0659                 | 3        | 3                  |
| 100        | popularity | 8.888e-03 | cpu_seconds | 0.00889         | 0.276                     | 0.0332       | 0.37                   | 3        | 3                  |
| 1,000      | popularity | 8.795e-02 | cpu_seconds | 0.0879          | 3                         | 0.121        | 3                      | 3        | 6                  |
| 10,000     | popularity | 8.786e-01 | cpu_seconds | 0.879           | 27                        | 0.996        | 34                     | 4        | 38                 |
| 100,000    | popularity | 8.785e+00 | cpu_seconds | 9               | 267                       | 10           | 338                    | 13       | 358                |
| 1,000,000  | popularity | 8.785e+01 | cpu_seconds | 88              | 2,668                     | 97           | 3,378                  | 100      | 3,554              |

### retraining

| retrain_every | n_requests | cheapest   | training_events | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|---------------|------------|------------|-----------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| never         | 100,000    | popularity | 1               | 9               | 267                       | 10           | 338                    | 13       | 358                |
| 1,000,000     | 100,000    | popularity | 1               | 9               | 267                       | 10           | 338                    | 13       | 358                |
| 100,000       | 100,000    | popularity | 2               | 9               | 267                       | 10           | 338                    | 15       | 361                |
| 10,000        | 100,000    | popularity | 11              | 9               | 267                       | 10           | 338                    | 41       | 386                |
| 1,000         | 100,000    | popularity | 101             | 9               | 268                       | 12           | 341                    | 295      | 639                |
| 100           | 100,000    | popularity | 1,001           | 9               | 276                       | 33           | 370                    | 2,841    | 3,164              |

## ml100k  (1,349 items)

### cost

| family     | reranker  | repeats | ndcg   | recall | exposure_parity | cpu_once  | cpu_per_request | spread_once | spread_per_request | cpu_train | cpu_rerank_setup | cpu_retrieve_score | cpu_retrieve_select | cpu_rerank |
|------------|-----------|---------|--------|--------|-----------------|-----------|-----------------|-------------|--------------------|-----------|------------------|--------------------|---------------------|------------|
| popularity | none      | 5       | 0.0527 | 0.1050 | 1.1855          | 1.668e-04 | 1.140e-04       | 24.6%       | 13.7%              | 1.668e-04 | 0.000e+00        | 1.202e-02          | 1.042e-02           | 0.000e+00  |
| als        | none      | 5       | 0.0685 | 0.1550 | 0.8280          | 5.781e+00 | 1.360e-04       | 25.1%       | 61.0%              | 5.781e+00 | 0.000e+00        | 1.562e-02          | 1.008e-02           | 0.000e+00  |
| itemknn    | none      | 5       | 0.0471 | 0.1000 | 1.1425          | 1.953e-01 | 1.855e-04       | 12.0%       | 37.0%              | 1.953e-01 | 0.000e+00        | 2.734e-02          | 9.766e-03           | 0.000e+00  |
| multvae    | none      | 5       | 0.0448 | 0.1000 | 0.9745          | 4.375e+00 | 6.510e-04       | 41.8%       | 57.7%              | 4.375e+00 | 0.000e+00        | 7.812e-02          | 5.208e-02           | 0.000e+00  |
| gru4rec    | none      | 5       | 0.0995 | 0.1850 | 0.9025          | 4.515e+02 | 1.198e-03       | 21.5%       | 16.1%              | 4.515e+02 | 0.000e+00        | 1.875e-01          | 5.208e-02           | 0.000e+00  |
| popularity | quota_mmr | 5       | 0.0539 | 0.1050 | 0.2570          | 9.782e-02 | 2.695e-03       | 12.0%       | 23.9%              | 1.637e-04 | 9.766e-02        | 1.202e-02          | 1.042e-02           | 5.156e-01  |
| itemknn    | quota_mmr | 5       | 0.0468 | 0.0950 | 0.2465          | 2.891e-01 | 2.835e-03       | 25.2%       | 23.8%              | 1.953e-01 | 9.375e-02        | 2.604e-02          | 9.766e-03           | 5.312e-01  |
| als        | quota_mmr | 5       | 0.0471 | 0.0950 | 0.2560          | 5.984e+00 | 3.289e-03       | 20.6%       | 13.1%              | 5.891e+00 | 9.375e-02        | 1.953e-02          | 1.008e-02           | 6.250e-01  |
| multvae    | quota_mmr | 5       | 0.0411 | 0.0850 | 0.2480          | 4.969e+00 | 5.282e-03       | 32.4%       | 22.4%              | 4.531e+00 | 4.375e-01        | 9.375e-02          | 5.208e-02           | 9.062e-01  |
| gru4rec    | quota_mmr | 5       | 0.0669 | 0.1200 | 0.2605          | 4.557e+02 | 6.797e-03       | 45.9%       | 30.2%              | 4.550e+02 | 6.250e-01        | 2.109e-01          | 6.250e-02           | 1.078e+00  |

### breakeven

| a                    | b                    | n_requests | lo        | hi        | replicates_crossing | repeats | stable | cheaper_below        | cheaper_above        |
|----------------------|----------------------|------------|-----------|-----------|---------------------|---------|--------|----------------------|----------------------|
| popularity           | popularity+quota_mmr | --         | --        | --        | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | itemknn              | --         | --        | --        | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | itemknn+quota_mmr    | --         | --        | --        | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | als                  | 3,440,884  | 648,764   | 5,391,603 | 5.4%                | 5       | no     | popularity           | als                  |
| popularity           | als+quota_mmr        | --         | --        | --        | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | multvae              | --         | --        | --        | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | multvae+quota_mmr    | --         | --        | --        | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | gru4rec              | --         | --        | --        | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity           | gru4rec+quota_mmr    | --         | --        | --        | 0.0%                | 5       | no     | popularity           | popularity           |
| popularity+quota_mmr | itemknn              | 41         | 32        | 49        | 100.0%              | 5       | yes    | popularity+quota_mmr | itemknn              |
| popularity+quota_mmr | itemknn+quota_mmr    | 460        | 440       | 694       | 5.1%                | 5       | no     | popularity+quota_mmr | itemknn+quota_mmr    |
| popularity+quota_mmr | als                  | 2,259      | 1,814     | 2,594     | 100.0%              | 5       | yes    | popularity+quota_mmr | als                  |
| popularity+quota_mmr | als+quota_mmr        | 164,753    | 164,753   | 164,753   | 0.4%                | 5       | no     | popularity+quota_mmr | als+quota_mmr        |
| popularity+quota_mmr | multvae              | 2,155      | 1,632     | 2,815     | 100.0%              | 5       | yes    | popularity+quota_mmr | multvae              |
| popularity+quota_mmr | multvae+quota_mmr    | --         | --        | --        | 0.0%                | 5       | no     | popularity+quota_mmr | popularity+quota_mmr |
| popularity+quota_mmr | gru4rec              | 301,611    | 219,110   | 353,124   | 100.0%              | 5       | yes    | popularity+quota_mmr | gru4rec              |
| popularity+quota_mmr | gru4rec+quota_mmr    | --         | --        | --        | 0.0%                | 5       | no     | popularity+quota_mmr | popularity+quota_mmr |
| itemknn              | itemknn+quota_mmr    | --         | --        | --        | 0.0%                | 5       | no     | itemknn              | itemknn              |
| itemknn              | als                  | 112,730    | 51,128    | 180,720   | 95.0%               | 5       | yes    | itemknn              | als                  |
| itemknn              | als+quota_mmr        | --         | --        | --        | 0.0%                | 5       | no     | itemknn              | itemknn              |
| itemknn              | multvae              | --         | --        | --        | 0.0%                | 5       | no     | itemknn              | itemknn              |
| itemknn              | multvae+quota_mmr    | --         | --        | --        | 0.0%                | 5       | no     | itemknn              | itemknn              |
| itemknn              | gru4rec              | --         | --        | --        | 0.0%                | 5       | no     | itemknn              | itemknn              |
| itemknn              | gru4rec+quota_mmr    | --         | --        | --        | 0.0%                | 5       | no     | itemknn              | itemknn              |
| itemknn+quota_mmr    | als                  | 2,021      | 1,601     | 2,388     | 100.0%              | 5       | yes    | itemknn+quota_mmr    | als                  |
| itemknn+quota_mmr    | als+quota_mmr        | 25,694     | 18,033    | 40,984    | 5.1%                | 5       | no     | itemknn+quota_mmr    | als+quota_mmr        |
| itemknn+quota_mmr    | multvae              | 1,875      | 1,407     | 2,529     | 100.0%              | 5       | yes    | itemknn+quota_mmr    | multvae              |
| itemknn+quota_mmr    | multvae+quota_mmr    | --         | --        | --        | 0.0%                | 5       | no     | itemknn+quota_mmr    | itemknn+quota_mmr    |
| itemknn+quota_mmr    | gru4rec              | 274,597    | 194,620   | 304,803   | 100.0%              | 5       | yes    | itemknn+quota_mmr    | gru4rec              |
| itemknn+quota_mmr    | gru4rec+quota_mmr    | --         | --        | --        | 0.0%                | 5       | no     | itemknn+quota_mmr    | itemknn+quota_mmr    |
| als                  | als+quota_mmr        | 30         | 4         | 309       | 35.4%               | 5       | no     | als+quota_mmr        | als                  |
| als                  | multvae              | 2,639      | 361       | 5,248     | 99.7%               | 5       | yes    | multvae              | als                  |
| als                  | multvae+quota_mmr    | 161        | 8         | 406       | 97.9%               | 5       | yes    | multvae+quota_mmr    | als                  |
| als                  | gru4rec              | --         | --        | --        | 0.0%                | 5       | no     | als                  | als                  |
| als                  | gru4rec+quota_mmr    | --         | --        | --        | 0.0%                | 5       | no     | als                  | als                  |
| als+quota_mmr        | multvae              | --         | --        | --        | 0.0%                | 5       | no     | multvae              | multvae              |
| als+quota_mmr        | multvae+quota_mmr    | 730        | 87        | 1,632     | 99.7%               | 5       | yes    | multvae+quota_mmr    | als+quota_mmr        |
| als+quota_mmr        | gru4rec              | 213,079    | 180,852   | 239,602   | 100.0%              | 5       | yes    | als+quota_mmr        | gru4rec              |
| als+quota_mmr        | gru4rec+quota_mmr    | --         | --        | --        | 0.0%                | 5       | no     | als+quota_mmr        | als+quota_mmr        |
| multvae              | multvae+quota_mmr    | 50         | 36        | 295       | 33.8%               | 5       | no     | multvae+quota_mmr    | multvae              |
| multvae              | gru4rec              | --         | --        | --        | 0.0%                | 5       | no     | multvae              | multvae              |
| multvae              | gru4rec+quota_mmr    | --         | --        | --        | 0.0%                | 5       | no     | multvae              | multvae              |
| multvae+quota_mmr    | gru4rec              | 109,336    | 89,769    | 126,628   | 100.0%              | 5       | yes    | multvae+quota_mmr    | gru4rec              |
| multvae+quota_mmr    | gru4rec+quota_mmr    | 2,391,257  | 1,231,985 | 2,391,257 | 1.6%                | 5       | no     | multvae+quota_mmr    | gru4rec+quota_mmr    |
| gru4rec              | gru4rec+quota_mmr    | 7,216      | 1,734     | 18,684    | 41.3%               | 5       | no     | gru4rec+quota_mmr    | gru4rec              |

### rerank_share

| family     | reranker  | cpu_rerank | cpu_serving_total | rerank_share_of_serving | cpu_rerank_setup | serving_multiplier |
|------------|-----------|------------|-------------------|-------------------------|------------------|--------------------|
| popularity | quota_mmr | 5.156e-01  | 5.389e-01         | 95.9%                   | 9.766e-02        | 24.2678            |
| itemknn    | quota_mmr | 5.312e-01  | 5.671e-01         | 93.7%                   | 9.375e-02        | 15.8364            |
| als        | quota_mmr | 6.250e-01  | 6.577e-01         | 95.6%                   | 9.375e-02        | 22.6340            |
| multvae    | quota_mmr | 9.062e-01  | 1.056e+00         | 85.9%                   | 4.375e-01        | 7.1071             |
| gru4rec    | quota_mmr | 1.078e+00  | 1.359e+00         | 82.5%                   | 6.250e-01        | 5.7250             |

### frontier

| n_requests | frontier                                       | dominated                                                                                                      | cheapest   | most_accurate |
|------------|------------------------------------------------|----------------------------------------------------------------------------------------------------------------|------------|---------------|
| 1          | popularity, popularity+quota_mmr, als, gru4rec | gru4rec+quota_mmr, als+quota_mmr, multvae+quota_mmr, multvae, itemknn+quota_mmr, itemknn                       | popularity | gru4rec       |
| 10         | popularity, popularity+quota_mmr, als, gru4rec | gru4rec+quota_mmr, als+quota_mmr, multvae+quota_mmr, multvae, itemknn+quota_mmr, itemknn                       | popularity | gru4rec       |
| 100        | popularity, popularity+quota_mmr, als, gru4rec | gru4rec+quota_mmr, als+quota_mmr, multvae+quota_mmr, multvae, itemknn+quota_mmr, itemknn                       | popularity | gru4rec       |
| 1,000      | popularity, popularity+quota_mmr, als, gru4rec | gru4rec+quota_mmr, multvae+quota_mmr, als+quota_mmr, multvae, itemknn+quota_mmr, itemknn                       | popularity | gru4rec       |
| 10,000     | popularity, als, gru4rec                       | gru4rec+quota_mmr, multvae+quota_mmr, als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr, multvae, itemknn | popularity | gru4rec       |
| 100,000    | popularity, als, gru4rec                       | gru4rec+quota_mmr, multvae+quota_mmr, als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr, multvae, itemknn | popularity | gru4rec       |
| 1,000,000  | popularity, als, gru4rec                       | gru4rec+quota_mmr, multvae+quota_mmr, als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr, multvae, itemknn | popularity | gru4rec       |

### regimes

| n_requests | cheapest   | cost      | unit        | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr | cost.multvae | cost.multvae+quota_mmr | cost.gru4rec | cost.gru4rec+quota_mmr |
|------------|------------|-----------|-------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|--------------|------------------------|--------------|------------------------|
| 1          | popularity | 2.808e-04 | cpu_seconds | 0.000281        | 0.101                     | 0.195        | 0.292                  | 6        | 6                  | 4            | 5                      | 451          | 456                    |
| 10         | popularity | 1.307e-03 | cpu_seconds | 0.00131         | 0.125                     | 0.197        | 0.317                  | 6        | 6                  | 4            | 5                      | 451          | 456                    |
| 100        | popularity | 1.156e-02 | cpu_seconds | 0.0116          | 0.367                     | 0.214        | 0.573                  | 6        | 6                  | 4            | 5                      | 452          | 456                    |
| 1,000      | popularity | 1.141e-01 | cpu_seconds | 0.114           | 3                         | 0.381        | 3                      | 6        | 9                  | 5            | 10                     | 453          | 462                    |
| 10,000     | popularity | 1.140e+00 | cpu_seconds | 1               | 27                        | 2            | 29                     | 7        | 39                 | 11           | 58                     | 463          | 524                    |
| 100,000    | popularity | 1.140e+01 | cpu_seconds | 11              | 270                       | 19           | 284                    | 19       | 335                | 69           | 533                    | 571          | 1,135                  |
| 1,000,000  | popularity | 1.140e+02 | cpu_seconds | 114             | 2,695                     | 186          | 2,836                  | 142      | 3,295              | 655          | 5,287                  | 1,649        | 7,253                  |

### retraining

| retrain_every | n_requests | cheapest   | training_events | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr | cost.multvae | cost.multvae+quota_mmr | cost.gru4rec | cost.gru4rec+quota_mmr |
|---------------|------------|------------|-----------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|--------------|------------------------|--------------|------------------------|
| never         | 100,000    | popularity | 1               | 11              | 270                       | 19           | 284                    | 19       | 335                | 69           | 533                    | 571          | 1,135                  |
| 1,000,000     | 100,000    | popularity | 1               | 11              | 270                       | 19           | 284                    | 19       | 335                | 69           | 533                    | 571          | 1,135                  |
| 100,000       | 100,000    | popularity | 2               | 11              | 270                       | 19           | 284                    | 25       | 341                | 74           | 538                    | 1,023        | 1,591                  |
| 10,000        | 100,000    | popularity | 11              | 11              | 271                       | 21           | 287                    | 77       | 395                | 113          | 583                    | 5,086        | 5,692                  |
| 1,000         | 100,000    | popularity | 101             | 11              | 279                       | 38           | 313                    | 598      | 933                | 507          | 1,030                  | 45,720       | 46,704                 |
| 100           | 100,000    | popularity | 1,001           | 12              | 367                       | 214          | 573                    | 5,801    | 6,319              | 4,444        | 5,502                  | 452,056      | 456,823                |

## luxury_beauty  (1,365 items)

### cost

| family     | reranker  | repeats | ndcg   | recall | exposure_parity | cpu_once  | cpu_per_request | spread_once | spread_per_request | cpu_train | cpu_rerank_setup | cpu_retrieve_score | cpu_retrieve_select | cpu_rerank |
|------------|-----------|---------|--------|--------|-----------------|-----------|-----------------|-------------|--------------------|-----------|------------------|--------------------|---------------------|------------|
| popularity | none      | 5       | 0.0050 | 0.0100 | 0.0000          | 1.464e-04 | 1.172e-04       | 25.1%       | 18.8%              | 1.464e-04 | 0.000e+00        | 1.302e-02          | 1.042e-02           | 0.000e+00  |
| itemknn    | none      | 5       | 0.2071 | 0.2650 | 0.9983          | 7.812e-02 | 1.395e-04       | 23.0%       | 51.6%              | 7.812e-02 | 0.000e+00        | 1.488e-02          | 1.250e-02           | 0.000e+00  |
| als        | none      | 5       | 0.1802 | 0.2250 | 0.7670          | 6.688e+00 | 1.458e-04       | 30.8%       | 90.3%              | 6.688e+00 | 0.000e+00        | 1.953e-02          | 1.078e-02           | 0.000e+00  |
| itemknn    | quota_mmr | 5       | 0.2021 | 0.2400 | 0.2670          | 1.185e-01 | 3.570e-03       | 68.1%       | 27.2%              | 8.203e-02 | 3.646e-02        | 1.488e-02          | 1.157e-02           | 6.875e-01  |
| als        | quota_mmr | 5       | 0.1805 | 0.2200 | 0.2685          | 6.666e+00 | 3.834e-03       | 25.2%       | 22.9%              | 6.625e+00 | 3.646e-02        | 2.404e-02          | 1.116e-02           | 7.344e-01  |
| popularity | quota_mmr | 5       | 0.0099 | 0.0250 | 0.0000          | 3.923e-02 | 4.877e-03       | 25.0%       | 88.7%              | 1.453e-04 | 3.906e-02        | 1.250e-02          | 9.766e-03           | 9.531e-01  |

### breakeven

| a                    | b                    | n_requests | lo      | hi      | replicates_crossing | repeats | stable | cheaper_below        | cheaper_above     |
|----------------------|----------------------|------------|---------|---------|---------------------|---------|--------|----------------------|-------------------|
| popularity           | popularity+quota_mmr | --         | --      | --      | 0.0%                | 5       | no     | popularity           | popularity        |
| popularity           | itemknn              | 88,752     | 13,195  | 88,752  | 4.2%                | 5       | no     | popularity           | itemknn           |
| popularity           | itemknn+quota_mmr    | --         | --      | --      | 0.0%                | 5       | no     | popularity           | popularity        |
| popularity           | als                  | 643,278    | 466,166 | 760,045 | 4.2%                | 5       | no     | popularity           | als               |
| popularity           | als+quota_mmr        | --         | --      | --      | 0.0%                | 5       | no     | popularity           | popularity        |
| popularity+quota_mmr | itemknn              | 8          | 4       | 12      | 100.0%              | 5       | yes    | popularity+quota_mmr | itemknn           |
| popularity+quota_mmr | itemknn+quota_mmr    | 61         | 15      | 286     | 100.0%              | 5       | yes    | popularity+quota_mmr | itemknn+quota_mmr |
| popularity+quota_mmr | als                  | 1,336      | 782     | 1,755   | 100.0%              | 5       | yes    | popularity+quota_mmr | als               |
| popularity+quota_mmr | als+quota_mmr        | 6,353      | 1,378   | 21,413  | 98.4%               | 5       | yes    | popularity+quota_mmr | als+quota_mmr     |
| itemknn              | itemknn+quota_mmr    | --         | --      | --      | 0.0%                | 5       | no     | itemknn              | itemknn           |
| itemknn              | als                  | 185,432    | 122,097 | 440,498 | 10.9%               | 5       | no     | itemknn              | als               |
| itemknn              | als+quota_mmr        | --         | --      | --      | 0.0%                | 5       | no     | itemknn              | itemknn           |
| itemknn+quota_mmr    | als                  | 1,856      | 1,374   | 2,329   | 100.0%              | 5       | yes    | itemknn+quota_mmr    | als               |
| itemknn+quota_mmr    | als+quota_mmr        | 49,032     | 8,655   | 86,177  | 36.5%               | 5       | no     | itemknn+quota_mmr    | als+quota_mmr     |
| als                  | als+quota_mmr        | 142        | 6       | 548     | 56.4%               | 5       | no     | als+quota_mmr        | als               |

### rerank_share

| family     | reranker  | cpu_rerank | cpu_serving_total | rerank_share_of_serving | cpu_rerank_setup | serving_multiplier |
|------------|-----------|------------|-------------------|-------------------------|------------------|--------------------|
| popularity | quota_mmr | 9.531e-01  | 9.754e-01         | 97.7%                   | 3.906e-02        | 43.8070            |
| itemknn    | quota_mmr | 6.875e-01  | 7.140e-01         | 96.3%                   | 3.646e-02        | 26.9875            |
| als        | quota_mmr | 7.344e-01  | 7.668e-01         | 95.6%                   | 3.646e-02        | 22.4988            |

### frontier

| n_requests | frontier                                  | dominated                                                   | cheapest   | most_accurate |
|------------|-------------------------------------------|-------------------------------------------------------------|------------|---------------|
| 1          | popularity, popularity+quota_mmr, itemknn | als, als+quota_mmr, itemknn+quota_mmr                       | popularity | itemknn       |
| 10         | popularity, itemknn                       | als+quota_mmr, als, itemknn+quota_mmr, popularity+quota_mmr | popularity | itemknn       |
| 100        | popularity, itemknn                       | als+quota_mmr, als, popularity+quota_mmr, itemknn+quota_mmr | popularity | itemknn       |
| 1,000      | popularity, itemknn                       | als+quota_mmr, als, popularity+quota_mmr, itemknn+quota_mmr | popularity | itemknn       |
| 10,000     | popularity, itemknn                       | popularity+quota_mmr, als+quota_mmr, itemknn+quota_mmr, als | popularity | itemknn       |
| 100,000    | popularity, itemknn                       | popularity+quota_mmr, als+quota_mmr, itemknn+quota_mmr, als | popularity | itemknn       |
| 1,000,000  | popularity, itemknn                       | popularity+quota_mmr, als+quota_mmr, itemknn+quota_mmr, als | popularity | itemknn       |

### regimes

| n_requests | cheapest   | cost      | unit        | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|------------|------------|-----------|-------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| 1          | popularity | 2.636e-04 | cpu_seconds | 0.000264        | 0.0441                    | 0.0783       | 0.122                  | 7        | 7                  |
| 10         | popularity | 1.318e-03 | cpu_seconds | 0.00132         | 0.088                     | 0.0795       | 0.154                  | 7        | 7                  |
| 100        | popularity | 1.187e-02 | cpu_seconds | 0.0119          | 0.527                     | 0.0921       | 0.475                  | 7        | 7                  |
| 1,000      | popularity | 1.173e-01 | cpu_seconds | 0.117           | 5                         | 0.218        | 4                      | 7        | 10                 |
| 10,000     | popularity | 1.172e+00 | cpu_seconds | 1               | 49                        | 1            | 36                     | 8        | 45                 |
| 100,000    | popularity | 1.172e+01 | cpu_seconds | 12              | 488                       | 14           | 357                    | 21       | 390                |
| 1,000,000  | popularity | 1.172e+02 | cpu_seconds | 117             | 4,877                     | 140          | 3,570                  | 152      | 3,841              |

### retraining

| retrain_every | n_requests | cheapest   | training_events | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|---------------|------------|------------|-----------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| never         | 100,000    | popularity | 1               | 12              | 488                       | 14           | 357                    | 21       | 390                |
| 1,000,000     | 100,000    | popularity | 1               | 12              | 488                       | 14           | 357                    | 21       | 390                |
| 100,000       | 100,000    | popularity | 2               | 12              | 488                       | 14           | 357                    | 28       | 397                |
| 10,000        | 100,000    | popularity | 11              | 12              | 488                       | 15           | 358                    | 88       | 457                |
| 1,000         | 100,000    | popularity | 101             | 12              | 492                       | 22           | 369                    | 690      | 1,057              |
| 100           | 100,000    | popularity | 1,001           | 12              | 527                       | 92           | 476                    | 6,709    | 7,056              |

## digital_music  (11,268 items)

### cost

| family     | reranker  | repeats | ndcg   | recall | exposure_parity | cpu_once  | cpu_per_request | spread_once | spread_per_request | cpu_train | cpu_rerank_setup | cpu_retrieve_score | cpu_retrieve_select | cpu_rerank |
|------------|-----------|---------|--------|--------|-----------------|-----------|-----------------|-------------|--------------------|-----------|------------------|--------------------|---------------------|------------|
| popularity | none      | 5       | 0.0047 | 0.0100 | 0.0000          | 3.600e-04 | 3.947e-04       | 18.9%       | 24.0%              | 3.600e-04 | 0.000e+00        | 1.645e-02          | 6.250e-02           | 0.000e+00  |
| itemknn    | none      | 5       | 0.0465 | 0.0700 | 1.2005          | 3.750e-01 | 4.545e-04       | 25.0%       | 19.9%              | 3.750e-01 | 0.000e+00        | 2.841e-02          | 6.250e-02           | 0.000e+00  |
| als        | none      | 5       | 0.0379 | 0.0650 | 1.3570          | 3.520e+01 | 6.641e-04       | 22.2%       | 26.9%              | 3.520e+01 | 0.000e+00        | 6.563e-02          | 5.729e-02           | 0.000e+00  |
| als        | quota_mmr | 5       | 0.0410 | 0.0750 | 0.2798          | 3.078e+01 | 3.464e-03       | 35.5%       | 28.7%              | 3.064e+01 | 1.406e-01        | 7.812e-02          | 5.729e-02           | 5.625e-01  |
| itemknn    | quota_mmr | 5       | 0.0507 | 0.0800 | 0.2650          | 5.469e-01 | 4.059e-03       | 35.7%       | 35.3%              | 3.906e-01 | 1.562e-01        | 2.734e-02          | 6.563e-02           | 7.188e-01  |
| popularity | quota_mmr | 5       | 0.0047 | 0.0100 | 0.0000          | 1.566e-01 | 6.879e-03       | 23.3%       | 20.7%              | 3.461e-04 | 1.562e-01        | 1.645e-02          | 6.250e-02           | 1.297e+00  |

### breakeven

| a                    | b                    | n_requests | lo     | hi        | replicates_crossing | repeats | stable | cheaper_below        | cheaper_above     |
|----------------------|----------------------|------------|--------|-----------|---------------------|---------|--------|----------------------|-------------------|
| popularity           | popularity+quota_mmr | --         | --     | --        | 0.0%                | 5       | no     | popularity           | popularity        |
| popularity           | itemknn              | 38,449     | 9,269  | 79,712    | 21.6%               | 5       | no     | popularity           | itemknn           |
| popularity           | itemknn+quota_mmr    | --         | --     | --        | 0.0%                | 5       | no     | popularity           | popularity        |
| popularity           | als                  | --         | --     | --        | 0.0%                | 5       | no     | popularity           | popularity        |
| popularity           | als+quota_mmr        | --         | --     | --        | 0.0%                | 5       | no     | popularity           | popularity        |
| popularity+quota_mmr | itemknn              | 34         | 23     | 46        | 100.0%              | 5       | yes    | popularity+quota_mmr | itemknn           |
| popularity+quota_mmr | itemknn+quota_mmr    | 133        | 88     | 263       | 100.0%              | 5       | yes    | popularity+quota_mmr | itemknn+quota_mmr |
| popularity+quota_mmr | als                  | 5,639      | 4,617  | 7,070     | 100.0%              | 5       | yes    | popularity+quota_mmr | als               |
| popularity+quota_mmr | als+quota_mmr        | 11,090     | 7,751  | 20,834    | 100.0%              | 5       | yes    | popularity+quota_mmr | als+quota_mmr     |
| itemknn              | itemknn+quota_mmr    | --         | --     | --        | 0.0%                | 5       | no     | itemknn              | itemknn           |
| itemknn              | als                  | --         | --     | --        | 0.0%                | 5       | no     | itemknn              | itemknn           |
| itemknn              | als+quota_mmr        | --         | --     | --        | 0.0%                | 5       | no     | itemknn              | itemknn           |
| itemknn+quota_mmr    | als                  | 10,209     | 7,971  | 13,131    | 100.0%              | 5       | yes    | itemknn+quota_mmr    | als               |
| itemknn+quota_mmr    | als+quota_mmr        | 50,801     | 20,115 | 1,561,686 | 77.8%               | 5       | no     | itemknn+quota_mmr    | als+quota_mmr     |
| als                  | als+quota_mmr        | 1,739      | 1,554  | 2,899     | 46.6%               | 5       | no     | als+quota_mmr        | als               |

### rerank_share

| family     | reranker  | cpu_rerank | cpu_serving_total | rerank_share_of_serving | cpu_rerank_setup | serving_multiplier |
|------------|-----------|------------|-------------------|-------------------------|------------------|--------------------|
| popularity | quota_mmr | 1.297e+00  | 1.376e+00         | 94.3%                   | 1.562e-01        | 17.4271            |
| itemknn    | quota_mmr | 7.188e-01  | 8.117e-01         | 88.5%                   | 1.562e-01        | 8.6875             |
| als        | quota_mmr | 5.625e-01  | 6.927e-01         | 81.3%                   | 1.406e-01        | 5.3434             |

### frontier

| n_requests | frontier                                                     | dominated                                | cheapest   | most_accurate     |
|------------|--------------------------------------------------------------|------------------------------------------|------------|-------------------|
| 1          | popularity, popularity+quota_mmr, itemknn, itemknn+quota_mmr | als, als+quota_mmr                       | popularity | itemknn+quota_mmr |
| 10         | popularity, popularity+quota_mmr, itemknn, itemknn+quota_mmr | als, als+quota_mmr                       | popularity | itemknn+quota_mmr |
| 100        | popularity, itemknn, itemknn+quota_mmr                       | als, als+quota_mmr, popularity+quota_mmr | popularity | itemknn+quota_mmr |
| 1,000      | popularity, itemknn, itemknn+quota_mmr                       | als, als+quota_mmr, popularity+quota_mmr | popularity | itemknn+quota_mmr |
| 10,000     | popularity, itemknn, itemknn+quota_mmr                       | popularity+quota_mmr, als+quota_mmr, als | popularity | itemknn+quota_mmr |
| 100,000    | popularity, itemknn, itemknn+quota_mmr                       | popularity+quota_mmr, als+quota_mmr, als | popularity | itemknn+quota_mmr |
| 1,000,000  | popularity, itemknn, itemknn+quota_mmr                       | popularity+quota_mmr, als+quota_mmr, als | popularity | itemknn+quota_mmr |

### regimes

| n_requests | cheapest   | cost      | unit        | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|------------|------------|-----------|-------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| 1          | popularity | 7.548e-04 | cpu_seconds | 0.000755        | 0.163                     | 0.375        | 0.551                  | 35       | 31                 |
| 10         | popularity | 4.307e-03 | cpu_seconds | 0.00431         | 0.225                     | 0.38         | 0.587                  | 35       | 31                 |
| 100        | popularity | 3.983e-02 | cpu_seconds | 0.0398          | 0.845                     | 0.42         | 0.953                  | 35       | 31                 |
| 1,000      | popularity | 3.951e-01 | cpu_seconds | 0.395           | 7                         | 0.83         | 5                      | 36       | 34                 |
| 10,000     | popularity | 3.948e+00 | cpu_seconds | 4               | 69                        | 5            | 41                     | 42       | 65                 |
| 100,000    | popularity | 3.947e+01 | cpu_seconds | 39              | 688                       | 46           | 406                    | 102      | 377                |
| 1,000,000  | popularity | 3.947e+02 | cpu_seconds | 395             | 6,879                     | 455          | 4,059                  | 699      | 3,494              |

### retraining

| retrain_every | n_requests | cheapest   | training_events | cost.popularity | cost.popularity+quota_mmr | cost.itemknn | cost.itemknn+quota_mmr | cost.als | cost.als+quota_mmr |
|---------------|------------|------------|-----------------|-----------------|---------------------------|--------------|------------------------|----------|--------------------|
| never         | 100,000    | popularity | 1               | 39              | 688                       | 46           | 406                    | 102      | 377                |
| 1,000,000     | 100,000    | popularity | 1               | 39              | 688                       | 46           | 406                    | 102      | 377                |
| 100,000       | 100,000    | popularity | 2               | 39              | 688                       | 46           | 407                    | 137      | 408                |
| 10,000        | 100,000    | popularity | 11              | 39              | 690                       | 50           | 412                    | 454      | 685                |
| 1,000         | 100,000    | popularity | 101             | 40              | 704                       | 83           | 461                    | 3,622    | 3,455              |
| 100           | 100,000    | popularity | 1,001           | 40              | 845                       | 421          | 953                    | 35,305   | 31,153             |
