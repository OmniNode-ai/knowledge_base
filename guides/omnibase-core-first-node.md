---
type: guide
status: current
date: "2026-11-24"
title: "Build Your First Node"
topics:
  - omnibase-core
  - first
  - node
refs:
  - guides/handler-authoring-guide.md
  - guides/getting-started-local.md
---

<!-- Migrated from omnibase_core:docs/getting-started/FIRST_NODE.md on 2026-09-02; rewritten 2026-11-24 for the definition-B handler shape -->

> **Note**: For authoritative coding standards, see CLAUDE.md.

# Build Your First Node

**Estimated Time**: 20 minutes

## Overview

This tutorial builds a complete ONEX COMPUTE node. You scaffold a project, define the typed request and response models, write a handler with `handle(request) -> response`, run the node through the local runtime, and test it.

Every file, command and output below was executed against `omnibase-core` 0.47.78 installed into a clean virtual environment on Linux. The code blocks are the files that ran, not a paraphrase of them.

## What You Will Build

A temperature converter COMPUTE node that:

- Converts between Celsius, Fahrenheit, and Kelvin
- Uses a YAML contract as the source of truth for the node
- Keeps business logic in a handler, not in the node
- Takes a typed request model and returns a typed response model, with no envelope in sight

## Prerequisites

- Python 3.12+ and `uv`
- Familiarity with Pydantic models

## Key Architecture Rules

1. **Handlers own all business logic.** Conversion formulas, validation and error handling live in the handler.
2. **A handler is definition-B:** one method, `handle(self, request: ModelX) -> ModelY`. A typed request goes in; a typed response comes out.
3. **A handler never touches the event envelope.** The envelope is the runtime adapter's concern. A handler imports no envelope type, accepts no envelope, and returns no envelope or output wrapper.
4. **The YAML contract defines the node.** It declares the archetype, the request and response models, the handler binding and the topics.
5. **Handlers are stateless.** A compute handler is pure: the same request produces the same response, with no I/O.

---

## Step 1: Install and Scaffold

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python "omnibase-core==0.47.78"
.venv/bin/onex init temperature-converter
cd temperature-converter
../.venv/bin/onex new node temperature-converter --type compute
```

Output of the last two commands:

```text
Created ONEX project 'temperature-converter' at temperature-converter
  Package name: temperature_converter

Next steps:
  cd temperature-converter
  onex new node my-first-node --type compute
Created compute node 'temperature-converter' at ./temperature-converter/src/temperature_converter/nodes/temperature_converter
  contract.yaml
  node_temperature_converter_compute.py
  handlers/handler_temperature_converter.py
  models/model_temperature_converter_input.py
  models/model_temperature_converter_output.py
```

The scaffold writes this tree (`pyproject.toml` and `tests/` come from `onex init`, the node package from `onex new node`):

```text
contracts/.gitkeep
pyproject.toml
src/temperature_converter/__init__.py
src/temperature_converter/nodes/__init__.py
src/temperature_converter/nodes/temperature_converter/contract.yaml
src/temperature_converter/nodes/temperature_converter/handlers/handler_temperature_converter.py
src/temperature_converter/nodes/temperature_converter/handlers/__init__.py
src/temperature_converter/nodes/temperature_converter/__init__.py
src/temperature_converter/nodes/temperature_converter/models/__init__.py
src/temperature_converter/nodes/temperature_converter/models/model_temperature_converter_input.py
src/temperature_converter/nodes/temperature_converter/models/model_temperature_converter_output.py
src/temperature_converter/nodes/temperature_converter/node_temperature_converter_compute.py
tests/__init__.py
```

The node directory is the unit of layout: `contract.yaml`, a `handlers/` package, a `models/` package. Larger repositories use the same layout with one directory per node under `src/<package>/nodes/`; the public [omnimarket node tree](https://github.com/OmniNode-ai/omnimarket/tree/v0.4.320/src/omnimarket/nodes) is the reference for it, with one `node_<name>_<kind>/` directory per node holding its `contract.yaml` and `handlers/` package.

File naming is enforced: `model_*.py`, `handler_*.py`, `enum_*.py`, and **one model class per file**. `onex validate` reports a second model in the same file as an architecture failure.

---

## Step 2: Read the Contract

The scaffold writes the contract for you. It is unedited here: the scaffold already points at the handler and the two models.

```yaml
name: temperature_converter

# Archetype as EnumNodeType names it. The friendly name is descriptor.node_archetype.
node_type: COMPUTE_GENERIC

