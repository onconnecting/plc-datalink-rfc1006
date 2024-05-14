# dockerfile-plc-datalink-rfc1006-frontend

## Setup venv
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
source .venv/bin/deactivate
pip install -r /home/ofitz/repo/plc-datalink-rfc1006/backend/requirements.txt

## Build and run
docker-compose -f ../dc-plc-datalink-rfc1006-local.yml up

## Rebuild each image
docker-compose -f dc-plc-datalink-rfc1006-debug.yml build plc-datalink-rfc1006-frontend && docker-compose -f dc-plc-datalink-rfc1006-debug.yml up  --no-deps --force-recreate plc-datalink-rfc1006-frontend
docker-compose -f dc-plc-datalink-rfc1006-debug.yml build plc-datalink-rfc1006-database && docker-compose -f dc-plc-datalink-rfc1006-debug.yml up  --no-deps --force-recreate plc-datalink-rfc1006-database
docker-compose -f dc-plc-datalink-rfc1006-debug.yml build plc-datalink-rfc1006-backend && docker-compose -f dc-plc-datalink-rfc1006-debug.yml up  --no-deps --force-recreate plc-datalink-rfc1006-backend

## Run local angular server
Run `ng serve` for a dev server. Navigate to `http://localhost:4200/`. The application will automatically reload if you change any of the source files.

## Build local angular server
Run `ng build` to build the project. The build artifacts will be stored in the `dist/` directory.
