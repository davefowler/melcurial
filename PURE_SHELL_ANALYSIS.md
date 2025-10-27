# Pure Shell Mel Analysis: Can We Eliminate Python?

## Current Python Dependencies Analysis

### Python Standard Library Usage
```python
import json, os, subprocess, sys, datetime, shlex, re, platform, urllib.request, urllib.error
```

### What Each Module Does in Current Mel

#### 1. **json** - JSON parsing/writing
- **Usage**: Loading/saving `.mel/config.json`, `package.json`
- **Shell Alternative**: `jq` command-line tool
- **Status**: ✅ **Replaceable with shell + jq**

#### 2. **datetime** - Timestamp generation
- **Usage**: `datetime.now().strftime("%Y-%m-%d %H:%M")` for commit messages
- **Shell Alternative**: `date` command
- **Status**: ✅ **Replaceable with shell**

#### 3. **platform** - OS detection
- **Usage**: `platform.system().lower()` for opening URLs
- **Shell Alternative**: `uname -s` or `$OSTYPE`
- **Status**: ✅ **Replaceable with shell**

#### 4. **urllib.request** - HTTP requests
- **Usage**: GitHub API calls for upgrade functionality
- **Shell Alternative**: `curl` or `wget`
- **Status**: ✅ **Replaceable with shell**

#### 5. **tempfile** - Temporary files
- **Usage**: Creating temp files during upgrade
- **Shell Alternative**: `mktemp`
- **Status**: ✅ **Replaceable with shell**

#### 6. **random** - Random number generation
- **Usage**: `random.randint(1, 3)` for update check frequency
- **Shell Alternative**: `$RANDOM` or `/dev/urandom`
- **Status**: ✅ **Replaceable with shell**

#### 7. **re** - Regular expressions
- **Usage**: URL parsing, branch name sanitization
- **Shell Alternative**: `sed`, `grep`, `awk`
- **Status**: ✅ **Replaceable with shell**

#### 8. **shlex** - Shell escaping
- **Usage**: `shlex.quote()` for safe argument passing
- **Shell Alternative**: Shell built-in quoting
- **Status**: ✅ **Replaceable with shell**

## Pure Shell Implementation

