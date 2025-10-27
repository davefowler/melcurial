# Mel Plugin System Design

## Plugin Architecture Overview

### Core Philosophy
- **Minimal core**: Mel remains a simple shell script
- **Plugin-based extensions**: Rich functionality through plugins
- **JSON configuration**: Plugins extend configuration via JSON files
- **Hook system**: Plugins can intercept and enhance command execution
- **Easy installation**: Simple plugin management commands

## Plugin Types

### 1. **Configuration Plugins** (Simple)
**Purpose**: Add new commands, modify existing ones, extend configuration
**Implementation**: JSON files that get merged into main config
**Examples**: Custom workflows, team-specific commands, VCS extensions

### 2. **Hook Plugins** (Advanced)
**Purpose**: Intercept command execution, add functionality, modify behavior
**Implementation**: Executable scripts that receive hook events
**Examples**: `mel-assistant`, logging, notifications, validation

### 3. **Command Plugins** (Hybrid)
**Purpose**: Add new commands that integrate with Mel's workflow
**Implementation**: Executable scripts + JSON configuration
**Examples**: `mel-docs`, `mel-backup`, `mel-sync`

## Plugin System Design

### File Structure
```
mel (core shell script - minimal launcher)
└── .mel/
    ├── config.json           # User config with plugin list
    ├── config_template.json  # Template config (can be in version control)
    └── plugins/              # All installed plugins
        ├── core/             # Core Mel functionality
        │   ├── config.json   # Core commands (help, version, etc.)
        │   └── bin/          # Core scripts
        ├── git/              # Git plugin (auto-installed)
        │   ├── config.json   # Git command definitions
        │   └── bin/          # Git-specific scripts (if needed)
        ├── hg/               # Mercurial plugin (auto-installed)
        │   ├── config.json   # Mercurial command definitions
        │   └── bin/          # Mercurial-specific scripts
        ├── mel-assistant/
        │   ├── config.json   # AI assistant configuration
        │   ├── hooks/        # Hook scripts
        │   └── bin/          # Executable commands
        └── mel-docs/
            ├── config.json   # Documentation configuration
            └── bin/          # Documentation scripts
```

### User Configuration (`.mel/config.json`)
```json
{
  "plugins": [
    "core",
    "git",
    "mel-assistant"
  ],
  "scripts": {
    "save": {
      "description": "My custom save command",
      "commands": ["echo 'Custom save'", "git add -A", "git commit -m \"{message}\""]
    }
  },
  "hooks": {
    "pre_save": [
      "echo 'User pre-save hook'"
    ]
  }
}
```

### Template Configuration (`.mel/config_template.json`)
```json
{
  "plugins": [
    "core",
    "git",
    "mel-docs"
  ],
  "scripts": {
    "test": "pytest -q --disable-warnings",
    "build": "npm run build -s"
  },
  "allow_package_scripts": true,
  "require_add_confirmation": true
}
```

### Core Plugin (`.mel/plugins/core/config.json`)
```json
{
  "scripts": {
    "help": {
      "description": "Show help information",
      "help_text": "Display available commands and usage information",
      "usage": "mel help [--all] [--mode basic|advanced]",
      "mode": "both",
      "commands": [
        ".mel/plugins/core/bin/help.sh"
      ]
    },
    "version": {
      "description": "Show version information",
      "help_text": "Display Mel version and executable path",
      "usage": "mel version",
      "mode": "both",
      "commands": [
        "echo 'mel 0.1.0'",
        "echo 'path: $(which mel)'"
      ]
    },
    "plugin": {
      "description": "Manage plugins",
      "help_text": "Install, remove, and manage Mel plugins",
      "usage": "mel plugin <command> [plugin-name]",
      "mode": "advanced",
      "commands": [
        ".mel/plugins/core/bin/plugin.sh"
      ]
    }
  }
}
```

