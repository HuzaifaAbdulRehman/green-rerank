# Results tables

Generated from `results\rerankers`.

## ml100k  (1,349 items)

### cost

| family     | reranker      | repeats | ndcg   | recall | exposure_parity | cpu_once  | cpu_per_request | spread_once | spread_per_request | cpu_train | cpu_rerank_setup | cpu_retrieve_score | cpu_retrieve_select | cpu_rerank |
|------------|---------------|---------|--------|--------|-----------------|-----------|-----------------|-------------|--------------------|-----------|------------------|--------------------|---------------------|------------|
| popularity | none          | 3       | 0.0398 | 0.0800 | 1.2040          | 1.621e-04 | 1.025e-04       | 3.4%        | 10.2%              | 1.621e-04 | 0.000e+00        | 5.787e-03          | 4.464e-03           | 0.000e+00  |
| als        | none          | 3       | 0.0638 | 0.1400 | 0.8440          | 5.625e+00 | 1.383e-04       | 11.9%       | 7.8%               | 5.625e+00 | 0.000e+00        | 9.549e-03          | 4.281e-03           | 0.000e+00  |
| itemknn    | none          | 3       | 0.0468 | 0.0900 | 1.1380          | 2.109e-01 | 1.805e-04       | 7.4%        | 3.7%               | 2.109e-01 | 0.000e+00        | 1.359e-02          | 4.167e-03           | 0.000e+00  |
| popularity | greedy_topk   | 3       | 0.0398 | 0.0800 | 1.2040          | 9.002e-02 | 2.681e-04       | 4.3%        | 17.9%              | 1.659e-04 | 8.984e-02        | 5.896e-03          | 4.529e-03           | 1.645e-02  |
| als        | greedy_topk   | 3       | 0.0638 | 0.1400 | 0.8440          | 6.055e+00 | 3.389e-04       | 7.5%        | 10.3%              | 5.969e+00 | 9.766e-02        | 7.440e-03          | 4.464e-03           | 2.083e-02  |
| itemknn    | greedy_topk   | 3       | 0.0468 | 0.0900 | 1.1380          | 2.969e-01 | 3.400e-04       | 15.4%       | 14.5%              | 2.031e-01 | 9.375e-02        | 1.488e-02          | 4.167e-03           | 1.562e-02  |
| popularity | quota_mmr     | 3       | 0.0507 | 0.1100 | 0.2630          | 9.003e-02 | 1.200e-03       | 16.0%       | 40.5%              | 1.816e-04 | 8.984e-02        | 6.010e-03          | 4.596e-03           | 1.094e-01  |
| itemknn    | quota_mmr     | 3       | 0.0523 | 0.1000 | 0.2450          | 2.891e-01 | 1.328e-03       | 5.4%        | 14.9%              | 1.953e-01 | 8.984e-02        | 1.420e-02          | 4.058e-03           | 1.146e-01  |
| als        | quota_mmr     | 3       | 0.0591 | 0.1100 | 0.2550          | 6.156e+00 | 1.660e-03       | 16.7%       | 23.6%              | 6.062e+00 | 9.375e-02        | 2.083e-02          | 4.664e-03           | 1.458e-01  |
| itemknn    | mmr           | 3       | 0.0629 | 0.1400 | 1.0180          | 2.969e-01 | 1.976e-03       | 3.9%        | 3.7%               | 2.031e-01 | 9.375e-02        | 1.427e-02          | 4.167e-03           | 1.797e-01  |
| popularity | mmr           | 3       | 0.0464 | 0.1000 | 0.9680          | 9.002e-02 | 1.980e-03       | 13.0%       | 20.7%              | 1.727e-04 | 8.984e-02        | 6.127e-03          | 4.401e-03           | 1.875e-01  |
| als        | mmr           | 3       | 0.0735 | 0.1300 | 0.7680          | 6.023e+00 | 2.033e-03       | 9.7%        | 12.5%              | 5.938e+00 | 8.984e-02        | 8.446e-03          | 4.223e-03           | 1.875e-01  |
| popularity | qubo_tabu     | 3       | 0.0452 | 0.1000 | 0.2000          | 9.001e-02 | 2.432e-01       | 8.7%        | 0.2%               | 1.596e-04 | 8.984e-02        | 6.010e-03          | 4.401e-03           | 2.431e+01  |
| als        | qubo_tabu     | 3       | 0.0634 | 0.1000 | 0.2000          | 5.777e+00 | 2.438e-01       | 23.6%       | 1.2%               | 5.688e+00 | 9.766e-02        | 1.157e-02          | 4.281e-03           | 2.436e+01  |
| itemknn    | qubo_tabu     | 3       | 0.0650 | 0.1400 | 0.2000          | 2.930e-01 | 2.446e-01       | 12.0%       | 1.0%               | 2.031e-01 | 9.375e-02        | 1.359e-02          | 4.735e-03           | 2.444e+01  |
| itemknn    | qubo_feasible | 3       | 0.0500 | 0.1200 | 0.2000          | 2.930e-01 | 3.114e-01       | 4.0%        | 39.0%              | 2.031e-01 | 8.984e-02        | 1.420e-02          | 4.167e-03           | 3.112e+01  |
| als        | qubo_feasible | 3       | 0.0658 | 0.1000 | 0.2000          | 5.734e+00 | 3.188e-01       | 29.0%       | 18.8%              | 5.641e+00 | 9.375e-02        | 1.116e-02          | 4.281e-03           | 3.186e+01  |
| popularity | qubo_feasible | 3       | 0.0409 | 0.0700 | 0.2000          | 9.782e-02 | 3.281e-01       | 8.0%        | 17.8%              | 1.671e-04 | 9.766e-02        | 6.378e-03          | 5.040e-03           | 3.280e+01  |

