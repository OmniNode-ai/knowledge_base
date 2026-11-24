---
type: guide
status: current
date: "2026-11-24"
title: "Handler Authoring Guide"
topics: [omnibase-core, handler, authoring]
refs:
  - guides/omnibase-core-first-node.md
  - guides/onex-node-building-03-compute-node-tutorial.md
---

# Handler Authoring Guide

This guide walks through writing a handler for an ONEX node: choosing its shape, writing `handle(request) -> response`, raising structured errors, binding it in the contract, and testing it. The running example is an EFFECT handler that appends audit records to a file. A COMPUTE handler is built in the [first-node tutorial](omnibase-core-first-node.md) and the [COMPUTE node tutorial](onex-node-building-03-compute-node-tutorial.md).

Every file, command and output below was executed against `omnibase-core` 0.47.78 installed into a clean virtual environment on Linux. The code blocks are the files that ran.

---

## Table of Contents

1. When to Create a Handler
2. The Handler Shape
3. Handler Classification
4. Step 1 — Scaffold the Node and the Handler File
5. Step 2 — Define the Request and Response Models
6. Step 3 — Implement handle
7. Step 4 — Handle Errors Correctly
8. Step 5 — Bind the Handler in contract.yaml
9. Step 6 — Write Tests
10. Step 7 — Validate and Run
11. Common Mistakes

---

## When to Create a Handler

Handlers are where business logic lives. A node's class is a thin stub; everything the node does at runtime passes through the handler its `contract.yaml` binds.

Create a new handler when:

- An existing node needs a new operation (for example, a new query against a table)
- A node must integrate with a transport it does not yet use
- A projection or read model needs its own dedicated update path

Do **not** create a handler when:

- The logic could belong in a COMPUTE node (pure transformation with no I/O)
- The behavior is only needed in tests (use fixtures instead)
- You are tempted to add the logic to the node class (that is always wrong)

---

## The Handler Shape

The canonical handler shape is **definition-B**:

```python
class HandlerSomething:
    def handle(self, request: ModelSomethingInput) -> ModelSomethingOutput:
        ...
```

- **One entry point**, named `handle`. It takes one typed request model and returns one typed response model, both named in the contract.
- **No envelope.** The handler does not take an event envelope as an argument, does not read fields out of one, and does not return an envelope or an output wrapper. The runtime adapter owns the envelope: it unwraps the message, builds the request model, calls `handle()`, and wraps the response.
- **Dependencies through the constructor.** Anything the handler needs from outside -- a location, a client, a store -- is a constructor argument, so a test passes its own.
- **`async def handle`** is allowed when the handler awaits I/O; the local runtime awaits it.