### Git Plugin (`.mel/plugins/git/config.json`)
```json
{
  "scripts": {
    "save": {
      "description": "Save changes and sync with main",
      "help_text": "Commits your changes, fetches latest from main, rebases your branch, and pushes to remote",
      "usage": "mel save \"your commit message\"",
      "mode": "basic",
      "commands": [
        "git add -A",
        "git commit -m \"{message}\"",
        "git fetch origin",
        "git rebase origin/{main}",
        "git push origin HEAD"
      ],
      "safety_checks": ["not_on_main", "clean_working_tree"],
      "requires_message": true,
      "confirmation_required": false
    },
    "publish": {
      "description": "Merge to main and push",
      "help_text": "Merges your branch to main using fast-forward merge, then updates your branch",
      "usage": "mel publish",
      "mode": "basic",
      "commands": [
        "git checkout {main}",
        "git merge --ff-only {branch}",
        "git push origin {main}",
        "git checkout {branch}",
        "git rebase origin/{main}"
      ],
      "safety_checks": ["not_on_main", "has_remote"],
      "confirmation_required": true
    }
  }
}
```

### Plugin Configuration (`.mel/plugins/mel-assistant/config.json`)
```json
{
  "scripts": {
    "assist": {
      "description": "Get AI assistance with current situation",
      "help_text": "Analyzes your current git state and provides AI-powered guidance",
      "usage": "mel assist [question]",
      "mode": "advanced",
      "commands": [
        "python3 .mel/plugins/mel-assistant/bin/assist.py"
      ],
      "parameters": {
        "question": {
          "type": "string",
          "required": false,
          "description": "Specific question to ask the assistant"
        }
      }
    }
  },
  "hooks": {
    "pre_command": [
      ".mel/plugins/mel-assistant/hooks/pre_command"
    ],
    "post_command": [
      ".mel/plugins/mel-assistant/hooks/post_command"
    ],
    "on_error": [
      ".mel/plugins/mel-assistant/hooks/on_error"
    ]
  },
  "config": {
    "openai_api_key": {
      "type": "string",
      "required": true,
      "description": "OpenAI API key for AI assistance"
    }
  }
}
```

## Plugin Management Commands

### Core Plugin Commands (Built into Mel)
```bash
# List installed plugins
mel plugin list

# Install a plugin
mel plugin install mel-assistant

# Remove a plugin
mel plugin remove mel-assistant

# Update plugins
mel plugin update
mel plugin update mel-assistant
```

### Plugin Installation Process
```bash
mel plugin install mel-assistant
# 1. Download plugin from registry
# 2. Install to .mel/plugins/mel-assistant/
# 3. Install dependencies (pip install -r requirements.txt)
# 4. Plugin is immediately active (no enable/disable)
```

## Hook System

### Hook Types
```bash
# Pre-command hooks
pre_command <command> <args...>

# Post-command hooks  
post_command <command> <exit_code> <output>

# Error hooks
on_error <command> <error_message> <context>

# Configuration hooks
on_config_change <config_path>

# VCS hooks
on_branch_change <old_branch> <new_branch>
```

### Hook Implementation
```bash
# plugins/installed/mel-assistant/hooks/on_error
#!/bin/bash
# Hook script for error handling

COMMAND="$1"
ERROR_MESSAGE="$2"
CONTEXT="$3"

# Log the error
echo "$(date): $COMMAND failed: $ERROR_MESSAGE" >> ~/.mel/assistant.log

# If it's a git error, offer assistance
if [[ "$ERROR_MESSAGE" == *"git"* ]]; then
    echo "🤖 Mel Assistant detected a git error. Run 'mel assist' for help."
fi
```

### Hook Registration in Core Mel
```bash
# In core mel script
execute_hooks() {
    local hook_type="$1"
    shift
    
    # Find all enabled plugins with this hook
    for plugin_dir in plugins/enabled/*/; do
        if [[ -f "$plugin_dir/hooks/$hook_type" ]]; then
            if [[ -x "$plugin_dir/hooks/$hook_type" ]]; then
                "$plugin_dir/hooks/$hook_type" "$@"
            fi
        fi
    done
}

# Usage in command execution
execute_command() {
    local config="$1" command="$2"
    shift 2
    
    # Pre-command hook
    execute_hooks "pre_command" "$command" "$@"
    
    # Execute command
    local exit_code=0
    local output=""
    output=$(eval "$cmd_string" 2>&1) || exit_code=$?
    
    # Post-command hook
    execute_hooks "post_command" "$command" "$exit_code" "$output"
    
    # Error hook if failed
    if [[ $exit_code -ne 0 ]]; then
        execute_hooks "on_error" "$command" "$output" "$(get_context)"
    fi
    
    return $exit_code
}
```

## Plugin Examples

### 1. Mel Assistant Plugin

