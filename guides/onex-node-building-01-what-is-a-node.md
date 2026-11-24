---
type: guide
status: current
date: "2026-11-24"
title: "What is a Node?"
topics:
  - omnibase-core
  - node
  - building
  - what
  - is
refs:
  - guides/omnibase-core-first-node.md
  - guides/handler-authoring-guide.md
---

<!-- Migrated from omnibase_core:docs/guides/node-building/01_WHAT_IS_A_NODE.md on 2026-09-02; rewritten 2026-11-24 for the definition-B handler shape -->

> **Note**: For authoritative coding standards, see CLAUDE.md.

# What is a Node?

**Reading Time**: 5 minutes
**Prerequisites**: None
**Next**: Node Types

The code in this guide was executed against `omnibase-core` 0.47.78 installed into a clean virtual environment.

## Definition

A **node** in the ONEX framework is a **self-contained, reusable component** that performs one specific kind of operation. A node is declared by a **YAML contract**, and its work is done by a **handler**.

> **Key Concept: Nodes and Handlers**
> Nodes are **thin coordination shells**. They do not contain business logic. The logic lives in a **handler**, a plain class the node's contract binds by dotted path. A handler has one entry point, `handle(self, request: ModelX) -> ModelY`: a typed request goes in and a typed response comes out. This is the **definition-B** handler shape.
> - **Node**: the contract plus a thin class. It declares the archetype, the models, the handler and the topics.
> - **Handler**: contains the actual business logic. Selected by the node's YAML contract.
> - **YAML Contract**: the source of truth for the node -- archetype, request and response models, handler binding, topics.

### Simple Analogy

Imagine a restaurant kitchen:

- **EFFECT Node** = The server (interfaces with external world - customers, suppliers)
- **COMPUTE Node** = The chef (transforms ingredients into dishes)
- **REDUCER Node** = The prep cook with a recipe card (FSM-driven state aggregation using intents)
- **ORCHESTRATOR Node** = The kitchen manager with a workflow chart (coordinates multi-step activities with leases)

Each has a specific role. Together, they create a complete system.

## Core Concept

```
┌──────────────────────────────────────────────────────────────┐
│                     ONEX Node (thin shell)                    │
│                                                               │
│  ┌─────────┐    ┌─────────────────┐    ┌──────────┐          │
│  │ Request │ ──▶│ Handler         │──▶ │ Response │          │
│  │ (typed) │    │ handle(request) │    │ (typed)  │          │
│  └─────────┘    └─────────────────┘    └──────────┘          │
│                        ^                                      │
│                        |                                      │
│                ┌───────────────┐                              │
│                │ YAML Contract │                              │
│                │ (declares     │                              │
│                │  behavior)    │                              │
│                └───────────────┘                              │
│                                                               │
│  • Strongly typed request and response                       │
│  • Node delegates to handler (no logic in node)              │
│  • The runtime adapter owns the event envelope               │
│  • Structured errors                                         │
└──────────────────────────────────────────────────────────────┘
```

The envelope that carries a message on the bus is **not** part of the handler's signature. The runtime adapter unwraps it, builds the typed request, calls `handle()`, and wraps the response again. A handler imports no envelope type and returns none.

## Key Characteristics

### 1. Single Responsibility

Each node does **one thing well**. This validator handler does one job:

```python
"""One handler, one job: validate an order. Definition-B: request in, response out."""

from __future__ import annotations

from omnibase_core.enums.enum_core_error_code import EnumCoreErrorCode
from omnibase_core.errors.model_onex_error import ModelOnexError
from pydantic import BaseModel, ConfigDict


class ModelOrderRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    order_id: str
    quantity: int


class ModelOrderVerdict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    order_id: str
    accepted: bool


class HandlerOrderValidator:
    """Typed request in, typed response out. No envelope, no I/O."""

    def handle(self, request: ModelOrderRequest) -> ModelOrderVerdict:
        if request.quantity > 1000:
            raise ModelOnexError(
                error_code=EnumCoreErrorCode.VALIDATION_ERROR,
                message="quantity above the order limit",
                context={"order_id": request.order_id, "quantity": request.quantity},
            )
        return ModelOrderVerdict(order_id=request.order_id, accepted=True)
```

