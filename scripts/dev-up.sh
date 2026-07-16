#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FD="$ROOT/frappe_docker"
COMPOSE_SRC="$ROOT/docker/docker-compose.yml"

if [[ ! -d "$FD/.git" ]]; then
  echo "==> Cloning frappe/frappe_docker..."
  git clone --depth 1 https://github.com/frappe/frappe_docker.git "$FD"
fi

mkdir -p "$FD/.devcontainer"
cp "$COMPOSE_SRC" "$FD/.devcontainer/docker-compose.yml"
cp "$ROOT/docker/apps-frappe-only.json" "$FD/development/apps-frappe-only.json"

# Compatibility path for bench venv shebangs (/workspace/development/...)
ln -sfn frappe_docker/development "$ROOT/development"

cd "$FD"
docker compose -f .devcontainer/docker-compose.yml up -d

echo
echo "Containers are up."
echo "If this is the first run, initialize bench + install the app:"
echo
cat <<'EOF'
docker compose -f frappe_docker/.devcontainer/docker-compose.yml exec frappe bash -lc '
  cd /workspace/development
  if [ ! -d frappe-bench ]; then
    python installer.py -j apps-frappe-only.json -t version-15 -a admin
  fi
  cd frappe-bench
  ln -sfn /workspace apps/user_growth_analytics
  ./env/bin/python -m pip install -e apps/frappe -e /workspace
  grep -q user_growth_analytics sites/apps.txt || echo user_growth_analytics >> sites/apps.txt
  bench --site development.localhost install-app user_growth_analytics || true
  bench --site development.localhost set-config developer_mode 1
  bench --site development.localhost migrate
  bench start
'
EOF
echo
echo "Login: http://development.localhost:8000  (Administrator / admin)"
