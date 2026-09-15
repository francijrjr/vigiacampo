#!/bin/bash
set -euo pipefail
mkdir -p /opt/vigiacampo/backups
chmod 700 /opt/vigiacampo/backups
docker exec vigiacampo-db pg_dump -U vigiacampo -Fc vigiacampo > "/opt/vigiacampo/backups/antes-atualizacao-$(date +%Y%m%d-%H%M%S).dump"
aws s3 cp "s3://${PROJECT_BUCKET}/release/app.tar.gz" /opt/vigiacampo/app.tar.gz --region "$AWS_REGION"
tar -xzf /opt/vigiacampo/app.tar.gz -C /opt/vigiacampo/app
docker build -t vigiacampo-api:next /opt/vigiacampo/app
docker run --rm --network vigiacampo --env-file /opt/vigiacampo/app.env vigiacampo-api:next python -m alembic upgrade head
docker stop vigiacampo-api
docker rm vigiacampo-api
docker tag vigiacampo-api vigiacampo-api:previous
docker tag vigiacampo-api:next vigiacampo-api
docker run -d --name vigiacampo-api --restart unless-stopped --network vigiacampo \
  --env-file /opt/vigiacampo/app.env -v /opt/vigiacampo/uploads:/app/uploads \
  -p 8000:8000 --log-opt max-size=5m --log-opt max-file=2 vigiacampo-api
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/health; then exit 0; fi
  sleep 2
done
echo 'API não respondeu após atualização. Verifique os logs antes de continuar.' >&2
exit 1
