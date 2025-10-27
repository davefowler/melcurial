# Mel Script Runner Implementation Plan

## Overview

This document outlines the complete implementation plan for building Mel as a lightweight script runner that uses JSON configuration files to define version control commands. This is a ground-up rebuild focused on transparency, simplicity, and multi-VCS support.

## Architecture

### Core Components

```
mel (executable)
├── core/
│   ├── runner.py          # Main script runner (Python)
│   ├── config.py          # Configuration management (Python)
│   └── vcs_detector.py    # VCS detection (Python)
├── configs/
│   ├── git_defaults.json  # Git command definitions
│   ├── hg_defaults.json   # Mercurial command definitions
│   └── svn_defaults.json  # SVN command definitions (future)
├── generators/
│   ├── help_generator.py  # CLI help generation (Python)
│   ├── docs_generator.py  # HTML docs generation (Python)
│   └── man_generator.py   # Man page generation (Python)
└── utils/
    ├── shell_runner.sh    # Shell command execution
    └── template_engine.py # Variable substitution (Python)
```

## Function Distribution: Shell vs Python

### Shell Functions (Fast, Simple)
**Why Shell**: Maximum performance, minimal dependencies, perfect for simple command execution

- **Command Execution**: `run_command()`, `run_commands()`
- **VCS Detection**: `detect_vcs()` - check for `.git`, `.hg`, etc.
- **File Operations**: `file_exists()`, `read_file()`, `write_file()`
- **Environment**: `get_env()`, `set_env()`
- **Basic Validation**: `validate_branch_name()`, `validate_message()`

### Python Functions (Complex Logic)
**Why Python**: Rich libraries, complex data structures, error handling, cross-platform compatibility

#### Core Runner (`runner.py`)
```python
def main():
    """Main entry point - argument parsing and command routing"""
    
def load_config(vcs_type: str) -> dict:
    """Load and merge configuration files"""
    
def execute_command(config: dict, command: str, args: list) -> int:
    """Execute a command with safety checks and variable substitution"""
    
def run_safety_checks(command_config: dict, context: dict) -> bool:
    """Run safety checks before command execution"""
```

#### Configuration Management (`config.py`)
```python
def load_vcs_defaults(vcs_type: str) -> dict:
    """Load default configuration for VCS type"""
    
def load_user_config() -> dict:
    """Load user configuration from .mel/config.json"""
    
def load_package_scripts() -> dict:
    """Load scripts from package.json, pyproject.toml, etc."""
    
def merge_configs(defaults: dict, user: dict, packages: dict) -> dict:
    """Merge configuration layers with proper precedence"""
    
def validate_config(config: dict) -> bool:
    """Validate configuration schema and values"""
```

#### VCS Detection (`vcs_detector.py`)
```python
def detect_vcs() -> str:
    """Detect version control system in current directory"""
    
def get_vcs_info(vcs_type: str) -> dict:
    """Get VCS-specific information (main branch, current branch, etc.)"""
    
def get_repo_root() -> str:
    """Get repository root directory"""
```

#### Documentation Generators
```python
# help_generator.py
def generate_cli_help(config: dict, mode: str = "basic") -> str:
    """Generate CLI help text from configuration"""
    
def generate_command_help(config: dict, command: str) -> str:
    """Generate detailed help for specific command"""

# docs_generator.py  
def generate_html_docs(config: dict, output_dir: str) -> None:
    """Generate HTML documentation from configuration"""
    
def generate_markdown_docs(config: dict, output_dir: str) -> None:
    """Generate Markdown documentation"""

# man_generator.py
def generate_man_pages(config: dict, output_dir: str) -> None:
    """Generate Unix man pages"""
```

#### Template Engine (`template_engine.py`)
```python
def substitute_variables(template: str, context: dict) -> str:
    """Substitute variables in command templates"""
    
def build_context(vcs_type: str, command: str, args: list) -> dict:
    """Build context dictionary for variable substitution"""
    
def format_message_template(template: str, context: dict) -> str:
    """Format message templates with datetime, author, etc."""
```