A handler that names its entry point `execute` and takes an `envelope` is the older shape. It does not match the canonical shape, and `onex validate` flags the name (see [Common Mistakes](#common-mistakes)).

The node directory holds the contract, the handlers and the models, one directory per node. The public [omnimarket node tree](https://github.com/OmniNode-ai/omnimarket/tree/v0.4.320/src/omnimarket/nodes) is the reference for that layout at scale: a `node_<name>_<kind>/` directory with `contract.yaml` and a `handlers/` package for each node.

---

## Handler Classification

The contract, not the handler class, classifies a handler. The archetype is declared once, in the node's contract, and the scaffold fills in the matching purity:

| Archetype | `node_type` in the scaffold | `descriptor.purity` | Use it for |
|-----------|-----------------------------|---------------------|------------|
| `compute` | `COMPUTE_GENERIC` | `pure` | Deterministic transformation in memory -- safe to replay |
| `effect` | `EFFECT_GENERIC` | `impure` | Side-effecting I/O -- files, databases, HTTP calls, external API writes |

(`onex new node` also accepts `reducer` and `orchestrator`.)

When in doubt between `effect` and `compute`: if the handler reads from or writes to anything external (database, API, file), it is an effect. If it only transforms data in memory, it is a compute.

---

## Step 1 — Scaffold the Node and the Handler File

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python "omnibase-core==0.47.78"
.venv/bin/onex init audit-log
cd audit-log
../.venv/bin/onex new node audit-writer --type effect
```

The scaffold writes the node package `src/audit_log/nodes/audit_writer/`:

```text
contract.yaml
node_audit_writer_effect.py
handlers/handler_audit_writer.py
models/model_audit_writer_input.py
models/model_audit_writer_output.py
```

File naming convention: `handler_<operation_name>.py`; class naming convention: `Handler<OperationName>`. To add a handler to an existing node, put the new `handler_*.py` file in that node's `handlers/` directory and its models in `models/`.

---

## Step 2 — Define the Request and Response Models

**File**: `src/audit_log/nodes/audit_writer/models/model_audit_writer_input.py`

```python
"""Input model for audit-writer."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["ModelAuditWriterInput"]


class ModelAuditWriterInput(BaseModel):
    """The typed request the handler receives."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subject: str = Field(min_length=1, description="What the audit record is about")
    event_type: str = Field(min_length=1, description="What happened, e.g. 'created'")
```

**File**: `src/audit_log/nodes/audit_writer/models/model_audit_writer_output.py`

```python
"""Output model for audit-writer."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["ModelAuditWriterOutput"]


class ModelAuditWriterOutput(BaseModel):
    """The typed response the handler returns."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str = Field(description="File the record was appended to")
    record_count: int = Field(description="Records in the file after this write")
```

Both models are frozen and `extra="forbid"`, so an unknown field is an error and not silent data loss. `min_length=1` means the handler never receives an empty `subject` or `event_type`. One model class per file.

---

## Step 3 — Implement handle

**File**: `src/audit_log/nodes/audit_writer/handlers/handler_audit_writer.py`

```python
"""Handler for audit-writer: appends one audit record to a JSON Lines file."""

from __future__ import annotations

import json
from pathlib import Path

from omnibase_core.enums.enum_core_error_code import EnumCoreErrorCode
from omnibase_core.errors.model_onex_error import ModelOnexError

from audit_log.nodes.audit_writer.models.model_audit_writer_input import (
    ModelAuditWriterInput,
)
from audit_log.nodes.audit_writer.models.model_audit_writer_output import (
    ModelAuditWriterOutput,
)

__all__ = ["HandlerAuditWriter"]


class HandlerAuditWriter:
    """Canonical definition-B handler: typed request in, typed response out.

    The file location arrives through the constructor, so a test points it at a
    temporary directory and the runtime points it at its own state root. The
    class holds no bus, no publisher and no envelope.
    """

    def __init__(self, state_root: Path = Path(".onex_state")) -> None:
        self._audit_file = state_root / "audit.jsonl"

    def handle(self, request: ModelAuditWriterInput) -> ModelAuditWriterOutput:
        record = json.dumps(
            {"subject": request.subject, "event_type": request.event_type}
        )
        try:
            self._audit_file.parent.mkdir(parents=True, exist_ok=True)
            with self._audit_file.open("a", encoding="utf-8") as sink:
                sink.write(record + "\n")
            record_count = len(self._audit_file.read_text(encoding="utf-8").splitlines())
        except OSError as exc:
            raise ModelOnexError(
                error_code=EnumCoreErrorCode.FILE_WRITE_ERROR,
                message="could not append the audit record",
                context={"path": str(self._audit_file)},
            ) from exc
        return ModelAuditWriterOutput(
            path=str(self._audit_file), record_count=record_count
        )
```

Points to note:

- **The signature is `handle(self, request: ModelAuditWriterInput) -> ModelAuditWriterOutput`.** There is no envelope in the argument list, in the body or in the return value.
- **The location comes in through the constructor.** `state_root` defaults to `.onex_state`; the local runtime passes its own state root when the constructor declares a parameter of that name, and a test passes a temporary directory.
- **The handler does its own I/O and nothing else.** It holds no bus, no publisher and no cache.
- **The side effect lives only in an effect handler.** A COMPUTE handler does no file or network access.

---

## Step 4 — Handle Errors Correctly

Raise `ModelOnexError` with an `EnumCoreErrorCode`, put the structured detail in `context`, and chain the original exception with `from`:

```python
from omnibase_core.enums.enum_core_error_code import EnumCoreErrorCode
from omnibase_core.errors.model_onex_error import ModelOnexError

raise ModelOnexError(
    error_code=EnumCoreErrorCode.FILE_WRITE_ERROR,
    message="could not append the audit record",
    context={"path": str(self._audit_file)},
) from exc
```

The handler above does exactly this around its file write. The message of such an error reads `[ONEX_CORE_023_FILE_WRITE_ERROR] could not append the audit record`, the code is on `exc.error_code`, and the chained original is on `__cause__`.

### Error code selection

| Scenario | Code |
|----------|------|
| The request is well-formed but not acceptable | `VALIDATION_ERROR` |
| A file could not be written | `FILE_WRITE_ERROR` |
| A file could not be read | `FILE_READ_ERROR` |
| A database operation failed | `DATABASE_OPERATION_ERROR` |
| The handler is configured wrongly | `CONFIGURATION_ERROR` |
| Everything else the handler cannot complete | `OPERATION_FAILED` |

### What is safe to include in error messages

Safe: operation names, identifiers, file names, table names.

Never include: passwords, API keys, connection strings, secret values, raw user input.

---

## Step 5 — Bind the Handler in contract.yaml

The scaffold has already written the binding. The part that matters for a handler is these four entries; the two models are named once at the top level and again as the handler's `input_model`:

```yaml
input_model: audit_log.nodes.audit_writer.models.model_audit_writer_input.ModelAuditWriterInput
output_model: audit_log.nodes.audit_writer.models.model_audit_writer_output.ModelAuditWriterOutput

handler:
  module: audit_log.nodes.audit_writer.handlers.handler_audit_writer
  class: HandlerAuditWriter
  input_model: audit_log.nodes.audit_writer.models.model_audit_writer_input.ModelAuditWriterInput

handler_routing:
  default_handler: audit_log.nodes.audit_writer.handlers.handler_audit_writer:HandlerAuditWriter
```

`handler.module`, `handler.class` and `handler.input_model` resolve the handler and build its typed request on the single-handler path; `handler_routing.default_handler` (`module:ClassName`) is the canonical binding. Keep both pointing at the same class. The scaffolded effect contract also declares `descriptor.node_archetype: effect`, `purity: impure`, and the `terminal_event` and `event_bus` topics.

A node with several operations lists them under `handler_routing.handlers` with `routing_strategy: operation_match`; published contracts in the omnimarket node tree show that form. The examples in this guide use the single-handler binding.

---

## Step 6 — Write Tests

A definition-B handler is an ordinary class: build the request model, call `handle()`, assert on the response. No envelope, container or runtime is involved, and the constructor argument points the handler at `tmp_path`.

**File**: `tests/test_audit_writer_handler.py`

```python
"""Tests for the audit-writer handler."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from omnibase_core.enums.enum_core_error_code import EnumCoreErrorCode
from omnibase_core.errors.model_onex_error import ModelOnexError

from audit_log.nodes.audit_writer.handlers.handler_audit_writer import (
    HandlerAuditWriter,
)
from audit_log.nodes.audit_writer.models.model_audit_writer_input import (
    ModelAuditWriterInput,
)


def test_appends_one_record_per_call(tmp_path: Path) -> None:
    handler = HandlerAuditWriter(state_root=tmp_path)
    request = ModelAuditWriterInput(subject="order-1", event_type="created")

    first = handler.handle(request)
    second = handler.handle(request)

    assert (first.record_count, second.record_count) == (1, 2)
    lines = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(line) for line in lines] == [
        {"subject": "order-1", "event_type": "created"}
    ] * 2


def test_unwritable_location_raises_structured_error(tmp_path: Path) -> None:
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("x", encoding="utf-8")
    handler = HandlerAuditWriter(state_root=blocker)

    with pytest.raises(ModelOnexError) as raised:
        handler.handle(ModelAuditWriterInput(subject="order-1", event_type="created"))

    assert raised.value.error_code == EnumCoreErrorCode.FILE_WRITE_ERROR


def test_empty_event_type_is_rejected_at_the_model() -> None:
    with pytest.raises(ValueError):
        ModelAuditWriterInput(subject="order-1", event_type="")
```

```bash
uv pip install --python ../.venv/bin/python pytest
../.venv/bin/python -m pytest tests -q
```

```text
...                                                                      [100%]
3 passed
```

---

## Step 7 — Validate and Run

```bash
../.venv/bin/onex --verbose validate .
```

```text
Validating ....
  [PASS] architecture
       Files processed: 6
  [PASS] union-usage
       Files processed: 12
  [PASS] contracts
       Files processed: 1
  [PASS] patterns
       Files processed: 12
All validations passed!
```

Run the node's contract through `RuntimeLocal` with the helper from the [first-node tutorial](omnibase-core-first-node.md#step-8-validate-and-run-the-node):

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

`input.json` is the request:

```json
{"subject": "order-1", "event_type": "created"}
```

Run it twice. The package must be importable, so install the project first:

```bash
uv pip install --python ../.venv/bin/python -e .
../.venv/bin/python run_local.py src/audit_log/nodes/audit_writer/contract.yaml input.json
../.venv/bin/python run_local.py src/audit_log/nodes/audit_writer/contract.yaml input.json
```

```text
RuntimeLocal DEGRADED BUS: kind=unknown reason=no bus binding was declared for this runtime; it uses the in-memory bus and its events go nowhere recorded=1 not_delivered=1
RuntimeLocal DEGRADED BUS (unknown): no bus binding was declared for this runtime; it uses the in-memory bus and its events go nowhere; 1 event(s) recorded, 1 not delivered
result: completed
```

`RuntimeLocal` constructed the handler with its own state root, so the records are in `.onex_state/audit.jsonl`:

```text
{"subject": "order-1", "event_type": "created"}
{"subject": "order-1", "event_type": "created"}
```

and `workflow_result.json` holds the handler's response from the second run:

```text
{
  "result": "completed",
  "exit_code": 0,
  "handler_result": {
    "path": ".onex_state/audit.jsonl",
    "record_count": 2
  }
}
```

The two `RuntimeLocal DEGRADED BUS` lines are expected on a local run: no bus binding was declared, so the runtime uses the in-memory bus and says so.

---

## Common Mistakes

### 1. Adding logic to the node class

```python
# WRONG -- the node class is a stub; the handler owns the logic
class NodeAuditWriter:
    def apply_effect(self, input_data: object) -> object:
        ...  # business logic here is always wrong
```

All logic belongs in the handler. Leave the scaffolded node class as it is.

### 2. Writing the older envelope shape

```python
# WRONG -- takes an envelope
class HandlerAuditWriter:
    def execute(self, envelope: dict) -> ModelAuditWriterOutput: ...

# CORRECT -- definition-B
class HandlerAuditWriter:
    def handle(self, request: ModelAuditWriterInput) -> ModelAuditWriterOutput: ...
```

Changing that one method on the audit writer makes `onex validate` print an advisory under its patterns check, and still end with `All validations passed!`:

```text
  [PASS] patterns
       Files processed: 12
       Issues: 1
         - src/audit_log/nodes/audit_writer/handlers/handler_audit_writer.py: Line 32: Function name 'execute' is too generic - use specific domain terminology
All validations passed!
```

The fix is not to rename the method; it is to take the typed request model and to return the typed response model, so the handler does not depend on the envelope at all.

### 3. Taking a `dict` instead of a request model

A `dict` argument pushes validation into the handler body. Declare a Pydantic request model with `extra="forbid"` and let it reject bad input before `handle()` runs.

### 4. Hiding state in a compute handler

A module-level cache or an attribute mutated on the instance makes a compute handler impure: the same request stops giving the same response. Keep compute handlers stateless; put anything stateful behind an effect handler.

### 5. Raising bare exceptions without structured context

```python
# WRONG -- no code, no context, no chain
raise RuntimeError("Query failed")

# CORRECT -- structured error with the original exception chained
raise ModelOnexError(
    error_code=EnumCoreErrorCode.OPERATION_FAILED,
    message="query failed",
    context={"operation": "audit.query"},
) from original_exc
```

### 6. Two models in one file

`onex validate` fails its architecture check when a `model_*.py` file holds two model classes. Give each model its own file.

---

## See Also

- [Build Your First Node](omnibase-core-first-node.md) -- the scaffold, a COMPUTE handler, `RuntimeLocal`
- [COMPUTE Node Tutorial](onex-node-building-03-compute-node-tutorial.md) -- validation and errors in a pure handler
- [Building on the ONEX runtime](getting-started-local.md) -- the local runtime in full
- The public [omnimarket node tree](https://github.com/OmniNode-ai/omnimarket/tree/v0.4.320/src/omnimarket/nodes) -- node directories at scale
