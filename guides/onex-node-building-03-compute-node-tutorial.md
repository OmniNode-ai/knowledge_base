---
type: guide
status: current
date: "2026-11-24"
title: "COMPUTE Node Tutorial"
topics:
  - omnibase-core
  - node
  - building
  - compute
  - tutorial
refs:
  - guides/omnibase-core-first-node.md
  - guides/handler-authoring-guide.md
---

<!-- Migrated from omnibase_core:docs/guides/node-building/03_COMPUTE_NODE_TUTORIAL.md on 2026-09-02; rewritten 2026-11-24 for the definition-B handler shape -->

> **Note**: For authoritative coding standards, see CLAUDE.md.

# COMPUTE Node Tutorial

**Reading Time**: 30 minutes
**Prerequisites**: What is a Node?, Node Types, and the [first-node tutorial](omnibase-core-first-node.md) for the scaffold and the install
**What You'll Build**: A price calculation node with discounts, tax and validation

Every file, command and output in this tutorial was executed against `omnibase-core` 0.47.78 installed into a clean virtual environment on Linux. The code blocks are the files that ran.

## Execution Shape

> **Canonical Execution Shape**: COMPUTE nodes are **pure transformations** with no I/O.
> They receive data from EFFECT nodes and pass results to REDUCER or ORCHESTRATOR nodes.
> See Canonical Execution Shapes for the complete pattern.

**Key Constraint**: COMPUTE nodes must not perform any I/O operations (no network calls, no file writes, no database access). All I/O is handled by EFFECT nodes. The scaffolded compute contract states it as `descriptor.purity: pure`.

---

## Handler Architecture

> **Architectural Rule**: Nodes are thin coordination shells. Business logic belongs in **handlers**, not in the node class. The node's contract binds a handler, and the handler is a definition-B handler: `handle(self, request: ModelX) -> ModelY`.

A COMPUTE handler:

- takes **one typed request model** and returns **one typed response model**, both named by the contract;
- is **pure and stateless** -- no I/O, no clock, no instance state, so the same request always gives the same response;
- never imports, accepts or returns an event envelope. The runtime adapter owns the envelope and calls `handle()` with the request already built.