### breakeven

| a                        | b                        | n_requests | lo       | hi        | replicates_crossing | repeats | stable | cheaper_below            | cheaper_above          |
|--------------------------|--------------------------|------------|----------|-----------|---------------------|---------|--------|--------------------------|------------------------|
| popularity               | popularity+greedy_topk   | --         | --       | --        | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | popularity+mmr           | --         | --       | --        | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | popularity+quota_mmr     | --         | --       | --        | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | popularity+qubo_feasible | --         | --       | --        | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | popularity+qubo_tabu     | --         | --       | --        | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | itemknn                  | --         | --       | --        | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | itemknn+greedy_topk      | --         | --       | --        | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | itemknn+mmr              | --         | --       | --        | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | itemknn+quota_mmr        | --         | --       | --        | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | itemknn+qubo_feasible    | --         | --       | --        | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | itemknn+qubo_tabu        | --         | --       | --        | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | als                      | --         | --       | --        | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | als+greedy_topk          | --         | --       | --        | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | als+mmr                  | --         | --       | --        | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | als+quota_mmr            | --         | --       | --        | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | als+qubo_feasible        | --         | --       | --        | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | als+qubo_tabu            | --         | --       | --        | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity+greedy_topk   | popularity+mmr           | 0.000571   | 5.31e-05 | 3         | 62.9%               | 3       | no     | popularity+mmr           | popularity+greedy_topk |
| popularity+greedy_topk   | popularity+quota_mmr     | 0.0205     | 0.00637  | 4         | 38.0%               | 3       | no     | popularity+quota_mmr     | popularity+greedy_topk |
| popularity+greedy_topk   | popularity+qubo_feasible | 5.76e-05   | 1.66e-05 | 0.013     | 26.1%               | 3       | no     | popularity+qubo_feasible | popularity+greedy_topk |
| popularity+greedy_topk   | popularity+qubo_tabu     | 1.48e-05   | 1.18e-05 | 0.0161    | 62.9%               | 3       | no     | popularity+qubo_tabu     | popularity+greedy_topk |
| popularity+greedy_topk   | itemknn                  | 1,336      | 856      | 1,772     | 100.0%              | 3       | yes    | popularity+greedy_topk   | itemknn                |
| popularity+greedy_topk   | itemknn+greedy_topk      | --         | --       | --        | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | itemknn+mmr              | --         | --       | --        | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | itemknn+quota_mmr        | --         | --       | --        | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | itemknn+qubo_feasible    | --         | --       | --        | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | itemknn+qubo_tabu        | --         | --       | --        | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | als                      | 42,647     | 33,578   | 58,818    | 100.0%              | 3       | yes    | popularity+greedy_topk   | als                    |
| popularity+greedy_topk   | als+greedy_topk          | --         | --       | --        | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | als+mmr                  | --         | --       | --        | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | als+quota_mmr            | --         | --       | --        | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | als+qubo_feasible        | --         | --       | --        | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | als+qubo_tabu            | --         | --       | --        | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+mmr           | popularity+quota_mmr     | 0.033      | 0.00868  | 105       | 61.3%               | 3       | no     | popularity+mmr           | popularity+quota_mmr   |
| popularity+mmr           | popularity+qubo_feasible | 0.0109     | 1.64e-05 | 0.0392    | 45.3%               | 3       | no     | popularity+qubo_feasible | popularity+mmr         |
| popularity+mmr           | popularity+qubo_tabu     | 5.91e-05   | 1.09e-05 | 0.0487    | 69.0%               | 3       | no     | popularity+qubo_tabu     | popularity+mmr         |
| popularity+mmr           | itemknn                  | 61         | 51       | 74        | 100.0%              | 3       | yes    | popularity+mmr           | itemknn                |
| popularity+mmr           | itemknn+greedy_topk      | 126        | 103      | 168       | 100.0%              | 3       | yes    | popularity+mmr           | itemknn+greedy_topk    |
| popularity+mmr           | itemknn+mmr              | 2,561      | 610      | 49,951    | 61.8%               | 3       | no     | popularity+mmr           | itemknn+mmr            |
| popularity+mmr           | itemknn+quota_mmr        | 305        | 221      | 634       | 100.0%              | 3       | yes    | popularity+mmr           | itemknn+quota_mmr      |
| popularity+mmr           | itemknn+qubo_feasible    | --         | --       | --        | 0.0%                | 3       | no     | popularity+mmr           | popularity+mmr         |
| popularity+mmr           | itemknn+qubo_tabu        | --         | --       | --        | 0.0%                | 3       | no     | popularity+mmr           | popularity+mmr         |
| popularity+mmr           | als                      | 3,005      | 2,630    | 3,696     | 100.0%              | 3       | yes    | popularity+mmr           | als                    |
| popularity+mmr           | als+greedy_topk          | 3,627      | 3,072    | 4,252     | 100.0%              | 3       | yes    | popularity+mmr           | als+greedy_topk        |
| popularity+mmr           | als+mmr                  | 78,076     | 18,096   | 94,319    | 37.9%               | 3       | no     | popularity+mmr           | als+mmr                |
| popularity+mmr           | als+quota_mmr            | 18,494     | 9,647    | 38,412    | 81.8%               | 3       | no     | popularity+mmr           | als+quota_mmr          |
| popularity+mmr           | als+qubo_feasible        | --         | --       | --        | 0.0%                | 3       | no     | popularity+mmr           | popularity+mmr         |
| popularity+mmr           | als+qubo_tabu            | --         | --       | --        | 0.0%                | 3       | no     | popularity+mmr           | popularity+mmr         |
| popularity+quota_mmr     | popularity+qubo_feasible | 0.0183     | 8.43e-05 | 0.0479    | 38.0%               | 3       | no     | popularity+qubo_feasible | popularity+quota_mmr   |
| popularity+quota_mmr     | popularity+qubo_tabu     | 9.58e-05   | 4.77e-05 | 0.0595    | 63.0%               | 3       | no     | popularity+qubo_tabu     | popularity+quota_mmr   |
| popularity+quota_mmr     | itemknn                  | 119        | 60       | 120       | 100.0%              | 3       | yes    | popularity+quota_mmr     | itemknn                |
| popularity+quota_mmr     | itemknn+greedy_topk      | 241        | 134      | 298       | 100.0%              | 3       | yes    | popularity+quota_mmr     | itemknn+greedy_topk    |
| popularity+quota_mmr     | itemknn+mmr              | --         | --       | --        | 0.0%                | 3       | no     | popularity+quota_mmr     | popularity+quota_mmr   |
| popularity+quota_mmr     | itemknn+quota_mmr        | 532        | 524      | 1,060     | 25.2%               | 3       | no     | popularity+quota_mmr     | itemknn+quota_mmr      |
| popularity+quota_mmr     | itemknn+qubo_feasible    | --         | --       | --        | 0.0%                | 3       | no     | popularity+quota_mmr     | popularity+quota_mmr   |
| popularity+quota_mmr     | itemknn+qubo_tabu        | --         | --       | --        | 0.0%                | 3       | no     | popularity+quota_mmr     | popularity+quota_mmr   |
| popularity+quota_mmr     | als                      | 5,214      | 3,554    | 5,895     | 100.0%              | 3       | yes    | popularity+quota_mmr     | als                    |
| popularity+quota_mmr     | als+greedy_topk          | 6,754      | 4,316    | 7,376     | 100.0%              | 3       | yes    | popularity+quota_mmr     | als+greedy_topk        |
| popularity+quota_mmr     | als+mmr                  | --         | --       | --        | 0.0%                | 3       | no     | popularity+quota_mmr     | popularity+quota_mmr   |
| popularity+quota_mmr     | als+quota_mmr            | 285,608    | 74,808   | 292,402   | 18.4%               | 3       | no     | popularity+quota_mmr     | als+quota_mmr          |
| popularity+quota_mmr     | als+qubo_feasible        | --         | --       | --        | 0.0%                | 3       | no     | popularity+quota_mmr     | popularity+quota_mmr   |
| popularity+quota_mmr     | als+qubo_tabu            | --         | --       | --        | 0.0%                | 3       | no     | popularity+quota_mmr     | popularity+quota_mmr   |
| popularity+qubo_feasible | popularity+qubo_tabu     | 0.000238   | 3.66e-05 | 0.134     | 25.5%               | 3       | no     | popularity+qubo_feasible | popularity+qubo_tabu   |
| popularity+qubo_feasible | itemknn                  | 0.345      | 0.271    | 0.401     | 100.0%              | 3       | yes    | popularity+qubo_feasible | itemknn                |
| popularity+qubo_feasible | itemknn+greedy_topk      | 0.607      | 0.521    | 0.799     | 100.0%              | 3       | yes    | popularity+qubo_feasible | itemknn+greedy_topk    |
| popularity+qubo_feasible | itemknn+mmr              | 0.61       | 0.523    | 0.69      | 100.0%              | 3       | yes    | popularity+qubo_feasible | itemknn+mmr            |
| popularity+qubo_feasible | itemknn+quota_mmr        | 0.585      | 0.522    | 0.702     | 100.0%              | 3       | yes    | popularity+qubo_feasible | itemknn+quota_mmr      |
| popularity+qubo_feasible | itemknn+qubo_feasible    | 7          | 3        | 124       | 62.6%               | 3       | no     | popularity+qubo_feasible | itemknn+qubo_feasible  |
| popularity+qubo_feasible | itemknn+qubo_tabu        | 2          | 2        | 4         | 100.0%              | 3       | yes    | popularity+qubo_feasible | itemknn+qubo_tabu      |
| popularity+qubo_feasible | als                      | 17         | 15       | 20        | 100.0%              | 3       | yes    | popularity+qubo_feasible | als                    |
| popularity+qubo_feasible | als+greedy_topk          | 18         | 16       | 21        | 100.0%              | 3       | yes    | popularity+qubo_feasible | als+greedy_topk        |
| popularity+qubo_feasible | als+mmr                  | 18         | 16       | 21        | 100.0%              | 3       | yes    | popularity+qubo_feasible | als+mmr                |
| popularity+qubo_feasible | als+quota_mmr            | 19         | 17       | 23        | 100.0%              | 3       | yes    | popularity+qubo_feasible | als+quota_mmr          |
| popularity+qubo_feasible | als+qubo_feasible        | 606        | 89       | 2,021     | 68.2%               | 3       | no     | popularity+qubo_feasible | als+qubo_feasible      |
| popularity+qubo_feasible | als+qubo_tabu            | 67         | 48       | 125       | 100.0%              | 3       | yes    | popularity+qubo_feasible | als+qubo_tabu          |
| popularity+qubo_tabu     | itemknn                  | 0.497      | 0.401    | 0.498     | 100.0%              | 3       | yes    | popularity+qubo_tabu     | itemknn                |
| popularity+qubo_tabu     | itemknn+greedy_topk      | 0.85       | 0.771    | 0.991     | 100.0%              | 3       | yes    | popularity+qubo_tabu     | itemknn+greedy_topk    |
| popularity+qubo_tabu     | itemknn+mmr              | 0.856      | 0.776    | 0.858     | 100.0%              | 3       | yes    | popularity+qubo_tabu     | itemknn+mmr            |
| popularity+qubo_tabu     | itemknn+quota_mmr        | 0.821      | 0.775    | 0.871     | 100.0%              | 3       | yes    | popularity+qubo_tabu     | itemknn+quota_mmr      |
| popularity+qubo_tabu     | itemknn+qubo_feasible    | --         | --       | --        | 0.0%                | 3       | no     | popularity+qubo_tabu     | popularity+qubo_tabu   |
| popularity+qubo_tabu     | itemknn+qubo_tabu        | 783        | 281      | 841       | 25.7%               | 3       | no     | popularity+qubo_tabu     | itemknn+qubo_tabu      |
| popularity+qubo_tabu     | als                      | 23         | 23       | 25        | 100.0%              | 3       | yes    | popularity+qubo_tabu     | als                    |
| popularity+qubo_tabu     | als+greedy_topk          | 25         | 24       | 26        | 100.0%              | 3       | yes    | popularity+qubo_tabu     | als+greedy_topk        |
| popularity+qubo_tabu     | als+mmr                  | 25         | 24       | 27        | 100.0%              | 3       | yes    | popularity+qubo_tabu     | als+mmr                |
| popularity+qubo_tabu     | als+quota_mmr            | 25         | 24       | 29        | 100.0%              | 3       | yes    | popularity+qubo_tabu     | als+quota_mmr          |
| popularity+qubo_tabu     | als+qubo_feasible        | --         | --       | --        | 0.0%                | 3       | no     | popularity+qubo_tabu     | popularity+qubo_tabu   |
| popularity+qubo_tabu     | als+qubo_tabu            | 9,722      | 5,431    | 9,861     | 25.7%               | 3       | no     | popularity+qubo_tabu     | als+qubo_tabu          |
| itemknn                  | itemknn+greedy_topk      | --         | --       | --        | 0.0%                | 3       | no     | itemknn                  | itemknn                |
| itemknn                  | itemknn+mmr              | --         | --       | --        | 0.0%                | 3       | no     | itemknn                  | itemknn                |
| itemknn                  | itemknn+quota_mmr        | --         | --       | --        | 0.0%                | 3       | no     | itemknn                  | itemknn                |
| itemknn                  | itemknn+qubo_feasible    | --         | --       | --        | 0.0%                | 3       | no     | itemknn                  | itemknn                |
| itemknn                  | itemknn+qubo_tabu        | --         | --       | --        | 0.0%                | 3       | no     | itemknn                  | itemknn                |
| itemknn                  | als                      | 128,240    | 113,159  | 202,255   | 100.0%              | 3       | yes    | itemknn                  | als                    |
| itemknn                  | als+greedy_topk          | --         | --       | --        | 0.0%                | 3       | no     | itemknn                  | itemknn                |
| itemknn                  | als+mmr                  | --         | --       | --        | 0.0%                | 3       | no     | itemknn                  | itemknn                |
| itemknn                  | als+quota_mmr            | --         | --       | --        | 0.0%                | 3       | no     | itemknn                  | itemknn                |
| itemknn                  | als+qubo_feasible        | --         | --       | --        | 0.0%                | 3       | no     | itemknn                  | itemknn                |
| itemknn                  | als+qubo_tabu            | --         | --       | --        | 0.0%                | 3       | no     | itemknn                  | itemknn                |
| itemknn+greedy_topk      | itemknn+mmr              | 21         | 7        | 30        | 37.7%               | 3       | no     | itemknn+mmr              | itemknn+greedy_topk    |
| itemknn+greedy_topk      | itemknn+quota_mmr        | 10         | 8        | 44        | 61.4%               | 3       | no     | itemknn+quota_mmr        | itemknn+greedy_topk    |
| itemknn+greedy_topk      | itemknn+qubo_feasible    | 0.0377     | 0.0126   | 0.147     | 61.9%               | 3       | no     | itemknn+qubo_feasible    | itemknn+greedy_topk    |
| itemknn+greedy_topk      | itemknn+qubo_tabu        | 0.0322     | 0.016    | 0.172     | 61.9%               | 3       | no     | itemknn+qubo_tabu        | itemknn+greedy_topk    |
| itemknn+greedy_topk      | als                      | 26,420     | 21,098   | 31,605    | 100.0%              | 3       | yes    | itemknn+greedy_topk      | als                    |
| itemknn+greedy_topk      | als+greedy_topk          | 201,476    | 77,126   | 5,320,219 | 68.0%               | 3       | no     | itemknn+greedy_topk      | als+greedy_topk        |
| itemknn+greedy_topk      | als+mmr                  | --         | --       | --        | 0.0%                | 3       | no     | itemknn+greedy_topk      | itemknn+greedy_topk    |
| itemknn+greedy_topk      | als+quota_mmr            | --         | --       | --        | 0.0%                | 3       | no     | itemknn+greedy_topk      | itemknn+greedy_topk    |
| itemknn+greedy_topk      | als+qubo_feasible        | --         | --       | --        | 0.0%                | 3       | no     | itemknn+greedy_topk      | itemknn+greedy_topk    |
| itemknn+greedy_topk      | als+qubo_tabu            | --         | --       | --        | 0.0%                | 3       | no     | itemknn+greedy_topk      | itemknn+greedy_topk    |
| itemknn+mmr              | itemknn+quota_mmr        | 7          | 6        | 26        | 39.2%               | 3       | no     | itemknn+mmr              | itemknn+quota_mmr      |
| itemknn+mmr              | itemknn+qubo_feasible    | 0.0131     | 0.0126   | 0.0379    | 55.1%               | 3       | no     | itemknn+qubo_feasible    | itemknn+mmr            |
| itemknn+mmr              | itemknn+qubo_tabu        | 0.0161     | 0.0161   | 0.0324    | 55.1%               | 3       | no     | itemknn+qubo_tabu        | itemknn+mmr            |
| itemknn+mmr              | als                      | 2,899      | 2,871    | 3,395     | 100.0%              | 3       | yes    | itemknn+mmr              | als                    |
| itemknn+mmr              | als+greedy_topk          | 3,517      | 3,408    | 3,880     | 100.0%              | 3       | yes    | itemknn+mmr              | als+greedy_topk        |
| itemknn+mmr              | als+mmr                  | 79,893     | 74,549   | 1,831,617 | 25.7%               | 3       | no     | itemknn+mmr              | als+mmr                |
| itemknn+mmr              | als+quota_mmr            | 18,082     | 15,357   | 23,597    | 75.0%               | 3       | no     | itemknn+mmr              | als+quota_mmr          |
| itemknn+mmr              | als+qubo_feasible        | --         | --       | --        | 0.0%                | 3       | no     | itemknn+mmr              | itemknn+mmr            |
| itemknn+mmr              | als+qubo_tabu            | --         | --       | --        | 0.0%                | 3       | no     | itemknn+mmr              | itemknn+mmr            |
| itemknn+quota_mmr        | itemknn+qubo_feasible    | 0.0126     | 0.00929  | 0.0504    | 38.2%               | 3       | no     | itemknn+qubo_feasible    | itemknn+quota_mmr      |
| itemknn+quota_mmr        | itemknn+qubo_tabu        | 0.0321     | 0.0321   | 0.0485    | 18.7%               | 3       | no     | itemknn+qubo_tabu        | itemknn+quota_mmr      |
| itemknn+quota_mmr        | als                      | 4,483      | 3,864    | 5,122     | 100.0%              | 3       | yes    | itemknn+quota_mmr        | als                    |
| itemknn+quota_mmr        | als+greedy_topk          | 5,669      | 4,790    | 6,265     | 100.0%              | 3       | yes    | itemknn+quota_mmr        | als+greedy_topk        |
| itemknn+quota_mmr        | als+mmr                  | --         | --       | --        | 0.0%                | 3       | no     | itemknn+quota_mmr        | itemknn+quota_mmr      |
| itemknn+quota_mmr        | als+quota_mmr            | --         | --       | --        | 0.0%                | 3       | no     | itemknn+quota_mmr        | itemknn+quota_mmr      |
| itemknn+quota_mmr        | als+qubo_feasible        | --         | --       | --        | 0.0%                | 3       | no     | itemknn+quota_mmr        | itemknn+quota_mmr      |
| itemknn+quota_mmr        | als+qubo_tabu            | --         | --       | --        | 0.0%                | 3       | no     | itemknn+quota_mmr        | itemknn+quota_mmr      |
| itemknn+qubo_feasible    | itemknn+qubo_tabu        | 0.155      | 0.0571   | 0.593     | 43.8%               | 3       | no     | itemknn+qubo_feasible    | itemknn+qubo_tabu      |
| itemknn+qubo_feasible    | als                      | 17         | 13       | 20        | 100.0%              | 3       | yes    | itemknn+qubo_feasible    | als                    |
| itemknn+qubo_feasible    | als+greedy_topk          | 19         | 13       | 20        | 100.0%              | 3       | yes    | itemknn+qubo_feasible    | als+greedy_topk        |
| itemknn+qubo_feasible    | als+mmr                  | 19         | 13       | 21        | 100.0%              | 3       | yes    | itemknn+qubo_feasible    | als+mmr                |
| itemknn+qubo_feasible    | als+quota_mmr            | 19         | 14       | 23        | 100.0%              | 3       | yes    | itemknn+qubo_feasible    | als+quota_mmr          |
| itemknn+qubo_feasible    | als+qubo_feasible        | 85         | 43       | 2,035     | 45.0%               | 3       | no     | itemknn+qubo_feasible    | als+qubo_feasible      |
| itemknn+qubo_feasible    | als+qubo_tabu            | 81         | 31       | 125       | 100.0%              | 3       | yes    | itemknn+qubo_feasible    | als+qubo_tabu          |
| itemknn+qubo_tabu        | als                      | 22         | 21       | 25        | 100.0%              | 3       | yes    | itemknn+qubo_tabu        | als                    |
| itemknn+qubo_tabu        | als+greedy_topk          | 24         | 23       | 25        | 100.0%              | 3       | yes    | itemknn+qubo_tabu        | als+greedy_topk        |
| itemknn+qubo_tabu        | als+mmr                  | 24         | 23       | 26        | 100.0%              | 3       | yes    | itemknn+qubo_tabu        | als+mmr                |
| itemknn+qubo_tabu        | als+quota_mmr            | 24         | 23       | 28        | 100.0%              | 3       | yes    | itemknn+qubo_tabu        | als+quota_mmr          |
| itemknn+qubo_tabu        | als+qubo_feasible        | --         | --       | --        | 0.0%                | 3       | no     | itemknn+qubo_tabu        | itemknn+qubo_tabu      |
| itemknn+qubo_tabu        | als+qubo_tabu            | 6,752      | 1,898    | 229,415   | 68.6%               | 3       | no     | itemknn+qubo_tabu        | als+qubo_tabu          |
| als                      | als+greedy_topk          | 1,283      | 1,099    | 1,934     | 18.8%               | 3       | no     | als+greedy_topk          | als                    |
| als                      | als+mmr                  | 128        | 128      | 189       | 18.7%               | 3       | no     | als+mmr                  | als                    |
| als                      | als+quota_mmr            | 75         | 72       | 165       | 18.7%               | 3       | no     | als+quota_mmr            | als                    |
| als                      | als+qubo_feasible        | 2          | 1        | 2         | 18.7%               | 3       | no     | als+qubo_feasible        | als                    |
| als                      | als+qubo_tabu            | 2          | 2        | 2         | 18.8%               | 3       | no     | als+qubo_tabu            | als                    |
| als+greedy_topk          | als+mmr                  | 76         | 18       | 266       | 55.1%               | 3       | no     | als+mmr                  | als+greedy_topk        |
| als+greedy_topk          | als+quota_mmr            | 146        | 29       | 253       | 31.4%               | 3       | no     | als+quota_mmr            | als+greedy_topk        |
| als+greedy_topk          | als+qubo_feasible        | 1          | 0.449    | 2         | 75.0%               | 3       | no     | als+qubo_feasible        | als+greedy_topk        |
| als+greedy_topk          | als+qubo_tabu            | 1          | 0.481    | 3         | 74.0%               | 3       | no     | als+qubo_tabu            | als+greedy_topk        |
| als+mmr                  | als+quota_mmr            | 356        | 307      | 24,141    | 60.9%               | 3       | no     | als+mmr                  | als+quota_mmr          |
| als+mmr                  | als+qubo_feasible        | 0.913      | 0.561    | 3         | 75.0%               | 3       | no     | als+qubo_feasible        | als+mmr                |
| als+mmr                  | als+qubo_tabu            | 1          | 0.646    | 3         | 74.0%               | 3       | no     | als+qubo_tabu            | als+mmr                |
| als+quota_mmr            | als+qubo_feasible        | 1          | 0.791    | 5         | 75.0%               | 3       | no     | als+qubo_feasible        | als+quota_mmr          |
| als+quota_mmr            | als+qubo_tabu            | 2          | 0.984    | 5         | 74.0%               | 3       | no     | als+qubo_tabu            | als+quota_mmr          |
| als+qubo_feasible        | als+qubo_tabu            | 1          | 0.0344   | 28        | 74.1%               | 3       | no     | als+qubo_feasible        | als+qubo_tabu          |