## Configuration Schema

### Enhanced JSON Schema
```json
{
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
    "hooks": {
      "pre": ["mel test"],
      "post": ["echo 'Command completed'"]
    },
    "variables": {
      "main": "auto-detected main branch",
      "branch": "current branch name",
      "message": "user-provided message",
      "author": "git config user.name",
      "datetime": "current timestamp"
    },
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
}
```

## Default Command Definitions

### Git Commands (`git_defaults.json`)

#### Basic Commands
```json
{
  "save": {
    "description": "Save changes and sync with main",
    "help_text": "Commits your changes, fetches latest from main, rebases your branch, and pushes to remote",
    "usage": "mel save \"your commit message\"",
    "examples": [
      "mel save \"Fixed typo in README\"",
      "mel save \"Updated documentation\""
    ],
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
    "confirmation_required": false,
    "troubleshooting": "If you get conflicts, resolve them and run 'git add -A && git rebase --continue'"
  },
  
  "publish": {
    "description": "Merge to main and push",
    "help_text": "Merges your branch to main using fast-forward merge, then updates your branch",
    "usage": "mel publish",
    "examples": ["mel publish"],
    "mode": "basic",
    "commands": [
      "git checkout {main}",
      "git merge --ff-only {branch}",
      "git push origin {main}",
      "git checkout {branch}",
      "git rebase origin/{main}"
    ],
    "safety_checks": ["not_on_main", "has_remote"],
    "confirmation_required": true,
    "troubleshooting": "Make sure your branch is up to date with main first using 'mel save'"
  },
  
  "status": {
    "description": "Show current status",
    "help_text": "Shows what changes you've made since saving",
    "usage": "mel status",
    "examples": ["mel status"],
    "mode": "basic",
    "commands": [
      "git status -sb",
      "git log -1 --pretty=%h %s (%cr)"
    ],
    "safety_checks": [],
    "confirmation_required": false
  },
  
  "reset": {
    "description": "Reset to latest main",
    "help_text": "Ditch your changes and start over from main",
    "usage": "mel reset",
    "examples": ["mel reset"],
    "mode": "basic",
    "commands": [
      "git fetch origin",
      "git reset --hard origin/{main}",
      "git push --force origin {branch}"
    ],
    "safety_checks": ["not_on_main"],
    "confirmation_required": true,
    "troubleshooting": "This will permanently delete your branch's commits. Make sure you've saved any important work."
  }
}
```