The node directory follows the layout used across the platform: `contract.yaml`, `handlers/`, `models/` under `src/<package>/nodes/<node>/`. The public [omnimarket node tree](https://github.com/OmniNode-ai/omnimarket/tree/v0.4.320/src/omnimarket/nodes) holds one such `node_<name>_<kind>/` directory per node and is the reference for the layout.

---

## Overview

In this tutorial you build a COMPUTE node that calculates prices with tax and discounts. You will:

- Scaffold a compute node and read the generated contract
- Define typed request and response models
- Write a definition-B handler with discount logic and structured errors
- Test the handler directly, without a runtime
- Validate the project and run the node through `RuntimeLocal`

## What We're Building

A cart goes in; a price breakdown comes out.

```json
{
  "items": [
    {"name": "Widget", "price": 10.00, "quantity": 2},
    {"name": "Gadget", "price": 25.00, "quantity": 1}
  ],
  "discount_code": "SAVE10",
  "tax_rate": 0.08
}
```

```json
{
  "subtotal": 45.0,
  "discount": 4.5,
  "tax": 3.24,
  "total": 43.74,
  "discount_code_applied": "SAVE10",
  "items_count": 2
}
```

Tax is charged on the discounted subtotal: 10% of 45.00 is 4.50, and 8% of 40.50 is 3.24.

## Project Setup

Install `omnibase-core` and scaffold the project as in the [first-node tutorial](omnibase-core-first-node.md):

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python "omnibase-core==0.47.78"
.venv/bin/onex init price-calculator
cd price-calculator
../.venv/bin/onex new node price-calculator --type compute
```

The scaffold produces the node package `src/price_calculator/nodes/price_calculator/` with a `contract.yaml`, a `handlers/handler_price_calculator.py` and two model files. The contract binds `HandlerPriceCalculator` and the two models by dotted path; you do not edit it for this tutorial.

---

## Define the Request Model

A cart line is its own model, and `onex validate` allows **one model class per file**, so the line item gets a file of its own.

**File**: `src/price_calculator/nodes/price_calculator/models/model_cart_item.py`

```python
"""One cart line for price-calculator."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["ModelCartItem"]


class ModelCartItem(BaseModel):
    """One line in the cart."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1, description="Product name")
    price: float = Field(gt=0, description="Unit price, must be positive")
    quantity: int = Field(gt=0, description="Quantity, must be positive")
```

**File**: `src/price_calculator/nodes/price_calculator/models/model_price_calculator_input.py`

```python
"""Input model for price-calculator."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from price_calculator.nodes.price_calculator.models.model_cart_item import (
    ModelCartItem,
)

__all__ = ["ModelPriceCalculatorInput"]


class ModelPriceCalculatorInput(BaseModel):
    """The typed request the handler receives."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    items: list[ModelCartItem] = Field(min_length=1, description="Cart lines")
    discount_code: str | None = Field(default=None, description="Optional code")
    tax_rate: float = Field(default=0.08, ge=0.0, le=1.0, description="0.0 to 1.0")
```

**Key points**:

- Pydantic validates every field before the handler runs: a cart must have at least one line (`min_length=1`), prices and quantities must be positive, `tax_rate` must be between 0 and 1.
- `frozen=True` and `extra="forbid"` make the request an immutable value that rejects unknown fields.
- The handler therefore never re-checks what the model already guarantees.

## Define the Response Model

**File**: `src/price_calculator/nodes/price_calculator/models/model_price_calculator_output.py`

```python
"""Output model for price-calculator."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["ModelPriceCalculatorOutput"]


class ModelPriceCalculatorOutput(BaseModel):
    """The typed response the handler returns."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subtotal: float = Field(description="Sum of all lines before discount")
    discount: float = Field(description="Discount amount")
    tax: float = Field(description="Tax on the discounted subtotal")
    total: float = Field(description="Final price")
    discount_code_applied: str | None = Field(
        default=None, description="The code that was applied, if any"
    )
    items_count: int = Field(description="Number of cart lines")
```

**Key points**:

- Every figure of the calculation is a field of the response.
- The response carries no timing or cache flags: a pure handler returns only what the request determines.

---

## Implement the Handler

**File**: `src/price_calculator/nodes/price_calculator/handlers/handler_price_calculator.py`

```python
"""Handler for price-calculator: subtotal, discount, tax and total."""

from __future__ import annotations

from omnibase_core.enums.enum_core_error_code import EnumCoreErrorCode
from omnibase_core.errors.model_onex_error import ModelOnexError

from price_calculator.nodes.price_calculator.models.model_price_calculator_input import (
    ModelPriceCalculatorInput,
)
from price_calculator.nodes.price_calculator.models.model_price_calculator_output import (
    ModelPriceCalculatorOutput,
)

__all__ = ["HandlerPriceCalculator"]

# Rates are fractions of the subtotal; amounts are flat currency units.
_PERCENT_CODES: dict[str, float] = {"SAVE10": 0.10, "SAVE20": 0.20, "SAVE30": 0.30}
_FLAT_CODES: dict[str, float] = {"FLAT5": 5.00}


class HandlerPriceCalculator:
    """Canonical definition-B handler: typed request in, typed response out.

    Pure and stateless: the same cart always prices the same, with no I/O and
    no cache held on the instance.
    """

    def handle(self, request: ModelPriceCalculatorInput) -> ModelPriceCalculatorOutput:
        subtotal = sum(item.price * item.quantity for item in request.items)
        discount = self._discount_for(request.discount_code, subtotal)
        tax = (subtotal - discount) * request.tax_rate
        return ModelPriceCalculatorOutput(
            subtotal=round(subtotal, 2),
            discount=round(discount, 2),
            tax=round(tax, 2),
            total=round(subtotal - discount + tax, 2),
            discount_code_applied=request.discount_code,
            items_count=len(request.items),
        )

    @staticmethod
    def _discount_for(code: str | None, subtotal: float) -> float:
        if code is None:
            return 0.0
        if code in _PERCENT_CODES:
            return subtotal * _PERCENT_CODES[code]
        if code in _FLAT_CODES:
            return min(_FLAT_CODES[code], subtotal)
        raise ModelOnexError(
            error_code=EnumCoreErrorCode.VALIDATION_ERROR,
            message=f"unknown discount code: {code}",
            context={"discount_code": code},
        )
```

**Key points**:

- **`handle(self, request) -> response`** is the whole public surface. There is no envelope, no correlation identifier and no wrapper around the response.
- **Pure.** The discount tables are module constants, the instance holds nothing, and calling `handle()` twice with one cart returns equal responses.
- **Structured errors.** An unknown discount code raises `ModelOnexError` with `EnumCoreErrorCode.VALIDATION_ERROR` and a `context` dict. Shape problems never reach this point because the request model rejects them first.
- **No cache in the handler.** A cache is state, and a compute handler is stateless. If repeated calculations are costly, cache at the caller or in an EFFECT node.

### The Node Class

`onex new node` also writes `node_price_calculator_compute.py`, a stub whose `compute()` method raises `NotImplementedError`. Leave it as it is. The runtime resolves the handler from the contract and calls `handle()`; the node class holds no logic.

---

## Write Tests

A definition-B handler is an ordinary class, so the tests build a request model and call `handle()`. No container, runtime or event loop is needed, and the tests are plain synchronous functions.

**File**: `tests/test_price_calculator_handler.py`

```python
"""Tests for the price-calculator handler."""

from __future__ import annotations

import pytest
from omnibase_core.enums.enum_core_error_code import EnumCoreErrorCode
from omnibase_core.errors.model_onex_error import ModelOnexError
from pydantic import ValidationError

from price_calculator.nodes.price_calculator.handlers.handler_price_calculator import (
    HandlerPriceCalculator,
)
from price_calculator.nodes.price_calculator.models.model_cart_item import (
    ModelCartItem,
)
from price_calculator.nodes.price_calculator.models.model_price_calculator_input import (
    ModelPriceCalculatorInput,
)

CART = [
    ModelCartItem(name="Widget", price=10.00, quantity=2),
    ModelCartItem(name="Gadget", price=25.00, quantity=1),
]


def _price(**fields):
    return HandlerPriceCalculator().handle(
        ModelPriceCalculatorInput(items=CART, **fields)
    )


def test_basic_calculation() -> None:
    response = _price()
    assert (response.subtotal, response.discount) == (45.00, 0.0)
    assert (response.tax, response.total) == (3.60, 48.60)
    assert response.items_count == 2


def test_percentage_discount() -> None:
    response = _price(discount_code="SAVE10")
    assert (response.discount, response.tax, response.total) == (4.50, 3.24, 43.74)
    assert response.discount_code_applied == "SAVE10"


def test_flat_discount() -> None:
    assert _price(discount_code="FLAT5").discount == 5.00


def test_unknown_code_raises_structured_error() -> None:
    with pytest.raises(ModelOnexError) as raised:
        _price(discount_code="NOPE")
    assert raised.value.error_code == EnumCoreErrorCode.VALIDATION_ERROR


def test_empty_cart_is_rejected_at_the_model() -> None:
    with pytest.raises(ValidationError):
        ModelPriceCalculatorInput(items=[])


def test_non_positive_price_is_rejected_at_the_model() -> None:
    with pytest.raises(ValidationError):
        ModelCartItem(name="Widget", price=-1, quantity=1)


def test_same_cart_prices_the_same_twice() -> None:
    assert _price(discount_code="SAVE20") == _price(discount_code="SAVE20")
```

## Run Tests

`onex init` wrote `pythonpath = ["src"]` into `pyproject.toml`, so the tests import the package from the source tree.

```bash
uv pip install --python ../.venv/bin/python pytest
../.venv/bin/python -m pytest tests -q
```

```text
.......                                                                  [100%]
7 passed
```

---

## Validate and Run the Node

```bash
../.venv/bin/onex --verbose validate .
```

```text
Validating ....
  [PASS] architecture
       Files processed: 7
  [PASS] union-usage
       Files processed: 13
  [PASS] contracts
       Files processed: 1
  [PASS] patterns
       Files processed: 13
All validations passed!
```

If you put `ModelCartItem` and `ModelPriceCalculatorInput` in one file, validation fails on the architecture check:

```text
  [FAIL] architecture
       Files processed: 6
       Issues: 1
         - src/price_calculator/nodes/price_calculator/models/model_price_calculator_input.py: 2 models in one file: ModelCartItem, ModelPriceCalculatorInput
```

To run the node, install the project so its package is importable, then hand its contract and a JSON request to `RuntimeLocal`. The helper below is the one from the [first-node tutorial](omnibase-core-first-node.md#step-8-validate-and-run-the-node).

**File**: `run_local.py` (project root; not part of the package)

```python
"""Run a project node's contract through RuntimeLocal."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from omnibase_core.runtime.runtime_local import RuntimeLocal

contract, input_json = Path(sys.argv[1]), Path(sys.argv[2])
runtime = RuntimeLocal(
    contract,
    state_root=Path(".onex_state"),
    input_path=input_json,
    timeout=30,
)
result = asyncio.run(runtime.run_async())
print(f"result: {result.value}")
```

Save the cart above as `input.json`, then:

```bash
uv pip install --python ../.venv/bin/python -e .
../.venv/bin/python run_local.py src/price_calculator/nodes/price_calculator/contract.yaml input.json
```

```text
RuntimeLocal DEGRADED BUS: kind=unknown reason=no bus binding was declared for this runtime; it uses the in-memory bus and its events go nowhere recorded=1 not_delivered=1
RuntimeLocal DEGRADED BUS (unknown): no bus binding was declared for this runtime; it uses the in-memory bus and its events go nowhere; 1 event(s) recorded, 1 not delivered
result: completed
```

The runtime wrote the handler's response to `.onex_state/workflow_result.json`:

```text
{
  "result": "completed",
  "exit_code": 0,
  "handler_result": {
    "subtotal": 45.0,
    "discount": 4.5,
    "tax": 3.24,
    "total": 43.74,
    "discount_code_applied": "SAVE10",
    "items_count": 2
  }
}
```

Change `"SAVE10"` to `"NOPE"` and run again: the handler raises `ModelOnexError`, the run prints `result: failed`, and `workflow_result.json` records `"result": "failed"` with exit code 1. The local runner does not print the error message, so assert on the error in a unit test, as `test_unknown_code_raises_structured_error` does.

---

## What You've Built

- **Typed request and response models** -- validated by Pydantic, one model per file.
- **A definition-B handler** -- `handle(request) -> response`, pure, with structured errors.
- **Direct tests** -- seven tests, no runtime in the loop.
- **A running node** -- the contract executed through `RuntimeLocal`.

## Next Steps

1. **Build more complex nodes**: try an EFFECT, REDUCER or ORCHESTRATOR node.
2. **Integrate with real systems**: connect to databases and APIs from an EFFECT handler -- see the [Handler Authoring Guide](handler-authoring-guide.md).
3. **Read real nodes**: browse the [omnimarket node tree](https://github.com/OmniNode-ai/omnimarket/tree/v0.4.320/src/omnimarket/nodes) for the same layout at scale.

## Related Tutorials

- EFFECT Node Tutorial - Build a database interaction node
- REDUCER Node Tutorial - Build a data aggregation node
- ORCHESTRATOR Node Tutorial - Coordinate workflows
- Patterns Catalog - Reusable patterns

## Troubleshooting

### `ModuleNotFoundError` when running the node

`RuntimeLocal` imports the handler by the dotted path in the contract. Run `uv pip install --python ../.venv/bin/python -e .` from the project root so the package is importable; a bare script run does not put `src/` on the import path.

### Architecture check fails with "2 models in one file"

Split each model class into its own `model_*.py` file, as above.

### Tests cannot import the package

Run pytest from the project root so `pythonpath = ["src"]` from `pyproject.toml` applies.

## Summary

You've learned:

- The COMPUTE handler shape: `handle(self, request: ModelX) -> ModelY`, pure and stateless
- Typed request and response models with Pydantic v2
- Structured errors with `ModelOnexError`
- Testing a handler directly
- Validating a project with `onex validate` and running it with `RuntimeLocal`

**Key Takeaway**: a COMPUTE node is a contract, two models and a pure `handle()` method. Everything the runtime needs comes from the contract, and nothing envelope-shaped appears in the handler.

**Next**: EFFECT Node Tutorial →