#### Installation
```bash
mel plugin install mel-assistant
# Prompts for OpenAI API key
# Installs Python dependencies
# Enables hooks
```

#### Usage
```bash
# Get general assistance
mel assist

# Ask specific question
mel assist "How do I resolve this merge conflict?"

# Explain last error
mel explain-error

# Automatic error detection (via hooks)
mel save "my changes"
# → Git error occurs
# → Hook triggers: "🤖 Mel Assistant detected a git error. Run 'mel assist' for help."
```

#### Implementation
```python
# plugins/installed/mel-assistant/bin/assist.py
#!/usr/bin/env python3
import sys
import json
import subprocess
from openai import OpenAI

def get_git_status():
    """Get current git status for context"""
    result = subprocess.run(['git', 'status', '--porcelain'], 
                          capture_output=True, text=True)
    return result.stdout

def get_recent_errors():
    """Get recent error logs"""
    try:
        with open('~/.mel/assistant.log', 'r') as f:
            return f.read()
    except:
        return "No recent errors"

def main():
    question = sys.argv[1] if len(sys.argv) > 1 else ""
    
    # Load plugin config
    with open('~/.mel/plugins/mel-assistant/config.json', 'r') as f:
        config = json.load(f)
    
    # Get context
    git_status = get_git_status()
    recent_errors = get_recent_errors()
    
    # Call OpenAI API
    client = OpenAI(api_key=config['openai_api_key'])
    
    prompt = f"""
    You are Mel Assistant, helping users with git and Mel commands.
    
    Current git status:
    {git_status}
    
    Recent errors:
    {recent_errors}
    
    User question: {question}
    
    Provide helpful, specific guidance for resolving their issue.
    """
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    print("🤖 Mel Assistant:")
    print(response.choices[0].message.content)
```

### 2. Mel Docs Plugin

#### Installation
```bash
mel plugin install mel-docs
# Installs Jinja2, creates docs templates
# Adds 'docs' command to mel
```

#### Usage
```bash
# Generate and serve docs
mel docs

# Generate static docs
mel docs --generate --output ./docs/

# Watch mode
mel docs --watch
```

#### Implementation
```json
{
  "docs": {
    "description": "Generate and serve documentation",
    "help_text": "Creates documentation for your current Mel configuration",
    "usage": "mel docs [--generate] [--output DIR] [--watch]",
    "mode": "advanced",
    "commands": [
      "python3 plugins/enabled/mel-docs/bin/docs_server.py"
    ],
    "parameters": {
      "generate": {
        "type": "boolean",
        "default": false,
        "description": "Generate static files instead of serving"
      },
      "output": {
        "type": "string",
        "default": "./docs/",
        "description": "Output directory for generated docs"
      },
      "watch": {
        "type": "boolean", 
        "default": false,
        "description": "Watch for config changes and auto-reload"
      }
    }
  }
}
```

## Plugin Registry

### Registry Structure
```json
{
  "plugins": {
    "mel-assistant": {
      "name": "mel-assistant",
      "version": "1.0.0",
      "description": "AI assistant for Mel command errors and guidance",
      "author": "Mel Team",
      "repository": "https://github.com/mel-plugins/mel-assistant",
      "download_url": "https://github.com/mel-plugins/mel-assistant/releases/download/v1.0.0/mel-assistant.tar.gz",
      "dependencies": {
        "python": ">=3.8",
        "packages": ["openai", "requests"]
      },
      "tags": ["ai", "assistance", "error-handling"]
    },
    "mel-docs": {
      "name": "mel-docs", 
      "version": "1.0.0",
      "description": "Generate and serve Mel documentation",
      "author": "Mel Team",
      "repository": "https://github.com/mel-plugins/mel-docs",
      "download_url": "https://github.com/mel-plugins/mel-docs/releases/download/v1.0.0/mel-docs.tar.gz",
      "dependencies": {
        "python": ">=3.8",
        "packages": ["jinja2", "watchdog"]
      },
      "tags": ["documentation", "web", "generation"]
    }
  }
}
```

### Registry Management
```bash
# Update plugin registry
mel plugin registry update

# Search plugins
mel plugin search "ai"
mel plugin search "docs"

# Show plugin info
mel plugin info mel-assistant
```

## Configuration Merging

### Merge Strategy: Append vs Overwrite

Different configuration sections need different merge strategies:

