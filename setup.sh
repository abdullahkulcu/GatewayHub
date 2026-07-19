#!/usr/bin/env bash
# One-shot setup: create .env if missing (with a random SECRET_KEY), build and
# start the stack, then print the panel URL once it's ready to accept requests.
#
# This is a shortcut on top of the README's `cp .env.example .env && docker
# compose up` flow, not a replacement for it — run that manually if you want
# more control over .env before the first start.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

random_secret() {
	if command -v openssl >/dev/null 2>&1; then
		openssl rand -hex 32
	elif command -v python3 >/dev/null 2>&1; then
		python3 -c "import secrets; print(secrets.token_hex(32))"
	else
		head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n'
	fi
}

if [ ! -f .env ]; then
	echo "No .env found — creating one from .env.example ..."
	cp .env.example .env
	secret="$(random_secret)"
	# `|` delimiter: the generated hex secret never contains it, unlike `/`.
	sed -i.bak "s|^SECRET_KEY=.*|SECRET_KEY=${secret}|" .env
	rm -f .env.bak
	echo "Generated a random SECRET_KEY in .env."
	echo "Review ADMIN_EMAIL/ADMIN_PASSWORD in .env before continuing if you want a non-default first admin login."
else
	echo ".env already exists — leaving it as is."
fi

echo "Building and starting the stack (postgres, redis, migrate, app, worker) ..."
docker compose up -d --build

app_port="$(grep -E '^APP_PORT=' .env | tail -n1 | cut -d= -f2-)"
app_port="${app_port:-8000}"
url="http://localhost:${app_port}"

echo "Waiting for the app to become healthy at ${url} ..."
for _ in $(seq 1 60); do
	if curl -fsS "${url}/healthz" >/dev/null 2>&1; then
		echo ""
		echo "GatewayHub is ready: ${url}"
		exit 0
	fi
	sleep 2
done

echo ""
echo "Timed out waiting for ${url}/healthz to respond." >&2
echo "Check the logs with: docker compose logs -f app migrate" >&2
exit 1
