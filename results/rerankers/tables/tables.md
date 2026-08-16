# Results tables

Generated from `results\rerankers`.

## ml100k  (1,349 items)

### cost

| family     | reranker      | repeats | ndcg   | recall | exposure_parity | cpu_once  | cpu_per_request | spread_once | spread_per_request | cpu_train | cpu_rerank_setup | cpu_retrieve_score | cpu_retrieve_select | cpu_rerank |
|------------|---------------|---------|--------|--------|-----------------|-----------|-----------------|-------------|--------------------|-----------|------------------|--------------------|---------------------|------------|
| popularity | none          | 3       | 0.0398 | 0.0800 | 1.2040          | 1.663e-04 | 9.954e-05       | 19.0%       | 2.2%               | 1.663e-04 | 0.000e+00        | 5.787e-03          | 4.167e-03           | 0.000e+00  |
| als        | none          | 3       | 0.0638 | 0.1400 | 0.8440          | 5.906e+00 | 1.133e-04       | 17.5%       | 25.4%              | 5.906e+00 | 0.000e+00        | 7.102e-03          | 4.223e-03           | 0.000e+00  |
| itemknn    | none          | 3       | 0.0468 | 0.0900 | 1.1380          | 2.109e-01 | 1.969e-04       | 18.5%       | 13.6%              | 2.109e-01 | 0.000e+00        | 1.488e-02          | 4.664e-03           | 0.000e+00  |
| popularity | greedy_topk   | 3       | 0.0398 | 0.0800 | 1.2040          | 9.000e-02 | 2.500e-04       | 4.3%        | 1.7%               | 1.581e-04 | 8.984e-02        | 5.896e-03          | 4.112e-03           | 1.488e-02  |
| als        | greedy_topk   | 3       | 0.0638 | 0.1400 | 0.8440          | 6.245e+00 | 3.714e-04       | 11.3%       | 13.7%              | 6.141e+00 | 9.375e-02        | 8.681e-03          | 4.281e-03           | 2.051e-02  |
| itemknn    | greedy_topk   | 3       | 0.0468 | 0.0900 | 1.1380          | 3.086e-01 | 3.815e-04       | 13.9%       | 49.0%              | 2.109e-01 | 9.766e-02        | 1.488e-02          | 4.735e-03           | 1.838e-02  |
| popularity | quota_mmr     | 3       | 0.0507 | 0.1100 | 0.2630          | 9.001e-02 | 1.359e-03       | 8.7%        | 11.4%              | 1.620e-04 | 8.984e-02        | 6.010e-03          | 4.401e-03           | 1.250e-01  |
| als        | quota_mmr     | 3       | 0.0591 | 0.1100 | 0.2550          | 5.871e+00 | 1.515e-03       | 9.7%        | 13.3%              | 5.781e+00 | 8.984e-02        | 7.267e-03          | 4.112e-03           | 1.406e-01  |
| itemknn    | quota_mmr     | 3       | 0.0523 | 0.1000 | 0.2450          | 3.125e-01 | 1.565e-03       | 12.1%       | 12.5%              | 2.188e-01 | 9.375e-02        | 1.645e-02          | 4.664e-03           | 1.354e-01  |
| popularity | mmr           | 3       | 0.0464 | 0.1000 | 0.9680          | 9.002e-02 | 1.986e-03       | 4.3%        | 4.0%               | 1.606e-04 | 8.984e-02        | 5.896e-03          | 4.401e-03           | 1.875e-01  |
| als        | mmr           | 3       | 0.0735 | 0.1300 | 0.7680          | 6.012e+00 | 2.034e-03       | 4.4%        | 26.4%              | 5.922e+00 | 8.984e-02        | 1.008e-02          | 4.464e-03           | 1.875e-01  |
| itemknn    | mmr           | 3       | 0.0629 | 0.1400 | 1.0180          | 2.969e-01 | 2.157e-03       | 56.6%       | 28.0%              | 2.031e-01 | 9.375e-02        | 1.562e-02          | 4.735e-03           | 1.953e-01  |
| popularity | qubo_tabu     | 3       | 0.0423 | 0.0700 | 0.2000          | 9.001e-02 | 2.471e-01       | 16.0%       | 1.7%               | 1.690e-04 | 8.984e-02        | 6.250e-03          | 4.340e-03           | 2.470e+01  |
| als        | qubo_tabu     | 3       | 0.0676 | 0.1000 | 0.2000          | 6.895e+00 | 2.473e-01       | 6.2%        | 2.1%               | 6.797e+00 | 9.766e-02        | 1.875e-02          | 5.123e-03           | 2.472e+01  |
| itemknn    | qubo_tabu     | 3       | 0.0600 | 0.1200 | 0.2000          | 2.891e-01 | 2.486e-01       | 8.1%        | 4.2%               | 1.953e-01 | 8.984e-02        | 1.420e-02          | 4.223e-03           | 2.484e+01  |
| itemknn    | qubo_feasible | 3       | 0.0480 | 0.0900 | 0.2000          | 3.047e-01 | 3.305e-01       | 11.1%       | 8.3%               | 2.109e-01 | 9.375e-02        | 1.562e-02          | 4.735e-03           | 3.303e+01  |
| als        | qubo_feasible | 3       | 0.0523 | 0.0800 | 0.2000          | 5.797e+00 | 3.328e-01       | 9.0%        | 21.7%              | 5.703e+00 | 9.375e-02        | 9.470e-03          | 4.281e-03           | 3.327e+01  |
| popularity | qubo_feasible | 3       | 0.0384 | 0.0700 | 0.2000          | 9.393e-02 | 3.409e-01       | 12.5%       | 23.5%              | 1.743e-04 | 9.375e-02        | 6.127e-03          | 4.664e-03           | 3.408e+01  |

