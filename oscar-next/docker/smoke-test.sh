#!/usr/bin/env bash
# smoke-test.sh — Run before declaring any module done.
# Usage: KEYCLOAK_USER=bdhawan KEYCLOAK_PASS=Oscar2026\!Rx bash smoke-test.sh
set -uo pipefail

KEYCLOAK_USER="${KEYCLOAK_USER:-bdhawan}"
KEYCLOAK_PASS="${KEYCLOAK_PASS:-}"  # Set via env: KEYCLOAK_PASS='Oscar2026!Rx' bash smoke-test.sh
API="https://api.mapleclinics.ca"
# For API endpoint tests use localhost:8000 directly — bypasses Cloudflare and avoids
# hitting a stale container after a redeploy (Cloudflare can take 30-60s to drain old conns)
API_LOCAL="http://localhost:8000"
APP="https://app.mapleclinics.ca"
AUTH="https://auth.mapleclinics.ca"
AUTH_LOCAL="http://localhost:8090"

PASS=0; FAIL=0
ok()   { echo "  ✓ $1"; PASS=$((PASS + 1)); }
fail() { echo "  ✗ $1"; FAIL=$((FAIL + 1)); }

echo "=== Oscar Smoke Test $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

# Wait for API to be ready (up to 30s after a fresh deploy)
for i in $(seq 1 10); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/health" 2>/dev/null || echo "000")
  [ "$STATUS" = "200" ] && break
  echo "  waiting for API... ($i/10)"
  sleep 3
done

# 1. API health
echo ""
echo "--- API health ---"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/health")
[ "$STATUS" = "200" ] && ok "GET /health → 200" || fail "GET /health → $STATUS"

# 2. Get token
echo ""
echo "--- Auth ---"
TOKEN_RESP=$(curl -s -X POST "$AUTH/realms/oscar/protocol/openid-connect/token" \
  -d "grant_type=password" -d "client_id=oscar-web" \
  -d "username=$KEYCLOAK_USER" -d "password=$KEYCLOAK_PASS" \
  -d "scope=openid email profile roles")