#### **Overwrite Strategy** (Default)
- `scripts` - Commands are overwritten (user can override plugin commands)
- `config` - Settings are overwritten (user config takes precedence)

#### **Append Strategy** (Explicit)
- `hooks` - Hook arrays are appended (multiple plugins can add hooks)
- `pre_save`, `post_save` - Hook arrays are appended

### Configuration Merge Implementation
```bash
# Core mel script - load and merge configurations
load_merged_config() {
    local merged_config="{}"
    
    # Load user config to get plugin list
    local user_config="{}"
    if [[ -f ".mel/config.json" ]]; then
        user_config=$(cat ".mel/config.json")
    fi
    
    # Get list of plugins to load (from user config)
    local plugins
    plugins=$(echo "$user_config" | jq -r '.plugins[]?' 2>/dev/null || echo "")
    
    # Merge plugin configurations in order (append hooks, overwrite scripts)
    for plugin in $plugins; do
        local plugin_dir=".mel/plugins/$plugin"
        if [[ -f "$plugin_dir/config.json" ]]; then
            # Merge scripts (overwrite)
            merged_config=$(echo "$merged_config" | jq '.scripts * input.scripts' "$plugin_dir/config.json")
            
            # Merge hooks (append)
            merged_config=$(echo "$merged_config" | jq '.hooks = (.hooks // {}) * input.hooks | .hooks |= with_entries(.value = (.value // []) + (input.hooks[.key] // []))' "$plugin_dir/config.json")
            
            # Merge config settings (overwrite)
            merged_config=$(echo "$merged_config" | jq '.config * input.config' "$plugin_dir/config.json")
        fi
    done
    
    # Merge user configuration (highest priority - overwrites everything)
    merged_config=$(echo "$merged_config" | jq '. * input' <(echo "$user_config"))
    
    echo "$merged_config"
}
```

### VCS Detection and Auto-Installation
```bash
# Detect VCS and auto-install plugin
detect_vcs_and_install() {
    local vcs=""
    
    if [[ -d ".git" ]]; then
        vcs="git"
    elif [[ -d ".hg" ]]; then
        vcs="hg"
    elif [[ -d ".svn" ]]; then
        vcs="svn"
    else
        echo "✖ No version control system detected"
        exit 1
    fi
    
    # Auto-install VCS plugin if not present
    if [[ ! -d ".mel/plugins/$vcs" ]]; then
        echo "📦 Installing $vcs plugin..."
        mel plugin install "$vcs"
    fi
    
    # Add to user config if not present
    local user_config="{}"
    if [[ -f ".mel/config.json" ]]; then
        user_config=$(cat ".mel/config.json")
    fi
    
    local has_vcs_plugin
    has_vcs_plugin=$(echo "$user_config" | jq -r ".plugins[]? | select(. == \"$vcs\")" 2>/dev/null)
    
    if [[ -z "$has_vcs_plugin" ]]; then
        echo "📝 Adding $vcs plugin to configuration..."
        user_config=$(echo "$user_config" | jq ".plugins = (.plugins // []) + [\"$vcs\"]")
        echo "$user_config" > ".mel/config.json"
    fi
    
    echo "$vcs"
}
```

### Template Configuration Processing
```bash
# Process template configuration on first run
process_template_config() {
    if [[ -f ".mel/config_template.json" ]]; then
        echo "📋 Found template configuration..."
        
        local template_config
        template_config=$(cat ".mel/config_template.json")
        
        # Install plugins from template
        local template_plugins
        template_plugins=$(echo "$template_config" | jq -r '.plugins[]?' 2>/dev/null || echo "")
        
        for plugin in $template_plugins; do
            if [[ ! -d ".mel/plugins/$plugin" ]]; then
                echo "📦 Installing plugin from template: $plugin"
                mel plugin install "$plugin"
            fi
        done
        
        # Merge template config into user config
        local user_config="{}"
        if [[ -f ".mel/config.json" ]]; then
            user_config=$(cat ".mel/config.json")
        fi
        
        # Merge template (lower priority than existing user config)
        user_config=$(echo "$user_config" | jq '. * input' <(echo "$template_config"))
        echo "$user_config" > ".mel/config.json"
        
        echo "✓ Template configuration applied"
    fi
}
```

### Example Configuration Merging