### breakeven

| a                        | b                        | n_requests | lo       | hi      | replicates_crossing | repeats | stable | cheaper_below            | cheaper_above          |
|--------------------------|--------------------------|------------|----------|---------|---------------------|---------|--------|--------------------------|------------------------|
| popularity               | popularity+greedy_topk   | --         | --       | --      | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | popularity+mmr           | --         | --       | --      | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | popularity+quota_mmr     | --         | --       | --      | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | popularity+qubo_feasible | --         | --       | --      | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | popularity+qubo_tabu     | --         | --       | --      | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | itemknn                  | --         | --       | --      | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | itemknn+greedy_topk      | --         | --       | --      | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | itemknn+mmr              | --         | --       | --      | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | itemknn+quota_mmr        | --         | --       | --      | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | itemknn+qubo_feasible    | --         | --       | --      | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | itemknn+qubo_tabu        | --         | --       | --      | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | als                      | --         | --       | --      | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | als+greedy_topk          | --         | --       | --      | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | als+mmr                  | --         | --       | --      | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | als+quota_mmr            | --         | --       | --      | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | als+qubo_feasible        | --         | --       | --      | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity               | als+qubo_tabu            | --         | --       | --      | 0.0%                | 3       | no     | popularity               | popularity             |
| popularity+greedy_topk   | popularity+mmr           | --         | --       | --      | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | popularity+quota_mmr     | --         | --       | --      | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | popularity+qubo_feasible | --         | --       | --      | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | popularity+qubo_tabu     | --         | --       | --      | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | itemknn                  | 2,520      | 1,506    | 3,209   | 100.0%              | 3       | yes    | popularity+greedy_topk   | itemknn                |
| popularity+greedy_topk   | itemknn+greedy_topk      | --         | --       | --      | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | itemknn+mmr              | --         | --       | --      | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | itemknn+quota_mmr        | --         | --       | --      | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | itemknn+qubo_feasible    | --         | --       | --      | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | itemknn+qubo_tabu        | --         | --       | --      | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | als                      | 47,256     | 39,829   | 49,804  | 100.0%              | 3       | yes    | popularity+greedy_topk   | als                    |
| popularity+greedy_topk   | als+greedy_topk          | --         | --       | --      | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | als+mmr                  | --         | --       | --      | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | als+quota_mmr            | --         | --       | --      | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | als+qubo_feasible        | --         | --       | --      | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+greedy_topk   | als+qubo_tabu            | --         | --       | --      | 0.0%                | 3       | no     | popularity+greedy_topk   | popularity+greedy_topk |
| popularity+mmr           | popularity+quota_mmr     | 11         | 0.00187  | 12      | 37.5%               | 3       | no     | popularity+mmr           | popularity+quota_mmr   |
| popularity+mmr           | popularity+qubo_feasible | 4.33e-05   | 4.33e-05 | 0.0115  | 19.4%               | 3       | no     | popularity+qubo_feasible | popularity+mmr         |
| popularity+mmr           | popularity+qubo_tabu     | 8.42e-05   | 4.06e-06 | 0.0161  | 63.1%               | 3       | no     | popularity+qubo_tabu     | popularity+mmr         |
| popularity+mmr           | itemknn                  | 66         | 56       | 81      | 100.0%              | 3       | yes    | popularity+mmr           | itemknn                |
| popularity+mmr           | itemknn+greedy_topk      | 134        | 114      | 165     | 100.0%              | 3       | yes    | popularity+mmr           | itemknn+greedy_topk    |
| popularity+mmr           | itemknn+mmr              | 2,708      | 2,708    | 2,708   | 6.8%                | 3       | no     | popularity+mmr           | itemknn+mmr            |
| popularity+mmr           | itemknn+quota_mmr        | 529        | 303      | 622     | 100.0%              | 3       | yes    | popularity+mmr           | itemknn+quota_mmr      |
| popularity+mmr           | itemknn+qubo_feasible    | --         | --       | --      | 0.0%                | 3       | no     | popularity+mmr           | popularity+mmr         |
| popularity+mmr           | itemknn+qubo_tabu        | --         | --       | --      | 0.0%                | 3       | no     | popularity+mmr           | popularity+mmr         |
| popularity+mmr           | als                      | 3,098      | 2,929    | 3,569   | 100.0%              | 3       | yes    | popularity+mmr           | als                    |
| popularity+mmr           | als+greedy_topk          | 3,813      | 3,318    | 4,033   | 100.0%              | 3       | yes    | popularity+mmr           | als+greedy_topk        |
| popularity+mmr           | als+mmr                  | 241,804    | 156,268  | 243,080 | 18.6%               | 3       | no     | popularity+mmr           | als+mmr                |
| popularity+mmr           | als+quota_mmr            | 12,295     | 10,587   | 18,623  | 100.0%              | 3       | yes    | popularity+mmr           | als+quota_mmr          |
| popularity+mmr           | als+qubo_feasible        | --         | --       | --      | 0.0%                | 3       | no     | popularity+mmr           | popularity+mmr         |
| popularity+mmr           | als+qubo_tabu            | --         | --       | --      | 0.0%                | 3       | no     | popularity+mmr           | popularity+mmr         |
| popularity+quota_mmr     | popularity+qubo_feasible | 0.0128     | 0.0115   | 0.0231  | 18.4%               | 3       | no     | popularity+qubo_feasible | popularity+quota_mmr   |
| popularity+quota_mmr     | popularity+qubo_tabu     | 0.0319     | 9.87e-06 | 0.0322  | 30.9%               | 3       | no     | popularity+qubo_tabu     | popularity+quota_mmr   |
| popularity+quota_mmr     | itemknn                  | 99         | 83       | 131     | 100.0%              | 3       | yes    | popularity+quota_mmr     | itemknn                |
| popularity+quota_mmr     | itemknn+greedy_topk      | 216        | 177      | 313     | 100.0%              | 3       | yes    | popularity+quota_mmr     | itemknn+greedy_topk    |
| popularity+quota_mmr     | itemknn+mmr              | --         | --       | --      | 0.0%                | 3       | no     | popularity+quota_mmr     | popularity+quota_mmr   |
| popularity+quota_mmr     | itemknn+quota_mmr        | 4,738      | 4,738    | 4,738   | 6.0%                | 3       | no     | popularity+quota_mmr     | itemknn+quota_mmr      |
| popularity+quota_mmr     | itemknn+qubo_feasible    | --         | --       | --      | 0.0%                | 3       | no     | popularity+quota_mmr     | popularity+quota_mmr   |
| popularity+quota_mmr     | itemknn+qubo_tabu        | --         | --       | --      | 0.0%                | 3       | no     | popularity+quota_mmr     | popularity+quota_mmr   |
| popularity+quota_mmr     | als                      | 4,662      | 4,271    | 5,613   | 100.0%              | 3       | yes    | popularity+quota_mmr     | als                    |
| popularity+quota_mmr     | als+greedy_topk          | 6,224      | 5,105    | 7,030   | 100.0%              | 3       | yes    | popularity+quota_mmr     | als+greedy_topk        |
| popularity+quota_mmr     | als+mmr                  | --         | --       | --      | 0.0%                | 3       | no     | popularity+quota_mmr     | popularity+quota_mmr   |
| popularity+quota_mmr     | als+quota_mmr            | --         | --       | --      | 0.0%                | 3       | no     | popularity+quota_mmr     | popularity+quota_mmr   |
| popularity+quota_mmr     | als+qubo_feasible        | --         | --       | --      | 0.0%                | 3       | no     | popularity+quota_mmr     | popularity+quota_mmr   |
| popularity+quota_mmr     | als+qubo_tabu            | --         | --       | --      | 0.0%                | 3       | no     | popularity+quota_mmr     | popularity+quota_mmr   |
| popularity+qubo_feasible | popularity+qubo_tabu     | 0.113      | 3.91e-05 | 0.178   | 37.4%               | 3       | no     | popularity+qubo_feasible | popularity+qubo_tabu   |
| popularity+qubo_feasible | itemknn                  | 0.343      | 0.242    | 0.457   | 100.0%              | 3       | yes    | popularity+qubo_feasible | itemknn                |
| popularity+qubo_feasible | itemknn+greedy_topk      | 0.63       | 0.474    | 0.763   | 100.0%              | 3       | yes    | popularity+qubo_feasible | itemknn+greedy_topk    |
| popularity+qubo_feasible | itemknn+mmr              | 0.611      | 0.476    | 1       | 100.0%              | 3       | yes    | popularity+qubo_feasible | itemknn+mmr            |
| popularity+qubo_feasible | itemknn+quota_mmr        | 0.644      | 0.475    | 0.749   | 100.0%              | 3       | yes    | popularity+qubo_feasible | itemknn+quota_mmr      |
| popularity+qubo_feasible | itemknn+qubo_feasible    | 10         | 3        | 24      | 62.4%               | 3       | no     | popularity+qubo_feasible | itemknn+qubo_feasible  |
| popularity+qubo_feasible | itemknn+qubo_tabu        | 2          | 1        | 4       | 100.0%              | 3       | yes    | popularity+qubo_feasible | itemknn+qubo_tabu      |
| popularity+qubo_feasible | als                      | 17         | 15       | 22      | 100.0%              | 3       | yes    | popularity+qubo_feasible | als                    |
| popularity+qubo_feasible | als+greedy_topk          | 18         | 15       | 21      | 100.0%              | 3       | yes    | popularity+qubo_feasible | als+greedy_topk        |
| popularity+qubo_feasible | als+mmr                  | 17         | 15       | 19      | 100.0%              | 3       | yes    | popularity+qubo_feasible | als+mmr                |
| popularity+qubo_feasible | als+quota_mmr            | 17         | 14       | 20      | 100.0%              | 3       | yes    | popularity+qubo_feasible | als+quota_mmr          |
| popularity+qubo_feasible | als+qubo_feasible        | 182        | 72       | 1,075   | 62.0%               | 3       | no     | popularity+qubo_feasible | als+qubo_feasible      |
| popularity+qubo_feasible | als+qubo_tabu            | 72         | 47       | 120     | 100.0%              | 3       | yes    | popularity+qubo_feasible | als+qubo_tabu          |
| popularity+qubo_tabu     | itemknn                  | 0.49       | 0.366    | 0.591   | 100.0%              | 3       | yes    | popularity+qubo_tabu     | itemknn                |
| popularity+qubo_tabu     | itemknn+greedy_topk      | 0.886      | 0.728    | 0.976   | 100.0%              | 3       | yes    | popularity+qubo_tabu     | itemknn+greedy_topk    |
| popularity+qubo_tabu     | itemknn+mmr              | 0.844      | 0.733    | 2       | 100.0%              | 3       | yes    | popularity+qubo_tabu     | itemknn+mmr            |
| popularity+qubo_tabu     | itemknn+quota_mmr        | 0.906      | 0.731    | 0.959   | 100.0%              | 3       | yes    | popularity+qubo_tabu     | itemknn+quota_mmr      |
| popularity+qubo_tabu     | itemknn+qubo_feasible    | --         | --       | --      | 0.0%                | 3       | no     | popularity+qubo_tabu     | popularity+qubo_tabu   |
| popularity+qubo_tabu     | itemknn+qubo_tabu        | 275        | 36       | 2,414   | 39.2%               | 3       | no     | popularity+qubo_tabu     | itemknn+qubo_tabu      |
| popularity+qubo_tabu     | als                      | 24         | 23       | 27      | 100.0%              | 3       | yes    | popularity+qubo_tabu     | als                    |
| popularity+qubo_tabu     | als+greedy_topk          | 25         | 23       | 26      | 100.0%              | 3       | yes    | popularity+qubo_tabu     | als+greedy_topk        |
| popularity+qubo_tabu     | als+mmr                  | 24         | 23       | 25      | 100.0%              | 3       | yes    | popularity+qubo_tabu     | als+mmr                |
| popularity+qubo_tabu     | als+quota_mmr            | 24         | 23       | 25      | 100.0%              | 3       | yes    | popularity+qubo_tabu     | als+quota_mmr          |
| popularity+qubo_tabu     | als+qubo_feasible        | --         | --       | --      | 0.0%                | 3       | no     | popularity+qubo_tabu     | popularity+qubo_tabu   |
| popularity+qubo_tabu     | als+qubo_tabu            | 4,772      | 1,198    | 14,442  | 44.9%               | 3       | no     | popularity+qubo_tabu     | als+qubo_tabu          |
| itemknn                  | itemknn+greedy_topk      | --         | --       | --      | 0.0%                | 3       | no     | itemknn                  | itemknn                |
| itemknn                  | itemknn+mmr              | --         | --       | --      | 0.0%                | 3       | no     | itemknn                  | itemknn                |
| itemknn                  | itemknn+quota_mmr        | --         | --       | --      | 0.0%                | 3       | no     | itemknn                  | itemknn                |
| itemknn                  | itemknn+qubo_feasible    | --         | --       | --      | 0.0%                | 3       | no     | itemknn                  | itemknn                |
| itemknn                  | itemknn+qubo_tabu        | --         | --       | --      | 0.0%                | 3       | no     | itemknn                  | itemknn                |
| itemknn                  | als                      | 75,026     | 55,316   | 116,655 | 100.0%              | 3       | yes    | itemknn                  | als                    |
| itemknn                  | als+greedy_topk          | --         | --       | --      | 0.0%                | 3       | no     | itemknn                  | itemknn                |
| itemknn                  | als+mmr                  | --         | --       | --      | 0.0%                | 3       | no     | itemknn                  | itemknn                |
| itemknn                  | als+quota_mmr            | --         | --       | --      | 0.0%                | 3       | no     | itemknn                  | itemknn                |
| itemknn                  | als+qubo_feasible        | --         | --       | --      | 0.0%                | 3       | no     | itemknn                  | itemknn                |
| itemknn                  | als+qubo_tabu            | --         | --       | --      | 0.0%                | 3       | no     | itemknn                  | itemknn                |
| itemknn+greedy_topk      | itemknn+mmr              | 15         | 7        | 30      | 54.7%               | 3       | no     | itemknn+mmr              | itemknn+greedy_topk    |
| itemknn+greedy_topk      | itemknn+quota_mmr        | 23         | 5        | 49      | 37.7%               | 3       | no     | itemknn+quota_mmr        | itemknn+greedy_topk    |
| itemknn+greedy_topk      | itemknn+qubo_feasible    | 0.0123     | 0.0113   | 0.0735  | 54.7%               | 3       | no     | itemknn+qubo_feasible    | itemknn+greedy_topk    |
| itemknn+greedy_topk      | itemknn+qubo_tabu        | 0.0963     | 0.0769   | 0.177   | 61.4%               | 3       | no     | itemknn+qubo_tabu        | itemknn+greedy_topk    |
| itemknn+greedy_topk      | als                      | 22,124     | 12,920   | 26,972  | 100.0%              | 3       | yes    | itemknn+greedy_topk      | als                    |
| itemknn+greedy_topk      | als+greedy_topk          | 117,599    | 26,706   | 591,868 | 68.5%               | 3       | no     | itemknn+greedy_topk      | als+greedy_topk        |
| itemknn+greedy_topk      | als+mmr                  | --         | --       | --      | 0.0%                | 3       | no     | itemknn+greedy_topk      | itemknn+greedy_topk    |
| itemknn+greedy_topk      | als+quota_mmr            | --         | --       | --      | 0.0%                | 3       | no     | itemknn+greedy_topk      | itemknn+greedy_topk    |
| itemknn+greedy_topk      | als+qubo_feasible        | --         | --       | --      | 0.0%                | 3       | no     | itemknn+greedy_topk      | itemknn+greedy_topk    |
| itemknn+greedy_topk      | als+qubo_tabu            | --         | --       | --      | 0.0%                | 3       | no     | itemknn+greedy_topk      | itemknn+greedy_topk    |
| itemknn+mmr              | itemknn+quota_mmr        | 48         | 26       | 100     | 56.2%               | 3       | no     | itemknn+mmr              | itemknn+quota_mmr      |
| itemknn+mmr              | itemknn+qubo_feasible    | 0.431      | 0.349    | 0.469   | 25.5%               | 3       | no     | itemknn+qubo_feasible    | itemknn+mmr            |
| itemknn+mmr              | itemknn+qubo_tabu        | 0.0485     | 0.031    | 0.696   | 61.4%               | 3       | no     | itemknn+qubo_tabu        | itemknn+mmr            |
| itemknn+mmr              | als                      | 2,738      | 2,146    | 3,452   | 100.0%              | 3       | yes    | itemknn+mmr              | als                    |
| itemknn+mmr              | als+greedy_topk          | 3,332      | 2,373    | 3,892   | 100.0%              | 3       | yes    | itemknn+mmr              | als+greedy_topk        |
| itemknn+mmr              | als+mmr                  | 41,936     | 9,740    | 158,400 | 61.4%               | 3       | no     | itemknn+mmr              | als+mmr                |
| itemknn+mmr              | als+quota_mmr            | 8,755      | 5,036    | 17,504  | 100.0%              | 3       | yes    | itemknn+mmr              | als+quota_mmr          |
| itemknn+mmr              | als+qubo_feasible        | --         | --       | --      | 0.0%                | 3       | no     | itemknn+mmr              | itemknn+mmr            |
| itemknn+mmr              | als+qubo_tabu            | --         | --       | --      | 0.0%                | 3       | no     | itemknn+mmr              | itemknn+mmr            |
| itemknn+quota_mmr        | itemknn+qubo_feasible    | 0.0246     | 0.0226   | 0.0574  | 54.7%               | 3       | no     | itemknn+qubo_feasible    | itemknn+quota_mmr      |
| itemknn+quota_mmr        | itemknn+qubo_tabu        | 0.0949     | 0.0158   | 0.156   | 74.1%               | 3       | no     | itemknn+qubo_tabu        | itemknn+quota_mmr      |
| itemknn+quota_mmr        | als                      | 3,852      | 3,663    | 4,971   | 100.0%              | 3       | yes    | itemknn+quota_mmr        | als                    |
| itemknn+quota_mmr        | als+greedy_topk          | 4,969      | 4,302    | 6,060   | 100.0%              | 3       | yes    | itemknn+quota_mmr        | als+greedy_topk        |
| itemknn+quota_mmr        | als+mmr                  | --         | --       | --      | 0.0%                | 3       | no     | itemknn+quota_mmr        | itemknn+quota_mmr      |
| itemknn+quota_mmr        | als+quota_mmr            | 66,199     | 44,176   | 111,219 | 54.7%               | 3       | no     | itemknn+quota_mmr        | als+quota_mmr          |
| itemknn+quota_mmr        | als+qubo_feasible        | --         | --       | --      | 0.0%                | 3       | no     | itemknn+quota_mmr        | itemknn+quota_mmr      |
| itemknn+quota_mmr        | als+qubo_tabu            | --         | --       | --      | 0.0%                | 3       | no     | itemknn+quota_mmr        | itemknn+quota_mmr      |
| itemknn+qubo_feasible    | itemknn+qubo_tabu        | 0.0477     | 0.0399   | 0.0553  | 19.3%               | 3       | no     | itemknn+qubo_feasible    | itemknn+qubo_tabu      |
| itemknn+qubo_feasible    | als                      | 17         | 16       | 20      | 100.0%              | 3       | yes    | itemknn+qubo_feasible    | als                    |
| itemknn+qubo_feasible    | als+greedy_topk          | 18         | 16       | 19      | 100.0%              | 3       | yes    | itemknn+qubo_feasible    | als+greedy_topk        |
| itemknn+qubo_feasible    | als+mmr                  | 17         | 16       | 18      | 100.0%              | 3       | yes    | itemknn+qubo_feasible    | als+mmr                |
| itemknn+qubo_feasible    | als+quota_mmr            | 17         | 16       | 19      | 100.0%              | 3       | yes    | itemknn+qubo_feasible    | als+quota_mmr          |
| itemknn+qubo_feasible    | als+qubo_feasible        | 262        | 147      | 575     | 37.6%               | 3       | no     | itemknn+qubo_feasible    | als+qubo_feasible      |
| itemknn+qubo_feasible    | als+qubo_tabu            | 79         | 64       | 97      | 100.0%              | 3       | yes    | itemknn+qubo_feasible    | als+qubo_tabu          |
| itemknn+qubo_tabu        | als                      | 23         | 21       | 27      | 100.0%              | 3       | yes    | itemknn+qubo_tabu        | als                    |
| itemknn+qubo_tabu        | als+greedy_topk          | 24         | 22       | 26      | 100.0%              | 3       | yes    | itemknn+qubo_tabu        | als+greedy_topk        |
| itemknn+qubo_tabu        | als+mmr                  | 23         | 22       | 24      | 100.0%              | 3       | yes    | itemknn+qubo_tabu        | als+mmr                |
| itemknn+qubo_tabu        | als+quota_mmr            | 23         | 21       | 25      | 100.0%              | 3       | yes    | itemknn+qubo_tabu        | als+quota_mmr          |
| itemknn+qubo_tabu        | als+qubo_feasible        | --         | --       | --      | 0.0%                | 3       | no     | itemknn+qubo_tabu        | itemknn+qubo_tabu      |
| itemknn+qubo_tabu        | als+qubo_tabu            | 5,013      | 590      | 16,986  | 81.3%               | 3       | no     | itemknn+qubo_tabu        | als+qubo_tabu          |
| als                      | als+greedy_topk          | 1,957      | 431      | 4,251   | 38.7%               | 3       | no     | als+greedy_topk          | als                    |
| als                      | als+mmr                  | 384        | 51       | 396     | 38.7%               | 3       | no     | als+mmr                  | als                    |
| als                      | als+quota_mmr            | 137        | 18       | 677     | 69.2%               | 3       | no     | als+quota_mmr            | als                    |
| als                      | als+qubo_feasible        | 0.568      | 0.286    | 3       | 62.6%               | 3       | no     | als+qubo_feasible        | als                    |
| als                      | als+qubo_tabu            | --         | --       | --      | 0.0%                | 3       | no     | als                      | als                    |
| als+greedy_topk          | als+mmr                  | 141        | 12       | 338     | 81.2%               | 3       | no     | als+mmr                  | als+greedy_topk        |
| als+greedy_topk          | als+quota_mmr            | 327        | 87       | 638     | 69.0%               | 3       | no     | als+quota_mmr            | als+greedy_topk        |
| als+greedy_topk          | als+qubo_feasible        | 1          | 0.0307   | 3       | 81.0%               | 3       | no     | als+qubo_feasible        | als+greedy_topk        |
| als+greedy_topk          | als+qubo_tabu            | --         | --       | --      | 0.0%                | 3       | no     | als+greedy_topk          | als+greedy_topk        |
| als+mmr                  | als+quota_mmr            | 444        | 86       | 459     | 37.0%               | 3       | no     | als+mmr                  | als+quota_mmr          |
| als+mmr                  | als+qubo_feasible        | 0.649      | 0.165    | 1       | 62.6%               | 3       | no     | als+qubo_feasible        | als+mmr                |
| als+mmr                  | als+qubo_tabu            | --         | --       | --      | 0.0%                | 3       | no     | als+mmr                  | als+mmr                |
| als+quota_mmr            | als+qubo_feasible        | 0.456      | 0.0236   | 2       | 62.3%               | 3       | no     | als+qubo_feasible        | als+quota_mmr          |
| als+quota_mmr            | als+qubo_tabu            | --         | --       | --      | 0.0%                | 3       | no     | als+quota_mmr            | als+quota_mmr          |
| als+qubo_feasible        | als+qubo_tabu            | 11         | 6        | 24      | 100.0%              | 3       | yes    | als+qubo_feasible        | als+qubo_tabu          |

