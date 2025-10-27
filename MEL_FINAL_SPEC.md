# Mel Final Specification & Implementation Plan

## Overview

This document provides the complete specification for building Mel as a plugin-based script runner with a minimal shell core. This represents a ground-up rebuild that treats everything as plugins, including core functionality, with a focus on transparency, simplicity, and multi-VCS support.

## Architecture Summary

### Core Philosophy
- **Everything is a plugin** - including git, mercurial, and core functionality
- **Minimal shell core** - only launcher and plugin management
- **Single dependency** - `jq` for JSON parsing
- **Template-driven** - project-specific configurations via templates
- **Auto-detection** - VCS detection and plugin installation

### File Structure
Repo-local scope and global launcher:
```
$PATH/mel                 # Global launcher (installed in PATH)

/path/to/repo/            # Any VCS-backed project you run mel in
└── .mel/                 # Repo-local state (created on first run in this repo)
    ├── config.json           # User config with plugin list (repo-local)
    ├── config_template.json  # Optional template (checked-in to the repo)
    └── plugins/              # All functionality as plugins (repo-local)
        ├── core/             # Core Mel (help, plugin management, flags)
        │   ├── config.json
        │   └── bin/
        ├── git/
        │   ├── config.json
        │   └── bin/
        ├── hg/
        │   ├── config.json
        │   └── bin/
        ├── mel-assistant/
        │   ├── config.json
        │   ├── hooks/
        │   └── bin/
        └── mel-docs/
            ├── config.json
            └── bin/
```

Notes:
- The `.mel/` directory is created per-repo at the project root, not in the global install location. Plugins and configuration are always repo-local.
- If a repo includes `.mel/config_template.json` in version control, it is used as defaults on first run, then merged into `.mel/config.json`.

See also: `[MEL_PLUGIN_SYSTEM.md](./MEL_PLUGIN_SYSTEM.md)`, `[PURE_SHELL_ANALYSIS.md](./PURE_SHELL_ANALYSIS.md)`.

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1-2)
**Goal**: Minimal shell launcher with plugin system

#### Deliverables:
- [ ] Minimal mel launcher script (~100 lines)
- [ ] Plugin system architecture
- [ ] Core plugin with basic commands
- [ ] Configuration merging system
- [ ] VCS detection and auto-installation

#### Files to Create:
```
# Installed globally (via installer):
mel                       # Executable shell script in PATH

# Created per-repo on first run:
.mel/
├── config.json (initial)
└── plugins/
    └── core/
        ├── config.json
        └── bin/
            ├── help.sh
            ├── plugin.sh
```
See also: `[MEL_PLUGIN_SYSTEM.md](./MEL_PLUGIN_SYSTEM.md)` for plugin layout; `[PARAMETER_STANDARDS_AND_DOCS.md](./PARAMETER_STANDARDS_AND_DOCS.md)` for help/docs expectations.

#### Core Commands and Flags:
- `mel help` - Show available commands (split into basic/advanced sections; `--advanced` shows advanced)
- `mel plugin` - Plugin management
- `mel ignoremel` - Add `.mel` to VCS ignore (hidden command)
- Flags: `mel -v` / `mel --version` print version; there is no `mel version` subcommand.
See also: `[PARAMETER_STANDARDS_AND_DOCS.md](./PARAMETER_STANDARDS_AND_DOCS.md)` for help-mode guidance.

### Phase 2: VCS Plugins (Week 3-4)
**Goal**: Git and Mercurial plugins with full command sets

#### Deliverables:
- [ ] Git plugin with all commands
- [ ] Mercurial plugin with all commands
- [ ] VCS auto-detection and installation
- [ ] Template configuration processing
- [ ] Enhanced parameter system

#### Git Plugin Commands:
- **Basic**: `save`, `publish`, `status`, `reset`
- **Advanced**: `b`/`branch`, `update:rebase`, `update:merge`, `diff`, `open`, `pr`, `clear`
- **Hidden**: `ignoremel` - adds .mel to .gitignore

#### Mercurial Plugin Commands:
- **Basic**: `save`, `publish`, `status`, `reset`
- **Advanced**: `b`/`branch`, `update`, `diff`, `open`, `pr`, `clear`
- **Hidden**: `ignoremel` - adds .mel to .hgignore

### Phase 3: Documentation System (Week 5)
**Goal**: Auto-generated documentation with mode-based filtering

#### Deliverables:
- [ ] Documentation plugin
- [ ] HTML documentation generation
- [ ] Mode-based help filtering
- [ ] Template-driven documentation
- [ ] Local documentation server

#### Documentation Features:
- **Auto-generated** from plugin configurations
- **Mode-based filtering** (basic/advanced/both/none)
- **Template support** for project-specific docs
- **Local server** for viewing documentation

