---
type: guide
status: current
date: "2026-11-24"
title: "Self-hosted quickstart: run OmniNode on one machine"
topics: [getting-started, self-hosting, quickstart, delegation, install, docker]
refs:
  - guides/onex-plugin-quickstart.md
  - guides/how-omninode-works.md
  - guides/supported-platforms.md
  - guides/getting-started-self-hosted.md
  - guides/getting-started-local.md
  - guides/connecting-to-the-cloud.md
  - reference/public-proof-index.md
summary: "The shortest real path to run OmniNode on one machine you control: a four-command install with no containers, then an optional container stack on the same machine. It lists what each path needs, what was run to check each command, and what is not supported or not built yet."
---

# Self-hosted quickstart: run OmniNode on one machine

This page is the short path. It gets OmniNode running on one machine you control, with no
OmniNode account and no hosted service, and it says for each step how it was checked. It does
not replace the longer guides, which it links where they hold the detail.

There are two paths on one machine. Start with the first.

| | Path 1: the tool | Path 2: the container stack |
|---|---|---|
| What you get | The `onex` command, delegation to a model you choose, a receipt for each run, spend metering, a local dashboard | The platform's own services in containers on the same machine: a Kafka-compatible broker, PostgreSQL, a cache, the runtime, and projections, with delegation running through the broker |
| Needs containers | No | Yes |
| Time | A few minutes plus the model setup | Several minutes for the first image build and boot |
| Use it to | Hand work to your own model and see what it cost | See the event flow and the projections described in [How OmniNode works](how-omninode-works.md) |

