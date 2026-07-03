# Credit Risk Report (10-year horizon)

**Total EAD**: 8,400,000  
**Expected Credit Loss (ECL)**: 613,225  
**Mean rating drift**: 1.09 buckets

## Portfolio

| Name | Rating | EAD | LGD |
|---|---|---:|---:|
| Northern Energy Holdings | AAA | 2,000,000 | 0.45 |
| Pinecrest Municipal Bonds | AA | 1,500,000 | 0.40 |
| Atlas Industrial Group | A | 1,200,000 | 0.45 |
| Cedar Valley Logistics | BBB | 1,000,000 | 0.45 |
| Sunrise Retail Corp | BB | 800,000 | 0.55 |
| Helios Energy Partners | B | 600,000 | 0.60 |
| Frontier Tech Ventures | B | 400,000 | 0.65 |
| Maritime Shipping Co | CCC | 250,000 | 0.75 |
| Beacon Hospitality | CCC | 150,000 | 0.70 |
| Sterling Real Estate Trust | BB | 500,000 | 0.50 |
| **Total** |  | **8,400,000** |  |

## Cumulative PD

| Obligor | Simulated PD | Analytical PD |
|---|---:|---:|
| Northern Energy Holdings | 0.60% | 0.61% |
| Pinecrest Municipal Bonds | 1.20% | 1.57% |
| Atlas Industrial Group | 2.80% | 3.28% |
| Cedar Valley Logistics | 5.20% | 6.23% |
| Sunrise Retail Corp | 16.80% | 16.94% |
| Helios Energy Partners | 35.70% | 37.14% |
| Frontier Tech Ventures | 36.80% | 37.14% |
| Maritime Shipping Co | 73.00% | 73.79% |
| Beacon Hospitality | 73.20% | 73.79% |
| Sterling Real Estate Trust | 20.10% | 16.94% |

## Terminal rating distribution

| Rating | Probability |
|---|---:|
| AAA | 4.40% |
| AA | 9.73% |
| A | 15.13% |
| BBB | 14.81% |
| BB | 13.98% |
| B | 11.95% |
| CCC | 3.46% |
| D | 26.54% |

## Annual transition matrix

| from \\ to | AAA | AA | A | BBB | BB | B | CCC | D |
|---|---|---|---|---|---|---|---|---|
| **AAA** | 0.9080 | 0.0820 | 0.0080 | 0.0010 | 0.0005 | 0.0003 | 0.0001 | 0.0001 |
| **AA** | 0.0070 | 0.9050 | 0.0780 | 0.0070 | 0.0010 | 0.0010 | 0.0005 | 0.0005 |
| **A** | 0.0006 | 0.0230 | 0.9080 | 0.0550 | 0.0080 | 0.0030 | 0.0010 | 0.0014 |
| **BBB** | 0.0002 | 0.0030 | 0.0500 | 0.8950 | 0.0380 | 0.0090 | 0.0020 | 0.0028 |
| **BB** | 0.0001 | 0.0008 | 0.0055 | 0.0610 | 0.8520 | 0.0610 | 0.0096 | 0.0100 |
| **B** | 0.0001 | 0.0004 | 0.0015 | 0.0060 | 0.0700 | 0.8300 | 0.0600 | 0.0320 |
| **CCC** | 0.0000 | 0.0002 | 0.0008 | 0.0025 | 0.0150 | 0.1000 | 0.6500 | 0.2315 |
| **D** | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |

## Narrative

_LLM narration was disabled (use `--llm-provider anthropic` to enable)._
