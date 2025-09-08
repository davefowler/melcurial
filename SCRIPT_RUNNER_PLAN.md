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
    "category": "basic|advanced|troubleshooting",
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
    "category": "basic",
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
    "category": "basic",
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
    "category": "basic",
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
    "category": "basic",
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
    "category": "advanced",
    "commands": [
      "git fetch origin",
      "git checkout -B {branch_name} origin/{main}"
    ],
    "safety_checks": ["clean_working_tree"],
    "requires_args": true
  },
  
  "update": {
    "description": "Update with latest main",
    "help_text": "Rebase on the latest from main",
    "usage": "mel update",
    "examples": ["mel update"],
    "category": "advanced",
    "commands": [
      "git fetch origin",
      "git rebase origin/{main}"
    ],
    "safety_checks": ["not_on_main", "clean_working_tree"]
  },
  
  "diff": {
    "description": "Show diff stats",
    "help_text": "Show staged/unstaged diff stats",
    "usage": "mel diff",
    "examples": ["mel diff"],
    "category": "advanced",
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
    "category": "advanced",
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
    "category": "advanced",
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
    "category": "advanced",
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
**Goal**: Automated documentation generation

#### Deliverables:
- [ ] CLI help generator
- [ ] HTML documentation generator
- [ ] Markdown documentation generator
- [ ] Man page generator
- [ ] Documentation build pipeline

#### Files to Create:
```
generators/help_generator.py
generators/docs_generator.py
generators/man_generator.py
utils/template_engine.py
```

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

#### Features to Implement:
- [ ] Pre/post command hooks
- [ ] Package.json script integration
- [ ] Configuration templates
- [ ] Migration utilities
- [ ] Performance profiling

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