# Versions are structured semver, not strings.
contract_version: {major: 1, minor: 0, patch: 0}
node_version: {major: 0, minor: 1, patch: 0}

input_model: temperature_converter.nodes.temperature_converter.models.model_temperature_converter_input.ModelTemperatureConverterInput
output_model: temperature_converter.nodes.temperature_converter.models.model_temperature_converter_output.ModelTemperatureConverterOutput

# Handler binding. RuntimeLocal reads BOTH of these:
#   - handler.module / handler.class / handler.input_model build the initial
#     typed payload and resolve the handler on the single-handler path;
#   - handler_routing.default_handler ("module_ref:ClassName") is the canonical
#     binding the compute path and the canon-shape ratchet resolve.
handler:
  module: temperature_converter.nodes.temperature_converter.handlers.handler_temperature_converter
  class: HandlerTemperatureConverter
  input_model: temperature_converter.nodes.temperature_converter.models.model_temperature_converter_input.ModelTemperatureConverterInput

handler_routing:
  default_handler: temperature_converter.nodes.temperature_converter.handlers.handler_temperature_converter:HandlerTemperatureConverter

# Topic the runtime treats as the completion signal. A contract without it is
# only executable on the handler-resolved compute path.
terminal_event: onex.evt.temperature_converter.temperature_converter-completed.v1

descriptor:
  node_archetype: compute
  purity: pure
  runtime_profiles:
    - compute
  idempotent: true
  timeout_ms: 30000

event_bus:
  subscribe_topics:
    - onex.cmd.temperature_converter.temperature_converter-requested.v1
  publish_topics:
    - onex.evt.temperature_converter.temperature_converter-completed.v1

golden_path: []
dod_evidence: []
```

Key points:

- `node_type: COMPUTE_GENERIC` and `descriptor.purity: pure` -- a compute node does no I/O.
- `input_model` and `output_model` are dotted paths to the request and response models.
- `handler_routing.default_handler` is `module:ClassName`, and `handler` repeats the binding as `module`, `class` and `input_model`. The local runtime reads both.
- `terminal_event` and `event_bus` name the topics the node uses when it runs on a bus.

---

## Step 3: Define the Enum

**File**: `src/temperature_converter/enums/enum_temperature_unit.py` (create the `enums/` directory and an empty `__init__.py` beside it)

```python
"""Temperature unit enumeration."""

from __future__ import annotations

from enum import Enum

__all__ = ["EnumTemperatureUnit"]


class EnumTemperatureUnit(str, Enum):
    """Supported temperature units."""

    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"
    KELVIN = "kelvin"
```

---

## Step 4: Define the Request and Response Models

The scaffold generates two empty models with `extra="forbid"`. Add your fields.

**File**: `src/temperature_converter/nodes/temperature_converter/models/model_temperature_converter_input.py`

```python
"""Input model for temperature conversion."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from temperature_converter.enums.enum_temperature_unit import EnumTemperatureUnit

__all__ = ["ModelTemperatureConverterInput"]


class ModelTemperatureConverterInput(BaseModel):
    """The typed request the handler receives."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: float = Field(description="Temperature value to convert")
    from_unit: EnumTemperatureUnit = Field(description="Source temperature unit")
    to_unit: EnumTemperatureUnit = Field(description="Target temperature unit")
    precision: int = Field(
        default=2, ge=0, le=10, description="Decimal places in the result"
    )
```

**File**: `src/temperature_converter/nodes/temperature_converter/models/model_temperature_converter_output.py`

```python
"""Output model for temperature conversion."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from temperature_converter.enums.enum_temperature_unit import EnumTemperatureUnit

__all__ = ["ModelTemperatureConverterOutput"]


class ModelTemperatureConverterOutput(BaseModel):
    """The typed response the handler returns."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    original_value: float = Field(description="Original input value")
    converted_value: float = Field(description="Converted temperature value")
    from_unit: EnumTemperatureUnit = Field(description="Source temperature unit")
    to_unit: EnumTemperatureUnit = Field(description="Target temperature unit")
    precision: int = Field(description="Decimal places used")
```

Note the use of:

- `ConfigDict(frozen=True, extra="forbid")` -- immutable value objects that reject unknown fields instead of dropping them silently
- `X | None` instead of `Optional[X]`, and lowercase generics (`list[str]`)

---

## Step 5: Write the Handler (Business Logic)

The scaffold generates a handler that returns an empty response. Replace its body with the real logic.

**File**: `src/temperature_converter/nodes/temperature_converter/handlers/handler_temperature_converter.py`

```python
"""Handler for temperature conversion."""