### rerank_share

| family     | reranker      | cpu_rerank | cpu_serving_total | rerank_share_of_serving | cpu_rerank_setup | serving_multiplier |
|------------|---------------|------------|-------------------|-------------------------|------------------|--------------------|
| popularity | greedy_topk   | 1.488e-02  | 2.500e-02         | 59.5%                   | 8.984e-02        | 2.4706             |
| popularity | mmr           | 1.875e-01  | 1.986e-01         | 94.8%                   | 8.984e-02        | 19.2081            |
| popularity | quota_mmr     | 1.250e-01  | 1.359e-01         | 92.2%                   | 8.984e-02        | 12.7717            |
| popularity | qubo_feasible | 3.408e+01  | 3.409e+01         | 100.0%                  | 9.375e-02        | 3212.1159          |
| popularity | qubo_tabu     | 2.470e+01  | 2.471e+01         | 100.0%                  | 8.984e-02        | 2333.6230          |
| itemknn    | greedy_topk   | 1.838e-02  | 3.815e-02         | 48.2%                   | 9.766e-02        | 1.9301             |
| itemknn    | mmr           | 1.953e-01  | 2.157e-01         | 90.5%                   | 9.375e-02        | 10.4875            |
| itemknn    | quota_mmr     | 1.354e-01  | 1.565e-01         | 86.5%                   | 9.375e-02        | 7.4143             |
| itemknn    | qubo_feasible | 3.303e+01  | 3.305e+01         | 99.9%                   | 9.375e-02        | 1641.8378          |
| itemknn    | qubo_tabu     | 2.484e+01  | 2.486e+01         | 99.9%                   | 8.984e-02        | 1383.9381          |
| als        | greedy_topk   | 2.051e-02  | 3.714e-02         | 61.3%                   | 9.375e-02        | 2.5822             |
| als        | mmr           | 1.875e-01  | 2.034e-01         | 92.8%                   | 8.984e-02        | 13.8911            |
| als        | quota_mmr     | 1.406e-01  | 1.515e-01         | 92.8%                   | 8.984e-02        | 13.8951            |
| als        | qubo_feasible | 3.327e+01  | 3.328e+01         | 100.0%                  | 9.375e-02        | 2355.8515          |
| als        | qubo_tabu     | 2.472e+01  | 2.473e+01         | 99.9%                   | 9.766e-02        | 1021.6356          |