State of this page: path 1 was re-run on 2026-11-24 against `omnibase-core 0.47.78`,
`omnibase-infra 0.38.83` and `omnimarket 0.4.326`. Path 2 was last checked, from source only,
on 2026-11-06 against `omnibase-infra 0.38.76`. The section
[How this was checked](#how-this-was-checked) says which commands were run and which were only
read in source.

## The path at a glance

Two diagrams follow, one per path, from the first command to the first delegation. Green boxes
are commands that were run for this page on 2026-11-24. Dashed grey boxes were not run for this
page: they were read in the source or in the tool's help. The section
[How this was checked](#how-this-was-checked) gives the detail for each.

Path 1, the tool, with no containers:

```mermaid
flowchart LR
  i1["1 Install<br/>uv tool install<br/>onex --version"] --> i2["2 onex local init<br/>identity and runtime<br/>declaration"]
  i2 --> d{"3 Which<br/>model?"}
  d -->|"a server you run"| m1["bifrost_overrides.yaml<br/>with the complete<br/>endpoint_url"]
  d -->|"your provider key"| m2["onex secret set<br/>asks for the key,<br/>never prints it"]
  d -->|"neither"| refuse["onex delegate refuses<br/>before any model:<br/>nothing ran, nothing spent"]
  m1 --> dl["4 onex delegate<br/>'say hello in one word'"]
  m2 --> dl
  dl --> rec["Model, cost and run id (stderr),<br/>then the answer, then the<br/>artifacts line (stdout)<br/>run folder: result.txt,<br/>receipt.json, run.json,<br/>workflow_result.json"]
  dl --> veto["Reply without the ANSWER<br/>marker line: ends<br/>quality_veto, exit code 1"]
  rec --> met["5 onex metering<br/>onex dashboard"]
  rec --> plug["6 Optional: plugin install,<br/>then /onex:delegate<br/>in Claude Code"]
  classDef ran fill:#eef6ee,stroke:#4a7c4a;
  classDef read stroke-dasharray: 5 4,fill:#f6f6f6,color:#444;
  class i1,i2,m1,dl,rec,refuse,veto,met ran;
  class m2,plug read;
```

Path 2, the container stack on the same machine. It is optional and was not started for this
page, so every box is read from the source:

```mermaid
flowchart LR
  c1["git clone omnibase_infra<br/>at the checked tag<br/>uv sync"] --> c2["make local-env<br/>generated passwords<br/>and a model overlay"]
  c2 --> c3["Edit model_endpoint<br/>in the overlay to your<br/>model's complete URL"]
  c3 --> c4["make up-local<br/>builds the runtime image,<br/>boots broker, PostgreSQL,<br/>cache and runtime"]
  c4 --> c5["make status-local<br/>migration gate, health on<br/>ports 8085 and 8086,<br/>delegate consumer group"]
  c5 --> c6["make delegate-local<br/>delegation through the broker,<br/>projections fill"]
  c6 -.-> nb["Not a quickstart step,<br/>not built end to end:<br/>mirror to a second bus,<br/>hosted service"]
  classDef read stroke-dasharray: 5 4,fill:#f6f6f6,color:#444;
  classDef notbuilt stroke-dasharray: 2 3,fill:#fbf3e4,stroke:#b08a3a;
  class c1,c2,c3,c4,c5,c6 read;
  class nb notbuilt;
```

## What you need

| You need | Path | Detail |
|---|---|---|
| A supported computer | 1 and 2 | Apple Silicon Mac, or Linux on x86_64 or arm64, install from prebuilt wheels. Intel Mac builds from source. Windows is not tested. See [Supported platforms](supported-platforms.md). |
| `uv` | 1 and 2 | Installs the tool and fetches Python 3.12 for it. `curl -LsSf https://astral.sh/uv/install.sh \| sh`, then `uv tool update-shell` and a new terminal window if `uv` is not found. |
| A model to send work to | 1 and 2 | Either a server you run that speaks the OpenAI chat-completions API (llama.cpp, vLLM or similar), or your own key with a provider such as OpenRouter. OmniNode does not sell inference. |
| Docker with Compose v2, `make` and `openssl` | 2 only | The stack and its generated passwords. |
| Claude Code | optional | Only for the plugin at the end of path 1. |

## Path 1: install the tool and delegate

Each command below is the same as in the [Delegation quickstart](onex-plugin-quickstart.md),
which has the longer explanation and a troubleshooting table.

**1. Install.** One line installs the three packages that must share an environment.

```bash
uv tool install --python 3.12 --with 'omnibase-infra>=0.38.67' --with 'omnimarket>=0.4.205' 'omnibase-core>=0.46.8'
onex --version
```

The second command prints `onex version 0.47.78` or newer. On 2026-11-24 the install line above
resolved to `omnibase-core 0.47.78`, `omnibase-infra 0.38.83` and `omnimarket 0.4.326`. Keep `--python 3.12` as written. On an
Intel Mac follow the from-source steps in [Supported platforms](supported-platforms.md#intel-macos-build-from-source) first.

**2. Give the machine its identity, once.**

```bash
onex local init
```

It mints a tenant identity and writes a local runtime declaration under `~/.omninode/`. Running
it again is safe.

**3. Declare the model.** Choose one.

If you run a model server, create `~/.omninode/delegation/bifrost_overrides.yaml`. The address
must be the complete path, including `/v1/chat/completions`.

```yaml
backends:
  - backend_id: local-coder
    endpoint_url: "http://127.0.0.1:8000/v1/chat/completions"
    model_name: "<the model id your server reports at /v1/models>"
  - backend_id: local-heavy-reasoning
    endpoint_url: "http://127.0.0.1:8000/v1/chat/completions"
    model_name: "<the model id your server reports at /v1/models>"
```

If you use a provider key, register it once. The command asks for the key and then the model id,
and never prints the key. Setting `OPENROUTER_API_KEY` in the environment does not register a key.

```bash
onex secret set llm.openrouter.api_key
```

A GLM Coding Plan key is refused by design. The [Delegation quickstart](onex-plugin-quickstart.md#step-3--tell-onex-which-model-to-use) explains both options.

**4. Delegate.**

```bash
onex delegate "say hello in one word"
```

The output has three parts, and the order on a terminal is not answer-first:

1. Several diagnostic lines on stderr, ending with `onex delegate: model <id>, cost $<amount>,
   run <run id>, full receipt <path>`. This is the line that names the model, the cost and the
   run id.
2. The model's answer, on stdout.
3. A `delegate artifacts:` line on stdout, listing `result.txt`, `receipt.json` and `run.json`
   with their full paths and the `state_root` they sit under.

The run folder is `~/.onex_state/runs/<run id>/`. It holds four files, not the three the
artifacts line lists: `result.txt`, `receipt.json`, `run.json` and `workflow_result.json`.
`receipt.json` names the backend, the endpoint and the model that answered.
`workflow_result.json` is the terminal result of the run, with `result` and `exit_code` at its
top. If you skip step 3, the command refuses before it reaches any model, exits with code 1 and
tells you to declare one.

**The reply must carry a `### ANSWER` line.** For the default task class (`document`, which the
tool falls back to when nothing in the request matches another class) the tool takes as the answer
only the text after a line reading `### ANSWER`. A reply without that line ends the run as
`quality_veto`: the command exits with code 1, prints `returned_to_caller: quality_veto; no model
you chose finished the task; do the task in this session`, and prints no answer. The one unmarked
reply that is accepted is a single word on one line, when the request asked for one word, as in
the example above. When the marker is present the printed answer starts after it. A model that does
not write the marker is vetoed on every try, and the same rung is tried three times before the
run ends. To see which case you are in, open `receipt.json` in the
run folder: each entry under `attempts` carries `acceptance_decision`, `acceptance_reason`
(`deterministic_floor_failed`) and `error_message`, which reads `DELIVERABLE_EXTRACTION:
ambiguous_unmarked_deliverable` for a missing marker. `onex delegate --json` prints the same
receipt as one line, and `workflow_result.json` repeats the reason as `terminal_failure_reason` inside its
`terminal_payload`.

**5. See the spend and the runs.**

```bash
onex metering
onex dashboard
```

`onex metering` totals runs, tokens and spend against a baseline model. A run that recorded no
measured cost is counted as unknown, never as zero. After one delegation to a model server you run
yourself, the check printed `Runs 1`, the token totals, and then `Spent`, `Would have cost` and
`Saved` all as `unknown`, with `unknown (spend) 1` and `measured over 0 of 1 runs`. The baseline
line still prints: `claude-sonnet-5-5` at its per-1k-token prices. The summary line of
`onex delegate` printed `cost $0.0000` for the same run, so a zero there is not a measurement:
trust the metering page. `onex metering --json` prints the same figures as one JSON object. A run
on a provider key was not run for this page.

`onex dashboard` serves a local page on a loopback address only. It stays in the foreground and
prints one line, `onex dashboard: http://127.0.0.1:<port>/`, with the port chosen at each start.
**That printed address carries no token, and a request to it without the token is answered
`401` with `token_required`.** Get the working address from a second terminal with
`onex dashboard open`, which opens the page in your browser with this start's token in the
address; the token changes on each start. `onex dashboard start` starts the server in the
background and returns, printing `Dashboard: success` and no address, so `onex dashboard open` is
how you reach that one too. `onex dashboard stop` ends the background server. Its first run
downloads the dashboard pages into `~/.omninode/dashboard/bundles/`.

**6. Optional: use it from Claude Code.**

```bash
claude plugin marketplace add OmniNode-ai/omniclaude
claude plugin install onex@omninode-tools
```

Both commands succeeded on a clean machine: `claude plugin list` then showed `onex@omninode-tools`
at version 0.3.3, enabled, and the plugin directory holds a `delegate` skill. Restart Claude Code
and run `/onex:delegate <task>`; that last step needs a logged-in Claude Code and was not run for
this page. The plugin is one skill that runs `onex delegate`, so the `### ANSWER` rule in step 4
applies to it as well.

On this path the event bus is in memory, and a run's record is the run folder plus a local SQLite
table. Nothing is sent anywhere except your call to your own model or provider.

## Path 2: the container stack on the same machine

This path runs the platform's services in containers, so delegation goes through a real broker
and the projections fill. It is the **laptop profile** of `omnibase-infra`, a catalog bundle named
`local`. It binds its ports to the loopback address, uses its own Docker Compose project, and
turns every operator integration off. It needs the model setup from path 1 only in the form of a
model your containers can reach.

```bash
git clone --branch v0.38.76 --depth 1 https://github.com/OmniNode-ai/omnibase_infra.git
cd omnibase_infra
uv sync
make local-env
```

`make local-env` writes `~/.omnibase/local.env` with freshly generated passwords and copies a
model overlay template to `~/.omnibase/local.bifrost.yaml`. It never overwrites an existing file.
Edit the line marked `model_endpoint` in the overlay to your model's complete
chat-completions URL, and set each `served_model_id` to what your server reports. From inside a
container, a model served on your own machine is at `host.docker.internal`, not `localhost`.

```bash
make up-local
make status-local
```

`make up-local` builds the runtime image and boots the stack. A cold runtime takes several
minutes to report healthy. `make status-local` prints the migration gate, the two runtime health
bodies on ports 8085 and 8086, and the delegate consumer group. Read the health body and not
only the HTTP status. Then send one delegation through the stack:

```bash
make delegate-local PROMPT="Reply with exactly one word: hello"
```

Two more targets are worth knowing. `make check-sasl-local` proves the local broker refuses
anonymous clients. `make down-local` stops the stack and keeps its volumes, and
`make down-local-volumes` also deletes the local data.

To run delegations on your own provider key instead of the model overlay, `make tenant-local`
writes a tenant id, `make up-local` applies it, and `make secret-local PROVIDER=<name>` registers
the key from a hidden prompt. [Self-hosting the full stack](getting-started-self-hosted.md#a-separate-container-path-for-one-machine)
describes this profile next to the larger operator stack and its limits.

## What is not supported or not built yet

- **`onex setup` does not exist.** The first lines of `onex --help` say `Quickstart (new
  developer): onex setup`, and `onex dashboard status` says to run `onex setup --action repair
  --component dashboard` when no dashboard is running. `setup` is not in the command list
  that `onex --help` prints, and `onex setup` ends with `Error: No such command 'setup'` and exit
  code 2, both on 0.47.78. Use `onex local init` (step 2) for first-time setup and
  `onex dashboard start` (step 5) for the dashboard.
- **The hosted service is not open.** Accounts are granted from a waitlist and nothing above
  needs one. See [Connecting to the cloud](connecting-to-the-cloud.md).
- **Windows is not tested.** Intel Mac works only by building from source.
- **One machine only.** Both paths are single-machine. Running the broker and the runtime across
  several machines is the larger stack in [Self-hosting the full stack](getting-started-self-hosted.md),
  which needs credentials and model addresses that this page does not provision.
- **The mirror to a second bus is not a quickstart step.** `make up-local-mirror` forwards the
  delegation topics from the container stack to another bus. It needs a bus you operate, a tenant
  and a credential map, and no public end-to-end proof of the full local, server and hosted chain
  exists.
- **Learning from earlier runs is not part of either path.** The installed plugin does not feed
  earlier event chains into later tasks.
- **A receipt is not a proof of correctness.** It records the reported route and outcome.
  Review generated work and run your own tests.
- **Free provider models are rate limited** by the provider, and a limit shows up as an error
  naming a rate limit, not as a wrong answer.

## How this was checked

Path 1 was re-run on 2026-11-24 on a Linux machine, as a user with an empty home directory and no
`ONEX_*` variables set, from the install line in step 1.

| Step | How it was checked |
|---|---|
| Install, `onex --version`, `onex local init` | Run. The install resolved `omnibase-core 0.47.78`, `omnibase-infra 0.38.83` and `omnimarket 0.4.326`; `onex --version` printed `onex version 0.47.78`; `onex local init` minted the tenant identity and wrote the runtime declaration under `~/.omninode/`. |
| Delegation refusal without a model | Run. It refused before reaching any model, exit code 1, with the message that no local model is declared. |
| Declare a model, `onex delegate`, the run folder | Run against a minimal local server that implements the chat-completions route and answers a fixed sentence, so the path from command to receipt was exercised with no provider. The receipt named the declared endpoint and model. The output order and the four-file run folder in step 4 are from these runs. This does not exercise a real model or a provider key. |
| The `### ANSWER` rule | Run twice against that server with the request `say hello in one word`: a one-word reply with no marker was accepted; a multi-word reply with no marker ended `quality_veto` with exit code 1 after three tries; the same reply after a `### ANSWER` line was accepted and printed without the marker line. |
| `onex metering` | Run after one delegation to that server: spend, would-have-cost and saved all `unknown`. Not run against a provider key. |
| `onex dashboard` | Run. The printed address answered `401` without a token and `200` with the token that `onex dashboard open` supplies. `start`, `status`, `stop` and `open` were run. The first start fetched the dashboard pages into `~/.omninode/dashboard/bundles/`. |
| `onex setup` | Run: `No such command 'setup'`, exit code 2. |
| `onex secret set` | Run only without a value: it refused with `no value was supplied`, exit code 1, and said to pipe the value in or run it on a terminal. Registering a real key was not run. |
| Plugin install | Run: `claude plugin marketplace add` and `claude plugin install` succeeded on a clean home. `/onex:delegate` inside Claude Code was not run. |
| Path 2 commands | Not re-run on 2026-11-24: the check machine has no `make`. As checked on 2026-11-06: make targets, the `local` bundle, the env and overlay templates and the ports read from the `omnibase-infra 0.38.76` source. The stack was not started, so image build time, boot time and health are not measured. |

The [public proof index](../reference/public-proof-index.md) records what has been inspected and
what has not.

## Where to go next

| If you want to | Read |
|---|---|
| Understand what the pieces are | [How OmniNode works](how-omninode-works.md), then [What OmniNode is, and where it stands](what-is-omninode.md) |
| Go further with delegation | [Delegation quickstart](onex-plugin-quickstart.md) |
| Write your own nodes | [Building on the ONEX runtime](getting-started-local.md) |
| Run the larger operator stack | [Self-hosting the full stack](getting-started-self-hosted.md) |