#### Advanced Commands
```json
{
  "b": {
    "description": "Create or switch to branch",
    "help_text": "Create or switch to branch if existing",
    "usage": "mel b <branch name>",
    "examples": [
      "mel b feature/new-login",
      "mel b bugfix/typo"
    ],
    "mode": "advanced",
    "commands": [
      "git fetch origin",
      "git checkout -B {branch_name} origin/{main}"
    ],
    "safety_checks": ["clean_working_tree"],
    "requires_args": true
  },
  
  "update": {
    "description": "Update with latest main (default strategy)",
    "help_text": "Updates your branch with latest main using the default strategy",
    "usage": "mel update",
    "examples": ["mel update"],
    "mode": "advanced",
    "commands": [
      "mel update:merge"
    ],
    "safety_checks": ["not_on_main", "clean_working_tree"],
    "default_command": true
  },
  
  "update:rebase": {
    "description": "Update with latest main via rebase",
    "help_text": "Rebase your branch on the latest from main",
    "usage": "mel update:rebase",
    "examples": ["mel update:rebase"],
    "mode": "advanced",
    "commands": [
      "git fetch origin",
      "git rebase origin/{main}"
    ],
    "safety_checks": ["not_on_main", "clean_working_tree"]
  },
  
  "update:merge": {
    "description": "Update with latest main via merge",
    "help_text": "Merge latest main into your branch",
    "usage": "mel update:merge",
    "examples": ["mel update:merge"],
    "mode": "advanced",
    "commands": [
      "git fetch origin",
      "git merge origin/{main}"
    ],
    "safety_checks": ["not_on_main", "clean_working_tree"]
  },
  
  "diff": {
    "description": "Show diff stats",
    "help_text": "Show staged/unstaged diff stats",
    "usage": "mel diff",
    "examples": ["mel diff"],
    "mode": "advanced",
    "commands": [
      "git diff --staged --stat",
      "git diff --stat"
    ],
    "safety_checks": []
  },
  
  "open": {
    "description": "Open remote repo page",
    "help_text": "Open remote repo page in your browser",
    "usage": "mel open",
    "examples": ["mel open"],
    "mode": "advanced",
    "commands": [
      "open {repo_url}"
    ],
    "safety_checks": ["has_remote"]
  },
  
  "pr": {
    "description": "Open PR page",
    "help_text": "Go to the page to make a new PR",
    "usage": "mel pr",
    "examples": ["mel pr"],
    "mode": "advanced",
    "commands": [
      "open {pr_url}"
    ],
    "safety_checks": ["has_remote", "not_on_main"]
  },
  
  "clear": {
    "description": "Stash uncommitted changes",
    "help_text": "Stash your uncommitted changes (worktree + untracked)",
    "usage": "mel clear",
    "examples": ["mel clear"],
    "mode": "advanced",
    "commands": [
      "git stash push -u -m \"mel clear @ {datetime}\""
    ],
    "safety_checks": [],
    "confirmation_required": true
  }
}
```

### Mercurial Commands (`hg_defaults.json`)
```json
{
  "save": {
    "description": "Save changes and sync with main",
    "help_text": "Commits your changes, pulls latest from main, and pushes to remote",
    "usage": "mel save \"your commit message\"",
    "examples": [
      "mel save \"Fixed typo in README\"",
      "mel save \"Updated documentation\""
    ],
    "category": "basic",
    "commands": [
      "hg add",
      "hg commit -m \"{message}\"",
      "hg pull",
      "hg rebase -d {main}",
      "hg push"
    ],
    "safety_checks": ["not_on_main", "clean_working_tree"],
    "requires_message": true,
    "troubleshooting": "If you get conflicts, resolve them and run 'hg rebase --continue'"
  },
  
  "publish": {
    "description": "Merge to main and push",
    "help_text": "Merges your branch to main and pushes",
    "usage": "mel publish",
    "examples": ["mel publish"],
    "category": "basic",
    "commands": [
      "hg update {main}",
      "hg merge {branch}",
      "hg commit -m \"Merge {branch} into {main}\"",
      "hg push"
    ],
    "safety_checks": ["not_on_main"],
    "confirmation_required": true
  }
}
```

## Auto-Generated Documentation System

### Documentation Architecture

The new system will auto-generate most documentation content from configuration files, with only intro/closing text being manually maintained.

#### File Organization
```
configs/
├── git_defaults.json          # Git command definitions
├── hg_defaults.json           # Mercurial command definitions  
├── config_schema.json         # Configuration options schema
└── docs_templates.json        # Documentation templates and static content
```