#### User Config (`.mel/config.json`)
```json
{
  "plugins": [
    "core",
    "git", 
    "mel-assistant"
  ],
  "scripts": {
    "save": {
      "description": "My custom save command",
      "commands": ["echo 'Custom save'", "git add -A", "git commit -m \"{message}\""]
    }
  },
  "hooks": {
    "pre_save": [
      "echo 'User pre-save hook'"
    ]
  }
}
```

#### Core Plugin (`.mel/plugins/core/config.json`)
```json
{
  "scripts": {
    "help": {
      "description": "Show help information",
      "commands": [".mel/plugins/core/bin/help.sh"]
    },
    "version": {
      "description": "Show version information", 
      "commands": ["echo 'mel 0.1.0'"]
    }
  }
}
```

#### Git Plugin (`.mel/plugins/git/config.json`)
```json
{
  "scripts": {
    "save": {
      "description": "Save changes and sync with main",
      "commands": ["git add -A", "git commit -m \"{message}\""]
    },
    "publish": {
      "description": "Merge to main and push",
      "commands": ["git checkout {main}", "git merge --ff-only {branch}"]
    }
  },
  "hooks": {
    "pre_save": []
  }
}
```

#### Mel Assistant Plugin (`.mel/plugins/mel-assistant/config.json`)
```json
{
  "scripts": {
    "assist": {
      "description": "Get AI assistance",
      "commands": ["python3 .mel/plugins/mel-assistant/bin/assist.py"]
    }
  },
  "hooks": {
    "pre_save": [
      ".mel/plugins/mel-assistant/hooks/pre_save"
    ],
    "on_error": [
      ".mel/plugins/mel-assistant/hooks/on_error"
    ]
  }
}
```

#### Final Merged Config
```json
{
  "scripts": {
    "help": {
      "description": "Show help information",
      "commands": [".mel/plugins/core/bin/help.sh"]
    },
    "version": {
      "description": "Show version information",
      "commands": ["echo 'mel 0.1.0'"]
    },
    "save": {
      "description": "My custom save command",
      "commands": ["echo 'Custom save'", "git add -A", "git commit -m \"{message}\""]
    },
    "publish": {
      "description": "Merge to main and push", 
      "commands": ["git checkout {main}", "git merge --ff-only {branch}"]
    },
    "assist": {
      "description": "Get AI assistance",
      "commands": ["python3 .mel/plugins/mel-assistant/bin/assist.py"]
    }
  },
  "hooks": {
    "pre_save": [
      ".mel/plugins/mel-assistant/hooks/pre_save",
      "echo 'User pre-save hook'"
    ],
    "on_error": [
      ".mel/plugins/mel-assistant/hooks/on_error"
    ]
  }
}
```

### Hook Execution Order
Hooks are executed in the order they appear in the merged array:
1. Plugin hooks first
2. User hooks last (highest priority)

## Minimal Mel Launcher

### Core Mel Script (Minimal)
```bash
#!/bin/bash
# mel - Minimal script runner launcher

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MEL_DIR="$SCRIPT_DIR/.mel"

# Initialize Mel if needed
init_mel() {
    if [[ ! -d "$MEL_DIR" ]]; then
        echo "🚀 Initializing Mel..."
        mkdir -p "$MEL_DIR/plugins"
        
        # Create initial config
        cat > "$MEL_DIR/config.json" << 'EOF'
{
  "plugins": ["core"]
}
EOF
        
        # Install core plugin
        mel plugin install core
        
        # Process template config if present
        process_template_config
        
        # Detect VCS and install plugin
        detect_vcs_and_install
        
        echo "✓ Mel initialized successfully"
    fi
}

# Main execution
main() {
    # Initialize if needed
    init_mel
    
    # Load merged configuration
    local config
    config=$(load_merged_config)
    
    # Parse arguments
    local command="$1"
    shift || true
    
    # Execute command
    execute_command "$config" "$command" "$@"
}

# Execute command from merged config
execute_command() {
    local config="$1"
    local command="$2"
    shift 2 || true
    
    # Get command definition
    local cmd_def
    cmd_def=$(echo "$config" | jq -r ".scripts[\"$command\"]" 2>/dev/null)
    
    if [[ "$cmd_def" == "null" || -z "$cmd_def" ]]; then
        echo "✖ Unknown command: $command"
        echo "Run 'mel help' for available commands"
        exit 1
    fi
    
    # Execute hooks
    execute_hooks "$config" "pre_command" "$command" "$@"
    
    # Execute command
    local commands
    commands=$(echo "$cmd_def" | jq -r '.commands[]?' 2>/dev/null)
    
    for cmd in $commands; do
        eval "$cmd"
    done
    
    # Execute hooks
    execute_hooks "$config" "post_command" "$command" "$@"
}

# Execute hooks
execute_hooks() {
    local config="$1"
    local hook_type="$2"
    shift 2 || true
    
    local hooks
    hooks=$(echo "$config" | jq -r ".hooks[\"$hook_type\"]?[]?" 2>/dev/null || echo "")
    
    for hook in $hooks; do
        if [[ -f "$hook" ]]; then
            bash "$hook" "$@"
        else
            eval "$hook"
        fi
    done
}

# Run main function
main "$@"
```