A handler that validated an order **and** saved it to a database would mix a COMPUTE job with an EFFECT job. Split it: a COMPUTE node validates, an EFFECT node writes.

### 2. Strongly Typed

The request and the response are explicit Pydantic models. The request model rejects bad input before `handle()` runs, so the handler holds no hand-written type checks. Calling the handler directly needs no runtime:

```python
from handler_order_validator import HandlerOrderValidator, ModelOrderRequest
from omnibase_core.errors.model_onex_error import ModelOnexError

handler = HandlerOrderValidator()
print(handler.handle(ModelOrderRequest(order_id="o-1", quantity=3)))
try:
    handler.handle(ModelOrderRequest(order_id="o-2", quantity=5000))
except ModelOnexError as exc:
    print(exc)
    print(exc.error_code.name)
```

```text
order_id='o-1' accepted=True
[ONEX_CORE_006_VALIDATION_ERROR] quantity above the order limit
VALIDATION_ERROR
```

### 3. Constructor Injection

A handler that needs a collaborator receives it through its constructor, so a test substitutes its own. The local runtime injects a `state_root` argument when the constructor declares one; the [Handler Authoring Guide](handler-authoring-guide.md) runs an effect handler that uses it.

### 4. Error Handling

Structured errors are built in. A handler raises `ModelOnexError` with an `EnumCoreErrorCode`; the output above shows the message form, `[ONEX_CORE_006_VALIDATION_ERROR] quantity above the order limit`, and the code on `exc.error_code`:

```python
from omnibase_core.enums.enum_core_error_code import EnumCoreErrorCode
from omnibase_core.errors.model_onex_error import ModelOnexError
```

## Why Nodes?

### Problem: Monolithic Systems

One service function that fetches data, transforms it, saves the result and notifies other services mixes every responsibility in one place. None of the steps can be tested or replaced alone.

### Solution: Node-Based Architecture

Each responsibility becomes its own node with its own contract and handler:

| Step | Node kind | Handler job |
|---|---|---|
| Fetch the record | EFFECT | read from the database |
| Transform it | COMPUTE | pure `handle(request) -> response` |
| Save the result | EFFECT | write to the database |
| Run fetch, transform, save in order | ORCHESTRATOR | declare the workflow |

**Benefits**:

- Each component is testable in isolation
- Easy to swap implementations
- Clear separation of concerns
- Each node can scale independently

## Nodes in the ONEX Ecosystem

### The Four Node Types

```
External World          │      ONEX System        │   Data Flow
                       │                          │
┌─────────────────┐    │                          │
│ APIs, Databases │────┼───▶ EFFECT Node ────────┼───▶ Raw data
│ File Systems    │    │     (Fetch/Save)         │
└─────────────────┘    │                          │
                       │         │                │
                       │         ▼                │
                       │    COMPUTE Node ─────────┼───▶ Transformed data
                       │    (Transform)           │
                       │         │                │
                       │         ▼                │
                       │    REDUCER Node ─────────┼───▶ Aggregated data
                       │    (FSM + Intents)       │
                       │         │                │
                       │         ▼                │
                       │  ORCHESTRATOR Node ──────┼───▶ Coordinated result
                       │  (Workflows + Leases)    │
```

### Data Flow Example

**Scenario**: process a user signup. Each step is a node, and the typed models passed between them are the contract:

1. **EFFECT**: validate the email through an external API -- request: the email; response: its validity.
2. **COMPUTE**: calculate the user tier -- request: the signup data and the email status; response: the tier.
3. **REDUCER**: aggregate the user profile -- request: the signup data, the email status and the tier; response: the profile.
4. **EFFECT**: save the profile to the database.
5. **ORCHESTRATOR**: declares the workflow that runs steps 1 to 4 in order and decides what happens when one fails.