### Phase 4: Advanced Plugins (Week 6-7)
**Goal**: AI assistant and other advanced plugins

#### Deliverables:
- [ ] Mel assistant plugin (AI error guidance)
- [ ] Plugin registry system
- [ ] Hook system implementation
- [ ] Enhanced parameter handling
- [ ] Plugin development tools

#### Advanced Features:
- **AI assistance** for error resolution
- **Hook system** for pre/post command execution
- **Enhanced parameters** with validation and documentation
- **Plugin registry** for community plugins

### Phase 5: Testing and Polish (Week 8)
**Goal**: Comprehensive testing and user experience polish

#### Deliverables:
- [ ] Comprehensive test suite
- [ ] Cross-platform testing
- [ ] Performance optimization
- [ ] User documentation
- [ ] Migration tools

## Detailed Specifications

### 1. Minimal Mel Launcher

#### Core Script (`mel`)
```bash
#!/bin/bash
# mel - Minimal script runner launcher

set -euo pipefail

# Determine project root (prefer VCS root; fallback to current directory)
if command -v git >/dev/null 2>&1 && git rev-parse --show-toplevel >/dev/null 2>&1; then
    PROJECT_ROOT="$(git rev-parse --show-toplevel)"
elif command -v hg >/dev/null 2>&1 && hg root >/dev/null 2>&1; then
    PROJECT_ROOT="$(hg root)"
else
    PROJECT_ROOT="$PWD"
fi
MEL_DIR="$PROJECT_ROOT/.mel"

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
    
    # Parse arguments (support -v/--version flags)
    if [[ "${1:-}" == "-v" || "${1:-}" == "--version" ]]; then
        echo "$(mel --internal-version)"
        exit 0
    fi
    local command="${1:-help}"
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

### 2. Plugin System Architecture

#### Plugin Configuration Schema
```json
{
  "scripts": {
    "command_name": {
      "description": "Short description for help text",
      "help_text": "Detailed explanation for web docs",
      "usage": "mel command [args]",
      "examples": [
        "mel command example1",
        "mel command example2"
      ],
      "mode": "basic|advanced|none|both",
      "troubleshooting": "Common issues and solutions",
      "see_also": ["related_command1", "related_command2"],
      "commands": [
        "git add -A",
        "git commit -m \"{message}\"",
        "git fetch origin",
        "git rebase origin/{main}"
      ],
      "safety_checks": [
        "not_on_main",
        "clean_working_tree",
        "has_remote"
      ],
      "confirmation_required": true,
      "requires_message": false,
      "requires_args": false,
      "parameters": {
        "param_name": {
          "type": "string|integer|boolean",
          "required": true,
          "description": "Parameter description",
          "position": 1,
          "env_var": "PARAM_NAME",
          "default": "default_value"
        }
      }
    }
  },
  "hooks": {
    "pre_command": [
      ".mel/plugins/plugin-name/hooks/pre_command"
    ],
    "post_command": [
      ".mel/plugins/plugin-name/hooks/post_command"
    ],
    "on_error": [
      ".mel/plugins/plugin-name/hooks/on_error"
    ]
  },
  "config": {
    "setting_name": {
      "type": "string",
      "required": true,
      "description": "Setting description"
    }
  }
}
```

See also: `[MEL_PLUGIN_SYSTEM.md](./MEL_PLUGIN_SYSTEM.md)` for deeper schema and merging rules; `[PARAMETER_STANDARDS_AND_DOCS.md](./PARAMETER_STANDARDS_AND_DOCS.md)` for parameter documentation standards.

#### Configuration Merging Strategy
- **Scripts**: Overwrite (user can override plugin commands)
- **Hooks**: Append (multiple plugins can add hooks)
- **Config**: Overwrite (user settings take precedence)

#### Plugin Management Commands
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

### 3. VCS Auto-Detection and Installation

#### VCS Detection
```bash
# Detect VCS and auto-install plugin
detect_vcs_and_install() {
    local vcs=""
    
    if [[ -d "$PROJECT_ROOT/.git" ]]; then
        vcs="git"
    elif [[ -d "$PROJECT_ROOT/.hg" ]]; then
        vcs="hg"
    elif [[ -d "$PROJECT_ROOT/.svn" ]]; then
        vcs="svn"
    else
        echo "✖ No version control system detected"
        exit 1
    fi
    
    # Auto-install VCS plugin if not present
    if [[ ! -d "$MEL_DIR/plugins/$vcs" ]]; then
        echo "📦 Installing $vcs plugin..."
        mel plugin install "$vcs"
    fi
    
    # Add to user config if not present
    local user_config="{}"
    if [[ -f "$MEL_DIR/config.json" ]]; then
        user_config=$(cat "$MEL_DIR/config.json")
    fi
    
    local has_vcs_plugin
    has_vcs_plugin=$(echo "$user_config" | jq -r ".plugins[]? | select(. == \"$vcs\")" 2>/dev/null)
    
    if [[ -z "$has_vcs_plugin" ]]; then
        echo "📝 Adding $vcs plugin to configuration..."
        user_config=$(echo "$user_config" | jq ".plugins = (.plugins // []) + [\"$vcs\"]")
        echo "$user_config" > "$MEL_DIR/config.json"
    fi
    
    echo "$vcs"
}
```

### 4. Template Configuration System

#### Template Processing
```bash
# Process template configuration on first run
process_template_config() {
    if [[ -f "$MEL_DIR/config_template.json" ]]; then
        echo "📋 Found template configuration..."
        
        local template_config
        template_config=$(cat "$MEL_DIR/config_template.json")
        
        # Install plugins from template
        local template_plugins
        template_plugins=$(echo "$template_config" | jq -r '.plugins[]?' 2>/dev/null || echo "")
        
        for plugin in $template_plugins; do
            if [[ ! -d "$MEL_DIR/plugins/$plugin" ]]; then
                echo "📦 Installing plugin from template: $plugin"
                mel plugin install "$plugin"
            fi
        done
        
        # Merge template config into user config
        local user_config="{}"
        if [[ -f "$MEL_DIR/config.json" ]]; then
            user_config=$(cat "$MEL_DIR/config.json")
        fi
        
        # Merge template (lower priority than existing user config)
        user_config=$(echo "$user_config" | jq '. * input' <(echo "$template_config"))
        echo "$user_config" > "$MEL_DIR/config.json"
        
        echo "✓ Template configuration applied"
    fi
}
```

See also: `[MEL_FINAL_SPEC.md](./MEL_FINAL_SPEC.md)` (this section), `[MEL_PLUGIN_SYSTEM.md](./MEL_PLUGIN_SYSTEM.md)` for install/merge flow.

#### Example Template Configuration
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

### 5. Enhanced Parameter System

#### Parameter Types and Handling
- **Positional Parameters**: `mel command arg1 arg2`
- **Named Parameters**: `mel command --param value`
- **Environment Variables**: `PARAM=value mel command`
- **Mixed Styles**: `mel command arg1 --param value`

#### Parameter Resolution Order
1. **Environment Variables** (highest priority)
2. **Command Line Flags** (`--param=value`)
3. **Positional Arguments** (by position)
4. **Default Values** (lowest priority)

#### Enhanced Help Generation
```bash
$ mel help ingest:json