#### Configuration Schema (`config_schema.json`)
```json
{
  "config_options": {
    "main": {
      "type": "string",
      "default": "auto-detected",
      "description": "Name of your default branch",
      "help_text": "Auto-detected as 'main' or 'master' if absent",
      "category": "basic"
    },
    "contributor_mode": {
      "type": "string",
      "default": "basic",
      "options": ["basic", "advanced"],
      "description": "Controls help text visibility",
      "help_text": "basic: Shows only basic commands for non-engineers, advanced: Shows both basic and advanced commands",
      "category": "basic"
    },
    "require_add_confirmation": {
      "type": "boolean",
      "default": true,
      "description": "Show file list before adding to commit",
      "help_text": "If true (default), show a list of files and require confirmation before adding them to a commit",
      "category": "basic"
    },
    "require_publish_confirmation": {
      "type": "boolean", 
      "default": true,
      "description": "Confirm before publishing",
      "help_text": "If false, skip the confirmation prompt in 'mel publish'",
      "category": "basic"
    },
    "open_pr_on_sync": {
      "type": "boolean",
      "default": false,
      "description": "Open PR URL after sync",
      "help_text": "When true, after 'mel sync' mel opens a prefilled PR URL (GitHub)",
      "category": "advanced"
    },
    "merge_message": {
      "type": "string",
      "default": null,
      "description": "Template for merge commit messages",
      "help_text": "Template for merge commit messages when using merge strategy. Supports {branch}, {main}, {author}, {datetime}",
      "category": "advanced"
    },
    "allow_package_scripts": {
      "type": "boolean",
      "default": false,
      "description": "Allow package manager scripts",
      "help_text": "If true, 'mel <name>' falls back to your package manager when a script is not defined locally",
      "category": "advanced"
    }
  }
}
```

#### Documentation Templates (`docs_templates.json`)
```json
{
  "static_content": {
    "home_intro": "Many non-engineers have contributions for codebases (static sites, docs, design tweaks, image swaps, etc.) and the learning curve on git is steep.\n\nmel is a simplification of a common git flow that makes versioned collaboration more approachable for those non-engineer contributors.\n\n**Mission: enable non-engineers to contribute!**",
    
    "home_how_it_works": "mel is just a wrapper around git. It keeps each person working in their own branch, and automatically pulling in changes from the main branch. If at any point someone gets stuck you can revert to directly using git.",
    
    "explained_intro": "No good abstraction should be without a full explanation of what has been abstracted. If you're an engineer or AI trying to figure your way out of some confusing scenario, hopefully this information can help:\n\nThis documentation explains what each mel command is doing under the hood, and you can get the same help by simply running `mel explain <command>`.",
    
    "config_intro": "mel reads `.mel/config.json` at the repository root. If it's missing, mel will create the `.mel` folder as needed. You can also provide a template (see Template) of defaults for anyone using the repo."
  },
  
  "generated_sections": {
    "home_usage": "auto_generate_from_commands",
    "explained_commands": "auto_generate_from_commands", 
    "config_options": "auto_generate_from_schema"
  }
}
```

### Mode-Based Help System

#### Mode Field Values
- **`"basic"`**: Show only in basic mode help
- **`"advanced"`**: Show only in advanced mode help  
- **`"both"`**: Show in both basic and advanced mode help
- **`"none"`**: Never show in help (but command still works)

#### Help Command Behavior
```bash
mel help                    # Show commands for current mode (basic/advanced)
mel help --all             # Show all commands regardless of mode
mel help --mode basic      # Show only basic commands
mel help --mode advanced   # Show only advanced commands
```

#### Default Command System
Instead of `update_strategy` boolean, we have:
- `mel update` → runs `mel update:merge` by default
- `mel update:rebase` → explicit rebase strategy
- `mel update:merge` → explicit merge strategy

Users can override the default by creating a script:
```json
{
  "scripts": {
    "update": "mel update:rebase"  // Override default to use rebase
  }
}
```

### Documentation Generation Pipeline

#### CLI Help Generator (`generators/help_generator.py`)
```python
def generate_cli_help(config: dict, mode: str = None, show_all: bool = False) -> str:
    """Generate CLI help text from configuration"""
    
def filter_commands_by_mode(commands: dict, mode: str, show_all: bool = False) -> dict:
    """Filter commands based on mode and show_all flag"""
    
def format_command_help(command_name: str, command_config: dict) -> str:
    """Format help text for individual command"""
```

