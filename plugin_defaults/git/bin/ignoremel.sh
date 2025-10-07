#!/bin/bash
# Add .mel to .gitignore if needed

set -euo pipefail

if git status --porcelain | grep -q "^?? .mel/"; then
  echo "📝 Adding .mel/ to .gitignore..."
  if [[ -f ".gitignore" ]]; then
    if ! grep -q "^\\.mel/$" .gitignore; then
      echo ".mel/" >> .gitignore
      echo "✓ Added .mel/ to .gitignore"
    else
      echo "✓ .mel/ already in .gitignore"
    fi
  else
    echo ".mel/" > .gitignore
    echo "✓ Created .gitignore with .mel/"
  fi
else
  echo "✓ .mel/ already ignored or no untracked files"
fi