ingest:json - Import JSON data into collection

Usage:
  mel ingest:json <json_file> <collection> [options]
  mel ingest:json --json-file <file> --collection <name> [options]
  JSON=<file> COLLECTION=<name> mel ingest:json [options]

Parameters:
  json_file (string, required)
    Path to JSON file to import
    Position: 1, Env: JSON
  
  collection (string, required)  
    Collection name to import into
    Position: 2, Env: COLLECTION
    
  dry_run (boolean, optional, default: false)
    Show what would be imported without doing it
    Flag: --dry-run

Examples:
  mel ingest:json data.json my-collection
  mel ingest:json --json-file data.json --collection my-collection --dry-run
  JSON=data.json COLLECTION=my-collection mel ingest:json
```

### 6. Hidden Commands

#### `mel ignoremel` Command
- **Hidden from all modes** - never appears in help
- **Auto-installed** with git/hg plugins
- **Smart detection** - checks if .mel files are showing in status
- **Safe operation** - only adds if not already present

#### Git Plugin Implementation
```json
{
  "scripts": {
    "ignoremel": {
      "description": "Add .mel directory to .gitignore",
      "mode": "none",
      "commands": [
        ".mel/plugins/git/bin/ignoremel.sh"
      ]
    }
  }
}
```
See also: `[MEL_PARAMETER_HANDLING.md](./MEL_PARAMETER_HANDLING.md)` and `[PARAMETER_STANDARDS_AND_DOCS.md](./PARAMETER_STANDARDS_AND_DOCS.md)`.

#### Ignoremel Script (`ignoremel.sh`)
```bash
#!/bin/bash
# Add .mel to .gitignore if needed