### rerank_share

| family     | reranker      | cpu_rerank | cpu_serving_total | rerank_share_of_serving | cpu_rerank_setup | serving_multiplier |
|------------|---------------|------------|-------------------|-------------------------|------------------|--------------------|
| popularity | greedy_topk   | 1.645e-02  | 2.681e-02         | 61.4%                   | 8.984e-02        | 2.5875             |
| popularity | mmr           | 1.875e-01  | 1.980e-01         | 94.7%                   | 8.984e-02        | 18.7043            |
| popularity | quota_mmr     | 1.094e-01  | 1.200e-01         | 91.6%                   | 8.984e-02        | 11.8472            |
| popularity | qubo_feasible | 3.280e+01  | 3.281e+01         | 100.0%                  | 9.766e-02        | 2945.7314          |
| popularity | qubo_tabu     | 2.431e+01  | 2.432e+01         | 100.0%                  | 8.984e-02        | 2340.7675          |
| itemknn    | greedy_topk   | 1.562e-02  | 3.400e-02         | 46.0%                   | 9.375e-02        | 1.8505             |
| itemknn    | mmr           | 1.797e-01  | 1.976e-01         | 90.7%                   | 9.375e-02        | 10.7482            |
| itemknn    | quota_mmr     | 1.146e-01  | 1.328e-01         | 86.3%                   | 8.984e-02        | 7.2741             |
| itemknn    | qubo_feasible | 3.112e+01  | 3.114e+01         | 99.9%                   | 8.984e-02        | 1880.7059          |
| itemknn    | qubo_tabu     | 2.444e+01  | 2.446e+01         | 99.9%                   | 9.375e-02        | 1334.7933          |
| als        | greedy_topk   | 2.083e-02  | 3.389e-02         | 62.7%                   | 9.766e-02        | 2.6827             |
| als        | mmr           | 1.875e-01  | 2.033e-01         | 94.0%                   | 8.984e-02        | 16.7336            |
| als        | quota_mmr     | 1.458e-01  | 1.660e-01         | 86.3%                   | 9.375e-02        | 7.3179             |
| als        | qubo_feasible | 3.186e+01  | 3.188e+01         | 99.9%                   | 9.375e-02        | 1760.6849          |
| als        | qubo_tabu     | 2.436e+01  | 2.438e+01         | 99.9%                   | 9.766e-02        | 1543.0208          |