#### HTML Documentation Generator (`generators/docs_generator.py`)
```python
def generate_home_page(config: dict, templates: dict) -> str:
    """Generate home page HTML from config and templates"""
    
def generate_explained_page(config: dict, templates: dict) -> str:
    """Generate explained page HTML from config and templates"""
    
def generate_config_page(config: dict, schema: dict, templates: dict) -> str:
    """Generate config page HTML from schema and templates"""
    
def generate_command_documentation(command_name: str, command_config: dict) -> str:
    """Generate detailed command documentation"""
```

#### Documentation Build Commands
```bash
# Generate all documentation
mel docs:generate --output docs/

# Generate specific pages
mel docs:generate --page home --output docs/index.html
mel docs:generate --page explained --output docs/explained.html  
mel docs:generate --page config --output docs/config.html

# Generate CLI help
mel help:generate --mode basic > help_basic.txt
mel help:generate --mode advanced > help_advanced.txt
mel help:generate --all > help_all.txt
```

### Configuration Management

#### Configuration Merging
```python
def load_merged_config(vcs_type: str) -> dict:
    """Load and merge configuration layers"""
    
    # 1. Load VCS defaults (git_defaults.json, hg_defaults.json)
    vcs_defaults = load_vcs_defaults(vcs_type)
    
    # 2. Load user config (.mel/config.json)  
    user_config = load_user_config()
    
    # 3. Load package scripts (package.json, pyproject.toml)
    package_scripts = load_package_scripts()
    
    # 4. Merge with proper precedence
    merged = merge_configs(vcs_defaults, user_config, package_scripts)
    
    # 5. Validate against schema
    validate_config(merged)
    
    return merged
```

#### Configuration Validation
```python
def validate_config(config: dict, schema: dict) -> bool:
    """Validate configuration against schema"""
    
def validate_command_config(command_name: str, command_config: dict) -> bool:
    """Validate individual command configuration"""
    
def suggest_config_fixes(config: dict, schema: dict) -> list:
    """Suggest fixes for invalid configuration"""
```

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
**Goal**: Basic script runner with git support

#### Deliverables:
- [ ] Core runner script (`mel`)
- [ ] Configuration loading system
- [ ] VCS detection
- [ ] Basic command execution
- [ ] Git default configuration
- [ ] Simple help generation

#### Files to Create:
```
mel (executable)
core/runner.py
core/config.py
core/vcs_detector.py
configs/git_defaults.json
utils/shell_runner.sh
```

#### Testing:
- [ ] Basic command execution
- [ ] Configuration loading
- [ ] Help generation
- [ ] Error handling

### Phase 2: Command Implementation (Week 3-4)
**Goal**: All basic and advanced commands working

#### Deliverables:
- [ ] Complete git command set
- [ ] Safety checks implementation
- [ ] Variable substitution
- [ ] Confirmation prompts
- [ ] Error handling and recovery

#### Commands to Implement:
- [ ] `save` - with message handling
- [ ] `publish` - with confirmation
- [ ] `status` - with detailed output
- [ ] `reset` - with safety checks
- [ ] `b`/`branch` - branch creation/switching
- [ ] `update` - rebase functionality
- [ ] `diff` - diff statistics
- [ ] `open` - browser integration
- [ ] `pr` - PR URL generation
- [ ] `clear` - stash functionality

### Phase 3: Documentation System (Week 5)
**Goal**: Automated documentation generation with mode-based filtering

#### Deliverables:
- [ ] CLI help generator with mode filtering
- [ ] HTML documentation generator
- [ ] Configuration schema system
- [ ] Documentation templates
- [ ] Mode-based command filtering
- [ ] Documentation build pipeline

#### Files to Create:
```
generators/help_generator.py
generators/docs_generator.py
generators/man_generator.py
utils/template_engine.py
configs/config_schema.json
configs/docs_templates.json
```