### rerankers

| family     | reranker      | repeats | cpu_rerank_per_request | cpu_serving_per_request | rerank_share | ndcg   | exposure_parity | recall | time_bounded | cost_vs_cheapest |
|------------|---------------|---------|------------------------|-------------------------|--------------|--------|-----------------|--------|--------------|------------------|
| als        | greedy_topk   | 3       | 2.051e-04              | 3.714e-04               | 61.3%        | 0.0638 | 0.8440          | 0.1400 | no           | 1.0000           |
| als        | quota_mmr     | 3       | 1.406e-03              | 1.515e-03               | 92.8%        | 0.0591 | 0.2550          | 0.1100 | no           | 6.8571           |
| als        | mmr           | 3       | 1.875e-03              | 2.034e-03               | 92.8%        | 0.0735 | 0.7680          | 0.1300 | no           | 9.1429           |
| als        | qubo_tabu     | 3       | 2.472e-01              | 2.473e-01               | 99.9%        | 0.0676 | 0.2000          | 0.1000 | yes          | 1205.3333        |
| als        | qubo_feasible | 3       | 3.327e-01              | 3.328e-01               | 100.0%       | 0.0523 | 0.2000          | 0.0800 | no           | 1622.0952        |
| itemknn    | greedy_topk   | 3       | 1.838e-04              | 3.815e-04               | 48.2%        | 0.0468 | 1.1380          | 0.0900 | no           | 1.0000           |
| itemknn    | quota_mmr     | 3       | 1.354e-03              | 1.565e-03               | 86.5%        | 0.0523 | 0.2450          | 0.1000 | no           | 7.3667           |
| itemknn    | mmr           | 3       | 1.953e-03              | 2.157e-03               | 90.5%        | 0.0629 | 1.0180          | 0.1400 | no           | 10.6250          |
| itemknn    | qubo_tabu     | 3       | 2.484e-01              | 2.486e-01               | 99.9%        | 0.0600 | 0.2000          | 0.1200 | yes          | 1351.5000        |
| itemknn    | qubo_feasible | 3       | 3.303e-01              | 3.305e-01               | 99.9%        | 0.0480 | 0.2000          | 0.0900 | no           | 1796.9000        |
| popularity | greedy_topk   | 3       | 1.488e-04              | 2.500e-04               | 59.5%        | 0.0398 | 1.2040          | 0.0800 | no           | 1.0000           |
| popularity | quota_mmr     | 3       | 1.250e-03              | 1.359e-03               | 92.2%        | 0.0507 | 0.2630          | 0.1100 | no           | 8.4000           |
| popularity | mmr           | 3       | 1.875e-03              | 1.986e-03               | 94.8%        | 0.0464 | 0.9680          | 0.1000 | no           | 12.6000          |
| popularity | qubo_tabu     | 3       | 2.470e-01              | 2.471e-01               | 100.0%       | 0.0423 | 0.2000          | 0.0700 | yes          | 1660.0500        |
| popularity | qubo_feasible | 3       | 3.408e-01              | 3.409e-01               | 100.0%       | 0.0384 | 0.2000          | 0.0700 | no           | 2290.0500        |