### rerankers

| family     | reranker      | repeats | cpu_rerank_per_request | cpu_serving_per_request | rerank_share | ndcg   | exposure_parity | recall | time_bounded | cost_vs_cheapest |
|------------|---------------|---------|------------------------|-------------------------|--------------|--------|-----------------|--------|--------------|------------------|
| als        | greedy_topk   | 3       | 2.083e-04              | 3.389e-04               | 62.7%        | 0.0638 | 0.8440          | 0.1400 | no           | 1.0000           |
| als        | quota_mmr     | 3       | 1.458e-03              | 1.660e-03               | 86.3%        | 0.0591 | 0.2550          | 0.1100 | no           | 7.0000           |
| als        | mmr           | 3       | 1.875e-03              | 2.033e-03               | 94.0%        | 0.0735 | 0.7680          | 0.1300 | no           | 9.0000           |
| als        | qubo_tabu     | 3       | 2.436e-01              | 2.438e-01               | 99.9%        | 0.0634 | 0.2000          | 0.1000 | yes          | 1169.2500        |
| als        | qubo_feasible | 3       | 3.186e-01              | 3.188e-01               | 99.9%        | 0.0658 | 0.2000          | 0.1000 | no           | 1529.2500        |
| itemknn    | greedy_topk   | 3       | 1.563e-04              | 3.400e-04               | 46.0%        | 0.0468 | 1.1380          | 0.0900 | no           | 1.0000           |
| itemknn    | quota_mmr     | 3       | 1.146e-03              | 1.328e-03               | 86.3%        | 0.0523 | 0.2450          | 0.1000 | no           | 7.3333           |
| itemknn    | mmr           | 3       | 1.797e-03              | 1.976e-03               | 90.7%        | 0.0629 | 1.0180          | 0.1400 | no           | 11.5000          |
| itemknn    | qubo_tabu     | 3       | 2.444e-01              | 2.446e-01               | 99.9%        | 0.0650 | 0.2000          | 0.1400 | yes          | 1564.0000        |
| itemknn    | qubo_feasible | 3       | 3.113e-01              | 3.114e-01               | 99.9%        | 0.0500 | 0.2000          | 0.1200 | no           | 1992.0000        |
| popularity | greedy_topk   | 3       | 1.645e-04              | 2.681e-04               | 61.4%        | 0.0398 | 1.2040          | 0.0800 | no           | 1.0000           |
| popularity | quota_mmr     | 3       | 1.094e-03              | 1.200e-03               | 91.6%        | 0.0507 | 0.2630          | 0.1100 | no           | 6.6500           |
| popularity | mmr           | 3       | 1.875e-03              | 1.980e-03               | 94.7%        | 0.0464 | 0.9680          | 0.1000 | no           | 11.4000          |
| popularity | qubo_tabu     | 3       | 2.431e-01              | 2.432e-01               | 100.0%       | 0.0452 | 0.2000          | 0.1000 | yes          | 1478.2000        |
| popularity | qubo_feasible | 3       | 3.280e-01              | 3.281e-01               | 100.0%       | 0.0409 | 0.2000          | 0.0700 | no           | 1994.0500        |

