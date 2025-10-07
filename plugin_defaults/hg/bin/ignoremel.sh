#!/bin/bash
# Add .mel to .hgignore if needed

set -euo pipefail

if [[ -f ".hgignore" ]]; then
  if ! grep -q '^\.mel/$' .hgignore; then
    echo ".mel/" >> .hgignore
    echo "✓ Added .mel/ to .hgignore"
  else
    echo "✓ .mel/ already in .hgignore"
  fi
else
  echo ".mel/" > .hgignore
  echo "✓ Created .hgignore with .mel/"
fi