### frontier

| n_requests | frontier                                                                                | dominated                                                                                                                                                                                                                                                                              | cheapest   | most_accurate |
|------------|-----------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------|---------------|
| 1          | popularity, popularity+quota_mmr, itemknn+mmr, als, als+mmr                             | als+qubo_tabu, als+greedy_topk, als+qubo_feasible, als+quota_mmr, itemknn+qubo_feasible, itemknn+qubo_tabu, popularity+qubo_feasible, popularity+qubo_tabu, itemknn+quota_mmr, itemknn+greedy_topk, itemknn, popularity+mmr, popularity+greedy_topk                                    | popularity | als+mmr       |
| 10         | popularity, popularity+quota_mmr, itemknn+mmr, als, als+mmr                             | als+qubo_tabu, als+qubo_feasible, als+greedy_topk, als+quota_mmr, itemknn+qubo_feasible, popularity+qubo_feasible, itemknn+qubo_tabu, popularity+qubo_tabu, itemknn+quota_mmr, itemknn+greedy_topk, itemknn, popularity+mmr, popularity+greedy_topk                                    | popularity | als+mmr       |
| 100        | popularity, popularity+quota_mmr, itemknn+quota_mmr, itemknn+mmr, als, als+mmr          | als+qubo_feasible, popularity+qubo_feasible, itemknn+qubo_feasible, als+qubo_tabu, itemknn+qubo_tabu, popularity+qubo_tabu, als+greedy_topk, als+quota_mmr, itemknn+greedy_topk, popularity+mmr, itemknn, popularity+greedy_topk                                                       | popularity | als+mmr       |
| 1,000      | popularity, itemknn, popularity+quota_mmr, itemknn+quota_mmr, itemknn+mmr, als, als+mmr | popularity+qubo_feasible, als+qubo_feasible, itemknn+qubo_feasible, als+qubo_tabu, itemknn+qubo_tabu, popularity+qubo_tabu, als+quota_mmr, als+greedy_topk, popularity+mmr, itemknn+greedy_topk, popularity+greedy_topk                                                                | popularity | als+mmr       |
| 10,000     | popularity, itemknn, als, als+mmr                                                       | popularity+qubo_feasible, als+qubo_feasible, itemknn+qubo_feasible, itemknn+qubo_tabu, als+qubo_tabu, popularity+qubo_tabu, itemknn+mmr, als+quota_mmr, popularity+mmr, itemknn+quota_mmr, popularity+quota_mmr, als+greedy_topk, itemknn+greedy_topk, popularity+greedy_topk          | popularity | als+mmr       |
| 100,000    | popularity, als, als+mmr                                                                | popularity+qubo_feasible, als+qubo_feasible, itemknn+qubo_feasible, itemknn+qubo_tabu, als+qubo_tabu, popularity+qubo_tabu, itemknn+mmr, popularity+mmr, als+quota_mmr, itemknn+quota_mmr, popularity+quota_mmr, als+greedy_topk, itemknn+greedy_topk, popularity+greedy_topk, itemknn | popularity | als+mmr       |
| 1,000,000  | popularity, als, als+mmr                                                                | popularity+qubo_feasible, als+qubo_feasible, itemknn+qubo_feasible, itemknn+qubo_tabu, als+qubo_tabu, popularity+qubo_tabu, itemknn+mmr, popularity+mmr, itemknn+quota_mmr, als+quota_mmr, popularity+quota_mmr, itemknn+greedy_topk, als+greedy_topk, popularity+greedy_topk, itemknn | popularity | als+mmr       |