### frontier

| n_requests | frontier                                                                                     | dominated                                                                                                                                                                                                                                                                              | cheapest   | most_accurate |
|------------|----------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------|---------------|
| 1          | popularity, popularity+quota_mmr, itemknn+quota_mmr, itemknn+mmr, itemknn+qubo_tabu, als+mmr | als+quota_mmr, als+greedy_topk, als+qubo_feasible, als+qubo_tabu, als, itemknn+qubo_feasible, popularity+qubo_feasible, popularity+qubo_tabu, itemknn+greedy_topk, itemknn, popularity+mmr, popularity+greedy_topk                                                                     | popularity | als+mmr       |
| 10         | popularity, popularity+quota_mmr, itemknn+quota_mmr, itemknn+mmr, itemknn+qubo_tabu, als+mmr | als+qubo_feasible, als+qubo_tabu, als+quota_mmr, als+greedy_topk, als, itemknn+qubo_feasible, popularity+qubo_feasible, popularity+qubo_tabu, itemknn+greedy_topk, itemknn, popularity+mmr, popularity+greedy_topk                                                                     | popularity | als+mmr       |
| 100        | popularity, popularity+quota_mmr, itemknn+quota_mmr, itemknn+mmr, als, als+mmr               | als+qubo_feasible, popularity+qubo_feasible, itemknn+qubo_feasible, als+qubo_tabu, itemknn+qubo_tabu, popularity+qubo_tabu, als+quota_mmr, als+greedy_topk, itemknn+greedy_topk, popularity+mmr, itemknn, popularity+greedy_topk                                                       | popularity | als+mmr       |
| 1,000      | popularity, itemknn, popularity+quota_mmr, itemknn+quota_mmr, itemknn+mmr, als, als+mmr      | popularity+qubo_feasible, als+qubo_feasible, itemknn+qubo_feasible, als+qubo_tabu, itemknn+qubo_tabu, popularity+qubo_tabu, als+quota_mmr, als+greedy_topk, popularity+mmr, itemknn+greedy_topk, popularity+greedy_topk                                                                | popularity | als+mmr       |
| 10,000     | popularity, itemknn, als, als+mmr                                                            | popularity+qubo_feasible, als+qubo_feasible, itemknn+qubo_feasible, itemknn+qubo_tabu, als+qubo_tabu, popularity+qubo_tabu, als+quota_mmr, itemknn+mmr, popularity+mmr, itemknn+quota_mmr, popularity+quota_mmr, als+greedy_topk, itemknn+greedy_topk, popularity+greedy_topk          | popularity | als+mmr       |
| 100,000    | popularity, itemknn, als, als+mmr                                                            | popularity+qubo_feasible, als+qubo_feasible, itemknn+qubo_feasible, itemknn+qubo_tabu, als+qubo_tabu, popularity+qubo_tabu, popularity+mmr, itemknn+mmr, als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr, als+greedy_topk, itemknn+greedy_topk, popularity+greedy_topk          | popularity | als+mmr       |
| 1,000,000  | popularity, als, als+mmr                                                                     | popularity+qubo_feasible, als+qubo_feasible, itemknn+qubo_feasible, itemknn+qubo_tabu, als+qubo_tabu, popularity+qubo_tabu, popularity+mmr, itemknn+mmr, als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr, als+greedy_topk, itemknn+greedy_topk, popularity+greedy_topk, itemknn | popularity | als+mmr       |

