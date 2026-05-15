# Backend

## Setup venv
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
source .venv/bin/deactivate
pip install -r /home/ofitz/repo/plc-datalink-rfc1006/backend/requirements.txt

## Build adn run
docker-compose -f ../dc-plc-datalink-rfc1006-local.yml up

## Rebuild each image
docker-compose -f dc-plc-datalink-rfc1006-debug.yml build plc-datalink-rfc1006-backend && docker-compose -f dc-plc-datalink-rfc1006-debug.yml up  --no-deps --force-recreate plc-datalink-rfc1006-backend
docker-compose -f dc-plc-datalink-rfc1006-debug.yml build plc-datalink-rfc1006-database && docker-compose -f dc-plc-datalink-rfc1006-debug.yml up  --no-deps --force-recreate plc-datalink-rfc1006-database
docker-compose -f dc-plc-datalink-rfc1006-debug.yml build plc-datalink-rfc1006-frontend && docker-compose -f dc-plc-datalink-rfc1006-debug.yml up  --no-deps --force-recreate plc-datalink-rfc1006-frontend

## Tests

All backend tests run inside the dedicated `backend-test` container — no
host-side venv. Sources live under [test/scripts/](test/scripts/), split
into two halves:

| Folder | Purpose | External deps |
|---|---|---|
| `test/scripts/unit/` | model, services, routes — all dependencies mocked | none |
| `test/scripts/integration/` | renderer against full ZKS tag set, CouchDB roundtrip, S7 smoke against the ZKS mock | docker socket (CouchDB testcontainer), running ZKS machine mock (S7 smoke) |

Every test under `integration/` is automatically tagged with the
`integration` marker — the unit suite can be run in isolation:

```bash
# build (after backend/Dockerfile.test, src/, test/, requirements.txt change)
docker compose -f ../dc-plc-datalink-rfc1006-test.yml build backend-test

# unit suite only (fast, no external deps)
docker compose -f ../dc-plc-datalink-rfc1006-test.yml run --rm backend-test \
    pytest -q -m "not integration"

# full suite (CouchDB spins up via testcontainers; S7 tests skip if ZKS mock down)
docker compose -f ../dc-plc-datalink-rfc1006-test.yml run --rm backend-test

# point the S7 tests at a non-default ZKS endpoint
docker compose -f ../dc-plc-datalink-rfc1006-test.yml run --rm \
    -e ZKS_S7_HOST=host.docker.internal -e ZKS_S7_PORT=1102 \
    backend-test pytest -q test/scripts/integration/test_zks_s7_smoke.py
```

The ZKS machine mock is documented under
[../docs/machines-db-layout/zks-machine-mock/README.md](../docs/machines-db-layout/zks-machine-mock/README.md).
Start it on the host before running the S7 smoke tests; the test
container reaches the host-bound port through
`host.docker.internal:host-gateway` (configured in the test compose).

### End-to-end test (REST → CouchDB → Telegraf → ZKS → MQTT)

[`test/scripts/integration/test_e2e_zks_mqtt.py`](test/scripts/integration/test_e2e_zks_mqtt.py)
walks the whole pipeline against a live production-image backend. It runs
in a dedicated compose stack — [`dc-plc-datalink-rfc1006-e2e.yml`](../dc-plc-datalink-rfc1006-e2e.yml)
— that wires up four containers:

| Service | Role |
|---|---|
| `couchdb-e2e` | real CouchDB (the database image) for persisting the machine config |
| `mosquitto-e2e` | real Mosquitto broker (anonymous listener, network-internal only) |
| `backend-e2e` | production backend image — gunicorn + supervisord + Telegraf |
| `backend-e2e-runner` | the `backend-test` image, executes only the E2E pytest |

The ZKS machine mock stays on the host; both `backend-e2e` (Telegraf reads
PLC tags) and `backend-e2e-runner` (snap7 fault injection) reach it via
`host.docker.internal:host-gateway`.

```bash
# 1) Start the ZKS mock on the host (see its README)
# 2) Build + run the E2E stack
docker compose -f ../dc-plc-datalink-rfc1006-e2e.yml build
docker compose -f ../dc-plc-datalink-rfc1006-e2e.yml run --rm backend-e2e-runner
docker compose -f ../dc-plc-datalink-rfc1006-e2e.yml down -v
```

The runner fixtures probe each dependency at session start (ZKS S7 port,
backend `/machine/online`, mosquitto port) and skip the test cleanly when
any piece is missing — running the stack without ZKS up produces a clear
`SKIPPED: ZKS machine mock not reachable at host.docker.internal:102`.
