# Mel Parameter Handling: Current State and Future Design

## The Problem: Why AI Uses Environment Variables

When AI generates Mel integrations, it often defaults to environment variables like:
```bash
JSON=/abs/file.json COLLECTION=NihAI mel ingest:json
OUT=/abs/seed.json COLLECTION=NihAI mel export:json
COLLECTION=NihAI_v3 N=10 mel dataset:nihai:build
```

This happens because:

1. **Unclear Parameter Passing**: The current Mel parameter system isn't well-documented
2. **Shell Script Conventions**: Environment variables are a common pattern in shell scripts
3. **AI Training Bias**: AI models see many examples of env var usage in shell contexts
4. **Lack of Explicit Parameter Schema**: No clear way to define what parameters a script expects

## Current Mel Parameter System

### How It Works Now

Mel currently supports parameter passing through:

#### 1. **Direct Arguments** (Limited)
```bash
mel save "commit message"     # Built-in commands
mel b "branch-name"          # Built-in commands
```

#### 2. **Extra Arguments with `--` Separator**
```bash
mel my-script -- arg1 arg2 arg3
```

#### 3. **Extra Arguments Without Separator** (Fallback)
```bash
mel my-script arg1 arg2 arg3
```

### Current Implementation Analysis

Looking at the code in `run_script_by_name()`:

```python
def run_script_by_name(cfg, name, extra_args):
    # For string commands:
    if extra_args:
        cmd = cmd + " " + " ".join(shlex.quote(a) for a in extra_args)
    
    # For package scripts:
    args = " ".join(shlex.quote(a) for a in extra_args) if extra_args else ""
    cmd = f"{pm} run {shlex.quote(name)}" + (f" -- {args}" if args else "")
```

**Problems with Current System:**
1. **No Parameter Validation**: Arguments are blindly appended
2. **No Parameter Documentation**: No way to specify what parameters are expected
3. **Inconsistent Behavior**: Different handling for different script types
4. **No Named Parameters**: Only positional arguments supported
5. **Poor Error Messages**: No help when wrong parameters are provided

## Proposed Enhanced Parameter System

### Design Goals

1. **Explicit Parameter Definition**: Scripts declare what parameters they expect
2. **Multiple Parameter Styles**: Support both positional and named parameters
3. **Automatic Documentation**: Parameters auto-generate help text
4. **Validation**: Type checking and required parameter validation
5. **Backward Compatibility**: Existing scripts continue to work
6. **AI-Friendly**: Clear patterns that AI can easily follow

### Enhanced JSON Schema for Scripts

```json
{
  "scripts": {
    "ingest:json": {
      "cmd": "python scripts/ingest.py",
      "description": "Import JSON data into collection",
      "parameters": {
        "json_file": {
          "type": "string",
          "required": true,
          "description": "Path to JSON file to import",
          "position": 1,
          "env_var": "JSON"
        },
        "collection": {
          "type": "string", 
          "required": true,
          "description": "Collection name to import into",
          "position": 2,
          "env_var": "COLLECTION"
        },
        "dry_run": {
          "type": "boolean",
          "required": false,
          "default": false,
          "description": "Show what would be imported without doing it",
          "flag": "--dry-run"
        }
      }
    },
    
    "export:json": {
      "cmd": "python scripts/export.py",
      "description": "Export collection to JSON file",
      "parameters": {
        "output_file": {
          "type": "string",
          "required": true,
          "description": "Output JSON file path",
          "position": 1,
          "env_var": "OUT"
        },
        "collection": {
          "type": "string",
          "required": true,
          "description": "Collection name to export",
          "position": 2,
          "env_var": "COLLECTION"
        },
        "format": {
          "type": "string",
          "required": false,
          "default": "json",
          "description": "Export format (json, csv, xml)",
          "flag": "--format"
        }
      }
    },
    
    "dataset:nihai:build": {
      "cmd": "python scripts/build_dataset.py",
      "description": "Build NihAI dataset",
      "parameters": {
        "collection": {
          "type": "string",
          "required": true,
          "description": "Collection name",
          "position": 1,
          "env_var": "COLLECTION"
        },
        "count": {
          "type": "integer",
          "required": true,
          "description": "Number of items to build",
          "position": 2,
          "env_var": "N"
        },
        "batch_size": {
          "type": "integer",
          "required": false,
          "default": 100,
          "description": "Batch size for processing",
          "flag": "--batch-size"
        }
      }
    }
  }
}
```

### Parameter Types and Handling

#### 1. **Positional Parameters**
```bash
# These are equivalent:
mel ingest:json /path/to/file.json my-collection
mel ingest:json --json-file /path/to/file.json --collection my-collection
JSON=/path/to/file.json COLLECTION=my-collection mel ingest:json
```

#### 2. **Named Parameters (Flags)**
```bash
mel export:json output.json my-collection --format csv
mel dataset:nihai:build my-collection 100 --batch-size 50
```

#### 3. **Environment Variables** (AI-Friendly)
```bash
JSON=/path/to/file.json COLLECTION=my-collection mel ingest:json
OUT=output.json COLLECTION=my-collection FORMAT=csv mel export:json
```

#### 4. **Mixed Styles**
```bash
# Positional + flags
mel ingest:json /path/to/file.json my-collection --dry-run

# Env vars + flags  
JSON=/path/to/file.json COLLECTION=my-collection mel ingest:json --dry-run
```

