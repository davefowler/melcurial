# Mel Rewrite Analysis: Lightweight Script Runner Strategy

## Executive Summary

This document analyzes the proposed rewrite of Mel from a monolithic Python script to a lightweight script runner that uses JSON configuration files to define version control commands. The analysis covers implementation strategy, comparison with current approach, evaluation of existing tools, and recommendations.

## Proposed Architecture

### Core Concept
Transform Mel into a minimal script runner that:
- Detects the version control system (git, hg, etc.)
- Loads appropriate default command definitions from JSON files
- Merges with user configuration and package scripts
- Executes commands transparently
- Provides `mel explain <command>` to show what will run

### File Structure
```
mel (executable script)
├── configs/
│   ├── git_defaults.json
│   ├── hg_defaults.json
│   └── svn_defaults.json
└── .mel/
    └── config.json (user overrides)
```

### Example Configuration (git_defaults.json)
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
    "commands": [
      "git add -A",
      "git commit -m \"{message}\"",
      "git fetch origin",
      "git rebase origin/{main}",
      "git push origin HEAD"
    ],
    "requires_message": true,
    "safety_checks": ["not_on_main", "clean_working_tree"],
    "category": "basic",
    "troubleshooting": "If you get conflicts, resolve them and run 'git add -A && git rebase --continue'"
  },
  "publish": {
    "description": "Merge to main and push",
    "help_text": "Merges your branch to main using fast-forward merge, then updates your branch",
    "usage": "mel publish",
    "examples": [
      "mel publish"
    ],
    "commands": [
      "git checkout {main}",
      "git merge --ff-only {branch}",
      "git push origin {main}",
      "git checkout {branch}",
      "git rebase origin/{main}"
    ],
    "confirmation_required": true,
    "category": "basic",
    "troubleshooting": "Make sure your branch is up to date with main first using 'mel save'"
  }
}
```

## Advantages of Script Runner Approach

### 1. **Transparency & Trust**
- Users can see exactly what commands will execute
- `mel explain save` shows the full command sequence
- No hidden behavior or "magic"
- Easy to audit and verify safety

### 2. **Multi-VCS Support**
- Trivial to add Mercurial, SVN, or other VCS support
- Just create new default configuration files
- Same user interface across different systems
- No code duplication for core logic

### 3. **Extensibility**
- Users can override any command via `.mel/config.json`
- Package scripts can be merged in automatically
- Easy to add new commands without code changes
- Community can contribute configuration files

### 4. **Maintainability**
- Core runner is ~100-200 lines of code
- All business logic moves to configuration
- Easier to test (just test command execution)
- Simpler debugging and troubleshooting

### 5. **Performance**
- Faster startup (no Python import overhead)
- Could be written in shell for maximum speed
- Minimal dependencies
- Smaller distribution size

## Comparison: Current vs. Proposed

| Aspect | Current Mel | Script Runner Mel |
|--------|-------------|-------------------|
| **Code Size** | ~1,150 lines Python | ~200 lines shell/Python |
| **Dependencies** | Python 3.8+, Jinja2 | Shell or minimal Python |
| **Transparency** | Commands hidden in code | Commands visible in JSON |
| **Multi-VCS** | Git-only | Trivial to add others |
| **Customization** | Limited config options | Full command override |
| **Maintenance** | Complex Python logic | Simple config management |
| **Performance** | Python startup overhead | Near-instant execution |
| **Debugging** | Python stack traces | Simple command execution |

## Existing Tools Analysis

### 1. **Just** (Rust-based task runner)
- **Pros**: Fast, simple syntax, good documentation
- **Cons**: Rust dependency, not VCS-focused, different paradigm
- **Verdict**: Could work but overkill for this use case

### 2. **Runner** (Bash task runner)
- **Pros**: Pure bash, lightweight, familiar syntax
- **Cons**: Bash-specific, less structured than JSON
- **Verdict**: Good inspiration but JSON config is cleaner

### 3. **Git Aliases**
- **Pros**: Built into git, no external dependencies
- **Cons**: Limited to git, no cross-VCS support, less user-friendly
- **Verdict**: Not suitable for non-engineer target audience

### 4. **Make/Justfile**
- **Pros**: Well-established, powerful
- **Cons**: Complex syntax, not user-friendly, not VCS-focused
- **Verdict**: Too complex for target audience

### 5. **Fossil SCM**
- **Pros**: Integrated VCS with web interface
- **Cons**: Different VCS entirely, not a wrapper
- **Verdict**: Not applicable to git/hg wrapper use case

## Implementation Strategy

### Phase 1: Core Runner
```bash
#!/bin/bash
# Minimal mel runner
VCS=$(detect_vcs)
CONFIG=$(load_config "$VCS")
COMMAND="$1"
shift

