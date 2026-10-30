#!/usr/bin/env bash
# start.sh — entry point for hosting the app as a single-port HTTP service.
#
# The host injects $PORT and expects the server to bind 0.0.0.0, so Streamlit
# must be told both explicitly. CORS/XSRF are relaxed because the app sits
# behind the host's reverse proxy on a different hostname.
set -e

PORT="${PORT:-8501}"

exec python -m streamlit run app.py \
  --server.port "$PORT" \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.enableCORS false \
  --server.enableXsrfProtection false \
  --browser.gatherUsageStats false
