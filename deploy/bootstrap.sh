#!/bin/bash
set -euo pipefail
# Variáveis PROJECT_BUCKET e AWS_REGION são preenchidas pelo provisionador.
dnf install -y docker
systemctl enable --now docker
if [ ! -f /swapfile ]; then
  fallocate -l 1G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi
mkdir -p /opt/vigiacampo/app /opt/vigiacampo/import /opt/vigiacampo/uploads
chmod 700 /opt/vigiacampo/import
aws s3 cp "s3://${PROJECT_BUCKET}/release/app.tar.gz" /opt/vigiacampo/app.tar.gz --region "$AWS_REGION"
tar -xzf /opt/vigiacampo/app.tar.gz -C /opt/vigiacampo/app
aws s3 cp "s3://${PROJECT_BUCKET}/private/pncd.db" /opt/vigiacampo/import/pncd.db --region "$AWS_REGION"
aws s3 cp "s3://${PROJECT_BUCKET}/private/app.env" /opt/vigiacampo/app.env --region "$AWS_REGION"
aws s3 cp "s3://${PROJECT_BUCKET}/private/db.env" /opt/vigiacampo/db.env --region "$AWS_REGION"
chmod 600 /opt/vigiacampo/*.env
if aws s3 cp "s3://${PROJECT_BUCKET}/private/uploads.tar.gz" /opt/vigiacampo/uploads.tar.gz --region "$AWS_REGION"; then
  tar -xzf /opt/vigiacampo/uploads.tar.gz -C /opt/vigiacampo/uploads
fi
chown -R 10001:10001 /opt/vigiacampo/uploads
chown -R 10001:10001 /opt/vigiacampo/import
docker network create vigiacampo || true
docker volume create vigiacampo-postgres
docker run -d --name vigiacampo-db --restart unless-stopped --network vigiacampo \
  --env-file /opt/vigiacampo/db.env -v vigiacampo-postgres:/var/lib/postgresql/data \
  --log-opt max-size=5m --log-opt max-file=2 postgres:16-alpine \
  -c shared_buffers=64MB -c max_connections=30
for i in $(seq 1 60); do
  if docker exec vigiacampo-db pg_isready -U vigiacampo; then break; fi
  sleep 2
done
docker build -t vigiacampo-api /opt/vigiacampo/app
docker run --rm --network vigiacampo --env-file /opt/vigiacampo/app.env \
  -v /opt/vigiacampo/import:/import:ro vigiacampo-api \
  sh -c 'python -m alembic upgrade head && python scripts/importar_sqlite.py /import/pncd.db'
sed -i '/^BOOTSTRAP_PASSWORD=/d' /opt/vigiacampo/app.env
docker run -d --name vigiacampo-api --restart unless-stopped --network vigiacampo \
  --env-file /opt/vigiacampo/app.env -v /opt/vigiacampo/uploads:/app/uploads \
  -p 8000:8000 --log-opt max-size=5m --log-opt max-file=2 vigiacampo-api
echo 'VigiaCampo: API e PostgreSQL iniciados.'