if [[ "$COMMAND" == "explain" ]]; then
    explain_command "$CONFIG" "$1"
    exit 0
fi

execute_command "$CONFIG" "$COMMAND" "$@"
```

### Phase 2: Configuration System
- JSON schema for command definitions
- Variable substitution (`{main}`, `{branch}`, `{message}`)
- Safety checks and confirmations
- Hook system for pre/post commands

### Phase 3: Multi-VCS Support
- Detection logic for git, hg, svn
- Default configurations for each system
- Unified command interface

### Phase 4: Advanced Features
- Package script integration
- Configuration templates
- Migration from current Mel

### Phase 5: Documentation Generation
- Auto-generate help text from JSON configs
- Generate HTML documentation from command definitions
- Keep CLI help and web docs in sync automatically
- Single source of truth for all command descriptions

## Risk Analysis

### Potential Issues
1. **Loss of Python Features**: No access to rich libraries, complex logic
2. **Shell Compatibility**: Different shell behaviors across platforms
3. **Error Handling**: Less sophisticated than Python exception handling
4. **User Migration**: Existing users need to migrate configurations

### Mitigation Strategies
1. **Hybrid Approach**: Keep Python for complex features, shell for simple commands
2. **Cross-Platform Testing**: Test on macOS, Linux, Windows (WSL)
3. **Graceful Degradation**: Fall back to Python for complex operations
4. **Migration Tools**: Provide scripts to convert existing configs

## Recommendation

### **Proceed with Script Runner Approach**

The script runner strategy offers significant advantages for Mel's target audience and use case:

1. **Aligns with Goals**: Non-engineers benefit from transparency and simplicity
2. **Future-Proof**: Easy to add new VCS support and features
3. **Maintainable**: Much simpler codebase to maintain and debug
4. **Performant**: Faster execution and smaller footprint

### Implementation Plan

1. **Start Small**: Begin with a shell-based runner for core git commands
2. **Preserve Compatibility**: Maintain current Mel as `mel-legacy` during transition
3. **Iterate**: Add features incrementally based on user feedback
4. **Document**: Create comprehensive migration guide

### Hybrid Approach (Recommended)

Consider a hybrid implementation:
- **Shell runner** for simple, fast commands (save, status, etc.)
- **Python fallback** for complex operations (upgrade, advanced git operations)
- **JSON configuration** for all command definitions
- **Unified interface** regardless of backend

This provides the best of both worlds: speed and transparency for common operations, power and flexibility for complex features.

## Documentation Strategy

### Single Source of Truth
The JSON configuration files become the single source of truth for all documentation:

- **CLI Help**: `mel help` reads from JSON configs and formats output
- **Web Documentation**: HTML docs generated from same JSON files
- **Command Explanations**: `mel explain <command>` shows full command details
- **Examples**: All examples stored in JSON and used everywhere

### Documentation Generation Pipeline

```bash
# Generate CLI help from configs
mel help --generate-cli > help_output.txt

# Generate HTML docs from configs  
mel docs --generate-html --output docs/

# Generate man pages
mel docs --generate-man --output man/
```

### Enhanced JSON Schema for Documentation

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
    "commands": ["actual commands to run"],
    "safety_checks": ["list of safety validations"],
    "confirmation_required": true,
    "requires_message": false
  }
}
```

### Benefits of Documentation Integration

1. **Consistency**: CLI help and web docs always match
2. **Maintainability**: Update command info in one place
3. **Completeness**: All commands automatically documented
4. **Accuracy**: No drift between different documentation sources
5. **Automation**: Docs update automatically when configs change

### Documentation Generation Tools

- **CLI Help Generator**: Reads JSON, formats for terminal output
- **HTML Generator**: Creates web documentation with examples
- **Man Page Generator**: Creates traditional Unix man pages
- **Markdown Generator**: Creates GitHub README sections
- **API Documentation**: Generates JSON schema documentation

## Conclusion

The script runner approach represents a significant improvement over the current monolithic design. It better serves Mel's mission of making version control accessible to non-engineers through transparency, simplicity, and flexibility. The risks are manageable, and the benefits far outweigh the costs.

**Key Innovation**: The JSON configuration files serve as both command definitions AND documentation source, ensuring perfect synchronization between CLI help, web docs, and actual functionality.

**Recommendation: Proceed with the rewrite using a hybrid shell/Python approach with JSON configuration files and integrated documentation generation.**