from __future__ import annotations

from temperature_converter.enums.enum_temperature_unit import EnumTemperatureUnit
from temperature_converter.nodes.temperature_converter.models.model_temperature_converter_input import (
    ModelTemperatureConverterInput,
)
from temperature_converter.nodes.temperature_converter.models.model_temperature_converter_output import (
    ModelTemperatureConverterOutput,
)

__all__ = ["HandlerTemperatureConverter"]


def _to_celsius(value: float, unit: EnumTemperatureUnit) -> float:
    if unit == EnumTemperatureUnit.FAHRENHEIT:
        return (value - 32) * 5 / 9
    if unit == EnumTemperatureUnit.KELVIN:
        return value - 273.15
    return value


def _from_celsius(celsius: float, unit: EnumTemperatureUnit) -> float:
    if unit == EnumTemperatureUnit.FAHRENHEIT:
        return celsius * 9 / 5 + 32
    if unit == EnumTemperatureUnit.KELVIN:
        return celsius + 273.15
    return celsius


class HandlerTemperatureConverter:
    """Canonical definition-B handler: typed request in, typed response out.

    Pure and stateless: same request, same response, no I/O. No envelope type
    is imported or returned; the runtime adapter owns that boundary.
    """

    def handle(
        self, request: ModelTemperatureConverterInput
    ) -> ModelTemperatureConverterOutput:
        celsius = _to_celsius(request.value, request.from_unit)
        converted = round(_from_celsius(celsius, request.to_unit), request.precision)
        return ModelTemperatureConverterOutput(
            original_value=request.value,
            converted_value=converted,
            from_unit=request.from_unit,
            to_unit=request.to_unit,
            precision=request.precision,
        )