#### New Features:
- [ ] Mode-based help filtering (`basic`, `advanced`, `both`, `none`)
- [ ] `mel help --all` to show all commands
- [ ] Auto-generated home page usage sections
- [ ] Auto-generated explained page command details
- [ ] Auto-generated config page from schema

### Phase 4: Multi-VCS Support (Week 6)
**Goal**: Support for Mercurial and other VCS

#### Deliverables:
- [ ] Mercurial command definitions
- [ ] VCS-specific variable handling
- [ ] Cross-VCS compatibility
- [ ] VCS-specific documentation

#### Files to Create:
```
configs/hg_defaults.json
configs/svn_defaults.json (future)
```

### Phase 5: Advanced Features (Week 7-8)
**Goal**: Hooks, package scripts, and advanced configuration

#### Deliverables:
- [ ] Hook system implementation
- [ ] Package script integration
- [ ] Configuration templates
- [ ] Migration tools from current Mel
- [ ] Performance optimizations
- [ ] Default command system (`mel update` → `mel update:merge`)

#### Features to Implement:
- [ ] Pre/post command hooks
- [ ] Package.json script integration
- [ ] Configuration templates
- [ ] Migration utilities
- [ ] Performance profiling
- [ ] Default command routing system
- [ ] Command override system for user configs

### Phase 6: Testing and Polish (Week 9-10)
**Goal**: Comprehensive testing and user experience polish

#### Deliverables:
- [ ] Comprehensive test suite
- [ ] Cross-platform testing
- [ ] Performance benchmarks
- [ ] User documentation
- [ ] Migration guide

#### Testing Areas:
- [ ] Unit tests for all components
- [ ] Integration tests for command flows
- [ ] Cross-platform compatibility
- [ ] Performance testing
- [ ] User acceptance testing

## Migration Strategy

### From Current Mel to Script Runner

#### Phase 1: Parallel Development
- Keep current Mel as `mel-legacy`
- Develop new script runner as `mel-new`
- Allow users to test both versions

#### Phase 2: Configuration Migration
```python
def migrate_config(old_config_path: str) -> dict:
    """Migrate .mel/config.json from old format to new format"""
    # Convert old config to new JSON schema
    # Preserve user customizations
    # Add new fields with defaults
```

#### Phase 3: Gradual Rollout
- Release as `mel` v2.0
- Provide migration tools
- Maintain backward compatibility where possible
- Deprecate old version after transition period

## Performance Targets

### Startup Time
- **Target**: < 50ms (vs current ~200ms)
- **Method**: Minimal Python imports, shell for simple operations

### Memory Usage
- **Target**: < 10MB (vs current ~30MB)
- **Method**: Lazy loading, minimal dependencies

### Command Execution
- **Target**: No overhead vs direct git commands
- **Method**: Direct shell execution for most operations

## Testing Strategy

### Unit Tests
```python
# test_runner.py
def test_command_execution():
    """Test basic command execution"""
    
def test_config_loading():
    """Test configuration loading and merging"""
    
def test_variable_substitution():
    """Test template variable substitution"""
    
def test_safety_checks():
    """Test safety check validation"""
```

### Integration Tests
```python
# test_integration.py
def test_save_workflow():
    """Test complete save workflow"""
    
def test_publish_workflow():
    """Test complete publish workflow"""
    
def test_multi_vcs():
    """Test multi-VCS support"""
```

### Performance Tests
```python
# test_performance.py
def test_startup_time():
    """Test script startup performance"""
    
def test_command_overhead():
    """Test command execution overhead"""
```

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
- [ ] Community contributions to config files
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

This script runner approach represents a fundamental improvement in Mel's architecture, providing:

- **90% reduction in codebase size** (200 vs 1,150 lines)
- **Multi-VCS support** with minimal effort
- **Complete transparency** through explain command
- **Automated documentation** generation
- **Better performance** through shell execution
- **Easier maintenance** through configuration-driven design

The phased implementation approach ensures we can deliver working functionality incrementally while maintaining quality and user experience standards.
