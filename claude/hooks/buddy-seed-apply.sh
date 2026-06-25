#!/bin/bash
# Re-apply custom buddy seed on session start.
# Claude Code overwrites oauthAccountUuid from the server on every startup,
# so this hook patches it back to the desired seed.

SEED="118a6b0b-9730-4d88-976b-e6c62fd2a4e1"
SETTINGS_FILE="$HOME/.claude.json"

if [ ! -f "$SETTINGS_FILE" ]; then
  exit 0
fi

CURRENT_UUID=$(python3 -c "
import json
with open('$SETTINGS_FILE') as f:
    data = json.load(f)
print(data.get('oauthAccount', {}).get('accountUuid', ''))
" 2>/dev/null)

if [ "$CURRENT_UUID" = "$SEED" ]; then
  exit 0
fi

python3 -c "
import json

settings_file = '$SETTINGS_FILE'
seed = '$SEED'

with open(settings_file) as f:
    data = json.load(f)

if 'oauthAccount' in data:
    data['oauthAccount']['accountUuid'] = seed

with open(settings_file, 'w') as f:
    json.dump(data, f, indent=2)
" 2>/dev/null

echo "Buddy seed re-applied: $SEED (Hermes - Legendary Shiny Cat)"