```

Key points about this handler:

1. **All logic lives here** -- conversion formulas, rounding, response construction.
2. **The signature is `handle(self, request: ModelX) -> ModelY`.** The request model is the one named by the contract's `handler.input_model`; the response is the contract's `output_model`.
3. **Pure and stateless** -- no state on the instance, no I/O. The same request always produces the same response.
4. **No envelope** -- no correlation or envelope identifiers are passed in or built here. The runtime adapter that calls the handler owns them.

---

## Step 6: The Node Class Stays a Stub

`onex new node` also writes `node_temperature_converter_compute.py`, a class with a `compute()` method that raises `NotImplementedError`. You do not fill it in: the runtime resolves the handler from the contract and calls `handle()`, and the node class is never called on this path. Business logic never goes in the node class.

---

## Step 7: Write Tests

A definition-B handler is an ordinary class with an ordinary method, so a test builds a request, calls `handle()`, and reads the response. No envelope, container or runtime is needed.

**File**: `tests/test_temperature_converter_handler.py`

```python
"""Tests for the temperature converter handler."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from temperature_converter.enums.enum_temperature_unit import EnumTemperatureUnit
from temperature_converter.nodes.temperature_converter.handlers.handler_temperature_converter import (
    HandlerTemperatureConverter,
)
from temperature_converter.nodes.temperature_converter.models.model_temperature_converter_input import (
    ModelTemperatureConverterInput,
)

C = EnumTemperatureUnit.CELSIUS
F = EnumTemperatureUnit.FAHRENHEIT
K = EnumTemperatureUnit.KELVIN


def _convert(value: float, from_unit, to_unit, precision: int = 2):
    request = ModelTemperatureConverterInput(
        value=value, from_unit=from_unit, to_unit=to_unit, precision=precision
    )
    return HandlerTemperatureConverter().handle(request)


@pytest.mark.parametrize(
    ("value", "from_unit", "to_unit", "expected"),
    [
        (100.0, C, F, 212.0),
        (32.0, F, C, 0.0),
        (0.0, C, K, 273.15),
        (42.0, C, C, 42.0),
        (-40.0, C, F, -40.0),
    ],
)
def test_conversions(value, from_unit, to_unit, expected) -> None:
    assert _convert(value, from_unit, to_unit).converted_value == expected


def test_precision_controls_rounding() -> None:
    response = _convert(100.0, F, C, precision=4)
    assert response.converted_value == 37.7778
    assert response.precision == 4


def test_response_echoes_request() -> None:
    response = _convert(100.0, C, F)
    assert (response.original_value, response.from_unit, response.to_unit) == (
        100.0,
        C,
        F,
    )


def test_unknown_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ModelTemperatureConverterInput(
            value=1.0, from_unit=C, to_unit=F, unexpected="x"
        )
```

Run the tests (`onex init` wrote `pythonpath = ["src"]` into `pyproject.toml`, so the package imports from the source tree):

```bash
uv pip install --python ../.venv/bin/python pytest
../.venv/bin/python -m pytest tests -q
```

```text
........                                                                 [100%]
8 passed
```

---

## Step 8: Validate and Run the Node

Validate the project:

```bash
../.venv/bin/onex --verbose validate .
```

```text
Validating ....
  [PASS] architecture
       Files processed: 7
  [PASS] union-usage
       Files processed: 14
  [PASS] contracts
       Files processed: 1
  [PASS] patterns
       Files processed: 14
All validations passed!
```

`onex validate` passes on the project as scaffolded and again after the handler is filled in. `--verbose` is a flag of the `onex` group, so it goes before `validate`.

Run the node through `RuntimeLocal`, the in-process runtime in `omnibase_core.runtime.runtime_local`. It loads the contract, builds the typed request from a JSON file, resolves the handler from the contract, calls `handle()`, and writes the outcome to `<state_root>/workflow_result.json`. The package must be importable, so install the project into the environment first.

**File**: `run_local.py` (project root; a helper, not part of the package)

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

`input.json` is the request, validated against `ModelTemperatureConverterInput`:

```json
{"value": 100, "from_unit": "celsius", "to_unit": "fahrenheit"}
```

```bash
uv pip install --python ../.venv/bin/python -e .
../.venv/bin/python run_local.py src/temperature_converter/nodes/temperature_converter/contract.yaml input.json
```

```text
RuntimeLocal DEGRADED BUS: kind=unknown reason=no bus binding was declared for this runtime; it uses the in-memory bus and its events go nowhere recorded=1 not_delivered=1
RuntimeLocal DEGRADED BUS (unknown): no bus binding was declared for this runtime; it uses the in-memory bus and its events go nowhere; 1 event(s) recorded, 1 not delivered
result: completed
```

The two `RuntimeLocal DEGRADED BUS` lines are expected on a local run: no bus binding was declared, so the runtime uses the in-memory bus and says so. The handler's response is in `.onex_state/workflow_result.json`:

```text
{
  "result": "completed",
  "exit_code": 0,
  "handler_result": {
    "original_value": 100.0,
    "converted_value": 212.0,
    "from_unit": "celsius",
    "to_unit": "fahrenheit",
    "precision": 2
  }
}
```

A request the request model rejects fails the run. With `"to_unit": "rankine"` in `input.json`, the run prints `result: failed`, `workflow_result.json` records `"result": "failed"` with exit code 1, and the traceback names `ModelTemperatureConverterInput.to_unit`.

---

## What You Learned

- **Contract-first development** -- the YAML contract declares the node, its models and its handler binding.
- **Definition-B handlers** -- `handle(request: ModelX) -> ModelY`, typed in and typed out, no envelope.
- **Thin node pattern** -- the node class is a stub; the handler owns the logic.
- **Pydantic model standards** -- frozen, `extra="forbid"`, one model per file.
- **Testing a handler directly** -- build a request, call `handle()`, assert on the response.
- **Running a project node** -- `RuntimeLocal` runs a project's contract in process.

## Common Mistakes to Avoid

| Mistake | Correct pattern |
|---|---|
| Writing `execute(self, envelope)` on a new handler | Write `handle(self, request: ModelX) -> ModelY` |
| Importing or returning an envelope or an output wrapper from a handler | Return your own typed response model |
| Business logic in the node class | Put it in `handlers/handler_*.py` |
| A handler taking a `dict` | Use a typed Pydantic request model |
| Two models in one file | One model class per `model_*.py` file |
| `Optional[str]`, `Dict[str, Any]` | `str \| None`, `dict[str, ...]` |
| Running a project node with `python -m omnibase_core.runtime.harness.harness_cli` | The harness runs the platform's own workflows; use `RuntimeLocal` for a project contract |

## Next Steps

- [Handler Authoring Guide](handler-authoring-guide.md) -- an effect handler, errors, contract registration and tests
- [Building on the ONEX runtime](getting-started-local.md) -- the local runtime in full
- [COMPUTE Node Tutorial](onex-node-building-03-compute-node-tutorial.md) -- a second compute node with validation and error handling
- [Node Building Guide](onex-node-building-overview.md) -- in-depth guide for each node type
