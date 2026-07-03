# Credit Risk Report (4-year horizon)

**Total EAD**: 8,400,000  
**Expected Credit Loss (ECL)**: 331,655  
**Mean rating drift**: 0.63 buckets

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
| Northern Energy Holdings | 0.00% | 0.10% |
| Pinecrest Municipal Bonds | 0.00% | 0.34% |
| Atlas Industrial Group | 1.20% | 0.82% |
| Cedar Valley Logistics | 2.80% | 1.65% |
| Sunrise Retail Corp | 7.80% | 5.50% |
| Helios Energy Partners | 15.80% | 16.16% |
| Frontier Tech Ventures | 15.60% | 16.16% |
| Maritime Shipping Co | 55.80% | 56.21% |
| Beacon Hospitality | 57.80% | 56.21% |
| Sterling Real Estate Trust | 6.20% | 5.50% |

## Terminal rating distribution

| Rating | Probability |
|---|---:|
| AAA | 7.32% |
| AA | 9.92% |
| A | 11.94% |
| BBB | 13.60% |
| BB | 17.52% |
| B | 16.56% |
| CCC | 6.84% |
| D | 16.30% |

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