### Core Mel Script (Pure Bash)
```bash
#!/bin/bash
# mel - Pure shell script runner

set -euo pipefail

# Configuration
VERSION="0.1.0"
CONFIG_DIR=".mel"
CONFIG_FILE="$CONFIG_DIR/config.json"

# Detect VCS
detect_vcs() {
    if [[ -d ".git" ]]; then
        echo "git"
    elif [[ -d ".hg" ]]; then
        echo "hg"
    elif [[ -d ".svn" ]]; then
        echo "svn"
    else
        echo "none"
    fi
}

# Load configuration
load_config() {
    local vcs="$1"
    local config_path=""
    
    # Try user config first
    if [[ -f "$CONFIG_FILE" ]]; then
        config_path="$CONFIG_FILE"
    else
        # Try VCS defaults
        if [[ -f "configs/${vcs}_defaults.json" ]]; then
            config_path="configs/${vcs}_defaults.json"
        fi
    fi
    
    if [[ -n "$config_path" ]]; then
        cat "$config_path"
    else
        echo "{}"
    fi
}

# Get JSON value (requires jq)
get_json_value() {
    local json="$1"
    local key="$2"
    echo "$json" | jq -r ".$key // empty"
}

# Get current timestamp
get_timestamp() {
    date "+%Y-%m-%d %H:%M"
}

# Get current branch
get_current_branch() {
    local vcs="$1"
    case "$vcs" in
        "git")
            git rev-parse --abbrev-ref HEAD
            ;;
        "hg")
            hg branch
            ;;
        *)
            echo "main"
            ;;
    esac
}

# Get repo root
get_repo_root() {
    local vcs="$1"
    case "$vcs" in
        "git")
            git rev-parse --show-toplevel
            ;;
        "hg")
            hg root
            ;;
        *)
            pwd
            ;;
    esac
}

# Execute command with safety checks
execute_command() {
    local config="$1"
    local command="$2"
    shift 2
    local args=("$@")
    
    # Get command configuration
    local cmd_config
    cmd_config=$(echo "$config" | jq -r ".scripts.\"$command\" // empty")
    
    if [[ -z "$cmd_config" ]]; then
        echo "✖ Command '$command' not found"
        exit 1
    fi
    
    # Get command string
    local cmd_string
    cmd_string=$(echo "$cmd_config" | jq -r '.cmd // empty')
    
    if [[ -z "$cmd_string" ]]; then
        echo "✖ Command '$command' has no 'cmd' field"
        exit 1
    fi
    
    # Variable substitution
    local vcs
    vcs=$(detect_vcs)
    local timestamp
    timestamp=$(get_timestamp)
    local current_branch
    current_branch=$(get_current_branch "$vcs")
    
    # Replace variables in command
    cmd_string=$(echo "$cmd_string" | sed "s/{timestamp}/$timestamp/g")
    cmd_string=$(echo "$cmd_string" | sed "s/{branch}/$current_branch/g")
    cmd_string=$(echo "$cmd_string" | sed "s/{main}/main/g")
    
    # Add arguments if provided
    if [[ ${#args[@]} -gt 0 ]]; then
        cmd_string="$cmd_string ${args[*]}"
    fi
    
    # Execute command
    echo "→ $cmd_string"
    eval "$cmd_string"
}

# Explain command
explain_command() {
    local config="$1"
    local command="$2"
    
    local cmd_config
    cmd_config=$(echo "$config" | jq -r ".scripts.\"$command\" // empty")
    
    if [[ -z "$cmd_config" ]]; then
        echo "✖ Command '$command' not found"
        exit 1
    fi
    
    echo "Command: $command"
    echo "Description: $(echo "$cmd_config" | jq -r '.description // "No description"')"
    echo "Usage: $(echo "$cmd_config" | jq -r '.usage // "No usage info"')"
    echo ""
    echo "Commands that will be executed:"
    echo "$cmd_config" | jq -r '.commands[]?' | while read -r cmd; do
        echo "  $cmd"
    done
}

# Generate help
generate_help() {
    local config="$1"
    local mode="${2:-basic}"
    
    echo "mel — a simpler git abstraction so non-engineers can contribute"
    echo ""
    echo "Basic commands:"
    
    # Filter commands by mode
    echo "$config" | jq -r ".scripts | to_entries[] | select(.value.mode == \"$mode\" or .value.mode == \"both\") | \"  mel \(.key)        \(.value.description // \"No description\")\"" | sort
}

# Main function
main() {
    local vcs
    vcs=$(detect_vcs)
    
    if [[ "$vcs" == "none" ]]; then
        echo "✖ No version control system detected"
        exit 1
    fi
    
    local config
    config=$(load_config "$vcs")
    
    if [[ $# -eq 0 ]]; then
        generate_help "$config"
        exit 0
    fi
    
    local command="$1"
    shift
    
    case "$command" in
        "help"|"-h"|"--help")
            generate_help "$config"
            ;;
        "explain")
            if [[ $# -eq 0 ]]; then
                echo "Usage: mel explain <command>"
                exit 1
            fi
            explain_command "$config" "$1"
            ;;
        "version"|"-v"|"--version")
            echo "mel $VERSION"
            ;;
        *)
            execute_command "$config" "$command" "$@"
            ;;
    esac
}

# Run main function
main "$@"
```

## Dependencies for Pure Shell Version

### Required External Tools
1. **jq** - JSON parsing (widely available)
2. **git/hg/svn** - Version control (already required)
3. **curl** - HTTP requests (for upgrade functionality)
4. **Standard Unix tools** - `date`, `sed`, `grep`, `awk` (universally available)

