---
type: reference
status: current
date: "2026-09-02"
title: "LLM Endpoint Service Level Objectives"
topics: [omnibase-infra, llm, endpoint, slo]
refs: []
---

<!-- Migrated from omnibase_infra:docs/performance/LLM_ENDPOINT_SLO.md on 2026-09-02. -->

# LLM Endpoint Service Level Objectives

This document defines Service Level Objectives (SLOs) for the distributed LLM endpoints
used by ONEX infrastructure. Endpoints can be hosted on separate machines and serve different
model tiers. Calibration methodology follows the same principles as the E2E registration
performance baselines (see ADR-004).

---

## Endpoint Inventory

An example topology. Each endpoint is configured through the environment variable shown; host and port are whatever a self-hoster binds.

| Environment Variable | Role | Example port | Model |
|---------------------|------|------|-------|
| `LLM_CODER_URL` | long-context coder | 8000 | Qwen3-Coder-30B-A3B-Instruct AWQ-4bit |
| `LLM_CODER_FAST_URL` | mid-tier routing and classification | 8001 | Qwen3-14B-AWQ |
| `LLM_EMBEDDING_URL` | embeddings | 8100 | Alibaba-NLP/gte-Qwen2-1.5B-instruct |
| `LLM_DEEPSEEK_R1_URL` | reasoning | 8101 | DeepSeek-R1-Distill-Qwen-32B-bf16 |

An optional small-model endpoint (`LLM_SMALL_URL`) can be added the same way; no SLO is set for it here.

---

## SLO Targets

### Time to First Token (TTFT)

TTFT measures latency from request submission to the first token appearing in the
response stream. Measured at P95 under single-request load from the development machine.

| Endpoint | Context Window | TTFT P95 | TTFT P99 | Notes |
|----------|---------------|----------|----------|-------|
| `LLM_CODER_URL` (port 8000) | 64K tokens | 2000ms | 4000ms | MoE architecture; 30B total / 3B active |
| `LLM_CODER_FAST_URL` (port 8001) | 40K tokens | 800ms | 1500ms | Mid-tier routing and classification |
| `LLM_EMBEDDING_URL` (port 8100) | N/A | 200ms | 400ms | Batch of 32 texts |
| `LLM_DEEPSEEK_R1_URL` (port 8101) | 32K tokens | 3000ms | 6000ms | Reasoning model; async-preferred |

### Throughput (tokens/second, generation phase)

| Endpoint | Sustained tok/s | Burst tok/s | Notes |
|----------|----------------|-------------|-------|
| `LLM_CODER_URL` | 80 | 150 | chunked prefill enabled |
| `LLM_CODER_FAST_URL` | 60 | 120 | |
| `LLM_EMBEDDING_URL` | 5000 embeddings/s | — | Measured at dim=4096 |
| `LLM_DEEPSEEK_R1_URL` | 40 | 80 | Metal acceleration |

### Availability

| Endpoint | Target availability | Recovery SLO |
|----------|--------------------|--------------|
| `LLM_CODER_URL` | 99% (business hours) | 5 minutes |
| `LLM_CODER_FAST_URL` | 99% (business hours) | 5 minutes |
| `LLM_EMBEDDING_URL` | 99.5% | 3 minutes |
| `LLM_DEEPSEEK_R1_URL` | 99% (best-effort async) | 10 minutes |
| `LLM_SMALL_URL` | best-effort | — |

---

## Request Routing Decision Matrix

Select the endpoint based on task type and token count:

| Task Type | Token Count | Recommended Endpoint | Rationale |
|-----------|-------------|---------------------|-----------|
| Code generation | > 40K context | `LLM_CODER_URL` | 64K window, large file context |
| Code generation | <= 40K context | `LLM_CODER_FAST_URL` | Faster, sufficient window |
| Routing / classification | Any | `LLM_CODER_FAST_URL` | Low latency, mid-tier |
| RAG embeddings | Any | `LLM_EMBEDDING_URL` | Purpose-built embeddings |
| Code review / reasoning | Any | `LLM_DEEPSEEK_R1_URL` | Deep analysis, async-preferred |
| Lightweight / portable | Any | `LLM_SMALL_URL` | Smallest tier, fastest path |

```python
import os

def select_llm_endpoint(task: str, token_count: int) -> str:
    """Select LLM endpoint based on task type and context size."""
    if task == "embedding":
        return os.environ["LLM_EMBEDDING_URL"]
    if task == "reasoning":
        return os.environ["LLM_DEEPSEEK_R1_URL"]
    if task == "code" and token_count > 40_000:
        return os.environ["LLM_CODER_URL"]
    return os.environ["LLM_CODER_FAST_URL"]
```

---

## Health Check Endpoints

```bash
# Check all endpoints
curl -s "${LLM_CODER_URL%/v1/*}/health"          # Coder (30B, 64K)
curl -s "${LLM_CODER_FAST_URL%/v1/*}/health"     # Coder Fast (14B, 40K)
curl -s "${LLM_EMBEDDING_URL%/v1/*}/health"      # Embeddings
curl -s "${LLM_DEEPSEEK_R1_URL%/v1/*}/health"   # DeepSeek-R1 reasoning

# Expected: HTTP 200 with {"status": "ok"} or similar
```

---

## Calibration Methodology

SLO values follow the same methodology as ADR-004:

```
threshold = (base_operation_time + network_overhead) * safety_margin
```

- `base_operation_time`: Measured P95 for the operation under single-request load
- `network_overhead`: RTT from development machine to host (10–25ms typical)
- `safety_margin`: 2x multiplier for GPU memory contention, thermal throttling,
  and concurrent request load

### Recalibration Triggers

Recalibrate SLOs when:
- Hardware changes (new GPU, different host, different model quantization)
- Model is updated or swapped for a different checkpoint
- Sustained threshold violations (>5% of requests exceeding P95 target)
- After optimization work (quantization, KV cache tuning, chunked prefill changes)

### Measurement Procedure

1. 50-iteration warmup (discard results)
2. 200 iterations of the target operation in isolation
3. Record P50, P95, P99 latencies
4. Apply 2x safety margin to P99
5. Round to nearest 100ms for TTFT, nearest 500 tokens/s for throughput
6. Document hardware state (GPU VRAM utilization, thermal state) at measurement time

---

## Environment Adjustment Guidelines

These SLOs are calibrated for the production-like development infrastructure.
Adjust for other environments:

| Environment | Adjustment |
|-------------|-----------|
| Local CPU-only inference | Not applicable — use remote endpoints |
| CI/CD pipeline (no GPU access) | Mock LLM endpoints; skip perf assertions |
| Production (dedicated infra) | Tighten by 30–50% after dedicated calibration |
| Degraded mode (one GPU down) | Expect 2–4x TTFT degradation on affected host |

---

## Deprecated Endpoints

The following endpoint is **no longer available**:

| Variable | Old value | Status |
|----------|-----------|--------|
| `OLLAMA_BASE_URL` | `http://<onex-host>:11434` | Decommissioned — do not use |

All code referencing `OLLAMA_BASE_URL` or port 11434 must be updated to use the
appropriate endpoint from the table above.

---

## Related Documentation

- ADR-004: Performance Baseline Thresholds - Calibration methodology for E2E registration tests
- `~/.claude/CLAUDE.md` — "LLM Inference" section (operator machine config, not tracked in this repo) - Authoritative endpoint list and selection guide
- docs/performance/README.md - Performance documentation index