TOKEN=$(echo "$TOKEN_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null)
[ -n "$TOKEN" ] && ok "ROPC token acquired" || { fail "ROPC token failed: $TOKEN_RESP"; exit 1; }

# 3. CORS preflight
echo ""
echo "--- CORS ---"
CORS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS "$API/api/v1/patients/search" \
  -H "Origin: $APP" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Authorization")
[ "$CORS_STATUS" = "200" ] && ok "CORS preflight → 200" || fail "CORS preflight → $CORS_STATUS"

ALLOW_ORIGIN=$(curl -si -X OPTIONS "$API/api/v1/patients/search" \
  -H "Origin: $APP" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Authorization" | grep -i "access-control-allow-origin" | tr -d '\r')
echo "    $ALLOW_ORIGIN"
[[ "$ALLOW_ORIGIN" == *"$APP"* ]] && ok "CORS allow-origin header present" || fail "CORS allow-origin missing/wrong: $ALLOW_ORIGIN"

# 4. Patient search
echo ""
echo "--- Patient search ---"
SEARCH=$(curl -s -H "Authorization: Bearer $TOKEN" "$API/api/v1/patients/search?limit=5")
TOTAL=$(echo "$SEARCH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total',0))" 2>/dev/null)
[ "${TOTAL:-0}" -gt 0 ] && ok "Patient search returned $TOTAL patients" || fail "Patient search returned 0 or error: $SEARCH"

# 5. Single patient detail (retry up to 5× with 5s gap — Cloudflare takes ~30s to drain old container after redeploy)
echo ""
echo "--- Patient detail ---"
FIRST_ID=$(echo "$SEARCH" | python3 -c "import sys,json; r=json.load(sys.stdin).get('results',[]); print(r[0]['demographic_no'] if r else '')" 2>/dev/null)
if [ -n "$FIRST_ID" ]; then
  DETAIL=$(curl -s -H "Authorization: Bearer $TOKEN" "$API/api/v1/patients/$FIRST_ID")
  for _retry in 1 2 3 4 5; do
    _ok=$(echo "$DETAIL" | python3 -c "import sys,json; d=json.load(sys.stdin); print('ok' if d.get('first_name') else 'no')" 2>/dev/null || echo "no")
    [ "$_ok" = "ok" ] && break
    echo "    retrying patient detail ($_retry/5)..."
    sleep 5
    DETAIL=$(curl -s -H "Authorization: Bearer $TOKEN" "$API/api/v1/patients/$FIRST_ID")
  done
  HAS_NAME=$(echo "$DETAIL" | python3 -c "import sys,json; d=json.load(sys.stdin); print('ok' if d.get('first_name') else 'missing')" 2>/dev/null || echo "missing")
  [ "$HAS_NAME" = "ok" ] && ok "GET /patients/$FIRST_ID has first_name" || fail "GET /patients/$FIRST_ID missing first_name: $DETAIL"
  HAS_SIN=$(echo "$DETAIL" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print('FOUND' if isinstance(d, dict) and 'sin' in d else 'absent')
except Exception:
    print('absent')
" 2>/dev/null)
  [ "$HAS_SIN" = "absent" ] && ok "SIN absent from patient detail (PHIPA)" || fail "SIN EXPOSED in patient detail!"
else
  fail "No patient ID to test detail"
fi

# 6. Patient banner (retry up to 5× with 5s gap for same Cloudflare drain reason)
echo ""
echo "--- Patient banner ---"
if [ -n "$FIRST_ID" ]; then
  BANNER=$(curl -s -H "Authorization: Bearer $TOKEN" "$API/api/v1/patients/$FIRST_ID/banner")
  for _retry in 1 2 3 4 5; do
    _ok=$(echo "$BANNER" | python3 -c "import sys,json; d=json.load(sys.stdin); print('ok' if d.get('display_name') else 'no')" 2>/dev/null || echo "no")
    [ "$_ok" = "ok" ] && break
    echo "    retrying banner ($_retry/5)..."
    sleep 5
    BANNER=$(curl -s -H "Authorization: Bearer $TOKEN" "$API/api/v1/patients/$FIRST_ID/banner")
  done
  HAS_NAME=$(echo "$BANNER" | python3 -c "import sys,json; d=json.load(sys.stdin); print('ok' if d.get('display_name') else 'missing')" 2>/dev/null || echo "missing")
  [ "$HAS_NAME" = "ok" ] && ok "GET /patients/$FIRST_ID/banner has display_name" || fail "Banner missing display_name: $BANNER"
fi

# 7. FHIR Patient bundle
echo ""
echo "--- FHIR ---"
FHIR=$(curl -s -H "Authorization: Bearer $TOKEN" -H "Accept: application/fhir+json" "$API/fhir/R4/Patient?_count=3")
# Retry once on transient error
RT=$(echo "$FHIR" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('resourceType','PARSE_ERROR'))" 2>/dev/null || echo "PARSE_ERROR")
if [ "$RT" != "Bundle" ]; then sleep 3; FHIR=$(curl -s -H "Authorization: Bearer $TOKEN" -H "Accept: application/fhir+json" "$API/fhir/R4/Patient?_count=3"); RT=$(echo "$FHIR" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('resourceType','PARSE_ERROR'))" 2>/dev/null || echo "PARSE_ERROR"); fi
[ "$RT" = "Bundle" ] && ok "FHIR /Patient returns Bundle" || fail "FHIR /Patient → not a Bundle ($RT): ${FHIR:0:200}"

# 8. App login page (unauthenticated)
echo ""
echo "--- Frontend pages ---"
LOGIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$APP/login")
[ "$LOGIN_STATUS" = "200" ] && ok "GET /login → 200" || fail "GET /login → $LOGIN_STATUS"

# 9. Patient page redirects to login when unauthenticated (correct)
PATIENT_PAGE=$(curl -s -o /dev/null -w "%{http_code}" -L --max-redirs 0 "$APP/patients/1" 2>/dev/null || true)
[[ "$PATIENT_PAGE" == "307" || "$PATIENT_PAGE" == "302" ]] \
  && ok "GET /patients/1 (unauthed) redirects to login → $PATIENT_PAGE" \
  || fail "GET /patients/1 (unauthed) unexpected status → $PATIENT_PAGE"

# 10. No bare getServerSession() calls in frontend
echo ""
echo "--- Code quality ---"
# Actual live call sites: getServerSession() without authOptions arg, not in comments
BARE=$(grep -rn "getServerSession()" /Users/bcdhawan/Documents/ND/oscar/migration/oscar-next/frontend --include="*.ts" --include="*.tsx" | python3 -c "
import sys
for line in sys.stdin:
    # Strip the filename:linenum: prefix, then check if it's a code line (not comment)
    parts = line.split(':', 2)
    if len(parts) < 3: continue
    code = parts[2].strip()
    if code.startswith('//') or code.startswith('*') or code.startswith('/*'): continue
    print(line.strip())
" || true)
[ -z "$BARE" ] && ok "No bare getServerSession() without authOptions" || fail "Found bare getServerSession(): $BARE"

# Summary
echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] && echo "ALL CLEAR — safe to declare done." || { echo "BLOCKED — fix failures before declaring done."; exit 1; }
