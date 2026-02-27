#!/bin/bash
# Simple test hook script for anvil's own fixtures.
# Reads event JSON from stdin, blocks "rm -rf" commands.
EVENT=$(cat)
TOOL=$(echo "$EVENT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

if echo "$TOOL" | grep -q "rm -rf"; then
    echo "blocked: dangerous command detected" >&2
    exit 2
fi
exit 0