### Parameter Resolution Order

1. **Environment Variables** (highest priority)
2. **Command Line Flags** (`--param=value`)
3. **Positional Arguments** (by position)
4. **Default Values** (lowest priority)

### Enhanced Help Generation

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

### Implementation in New Script Runner

#### Parameter Parser (`core/parameter_parser.py`)
```python
def parse_parameters(script_config: dict, args: list, env: dict) -> dict:
    """Parse parameters from command line and environment"""
    
def validate_parameters(script_config: dict, parsed_params: dict) -> bool:
    """Validate parameter types and required fields"""
    
def build_command_with_params(script_config: dict, params: dict) -> str:
    """Build final command with parameter substitution"""
    
def generate_parameter_help(script_config: dict) -> str:
    """Generate help text for script parameters"""
```

#### Enhanced Command Execution
```python
def execute_script_with_params(script_config: dict, args: list) -> int:
    """Execute script with full parameter support"""
    
    # Parse parameters
    params = parse_parameters(script_config, args, os.environ)
    
    # Validate parameters  
    if not validate_parameters(script_config, params):
        return 1
        
    # Build command with parameter substitution
    cmd = build_command_with_params(script_config, params)
    
    # Execute command
    return run_command(cmd)
```

### Backward Compatibility

#### Legacy Script Support
```json
{
  "scripts": {
    "old-script": "echo 'This still works'",
    "old-script-with-args": "python script.py"
  }
}
```

Legacy scripts continue to work exactly as before, with extra arguments appended directly.

#### Migration Path
```json
{
  "scripts": {
    "migrated-script": {
      "cmd": "python script.py",
      "description": "Updated script with parameters",
      "parameters": {
        "input": {
          "type": "string",
          "required": true,
          "position": 1
        }
      }
    }
  }
}
```

### AI-Friendly Patterns

#### 1. **Clear Parameter Documentation**
```json
{
  "parameters": {
    "json_file": {
      "description": "Path to JSON file to import",
      "env_var": "JSON",
      "example": "JSON=/path/to/file.json mel ingest:json"
    }
  }
}
```

#### 2. **Multiple Input Methods**
```bash
# AI can use any of these patterns:
mel ingest:json file.json collection
mel ingest:json --json-file file.json --collection collection  
JSON=file.json COLLECTION=collection mel ingest:json
```

#### 3. **Consistent Naming**
- Environment variables match parameter names (uppercase)
- Flag names use kebab-case
- Positional parameters have clear descriptions

### Error Handling and Validation

#### Parameter Validation
```bash
$ mel ingest:json
✖ Missing required parameter: json_file
Usage: mel ingest:json <json_file> <collection>
  or: JSON=<file> COLLECTION=<name> mel ingest:json

$ mel ingest:json file.json
✖ Missing required parameter: collection  
Usage: mel ingest:json <json_file> <collection>
  or: JSON=<file> COLLECTION=<name> mel ingest:json

$ mel ingest:json file.json collection --invalid-flag
✖ Unknown parameter: invalid-flag
Available parameters: --dry-run
```

#### Type Validation
```bash
$ mel dataset:nihai:build collection not-a-number
✖ Parameter 'count' must be an integer, got 'not-a-number'
Usage: mel dataset:nihai:build <collection> <count>
```

### Benefits of Enhanced System

#### 1. **For AI Integration**
- Clear parameter patterns to follow
- Multiple input methods (positional, flags, env vars)
- Automatic help generation
- Consistent error messages

#### 2. **For Users**
- Better help text and examples
- Parameter validation and error messages
- Flexible input methods
- Auto-completion support (future)

#### 3. **For Developers**
- Explicit parameter contracts
- Type safety and validation
- Better debugging and testing
- Documentation generation

#### 4. **For Teams**
- Standardized script interfaces
- Consistent parameter patterns
- Better onboarding for new team members
- Reduced support requests

## Implementation Timeline

### Phase 1: Core Parameter System
- [ ] Parameter parser implementation
- [ ] Basic validation and type checking
- [ ] Enhanced JSON schema support
- [ ] Backward compatibility maintenance

### Phase 2: Enhanced Features
- [ ] Multiple parameter input methods
- [ ] Advanced validation rules
- [ ] Help text generation
- [ ] Error message improvements

### Phase 3: AI-Friendly Features
- [ ] Environment variable mapping
- [ ] Consistent naming conventions
- [ ] Example generation
- [ ] Documentation improvements

### Phase 4: Advanced Features
- [ ] Auto-completion support
- [ ] Parameter suggestions
- [ ] Interactive parameter prompts
- [ ] Configuration templates

## Conclusion

The enhanced parameter system addresses the core issue of why AI defaults to environment variables: **lack of clear, documented parameter patterns**. By providing:

1. **Explicit parameter definitions** in JSON
2. **Multiple input methods** (positional, flags, env vars)
3. **Automatic documentation** generation
4. **Consistent error handling**
5. **Backward compatibility**

We create a system that's both user-friendly and AI-friendly, while maintaining the simplicity that makes Mel appealing to non-engineers.

The key insight is that AI uses environment variables not because they're better, but because they're the most explicit and well-documented pattern available. By making Mel's parameter system equally explicit and well-documented, we can guide AI toward better patterns while maintaining flexibility for all users.