# Check if .mel files are showing in git status
if git status --porcelain | grep -q "^?? .mel/"; then
    echo "📝 Adding .mel/ to .gitignore..."
    
    # Check if .gitignore exists and doesn't already contain .mel
    if [[ -f ".gitignore" ]]; then
        if ! grep -q "^\.mel/$" .gitignore; then
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
```

### 7. Documentation System

#### Documentation Plugin
```json
{
  "scripts": {
    "docs": {
      "description": "Start documentation server",
      "help_text": "Start a local web server to view Mel documentation",
      "usage": "mel docs [--port 8080] [--host localhost]",
      "mode": "advanced",
      "commands": [
        ".mel/plugins/mel-docs/bin/docs.sh"
      ],
      "parameters": {
        "port": {
          "type": "integer",
          "required": false,
          "default": 8080,
          "description": "Port for documentation server",
          "flag": "--port"
        },
        "host": {
          "type": "string",
          "required": false,
          "default": "localhost",
          "description": "Host for documentation server",
          "flag": "--host"
        }
      }
    }
  }
}
```

#### Documentation Generation
- **Auto-generated** from plugin configurations
- **Mode-based filtering** for different user types
- **Template-driven** for project-specific documentation
- **Local server** for immediate viewing

See also: `[PARAMETER_STANDARDS_AND_DOCS.md](./PARAMETER_STANDARDS_AND_DOCS.md)` and `[MEL_DOCS_DEPENDENCY_ANALYSIS.md](./MEL_DOCS_DEPENDENCY_ANALYSIS.md)`.

### 8. Hook System

#### Hook Types
- **pre_command**: Before command execution
- **post_command**: After successful command execution
- **on_error**: When command fails
- **pre_save**: Before save command
- **post_save**: After save command

#### Hook Execution Order
1. **Plugin hooks first** (in plugin order)
2. **User hooks last** (highest priority)

#### Example Hook Implementation
```bash
#!/bin/bash
# .mel/plugins/mel-assistant/hooks/on_error

# Get error information
local command="$1"
local exit_code="$2"
local error_output="$3"

# Send to AI assistant for analysis
python3 .mel/plugins/mel-assistant/bin/analyze_error.py \
    --command "$command" \
    --exit-code "$exit_code" \
    --error "$error_output"
```

See also: `[MEL_PLUGIN_SYSTEM.md](./MEL_PLUGIN_SYSTEM.md)` for hook ordering and lifecycle.

## Implementation Timeline

### Week 1-2: Core Infrastructure
- [ ] Minimal mel launcher script
- [ ] Plugin system architecture
- [ ] Core plugin with basic commands
- [ ] Configuration merging system
- [ ] VCS detection and auto-installation

### Week 3-4: VCS Plugins
- [ ] Git plugin with all commands
- [ ] Mercurial plugin with all commands
- [ ] Template configuration processing
- [ ] Enhanced parameter system
- [ ] Hidden ignoremel command

### Week 5: Documentation System
- [ ] Documentation plugin
- [ ] HTML documentation generation
- [ ] Mode-based help filtering
- [ ] Template-driven documentation
- [ ] Local documentation server

### Week 6-7: Advanced Plugins
- [ ] Mel assistant plugin (AI error guidance)
- [ ] Plugin registry system
- [ ] Hook system implementation
- [ ] Enhanced parameter handling
- [ ] Plugin development tools

### Week 8: Testing and Polish
- [ ] Comprehensive test suite
- [ ] Cross-platform testing
- [ ] Performance optimization
- [ ] User documentation
- [ ] Migration tools

## Success Metrics

### Technical Metrics
- [ ] Startup time < 50ms
- [ ] Memory usage < 10MB
- [ ] Zero command execution overhead
- [ ] 100% test coverage
- [ ] Cross-platform compatibility

### User Experience Metrics
- [ ] Seamless migration from current Mel
- [ ] All current functionality preserved
- [ ] Improved transparency (explain command)
- [ ] Multi-VCS support working
- [ ] Documentation always in sync

### Adoption Metrics
- [ ] Existing users successfully migrate
- [ ] New users can use without training
- [ ] Community contributions to plugins
- [ ] Reduced support requests

## Risk Mitigation

### Technical Risks
1. **Shell Compatibility**: Test on multiple shells and platforms
2. **Performance Regression**: Benchmark against current implementation
3. **Feature Parity**: Comprehensive feature comparison matrix

### User Experience Risks
1. **Migration Complexity**: Provide automated migration tools
2. **Learning Curve**: Maintain familiar command interface
3. **Documentation Drift**: Automated documentation generation

### Project Risks
1. **Timeline Overrun**: Phased delivery with working increments
2. **Scope Creep**: Strict adherence to MVP in early phases
3. **Quality Issues**: Comprehensive testing at each phase

## Conclusion

This plugin-based architecture represents a fundamental improvement in Mel's design, providing:

- **90% reduction in codebase size** (100 vs 1,150 lines)
- **Multi-VCS support** with minimal effort
- **Complete transparency** through explain command
- **Automated documentation** generation
- **Better performance** through shell execution
- **Easier maintenance** through configuration-driven design
- **Extensibility** through plugin system
- **Team collaboration** through template configurations

The phased implementation approach ensures we can deliver working functionality incrementally while maintaining quality and user experience standards.

