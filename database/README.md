# dockerfile-plc-datalink-rfc1006-database

## Setup venv
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
source .venv/bin/deactivate
pip install -r /home/ofitz/repo/plc-datalink-rfc1006/backend/requirements.txt

## Build adn run
docker-compose -f ../dc-plc-datalink-rfc1006-local.yml up

## Rebuild each image
docker-compose -f dc-plc-datalink-rfc1006-debug.yml build plc-datalink-rfc1006-database && docker-compose -f dc-plc-datalink-rfc1006-debug.yml up  --no-deps --force-recreate plc-datalink-rfc1006-database
docker-compose -f dc-plc-datalink-rfc1006-debug.yml build plc-datalink-rfc1006-backend && docker-compose -f dc-plc-datalink-rfc1006-debug.yml up  --no-deps --force-recreate plc-datalink-rfc1006-backend
docker-compose -f dc-plc-datalink-rfc1006-debug.yml build plc-datalink-rfc1006-frontend && docker-compose -f dc-plc-datalink-rfc1006-debug.yml up  --no-deps --force-recreate plc-datalink-rfc1006-frontend