## Real-World Example

`onex new node` scaffolds a node whose handler is already definition-B. The scaffold for a compute node named `my-first-node` writes this tree:

```text
src/my_project/nodes/my_first_node/contract.yaml
src/my_project/nodes/my_first_node/node_my_first_node_compute.py
src/my_project/nodes/my_first_node/handlers/handler_my_first_node.py
src/my_project/nodes/my_first_node/models/model_my_first_node_input.py
src/my_project/nodes/my_first_node/models/model_my_first_node_output.py
```

and the handler it generates has this shape (docstrings omitted):

```python
class HandlerMyFirstNode:
    def handle(self, request: ModelMyFirstNodeInput) -> ModelMyFirstNodeOutput:
        return ModelMyFirstNodeOutput()
```

The scaffold returns an empty response so a new node runs end to end with no edits; you replace the body with real logic. The matching contract binds the handler and the two models:

```yaml
input_model: my_project.nodes.my_first_node.models.model_my_first_node_input.ModelMyFirstNodeInput
output_model: my_project.nodes.my_first_node.models.model_my_first_node_output.ModelMyFirstNodeOutput

handler:
  module: my_project.nodes.my_first_node.handlers.handler_my_first_node
  class: HandlerMyFirstNode
  input_model: my_project.nodes.my_first_node.models.model_my_first_node_input.ModelMyFirstNodeInput

handler_routing:
  default_handler: my_project.nodes.my_first_node.handlers.handler_my_first_node:HandlerMyFirstNode
```

**Notice**:

- The node directory holds the contract, the handler and the models. The public [omnimarket node tree](https://github.com/OmniNode-ai/omnimarket/tree/v0.4.320/src/omnimarket/nodes) uses the same layout for every node, one `node_<name>_<kind>/` directory each.
- The node class `node_my_first_node_compute.py` is a stub; the runtime resolves the handler from the contract.
- Typed request and response models, no envelope.

Build one from the scaffold in the [first-node tutorial](omnibase-core-first-node.md).

## When to Create a Node

Create a new node when you have:

✅ **A distinct operation** that fits one of the four types
✅ **Reusable logic** that might be used in multiple places
✅ **Testable unit** with clear input/output
✅ **Scalability needs** (the node can scale independently)

Don't create a node when:

❌ **Simple utility function** would suffice
❌ **One-time script** with no reuse potential
❌ **Tightly coupled** to a specific implementation
❌ **No clear input/output** contract

## Summary

**A node is**:

- A thin shell declared by a YAML contract, with its business logic in a handler
- Strongly typed: a request model in, a response model out
- Bound to its handler, `handle(self, request: ModelX) -> ModelY`, by the contract
- Never carrying business logic in the node class

**Four node types**:

1. **EFFECT**: External interactions (APIs, databases, files)
2. **COMPUTE**: Data transformation and computation
3. **REDUCER**: FSM-driven state aggregation using ModelIntent
4. **ORCHESTRATOR**: Workflow coordination with ModelAction and leases

**Key benefits**: testability, reusability, scalability, maintainability.

## What's Next?

Now that you understand what nodes are, learn about the **four node types** and when to use each:

→ Next: Node Types

## Quick Reference

```bash
# in an activated virtual environment
uv pip install "omnibase-core==0.47.78"
onex init my-project
cd my-project
onex new node my-first-node --type compute   # contract, handler, two models
onex validate .                              # passes on the fresh scaffold
```

**Essential imports** for a handler:

- `from omnibase_core.errors.model_onex_error import ModelOnexError` - structured errors
- `from omnibase_core.enums.enum_core_error_code import EnumCoreErrorCode` - error codes
- your own request and response models (Pydantic `BaseModel`, `extra="forbid"`)

**Next step**: Learn about the four node types -->
