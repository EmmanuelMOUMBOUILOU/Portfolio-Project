#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
PASS="${PASS:-12345678}"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1"; exit 1; }; }
need curl
need jq

# Global var to store last HTTP status
HTTP_STATUS=""

req() {
  local method="$1"
  local url="$2"
  local token="${3:-}"
  local data="${4:-}"

  local body_file
  body_file="$(mktemp)"

  if [ -n "$token" ] && [ -n "$data" ]; then
    HTTP_STATUS=$(curl -sS -o "$body_file" -w "%{http_code}" -X "$method" \
      -H "Authorization: Bearer $token" \
      -H "Content-Type: application/json" \
      -d "$data" \
      "$url" || true)
  elif [ -n "$token" ]; then
    HTTP_STATUS=$(curl -sS -o "$body_file" -w "%{http_code}" -X "$method" \
      -H "Authorization: Bearer $token" \
      "$url" || true)
  elif [ -n "$data" ]; then
    HTTP_STATUS=$(curl -sS -o "$body_file" -w "%{http_code}" -X "$method" \
      -H "Content-Type: application/json" \
      -d "$data" \
      "$url" || true)
  else
    HTTP_STATUS=$(curl -sS -o "$body_file" -w "%{http_code}" -X "$method" \
      "$url" || true)
  fi

  echo "$body_file"
}

show() {
  local title="$1"
  local file="$2"
  echo
  echo "== $title =="
  echo "HTTP $HTTP_STATUS"
  if jq -e . "$file" >/dev/null 2>&1; then
    jq . "$file"
  else
    head -n 60 "$file"
    echo
    echo "(not JSON; first 60 lines shown)"
  fi
}

echo "== Base URL: $BASE_URL =="

# --- Register (ignore if already exists) ---
f=$(req POST "$BASE_URL/api/users/register/" "" "{\"username\":\"emma\",\"email\":\"emma@test.com\",\"password\":\"$PASS\"}")
show "Register emma" "$f"

f=$(req POST "$BASE_URL/api/users/register/" "" "{\"username\":\"alex\",\"email\":\"alex@test.com\",\"password\":\"$PASS\"}")
show "Register alex" "$f"

# --- Login emma ---
login_emma=$(req POST "$BASE_URL/api/auth/login/" "" "{\"username\":\"emma\",\"password\":\"$PASS\"}")
show "Login emma" "$login_emma"
EMMA_ACCESS=$(jq -r '.access // empty' "$login_emma")
[ -n "$EMMA_ACCESS" ] || { echo "Emma login failed"; exit 1; }

# --- Login alex ---
login_alex=$(req POST "$BASE_URL/api/auth/login/" "" "{\"username\":\"alex\",\"password\":\"$PASS\"}")
show "Login alex" "$login_alex"
ALEX_ACCESS=$(jq -r '.access // empty' "$login_alex")
[ -n "$ALEX_ACCESS" ] || { echo "Alex login failed"; exit 1; }

# --- me/ emma ---
me_emma=$(req GET "$BASE_URL/api/users/me/" "$EMMA_ACCESS")
show "Me emma" "$me_emma"
EMMA_ID=$(jq -r '.user_id' "$me_emma")

# --- me/ alex ---
me_alex=$(req GET "$BASE_URL/api/users/me/" "$ALEX_ACCESS")
show "Me alex" "$me_alex"
ALEX_ID=$(jq -r '.user_id' "$me_alex")

echo
echo "EMMA_ID=$EMMA_ID"
echo "ALEX_ID=$ALEX_ID"

# --- Patch profile emma ---
f=$(req PATCH "$BASE_URL/api/users/me/" "$EMMA_ACCESS" '{"bio":"Je suis fan des balades avec mon chien.","location":"Paris"}')
show "PATCH profile emma" "$f"

# --- Create animals ---
f=$(req POST "$BASE_URL/api/animals/me/" "$EMMA_ACCESS" '{"name":"Rex","species":"Dog","age":3}')
show "POST animal emma" "$f"

f=$(req POST "$BASE_URL/api/animals/me/" "$ALEX_ACCESS" '{"name":"Mina","species":"Cat","age":2}')
show "POST animal alex" "$f"

f=$(req GET "$BASE_URL/api/animals/me/" "$EMMA_ACCESS")
show "GET animals emma" "$f"

# --- Match ---
match=$(req POST "$BASE_URL/api/matches/" "$EMMA_ACCESS" "{\"receiver\": $ALEX_ID}")
show "POST match emma -> alex" "$match"
MATCH_ID=$(jq -r '.id // empty' "$match")
echo "MATCH_ID=$MATCH_ID"

f=$(req GET "$BASE_URL/api/matches/" "$ALEX_ACCESS")
show "GET matches alex" "$f"

if [ -n "$MATCH_ID" ]; then
  f=$(req PUT "$BASE_URL/api/matches/$MATCH_ID/" "$ALEX_ACCESS" '{"status":"accepted"}')
  show "PUT match accept (alex)" "$f"
fi

# --- Conversation + Messages ---
convo=$(req POST "$BASE_URL/api/messaging/conversations/" "$EMMA_ACCESS" "{\"participant_id\": $ALEX_ID}")
show "POST conversation emma+alex" "$convo"
CONVO_ID=$(jq -r '.id // .conversation_id // empty' "$convo")
echo "CONVO_ID=$CONVO_ID"
[ -n "$CONVO_ID" ] || { echo "Conversation failed"; exit 1; }

f=$(req POST "$BASE_URL/api/messaging/conversations/$CONVO_ID/messages/" "$EMMA_ACCESS" '{"content":"Salut Alex !"}')
show "POST message emma" "$f"

f=$(req POST "$BASE_URL/api/messaging/conversations/$CONVO_ID/messages/" "$ALEX_ACCESS" '{"content":"Salut Emma ! Ça va ?"}')
show "POST message alex" "$f"

f=$(req GET "$BASE_URL/api/messaging/conversations/$CONVO_ID/messages/" "$ALEX_ACCESS")
show "GET messages alex" "$f"

echo
echo "✅ Tests finished."
