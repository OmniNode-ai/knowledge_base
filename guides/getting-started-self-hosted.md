---
type: guide
status: current
date: "2026-08-26"
title: "Getting Started: Self-Hosting the Full Stack"
topics:
  - getting-started
  - self-hosting
  - docker
  - kafka
  - postgres
  - valkey
  - runtime
refs:
  - runbooks/cold-lane-full-bringup.md
  - runbooks/apply-migrations.md
  - runbooks/kafka-reconnect-and-broker-recovery.md
  - runbooks/volume-config-drift-and-reseed.md
---

# Getting Started: Self-Hosting the Full Stack

This is the **scale-up chapter**. It brings the whole ONEX platform up on your own
infrastructure: a Kafka-compatible broker, PostgreSQL, a Valkey cache, an OIDC
provider, a secrets-manager container, and the runtime services that sit on top of
them.

Source audit: 2026-10-20 against `omnibase-infra v0.38.75`. The public catalog and
CLI source support the requirements below; this update did not deploy the stack.
For containers on one development machine with fewer integrations, use the
[separate local bundle procedure](#a-separate-container-path-for-one-machine).

## Read this only after you have outgrown tier-0

The first-class entry path into ONEX is **tier-0**: the in-memory event bus plus a
local file-backed store, with **zero external infrastructure** — no Docker, no
broker, no database server. Tier-0 is not a toy or a demo mode; it is the supported
default, and it is where you should start and where most single-machine work stays.

Come here when one of these is actually true:

| Reason to scale up | What tier-0 cannot do |
|---|---|
| More than one process must see the same events | The in-memory bus is per-process by construction |
| You need transport events retained for recovery after a restart | The in-memory event bus loses its events on process exit; a broker provides distributed event persistence/recovery |
| You need server-hosted projection/analytics storage | Tier-0 can persist projections in a local SQLite file; this stack adds PostgreSQL-backed consumers |
| You need multiple runtime replicas or workers | Consumer groups require a real broker |
| You need OIDC-authenticated service-to-service calls | The auth provider is a container in this stack |

A file-backed SQLite projection and saved run artifacts can survive a local process
restart without a broker. That persistence is separate from retaining the event
stream for replay and recovery: the in-memory transport is not a durable event log.
See the [local projection check](getting-started-local.md#53-the-projection-row-read-back-independently).

If none of those apply, close this page. Running a five-service data plane to get
what tier-0 already gives you is a cost with no return.

> **Not covered here.** Connecting a client to a *hosted* ONEX platform rather than
> running your own is a different procedure with different prerequisites (endpoint,
> credentials, gateway). This page does not cover it, and does not guess at it.

---

## Before you start

| Requirement | Why | Check |
|---|---|---|
| Docker Engine + Compose v2 | Every service in this chapter is a container | `docker info` |
| `uv` | The catalog CLI and all repo scripts run under `uv run` | `uv --version` |
| `openssl` | Generates local base passwords; runtime and integration credentials require their owning services | `openssl version` |
| A clone of `omnibase_infra` | The operational `scripts/` and the service catalog are **not** shipped in the pip package | see below |
| ~8 GB RAM free | The broker alone defaults to a large memory reservation | — |

### Two install shapes, and why you need the clone

`omnibase_infra` ships **both** as a pip-installable package and as a cloneable
repository, and they are not interchangeable:

```bash
# Library + the bundled runtime CLIs
pip install omnibase-infra
# or
uv add omnibase-infra
```

The package's console entry points are declared in its `pyproject.toml` under
`[project.scripts]` — that table is the authoritative list, not any copy of it. It
includes `onex-runtime` (the runtime kernel), `omni-infra`, `onex-infra-test`, and
`onex-status`.

What the package does **not** carry is `scripts/` and `docker/`. The operational
scripts scan the repository source tree directly (they iterate over the node
`contract.yaml` files under `src/omnibase_infra/nodes/`, and read the service
catalog under `docker/catalog/`), so they only work from a checkout:

```bash
git clone --branch v0.38.75 --depth 1 https://github.com/OmniNode-ai/omnibase_infra.git omnibase_infra
cd omnibase_infra
uv sync
```

This selects the public `v0.38.75` source snapshot, whose checked commit is
`ea342c1741393e77c7be04f0286795c2e1067a98`, rather than a moving default branch.
The tag contains the service catalog referenced below. This source check does not
establish that a full deployment at that revision has been independently validated.
Everything from here on assumes your shell is inside that checkout.

---

## The service catalog: what you are actually deploying

There is **no hand-maintained compose file to edit**. Every deployable unit is a
typed YAML manifest and the compose file is generated:

| Term | Where it lives | What it is |
|---|---|---|
| **Manifest** | `docker/catalog/services/<name>.yaml` | One service: image, ports, healthcheck, volumes, `depends_on`, and its env contract |
| **Bundle** | `docker/catalog/bundles.yaml` | A named group of services, composable through `includes` |
| **Resolver** | `src/omnibase_infra/docker/catalog/resolver.py` | Expands `includes` transitively and returns the resolved stack |
| **Generator** | `src/omnibase_infra/docker/catalog/generator.py` | Renders the resolved stack to `docker/docker-compose.generated.yml` |
| **Validator** | `src/omnibase_infra/docker/catalog/validator.py` | Refuses to start while any `required_env` var is unset |

**Never hand-edit `docker/docker-compose.generated.yml`.** It is an output. The next
`generate` or `up` overwrites it.

Read `docker/catalog/bundles.yaml` for the live bundle membership rather than
trusting a table anywhere (copied tables drift). The shape that matters:

- `core` — PostgreSQL, the broker, Valkey, the secrets manager, the OIDC provider.
- `runtime-core`, `runtime-integrations`, `runtime-observability-projections`,
  `runtime-infrastructure` — the runtime platform, split so you can roll out one
  slice at a time.
- `runtime` — `includes` all four runtime sub-bundles plus `core` and `tracing`.
- `memgraph`, `omnimemory`, `omnimarket-projections`, `omnidash`, `auth`,
  `observability`, `tracing`, `canary`, `fault-injection` — optional add-ons.

Bundle requirements are the union of selected service manifests, transitive
service dependencies and bundle-level requirements, after declared injection
rules. An empty bundle `inject_required_env` list does not mean an empty resolved
requirement set. In the pinned [bundle declarations](https://github.com/OmniNode-ai/omnibase_infra/blob/v0.38.75/docker/catalog/bundles.yaml),
`runtime-core` includes services that need credentials and model configuration
beyond `core`; the earlier claim of base-only requirements was false.

For example, the [primary runtime manifest](https://github.com/OmniNode-ai/omnibase_infra/blob/v0.38.75/docker/catalog/services/omninode-runtime.yaml)
requires database/cache passwords, identity/service-client secrets, registration
settings, model URLs, endpoint CIDR/host allowlists, a local-model shared secret and
an analytics database URL. Other resolved services add their own requirements,
including integration credentials. These are your self-hosted configuration and
credentials, not values supplied by OmniNode. Use the resolved validator output;
do not infer readiness from a sub-bundle name or copy a partial list as a complete
contract.

### The env-var contract

Three categories, and mixing them up is the most common self-host failure:

| Category | Declared in | Rule |
|---|---|---|
| `required_env` | per-service manifest | Required operator inputs, including secrets, model addresses and operational settings; checked after bundle resolution |
| `hardcoded_env` | per-service manifest | Manifest-owned values/expressions; may reference operator variables |
| `inject_env` / `inject_required_env` | per-bundle in `bundles.yaml` | Bundle-provided overrides and additional operator requirements; included bundles also contribute |

Use the selected manifest as authority. Stable container service addresses can
be declared by the manifest; model endpoints and externally supplied configuration
can still be required operator inputs. The `local` bundle deliberately injects
values that disable integrations on runtime-layer services. The
[resolver](https://github.com/OmniNode-ai/omnibase_infra/blob/v0.38.75/src/omnibase_infra/docker/catalog/resolver.py)
removes an injected variable from operator requirements only under its declared
rules, including which service layers require it.

---

## Step 1 — Generate the base secrets and inventory runtime inputs

The base-secret generator creates local database/cache passwords and the
secrets-manager bootstrap values. It does not provision the runtime's service-client
credentials, model endpoints/allowlists, integration credentials or machine identity.
Inventory the selected bundle's requirements before expecting the runtime to start.
Generating this base file itself contacts no external service:

```bash
./scripts/generate-local-env.sh              # writes ~/.omnibase/.env
./scripts/generate-local-env.sh ./.env       # or a specific path
./scripts/generate-local-env.sh --print      # print to stdout, write nothing
./scripts/generate-local-env.sh --force      # overwrite an existing file
```

The script requires `openssl`, writes with `umask 077`, and `chmod 600`s the result.

> **`--force` rotates every value.** Existing PostgreSQL and Valkey volumes will
> reject the new passwords. On an already-initialized stack this is a credential
> rotation, not a re-run — see [Securing the cache](#securing-the-cache) for the
> shape a real rotation has to take.

If you prefer to start from `.env.example`, replace its placeholders and then
compare with the selected release's resolved bundle requirements. The template and
base generator are not complete runtime provisioning. Base bootstrap values include:

| Variable | Generate with | Needed by |
|---|---|---|
| `POSTGRES_PASSWORD` | `openssl rand -hex 32` | `core` (and every service that talks to PostgreSQL) |
| `VALKEY_PASSWORD` | `openssl rand -hex 32` | `core` — the cache starts with `--requirepass`, so it is not optional |
| secrets-manager encryption key | `openssl rand -hex 16` (must be 32 hex chars) | `core` |
| secrets-manager auth secret | `openssl rand -base64 32` | `core` |
| secrets-manager cache URL | reuse `VALKEY_PASSWORD`, in-network host and port | `core` |
| `KEYCLOAK_ADMIN_PASSWORD` | choose your own local admin password | The OIDC service in `core`; its manifest supplies a development default, not a value generated by this script |

> **Naming note.** This book redacts the secrets-manager product name under its own
> sanitization gate, so the last three rows are described rather than named. Their
> exact variable names, and the exact placeholder text, are in `.env.example` in the
> checkout — read them there. Do not guess at the names.

The required-env validator checks that resolved names have nonempty values; it
does not authenticate a credential or validate a model endpoint. With explicit
`--env-file`, the pinned CLI also refuses its recognized `__REPLACE_WITH_`
template markers. That check is not a general secret-validity test, and the
legacy implicit env-file path does not apply that placeholder scan.

### Where the CLI looks for your env

Without `--env-file`, the CLI reads `~/.omnibase/.env`, then repo `.env`. With
`--env-file <path>`, it reads only that operator file instead of those two.
In both cases it loads the release's runtime-policy contract afterward; already
exported process values win, followed by earlier files. The local bundle procedure
uses the explicit-file path to avoid inheriting the two implicit operator files.
See the [loader](https://github.com/OmniNode-ai/omnibase_infra/blob/v0.38.75/src/omnibase_infra/docker/catalog/cli.py)
for precedence and placeholder checks.

---

## Step 2 — Bring up core

```bash
uv run python -m omnibase_infra.docker.catalog.cli up core
```

The `up` command is `validate` → `generate` → `docker compose up -d`, in that order,
with a `docker compose rm -f --stop -v` pre-cleanup pass for selected services.
That command can stop/remove their running containers as well as exited ones;
named data volumes are retained. Do not assume this is a rolling or restart-free
update. It also records your bundle selection in
`.onex/stack.yml`, so a later bare `up` with no arguments repeats the same stack
(defaulting to `core` if nothing was ever saved).

The other commands on the same CLI:

```bash
uv run python -m omnibase_infra.docker.catalog.cli generate core        # render only
uv run python -m omnibase_infra.docker.catalog.cli validate runtime     # env check only
uv run python -m omnibase_infra.docker.catalog.cli validate-runtime runtime
uv run python -m omnibase_infra.docker.catalog.cli status               # compose ps
uv run python -m omnibase_infra.docker.catalog.cli read-stack           # saved selection
uv run python -m omnibase_infra.docker.catalog.cli down
```

`up` also accepts `--build` (rebuild images first) and `--seed` (seed the secrets
manager from the node contracts after the stack is up; this happens automatically
whenever the `runtime` bundle is in the selection).

`scripts/onex-cli.sh` defines convenience shell functions that forward to exactly
these commands — `infra-up` → `up core`, `infra-up-runtime` → `up runtime`,
`infra-up-memory` → `up runtime memgraph`, `infra-up-auth` → `up core auth`,
`infra-down`, `infra-status`. Source it if you want them. They are wrappers, not a
second code path.

### Published ports

The catalog publishes deliberately non-default host ports so the stack can coexist
with anything you already run:

| Service | Host port | In-container |
|---|---|---|
| PostgreSQL | 5436 | 5432 |
| Valkey | 16379 | 6379 |
| Broker (Kafka API) | 19092 | 9092 internal / 19092 external |
| OIDC provider | 28080 | 8080 |
| Runtime kernel | 8085 | 8085 |
| Runtime effects | 8086 | 8085 |

Confirm against the manifests before wiring a firewall rule — the manifest is the
source of truth, this table is a convenience.

### Set the broker's advertised address

This is the one value in the catalog you almost certainly must override. The broker
manifest advertises itself to external clients using `REDPANDA_ADVERTISE_HOST`, and
its pinned default is **`localhost`**. That is appropriate for a client on the
same host, but a remote client would interpret it as its own machine. For remote
access, set the advertised address to the host your clients can reach:

```bash
REDPANDA_ADVERTISE_HOST=<the host address your clients use>
```

In-container clients use the internal listener. With the default external
advertisement, a client on another host may connect for metadata and then fail
when it follows the advertised `localhost` address. `REDPANDA_EXTERNAL_PORT`,
`REDPANDA_PANDAPROXY_PORT`, and `REDPANDA_MEMORY` are overridable the same way.

---

## Step 3 — Migrations are a gate, not a side effect

Do not skip this section. The runtime will not start without it, and the way it
refuses is deliberately opaque if you do not know the mechanism.

Three catalog entries implement it:

| Entry | Kind | What it does |
|---|---|---|
| `forward-migration` | one-shot (`restart: 'no'`) | Applies pending files from `docker/migrations/forward` in sorted order |
| `intelligence-migration` | one-shot (`restart: 'no'`) | Same, for `docker/migrations/intelligence` |
| `migration-gate` | long-running sentinel | Healthcheck-only service that reports healthy iff migrations are complete |

Both one-shots `depends_on` PostgreSQL being `service_healthy`, and `migration-gate`
additionally waits for `forward-migration` to reach
`service_completed_successfully`. The runtime kernel in turn `depends_on`
`migration-gate` being `service_healthy`. That chain is the whole boot order.

**How the sentinel works.** The forward runner clears a `migrations_complete` flag
in a metadata table at the *start* of every invocation and sets it back to true only
as its final act, after every infra and node migration has applied without error.
Any nonzero exit anywhere leaves the flag false. The gate's healthcheck reads that
flag and also asserts that the required projection tables exist — so a migration run
that "succeeded" without producing the tables still fails the gate, by design.

**Fresh volume vs. warm volume.** On a brand-new PostgreSQL volume the forward
migrations are also mounted into the image's init directory and applied at first
initialization (standard PostgreSQL image behavior: that directory runs only when
the data directory is empty). The `forward-migration` one-shot is what keeps a
**warm** volume current — it records what it has applied and re-applying is a no-op.
You need both; neither replaces the other.

**Give it time.** The gate's healthcheck `start_period` is 180 seconds, not the
usual 10. That is not padding: on a cold database the two migration runs take on the
order of two minutes, and a shorter start period makes a *correctly working* gate
report UNHEALTHY for that whole window. If you shorten it, you will misdiagnose a
healthy bring-up as a failure.

**The only sanctioned skip.** A migration that genuinely must not run is listed in
the committed `docker/migrations/skip-manifest.yaml` with an id and a reason. There
is no flag, no env var, and no override. Adding an entry is a code change that
belongs in the same change as the decision.

### Historical cold-database caveat

The original 2026-08-26 guide reported a cold-database failure involving
`CREATE OR REPLACE VIEW`; this source audit did not reproduce that failure or
establish that the same migration defect persists in `v0.38.75`. In general, a
forward migration that does `CREATE OR REPLACE VIEW`
with reordered columns can fail outright — PostgreSQL forbids renaming view columns
in place. This only manifests on a from-scratch database; incremental redeploys
never re-run the offending migration. The bring-up **correctly fails fast** at the
migration preflight rather than booting the kernel against a half-migrated schema.
This is a migration-source defect, not something the bring-up can paper over. If you
hit it, fix the migration.

---

## Step 4 — Bring up the runtime

```bash
uv run python -m omnibase_infra.docker.catalog.cli up runtime
```

Before this command, provision all resolved runtime/service/integration inputs and
validate the selection. The base env generator is not sufficient. `runtime`
transitively includes `core`, `tracing` and all runtime slices. The CLI pre-cleanup
can stop/recreate selected service containers; retaining volumes does not make
this a restart-free update.

**One ordering constraint you cannot avoid.** The `runtime` bundle requires a
secrets-manager *machine identity* (a client id, a client secret, and a project id).
That identity is minted **against the secrets-manager container that `up core`
started**, so it cannot exist before the first bring-up. The sequence is therefore:

1. `up core`
2. mint the machine identity with the identity-setup script in `scripts/`
3. put the three values in your env file
4. `up runtime`

`.env.example` carries a commented block naming those three variables and the script
that mints them — read it there rather than guessing. `core` deliberately does
**not** require them, precisely so that step 1 is reachable from a cold start.

### Rolling out one slice at a time

Validate the selected slice and its transitive dependencies before starting it:

```bash
uv run python -m omnibase_infra.docker.catalog.cli validate runtime-core
# After supplying all reported requirements:
uv run python -m omnibase_infra.docker.catalog.cli up runtime-core
```

`runtime-core` is not a low-secret profile. Its empty bundle-level requirement list
still resolves service-level identity credentials, model URLs/allowlists and other
operator inputs. The remaining slices also require their resolved service inputs:

- `runtime-observability-projections` adds projection consumers and database DSNs.
- `runtime-infrastructure` adds migrations, workers and recovery services.
- `runtime-integrations` adds webhook/chat integration credentials.

Selecting one slice does not erase its service dependencies or credentials. The
full `runtime` bundle additionally requires the secrets-manager machine identity
described above. Validation checks declared input presence; readiness also requires
correct values, images, migrations, working endpoints and healthy consumers.

### A separate container path for one machine

For a developer who wants a broker and runtime in containers without the full
operator integrations, the release defines a distinct `local` bundle. Follow the
pinned [Makefile](https://github.com/OmniNode-ai/omnibase_infra/blob/v0.38.75/Makefile),
[local env template](https://github.com/OmniNode-ai/omnibase_infra/blob/v0.38.75/docker/local.env.example)
and [model overlay template](https://github.com/OmniNode-ai/omnibase_infra/blob/v0.38.75/docker/lane-overlays/local.bifrost.example.yaml).
From the pinned checkout, its separate procedure is:

```bash
make local-env
# Edit the generated model overlay to point at your own model.
make up-local
make status-local
```

`local-env` creates the local env/overlay files when absent and can add missing
local credential fields to an existing env file. The template names five local
passwords (database, cache, two database principals and broker superuser), plus the
model-overlay path; do not confuse this with having no credentials or only two
passwords. `up-local` selects `local --env-file` and builds the runtime image.
The bundle injects integration-disable values, uses its own compose project and
binds published ports to loopback. It still needs Docker resources, its declared
local passwords, a model reachable from the containers, migrations and runtime
readiness checks. This is a source-inspected procedure, not a deployment performed
for this documentation update. It is separate from the broker-free quickstart and
from the operator `runtime-core`/`runtime` sequence above.

---

## The compose-profile gotcha

You will find checked-in compose files under `docker/` — most notably
`docker/docker-compose.infra.yml`. **The catalog path above does not use them**, and
the generated compose has no profiles at all. But if you ever invoke a checked-in
compose file directly, this will bite you:

```yaml
profiles: ["runtime", "full"]
```

Every runtime service in that file is profile-gated. A bare
`docker compose -f docker/docker-compose.infra.yml up -d` matches **no** profiled
service and **starts nothing** of the runtime — the dependencies come up and the
kernel, effects, projection API, and the whole consumer fleet stay down, with no
error. `--profile runtime` (or `--profile full`) is mandatory on that path.

The matching teardown trap: a bare `down` leaves profile-gated containers orphaned.
Use `down --remove-orphans`.

The general rule: **prefer the catalog CLI, and do not mix the two paths.** Raw
`docker compose -f <path>` against a checked-in file bypasses env validation, the
generated-compose contract, and the stack-selection file.

---

## Step 5 — Verify

```bash
# every container in the current stack
uv run python -m omnibase_infra.docker.catalog.cli status

# runtime kernel health
curl -fsS "http://<your-host>:8085/health"

# the gate specifically — this is the one that tells you migrations landed
docker inspect --format '{{.State.Health.Status}}' omnibase-infra-migration-gate
```

Read health in this order — gate, then kernel — because a kernel that never started
is almost always a gate that never went healthy, and the kernel's own health output
will not tell you that.

The pinned kernel healthcheck has a 1800-second start period and a semantic
health probe. An HTTP `200` from `/health` alone is insufficient: read the JSON
status and verify the expected handlers/consumers, because a degraded runtime can
still answer HTTP successfully. A long start period is not proof that a slow boot
will eventually become healthy; inspect logs and dependency state.

---

## Securing the cache

The cache holds session state and is reachable from every runtime service. Two
things go wrong in practice: it gets deployed with **no** password at all, and the
password it does have gets embedded somewhere that makes rotation impossible. The
pattern below prevents both.

### 1. Require a password, and read it from a file

Both the compose and Kubernetes shapes start the server with `--requirepass`. The
compose manifest does it conditionally on the variable being set:

```sh
valkey-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru \
  ${VALKEY_PASSWORD:+--requirepass "$VALKEY_PASSWORD"}
```

That `${VAR:+...}` form is a real hazard in disguise: **an unset variable silently
yields a server with no authentication.** Under the catalog CLI this cannot happen —
`VALKEY_PASSWORD` is declared `required_env` and validation refuses to start without
it. If you deploy the cache any other way, add your own check. An unauthenticated
cache does not fail; it works perfectly, which is why nobody notices.

Outside compose, read the password from a **mounted secret file** rather than an
environment variable in the pod spec:

```yaml
command:
  - sh
  - -c
  - |
    exec valkey-server \
      --save 60 1 \
      --loglevel warning \
      --requirepass "$(cat /etc/valkey-secret/password)"
volumeMounts:
  - name: valkey-secret
    mountPath: /etc/valkey-secret
    readOnly: true
```

The example records a file path in the command rather than a literal password.
The shell reads the mounted file when starting the process; the snippet does not
claim that environment expansion rewrites a stored Pod object. This Kubernetes
example is separate from the release's Compose catalog procedure.

### 2. Give the probes their own auth channel

Once `--requirepass` is on, an unauthenticated `valkey-cli ping` fails, and a
liveness probe that does exactly that will kill the container it was meant to watch.
`valkey-cli` reads `REDISCLI_AUTH` from the environment:

```yaml
env:
  - name: REDISCLI_AUTH
    valueFrom:
      secretKeyRef:
        name: <cache-credentials-secret>
        key: password
```

The same idea in a compose healthcheck, guarded so it still works before the
password exists:

```sh
valkey-cli ${VALKEY_PASSWORD:+-a "$VALKEY_PASSWORD" --no-auth-warning} ping | grep -q PONG
```

`--no-auth-warning` suppresses the "password on the command line" notice that would
otherwise pollute every health log line.

> **Turning auth on is a two-sided change.** Enabling `--requirepass` on a server
> whose consumers are not yet configured with the password takes the cache down for
> all of them; wiring the password into consumers that talk to a server without auth
> is harmless. So configure consumers first, then enable the server. Doing it in the
> other order is a self-inflicted outage.

### 3. One authority, explicit mirrors

Where consumers live in a different trust boundary from the cache (separate
namespaces, separate compose projects), do not let each one hold its own copy of the
credential by accident. Name one **authoritative** secret next to the cache, and
treat every consumer-side copy as an explicit **mirror** of it. Then make the
mirroring checkable:

- Every consumer references the credential through the *same* named secret and key —
  never an inline literal, never a per-consumer variant.
- Rotation compares a digest (e.g. `sha256`) of the source and the mirror and fails
  if they differ, rather than assuming they are in sync.
- Rotation **refuses to run** if any consumer's live configuration does not reference
  the expected secret and key. This check matters more than it sounds: if a consumer
  is still reading a stale reference, rotating the mirror changes nothing for it, and
  you would end the rotation believing a consumer was updated when it was not. Fix
  the consumer's configuration; never weaken the check to accept the stale reference.

### 4. Rotation is a script, not a procedure

Rotation touches a server, a source secret, N mirrors, and N consumer restarts. Done
by hand it is a partial-failure generator. Encode it once, with three modes:

| Mode | Does | Safe to run any time |
|---|---|---|
| `prepare` | Copies the current authoritative value into the mirror(s). Changes **no** server credential and restarts **nothing**. | Yes |
| `rotate` | Generates a new value, writes mirror then source, restarts the server, restarts every consumer, verifies. | No — this is the mutation |
| `verify` | Asserts source/mirror digests match, consumer references are correct, and an authenticated ping returns `PONG`. | Yes |

Non-negotiable properties of the `rotate` path:

1. **Generate URL-safe.** `openssl rand -hex 32`. Consumers that build a
   `redis://user:pass@host` URL from the credential will corrupt it otherwise.
2. **Assert the new value differs from the old** before doing anything.
3. **Install a rollback trap first.** On any error or interrupt, restore the previous
   value to both source and mirror, restart the server, restart the consumers, and
   report the restored digest. Arm the trap *before* the first write.
4. **Order the writes: mirror, then source.** The window where consumers hold a
   credential the server has not adopted yet is harmless; the reverse is an outage.
5. **Restart the server, then prove an authenticated ping succeeds** — before
   touching a single consumer. If the server did not take the new credential, stop
   there and roll back rather than restarting consumers into a broken cache.
6. **Restart consumers one at a time**, waiting for each rollout to complete.
7. **Prove the old credential is rejected.** Attempt an `auth` with the previous
   value and fail the rotation if it returns `OK`. Without this, a server that
   silently ignored the new configuration passes every other check.
8. **Clear the values from the shell** when done, and never echo a credential.

Point 7 is the one most often left out, and it is the only step that distinguishes
"rotation completed" from "rotation appeared to complete".

### 5. Verify auth is actually on

```sh
# from inside the cache container — must succeed
REDISCLI_AUTH="$(cat /etc/valkey-secret/password)" valkey-cli --no-auth-warning ping

# unauthenticated — must FAIL. If this returns PONG, you have no auth.
valkey-cli ping
```

Run the second command. A cache you *believe* is authenticated and a cache that
*is* authenticated look identical from every consumer.

---

## Cold vs. warm restarts

Once running, the stack has two distinct restart shapes, and using the wrong one is
a common way to lose an hour:

| | **Warm** | **Cold** |
|---|---|---|
| Going in | Dependencies and broker already running | Zero containers — reclaimed, or torn down |
| What you touch | The runtime services only | Dependencies, the migration one-shots, then the whole stack |
| Migrations | Already applied | Must run, and must be waited on |

A warm refresh that assumes the dependencies are up will half-start against a cold
stack and fail in the runtime, not at the dependency that is actually missing. The
full sequencing — dependency readiness, broker topic provisioning, the migration
one-shots, and the raised broker-join timeout a cold start needs — is in
[the cold-lane full bring-up runbook](../runbooks/cold-lane-full-bringup.md).

---

## When it does not come up

| Symptom | Most likely cause |
|---|---|
| `Cannot start: missing required env vars` | The listed vars are absent from both `~/.omnibase/.env` and the repo `.env` |
| Stack starts, then a service fails on a malformed key | Presence validation does not authenticate values. Explicit `--env-file` rejects recognized template markers, but real-looking invalid credentials can still pass that check |
| Runtime never starts | First check resolved required inputs and images, then `migration-gate` and runtime health/logs. Base secrets alone do not satisfy `runtime-core` |
| Gate stays in `starting` on a cold DB | Its declared start period is 180s. Inspect migration progress; that grace period is not proof of eventual success |
| Gate never goes healthy | A migration failed; the sentinel flag is correctly still false. Read the one-shot's logs |
| Nothing at all starts from a checked-in compose file | Missing `--profile runtime` |
| Orphaned containers after `down` | Use `down --remove-orphans` |
| Remote clients connect, then fail on the next call | The advertised host still resolves to `localhost` or another address those clients cannot reach |
| Cache-dependent services fail after enabling auth | Consumers were not configured with the password before the server required it |
| A rotation "succeeded" but a consumer still uses the old value | The consumer referenced a stale secret; the reference check would have caught it |

---

## Related pages

- [Cold-lane full bring-up](../runbooks/cold-lane-full-bringup.md) — cold vs. warm
  sequencing in full
- [Applying migrations](../runbooks/apply-migrations.md) — migration mechanics
- [Broker reconnect and recovery](../runbooks/kafka-reconnect-and-broker-recovery.md)
  — when the broker drops
- [Volume config drift and reseed](../runbooks/volume-config-drift-and-reseed.md) —
  when a volume's copy of config diverges from its authority