### regimes

| n_requests | cheapest   | cost      | unit        | cost.popularity | cost.popularity+greedy_topk | cost.popularity+mmr | cost.popularity+quota_mmr | cost.popularity+qubo_feasible | cost.popularity+qubo_tabu | cost.itemknn | cost.itemknn+greedy_topk | cost.itemknn+mmr | cost.itemknn+quota_mmr | cost.itemknn+qubo_feasible | cost.itemknn+qubo_tabu | cost.als | cost.als+greedy_topk | cost.als+mmr | cost.als+quota_mmr | cost.als+qubo_feasible | cost.als+qubo_tabu |
|------------|------------|-----------|-------------|-----------------|-----------------------------|---------------------|---------------------------|-------------------------------|---------------------------|--------------|--------------------------|------------------|------------------------|----------------------------|------------------------|----------|----------------------|--------------|--------------------|------------------------|--------------------|
| 1          | popularity | 2.646e-04 | cpu_seconds | 0.000265        | 0.0903                      | 0.092               | 0.0912                    | 0.426                         | 0.333                     | 0.211        | 0.297                    | 0.299            | 0.29                   | 0.604                      | 0.538                  | 6        | 6                    | 6            | 6                  | 6                      | 6                  |
| 10         | popularity | 1.187e-03 | cpu_seconds | 0.00119         | 0.0927                      | 0.11                | 0.102                     | 3                             | 3                         | 0.213        | 0.3                      | 0.317            | 0.302                  | 3                          | 3                      | 6        | 6                    | 6            | 6                  | 9                      | 8                  |
| 100        | popularity | 1.041e-02 | cpu_seconds | 0.0104          | 0.117                       | 0.288               | 0.21                      | 33                            | 24                        | 0.229        | 0.331                    | 0.494            | 0.422                  | 31                         | 25                     | 6        | 6                    | 6            | 6                  | 38                     | 30                 |
| 1,000      | popularity | 1.027e-01 | cpu_seconds | 0.103           | 0.358                       | 2                   | 1                         | 328                           | 243                       | 0.391        | 0.637                    | 2                | 2                      | 312                        | 245                    | 6        | 6                    | 8            | 8                  | 325                    | 250                |
| 10,000     | popularity | 1.025e+00 | cpu_seconds | 1               | 3                           | 20                  | 12                        | 3,281                         | 2,432                     | 2            | 4                        | 20               | 14                     | 3,114                      | 2,446                  | 7        | 9                    | 26           | 23                 | 3,193                  | 2,443              |
| 100,000    | popularity | 1.025e+01 | cpu_seconds | 10              | 27                          | 198                 | 120                       | 32,808                        | 24,324                    | 18           | 34                       | 198              | 133                    | 31,142                     | 24,456                 | 19       | 40                   | 209          | 172                | 31,883                 | 24,381             |
| 1,000,000  | popularity | 1.025e+02 | cpu_seconds | 103             | 268                         | 1,980               | 1,200                     | 328,083                       | 243,235                   | 181          | 340                      | 1,976            | 1,329                  | 311,416                    | 244,559                | 144      | 345                  | 2,039        | 1,666              | 318,781                | 243,757            |

