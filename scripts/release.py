#!/usr/bin/env python3

import json, os, subprocess, sys, re

def get_version():
    """Get version from pyproject.toml"""
    with open('pyproject.toml', 'r') as f:
        content = f.read()
        match = re.search(r'version = "([^"]+)"', content)
        if match:
            return match.group(1)
    return None

def get_current_branch():
    """Get current git branch"""
    result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                          capture_output=True, text=True)
    return result.stdout.strip()

def has_uncommitted_changes():
    """Check if there are uncommitted changes"""
    result = subprocess.run(['git', 'status', '--porcelain'], 
                          capture_output=True, text=True)
    return bool(result.stdout.strip())

def main():
    # Check we're on main branch
    branch = get_current_branch()
    if branch != 'main':
        print(f'✖ Must be on main branch, currently on {branch}')
        sys.exit(1)
    
    # Check for uncommitted changes
    if has_uncommitted_changes():
        print('✖ You have uncommitted changes. Commit them first.')
        sys.exit(1)
    
    # Get version
    version = get_version()
    if not version:
        print('✖ Could not determine version from pyproject.toml')
        sys.exit(1)
    
    print(f'📦 Creating release v{version}')
    
    # Confirm
    response = input(f'Create release v{version}? (y/N): ')
    if response.lower() != 'y':
        print('Release cancelled.')
        sys.exit(0)
    
    # Create and push tag
    tag = f'v{version}'
    print(f'🏷️  Creating tag {tag}')
    subprocess.run(['git', 'tag', tag], check=True)
    subprocess.run(['git', 'push', 'origin', 'main'], check=True)
    subprocess.run(['git', 'push', 'origin', tag], check=True)
    
    print(f'✅ Tag {tag} created and pushed')
    print(f'📝 Next steps:')
    print(f'   1. Go to https://github.com/davefowler/melcurial/releases')
    print(f'   2. Click "Create a new release"')
    print(f'   3. Choose tag {tag}')
    print(f'   4. Upload the mel script as an asset named "mel"')
    print(f'   5. Add release notes and publish')

if __name__ == '__main__':
    main()