### regimes

| n_requests | cheapest   | cost      | unit        | cost.popularity | cost.popularity+greedy_topk | cost.popularity+mmr | cost.popularity+quota_mmr | cost.popularity+qubo_feasible | cost.popularity+qubo_tabu | cost.itemknn | cost.itemknn+greedy_topk | cost.itemknn+mmr | cost.itemknn+quota_mmr | cost.itemknn+qubo_feasible | cost.itemknn+qubo_tabu | cost.als | cost.als+greedy_topk | cost.als+mmr | cost.als+quota_mmr | cost.als+qubo_feasible | cost.als+qubo_tabu |
|------------|------------|-----------|-------------|-----------------|-----------------------------|---------------------|---------------------------|-------------------------------|---------------------------|--------------|--------------------------|------------------|------------------------|----------------------------|------------------------|----------|----------------------|--------------|--------------------|------------------------|--------------------|
| 1          | popularity | 2.658e-04 | cpu_seconds | 0.000266        | 0.0903                      | 0.092               | 0.0914                    | 0.435                         | 0.337                     | 0.211        | 0.309                    | 0.299            | 0.314                  | 0.635                      | 0.538                  | 6        | 6                    | 6            | 6                  | 6                      | 7                  |
| 10         | popularity | 1.162e-03 | cpu_seconds | 0.00116         | 0.0925                      | 0.11                | 0.104                     | 4                             | 3                         | 0.213        | 0.312                    | 0.318            | 0.328                  | 4                          | 3                      | 6        | 6                    | 6            | 6                  | 9                      | 9                  |
| 100        | popularity | 1.012e-02 | cpu_seconds | 0.0101          | 0.115                       | 0.289               | 0.226                     | 34                            | 25                        | 0.231        | 0.347                    | 0.513            | 0.469                  | 33                         | 25                     | 6        | 6                    | 6            | 6                  | 39                     | 32                 |
| 1,000      | popularity | 9.970e-02 | cpu_seconds | 0.0997          | 0.34                        | 2                   | 1                         | 341                           | 247                       | 0.408        | 0.69                     | 2                | 2                      | 331                        | 249                    | 6        | 7                    | 8            | 7                  | 339                    | 254                |
| 10,000     | popularity | 9.955e-01 | cpu_seconds | 0.996           | 3                           | 20                  | 14                        | 3,409                         | 2,471                     | 2            | 4                        | 22               | 16                     | 3,305                      | 2,487                  | 7        | 10                   | 26           | 21                 | 3,334                  | 2,480              |
| 100,000    | popularity | 9.954e+00 | cpu_seconds | 10              | 25                          | 199                 | 136                       | 34,089                        | 24,714                    | 20           | 38                       | 216              | 157                    | 33,052                     | 24,864                 | 17       | 43                   | 209          | 157                | 33,288                 | 24,741             |
| 1,000,000  | popularity | 9.954e+01 | cpu_seconds | 100             | 250                         | 1,986               | 1,359                     | 340,887                       | 247,137                   | 197          | 382                      | 2,157            | 1,566                  | 330,519                    | 248,636                | 119      | 378                  | 2,040        | 1,521              | 332,823                | 247,351            |