### Installation Process

#### User Installation
```bash
# Install Mel
curl -sSL https://install.mel.sh | bash

# This creates:
# - /usr/local/bin/mel (symlink to ~/.mel/mel)
# - ~/.mel/ directory structure
# - Core plugin installation
```

#### Project Setup
```bash
# In a project directory
echo '{
  "plugins": ["core", "git", "mel-docs"],
  "scripts": {
    "test": "pytest -q --disable-warnings",
    "build": "npm run build -s"
  }
}' > .mel/config_template.json

# First time running mel in this project
mel help
# - Detects git repository
# - Installs git plugin
# - Processes config_template.json
# - Installs mel-docs plugin
# - Creates .mel/config.json
```

### Plugin Installation Sources

#### Built-in Plugins (Always Available)
- `core` - Core Mel functionality (help, version, plugin management)
- `git` - Git commands and workflows
- `hg` - Mercurial commands and workflows
- `svn` - Subversion commands and workflows

#### External Plugins (Downloaded)
- `mel-assistant` - AI assistance for errors
- `mel-docs` - Documentation generation
- `mel-backup` - Backup and sync functionality
- `mel-sync` - Multi-repo synchronization

#### Plugin Registry
```bash
# Install from registry
mel plugin install mel-assistant

# Install from URL
mel plugin install https://github.com/user/mel-plugin

# Install from local directory
mel plugin install ./my-mel-plugin
```

## Plugin Development

### Plugin Template
```bash
# Create new plugin
mel plugin create my-plugin

# Generates:
# plugins/installed/my-plugin/
# ├── plugin.json
# ├── commands.json
# ├── hooks/
# ├── bin/
# └── README.md
```

### Plugin Testing
```bash
# Test plugin locally
mel plugin test my-plugin

# Publish plugin
mel plugin publish my-plugin
```

## Benefits of Plugin System

### 1. **Minimal Core**
- Mel core remains simple shell script
- Rich functionality through plugins
- Users choose what they need

### 2. **Easy Extension**
- JSON-based configuration
- Hook system for advanced functionality
- Standard plugin format

### 3. **Community Ecosystem**
- Plugin registry for sharing
- Easy installation and management
- Version control and updates

### 4. **Flexibility**
- Configuration plugins (simple)
- Hook plugins (advanced)
- Command plugins (hybrid)

### 5. **Maintainability**
- Separated concerns
- Independent plugin development
- Core stability

## Implementation Timeline

### Phase 1: Basic Plugin System
- [ ] Plugin directory structure
- [ ] JSON configuration merging
- [ ] Basic plugin management commands
- [ ] Command plugin support

### Phase 2: Hook System
- [ ] Hook registration and execution
- [ ] Pre/post command hooks
- [ ] Error handling hooks
- [ ] Plugin hook examples

### Phase 3: Plugin Registry
- [ ] Plugin registry format
- [ ] Plugin installation from registry
- [ ] Plugin search and discovery
- [ ] Version management

### Phase 4: Plugin Development Tools
- [ ] Plugin template generation
- [ ] Plugin testing framework
- [ ] Plugin publishing system
- [ ] Documentation and examples

## Conclusion

The plugin system transforms Mel from a simple script runner into an extensible platform while maintaining its core simplicity. Users get:

- **Minimal core**: Fast, dependency-free base
- **Rich extensions**: AI assistance, documentation, custom workflows
- **Easy management**: Simple plugin commands
- **Community ecosystem**: Shared plugins and tools

This approach perfectly balances simplicity with extensibility, allowing Mel to grow with user needs while keeping the core lean and fast.
