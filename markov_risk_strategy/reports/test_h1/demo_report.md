# Credit Risk Report (1-year horizon)

**Total EAD**: 8,400,000  
**Expected Credit Loss (ECL)**: 98,100  
**Mean rating drift**: 0.20 buckets

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
| Northern Energy Holdings | 0.00% | 0.01% |
| Pinecrest Municipal Bonds | 0.00% | 0.05% |
| Atlas Industrial Group | 0.20% | 0.14% |
| Cedar Valley Logistics | 0.40% | 0.28% |
| Sunrise Retail Corp | 1.20% | 1.00% |
| Helios Energy Partners | 2.50% | 3.20% |
| Frontier Tech Ventures | 3.30% | 3.20% |
| Maritime Shipping Co | 24.00% | 23.15% |
| Beacon Hospitality | 23.20% | 23.15% |
| Sterling Real Estate Trust | 1.20% | 1.00% |

## Terminal rating distribution

| Rating | Probability |
|---|---:|
| AAA | 9.15% |
| AA | 10.01% |
| A | 10.69% |
| BBB | 10.97% |
| BB | 19.56% |
| B | 19.70% |
| CCC | 14.32% |
| D | 5.60% |

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