### Installation Check
```bash
# Check for required tools
check_dependencies() {
    local missing=()
    
    if ! command -v jq &> /dev/null; then
        missing+=("jq")
    fi
    
    if ! command -v curl &> /dev/null; then
        missing+=("curl")
    fi
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "✖ Missing required tools: ${missing[*]}"
        echo "Please install:"
        for tool in "${missing[@]}"; do
            case "$tool" in
                "jq")
                    echo "  - jq: https://stedolan.github.io/jq/"
                    ;;
                "curl")
                    echo "  - curl: Usually pre-installed"
                    ;;
            esac
        done
        exit 1
    fi
}
```

## Benefits of Pure Shell Implementation

### 1. **Zero Python Dependencies**
- No Python installation required
- No pip/pipx needed
- Works on any Unix-like system

### 2. **Faster Startup**
- No Python interpreter startup
- No module imports
- Near-instant execution

### 3. **Smaller Distribution**
- Single shell script (~200 lines)
- No Python runtime
- Minimal external dependencies

### 4. **Better Integration**
- Native shell environment
- Direct access to shell variables
- Seamless with existing shell workflows

### 5. **Easier Debugging**
- Standard shell debugging tools
- No Python stack traces
- Simple command execution

## Limitations of Pure Shell

### 1. **JSON Handling**
- Requires `jq` external dependency
- More complex JSON operations
- Less robust error handling

### 2. **Cross-Platform Compatibility**
- Shell differences (bash vs zsh vs dash)
- Different `date` command formats
- Platform-specific tools

### 3. **Complex Logic**
- Harder to implement complex validation
- Limited data structures
- More verbose error handling

### 4. **Parameter Validation**
- Basic type checking only
- Limited validation rules
- Manual error messages

## Hybrid Approach (Recommended)

### Core: Pure Shell + Python for Complex Features

```bash
#!/bin/bash
# mel - Hybrid shell/Python runner

# Core functionality in shell
detect_vcs() { ... }
load_config() { ... }
execute_command() { ... }

# Complex features in Python
if [[ "$1" == "upgrade" ]]; then
    python3 -c "
import sys, os
sys.path.insert(0, os.path.dirname('$0'))
from mel_upgrade import upgrade_mel
upgrade_mel()
"
    exit $?
fi

# Rest of shell implementation...
```

### File Structure
```
mel (shell script - main entry point)
├── mel_upgrade.py          # Python for upgrade functionality
├── mel_validate.py         # Python for parameter validation
├── configs/
│   ├── git_defaults.json
│   └── hg_defaults.json
└── docs/                   # Separate documentation system
    ├── generate.py         # Python for doc generation
    └── serve.py           # Python for doc server
```

## Recommendation: Pure Shell Core

### **Go with Pure Shell for Core Functionality**

**Why:**
1. **Zero Python dependencies** for basic usage
2. **Faster startup** and execution
3. **Simpler distribution** and installation
4. **Better shell integration**

**Implementation:**
- **Core mel**: Pure shell script (~200 lines)
- **Complex features**: Optional Python modules
- **Documentation**: Separate Python package
- **Dependencies**: Only `jq` (widely available)

**User Experience:**
```bash
# Basic usage - no Python needed
mel save "my changes"
mel status
mel explain save

# Advanced features - Python modules
mel upgrade          # Uses mel_upgrade.py
mel docs            # Uses separate docs package
```

This gives us the best of both worlds: a fast, dependency-free core with optional Python features for complex functionality.

## Documentation Separation

### Separate Documentation Package
```bash
# Install docs separately
pip install mel-docs

# Or use standalone
mel-docs generate
mel-docs serve
```

### Benefits
- **Core mel**: Zero dependencies
- **Documentation**: Rich Python features
- **Optional**: Users choose what they need
- **Maintainable**: Separate concerns

This approach aligns perfectly with your vision of a super minimal core with optional enhancements.