### retraining

| retrain_every | n_requests | cheapest   | training_events | cost.popularity | cost.popularity+greedy_topk | cost.popularity+mmr | cost.popularity+quota_mmr | cost.popularity+qubo_feasible | cost.popularity+qubo_tabu | cost.itemknn | cost.itemknn+greedy_topk | cost.itemknn+mmr | cost.itemknn+quota_mmr | cost.itemknn+qubo_feasible | cost.itemknn+qubo_tabu | cost.als | cost.als+greedy_topk | cost.als+mmr | cost.als+quota_mmr | cost.als+qubo_feasible | cost.als+qubo_tabu |
|---------------|------------|------------|-----------------|-----------------|-----------------------------|---------------------|---------------------------|-------------------------------|---------------------------|--------------|--------------------------|------------------|------------------------|----------------------------|------------------------|----------|----------------------|--------------|--------------------|------------------------|--------------------|
| never         | 100,000    | popularity | 1               | 10              | 27                          | 198                 | 120                       | 32,808                        | 24,324                    | 18           | 34                       | 198              | 133                    | 31,142                     | 24,456                 | 19       | 40                   | 209          | 172                | 31,883                 | 24,381             |
| 1,000,000     | 100,000    | popularity | 1               | 10              | 27                          | 198                 | 120                       | 32,808                        | 24,324                    | 18           | 34                       | 198              | 133                    | 31,142                     | 24,456                 | 19       | 40                   | 209          | 172                | 31,883                 | 24,381             |
| 100,000       | 100,000    | popularity | 2               | 10              | 27                          | 198                 | 120                       | 32,808                        | 24,324                    | 18           | 35                       | 198              | 133                    | 31,142                     | 24,456                 | 25       | 46                   | 215          | 178                | 31,889                 | 24,387             |
| 10,000        | 100,000    | popularity | 11              | 10              | 28                          | 199                 | 121                       | 32,809                        | 24,324                    | 20           | 37                       | 201              | 136                    | 31,145                     | 24,459                 | 76       | 100                  | 270          | 234                | 31,941                 | 24,439             |
| 1,000         | 100,000    | popularity | 101             | 10              | 36                          | 207                 | 129                       | 32,818                        | 24,333                    | 39           | 64                       | 228              | 162                    | 31,171                     | 24,485                 | 582      | 645                  | 812          | 788                | 32,457                 | 24,959             |
| 100           | 100,000    | popularity | 1,001           | 10              | 117                         | 288                 | 210                       | 32,906                        | 24,414                    | 229          | 331                      | 495              | 422                    | 31,435                     | 24,749                 | 5,644    | 6,095                | 6,233        | 6,328              | 37,618                 | 30,158             |