### retraining

| retrain_every | n_requests | cheapest   | training_events | cost.popularity | cost.popularity+greedy_topk | cost.popularity+mmr | cost.popularity+quota_mmr | cost.popularity+qubo_feasible | cost.popularity+qubo_tabu | cost.itemknn | cost.itemknn+greedy_topk | cost.itemknn+mmr | cost.itemknn+quota_mmr | cost.itemknn+qubo_feasible | cost.itemknn+qubo_tabu | cost.als | cost.als+greedy_topk | cost.als+mmr | cost.als+quota_mmr | cost.als+qubo_feasible | cost.als+qubo_tabu |
|---------------|------------|------------|-----------------|-----------------|-----------------------------|---------------------|---------------------------|-------------------------------|---------------------------|--------------|--------------------------|------------------|------------------------|----------------------------|------------------------|----------|----------------------|--------------|--------------------|------------------------|--------------------|
| never         | 100,000    | popularity | 1               | 10              | 25                          | 199                 | 136                       | 34,089                        | 24,714                    | 20           | 38                       | 216              | 157                    | 33,052                     | 24,864                 | 17       | 43                   | 209          | 157                | 33,288                 | 24,741             |
| 1,000,000     | 100,000    | popularity | 1               | 10              | 25                          | 199                 | 136                       | 34,089                        | 24,714                    | 20           | 38                       | 216              | 157                    | 33,052                     | 24,864                 | 17       | 43                   | 209          | 157                | 33,288                 | 24,741             |
| 100,000       | 100,000    | popularity | 2               | 10              | 25                          | 199                 | 136                       | 34,089                        | 24,714                    | 20           | 39                       | 216              | 157                    | 33,053                     | 24,864                 | 23       | 50                   | 215          | 163                | 33,293                 | 24,748             |
| 10,000        | 100,000    | popularity | 11              | 10              | 26                          | 200                 | 137                       | 34,090                        | 24,715                    | 22           | 42                       | 219              | 160                    | 33,055                     | 24,867                 | 76       | 106                  | 270          | 216                | 33,346                 | 24,810             |
| 1,000         | 100,000    | popularity | 101             | 10              | 34                          | 208                 | 145                       | 34,098                        | 24,723                    | 41           | 69                       | 246              | 188                    | 33,083                     | 24,893                 | 608      | 668                  | 811          | 745                | 33,867                 | 25,431             |
| 100           | 100,000    | popularity | 1,001           | 10              | 115                         | 289                 | 226                       | 34,183                        | 24,804                    | 231          | 347                      | 513              | 469                    | 33,357                     | 25,153                 | 5,923    | 6,288                | 6,221        | 6,028              | 39,084                 | 31,636             |
