---
type: reference
status: current
date: '2026-10-18'
title: LLM Endpoint Service Level Objectives
topics: [runtime]
refs: []
---

# LLM Endpoint Service Level Objectives

This is a calibration method for a self-hosted model endpoint, not an inventory or availability report for OmniNode's infrastructure. Set objectives from measurements of your own endpoint, model and workload.

## Example endpoint configuration

| Environment variable | Role | Illustrative local endpoint |
|---|---|---|
| `LLM_CODER_URL` | Main coding model | `http://localhost:8000/v1/chat/completions` |
| `LLM_CODER_FAST_URL` | Smaller coding or classification model | `http://localhost:8001/v1/chat/completions` |
| `LLM_EMBEDDING_URL` | Embedding model | `http://localhost:8100/v1/embeddings` |
| `LLM_DEEPSEEK_R1_URL` | Reasoning model | `http://localhost:8101/v1/chat/completions` |

These ports are examples, not discovery defaults. Supply the complete endpoint URL your model server exposes. For delegation backends, use [the routing contract](../architecture/delegation-routing-contract.md) and the customer's local overlay. The customer owns the model or pays the provider on their own key; OmniNode does not sell inference.

## Set objectives

Record the model revision, quantization, context limit, concurrency and input/output token distribution before measuring. Separate time to first token from generation throughput and total request latency. For embeddings, report documents per second, batch size and vector dimensions instead of generation tokens per second.

1. Warm the endpoint with 50 representative requests and exclude those from the sample.
2. Run at least 200 measured requests at the intended concurrency.
3. Record success rate, P50/P95/P99 latency, token usage and throughput.
4. Choose a timeout and error budget that your measured tail and expected recovery behavior can satisfy.
5. Repeat under expected concurrent load and record the tested revision beside the results.

No numerical performance result is claimed on this page. A chosen objective becomes a measured result only when its run evidence is published in the owning repository.

## Diagnose and recalibrate

Check the server's documented health endpoint, then submit a small representative request to the configured API URL. A health response alone does not prove inference works. On a model, workload or concurrency change, repeat calibration; after an outage, verify a terminal response and its receipt before treating recovery as complete.

See [LLM infrastructure](../architecture/llm-infrastructure.md) for transport, retries and endpoint security.
