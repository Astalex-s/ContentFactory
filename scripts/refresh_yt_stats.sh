#!/bin/bash
# Refresh YouTube/VK stats: POST /analytics/refresh-stats
# Run via cron: */15 * * * * /path/to/scripts/refresh_yt_stats.sh

set -e
BASE_URL="${CONTENTFACTORY_URL:-http://127.0.0.1:8000}"
curl -sS -X POST "${BASE_URL}/analytics/refresh-stats"
