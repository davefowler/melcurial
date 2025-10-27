# Parameter Standards and Documentation Hosting

## Package.json Scripts Parameter Handling

### Current npm Scripts Standards

#### 1. **Command Line Arguments with `--` Separator**
```bash
# package.json
{
  "scripts": {
    "start": "node server.js",
    "test": "jest",
    "build": "webpack"
  }
}

# Usage
npm run start -- --port=8080 --env=production
npm run test -- --watch --coverage
npm run build -- --mode=production
```

#### 2. **Environment Variables with `npm_config_` Prefix**
```bash
# Usage
npm run start --port=8080 --env=production

# In script, access via:
process.env.npm_config_port    # "8080"
process.env.npm_config_env     # "production"
```

#### 3. **Direct Environment Variables**
```bash
# Usage
PORT=8080 NODE_ENV=production npm run start

# In script, access via:
process.env.PORT       # "8080"
process.env.NODE_ENV   # "production"
```

### Package.json Scripts Limitations

**What npm scripts DON'T support:**
- No parameter validation
- No parameter documentation
- No type checking
- No default values
- No required parameter enforcement
- No help text generation

## Other Task Runner Standards

### Makefile Parameters
```makefile
# Makefile
.PHONY: build test deploy

build:
	@echo "Building for environment: $(ENV)"
	webpack --mode=$(ENV)

test:
	@echo "Running tests with coverage: $(COVERAGE)"
	jest --coverage=$(COVERAGE)

deploy:
	@echo "Deploying to: $(TARGET)"
	rsync -av dist/ $(TARGET)/

# Usage
make build ENV=production
make test COVERAGE=true
make deploy TARGET=user@server:/var/www
```

### Justfile Parameters
```justfile
# justfile
set shell := ["bash", "-c"]

# Default parameters
ENV := "development"
PORT := 3000

# Tasks with parameters
serve env ENV PORT:
    @echo "Starting server in {{env}} mode on port {{port}}"
    node server.js --env={{env}} --port={{port}}

test watch COVERAGE="false":
    @echo "Running tests with watch={{watch}}, coverage={{coverage}}"
    jest --watch={{watch}} --coverage={{coverage}}

build target ENV="production":
    @echo "Building {{target}} for {{env}}"
    webpack --mode={{env}} --output={{target}}

# Usage
just serve development 8080
just test true true
just build dist production
```

### Task Runner Comparison

| Feature | npm scripts | Makefile | Justfile | Mel (Proposed) |
|---------|-------------|----------|----------|----------------|
| **Parameter Passing** | `--` separator | Environment vars | Named parameters | Multiple methods |
| **Parameter Validation** | ❌ | ❌ | ❌ | ✅ |
| **Type Checking** | ❌ | ❌ | ❌ | ✅ |
| **Default Values** | ❌ | ❌ | ✅ | ✅ |
| **Required Parameters** | ❌ | ❌ | ❌ | ✅ |
| **Help Generation** | ❌ | ❌ | ✅ | ✅ |
| **Documentation** | ❌ | ❌ | ❌ | ✅ |
| **Environment Variables** | ✅ | ✅ | ✅ | ✅ |

## Recommended Mel Parameter System

### Align with npm Scripts Standards

Since Mel will commonly ingest scripts from `package.json`, we should align with npm's conventions while adding our enhancements:

#### 1. **Support npm's `--` Separator**
```bash
# These should work identically:
npm run my-script -- --port=8080 --env=production
mel my-script -- --port=8080 --env=production
```

#### 2. **Support npm's Environment Variable Pattern**
```bash
# These should work identically:
npm run my-script --port=8080 --env=production
mel my-script --port=8080 --env=production
```

#### 3. **Enhanced JSON Schema for npm Compatibility**
```json
{
  "scripts": {
    "my-script": {
      "cmd": "node server.js",
      "description": "Start the server",
      "parameters": {
        "port": {
          "type": "integer",
          "required": true,
          "description": "Port number to listen on",
          "position": 1,
          "env_var": "PORT",
          "npm_config": "port",
          "default": 3000
        },
        "env": {
          "type": "string",
          "required": false,
          "description": "Environment mode",
          "env_var": "NODE_ENV",
          "npm_config": "env",
          "default": "development"
        }
      }
    }
  }
}
```

### Parameter Resolution Order (npm Compatible)

1. **Command Line Flags** (`--param=value`)
2. **Environment Variables** (`PARAM=value`)
3. **npm_config Variables** (`npm_config_param`)
4. **Default Values** (from JSON config)

### Backward Compatibility with npm Scripts

```json
{
  "scripts": {
    // Legacy npm script - works exactly as before
    "legacy-script": "node server.js",
    
    // Enhanced mel script - adds parameter support
    "enhanced-script": {
      "cmd": "node server.js",
      "parameters": {
        "port": {
          "type": "integer",
          "default": 3000,
          "env_var": "PORT"
        }
      }
    }
  }
}
```

## Mel Docs Command Implementation

### Feature Overview

The `mel docs` command would host documentation specific to the user's current configuration, making it always up-to-date and relevant.

### Implementation Strategy

#### 1. **Dynamic Documentation Server**
```python
def cmd_docs(port=8080, host="localhost", open_browser=True):
    """Start documentation server for current configuration"""
    
    # Generate documentation from current config
    config = load_merged_config(detect_vcs())
    docs_html = generate_docs_html(config)
    
    # Start lightweight HTTP server
    server = start_docs_server(docs_html, port, host)
    
    # Open browser if requested
    if open_browser:
        open_url(f"http://{host}:{port}")
    
    print(f"📚 Documentation server running at http://{host}:{port}")
    print("Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✓ Documentation server stopped")
```

#### 2. **Real-time Configuration Monitoring**
```python
def watch_config_changes(callback):
    """Watch for configuration file changes and regenerate docs"""
    
    import watchdog
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    
    class ConfigHandler(FileSystemEventHandler):
        def on_modified(self, event):
            if event.src_path.endswith('.mel/config.json'):
                callback()  # Regenerate documentation
    
    observer = Observer()
    observer.schedule(ConfigHandler(), '.mel/', recursive=False)
    observer.start()
    return observer
```

#### 3. **Enhanced Documentation Generation**
```python
def generate_docs_html(config: dict) -> str:
    """Generate HTML documentation from current configuration"""
    
    # Generate command documentation
    commands_html = generate_commands_section(config)
    
    # Generate configuration documentation
    config_html = generate_config_section(config)
    
    # Generate examples based on user's scripts
    examples_html = generate_examples_section(config)
    
    # Combine with template
    return render_docs_template({
        'commands': commands_html,
        'config': config_html,
        'examples': examples_html,
        'user_config': config
    })
```

### Usage Examples

#### Basic Usage
```bash
# Start docs server on default port (8080)
mel docs

# Start on custom port
mel docs --port 3000

# Start without opening browser
mel docs --no-open

# Start on different host
mel docs --host 0.0.0.0 --port 8080
```

#### Advanced Usage
```bash
# Generate static docs instead of serving
mel docs --generate --output ./docs/

# Generate docs for specific VCS
mel docs --vcs git --generate --output ./git-docs/

# Watch mode - auto-regenerate on config changes
mel docs --watch --port 8080
```

### Documentation Features

#### 1. **User-Specific Content**
- Commands available in their configuration
- Their custom scripts and parameters
- Their current settings and overrides
- Examples using their actual configuration

#### 2. **Interactive Features**
- Command search and filtering
- Parameter validation examples
- Live configuration editor
- Command explanation with actual git commands

#### 3. **Multi-VCS Support**
- Documentation adapts to detected VCS (git, hg, etc.)
- VCS-specific command explanations
- VCS-specific examples and workflows

### Implementation Complexity

#### **Low Complexity** (Recommended MVP)
```bash
mel docs                    # Start server on port 8080
mel docs --port 3000       # Custom port
mel docs --no-open         # Don't open browser
```

**Implementation**: ~100 lines of Python using `http.server`

#### **Medium Complexity** (Enhanced)
```bash
mel docs --watch           # Auto-reload on config changes
mel docs --generate        # Generate static files
mel docs --vcs git         # Force specific VCS
```

**Implementation**: ~300 lines with `watchdog` for file monitoring

#### **High Complexity** (Full Featured)
```bash
mel docs --interactive     # Live config editor
mel docs --search "save"   # Search functionality
mel docs --export pdf      # Export to PDF
```

**Implementation**: ~500+ lines with full web framework

### Benefits of `mel docs`

#### 1. **Always Current**
- Documentation reflects actual configuration
- No drift between docs and reality
- Automatic updates when config changes

#### 2. **User-Specific**
- Shows only relevant commands
- Uses actual user settings in examples
- Highlights user's custom scripts

#### 3. **Interactive**
- Can test commands directly from docs
- Live parameter validation
- Configuration editing interface

#### 4. **Offline Access**
- No internet required
- Fast local serving
- Always available

### Integration with Existing Plan

#### Phase 3 Addition: Documentation Hosting
```python
# Add to generators/docs_generator.py
def start_docs_server(config: dict, port: int = 8080, host: str = "localhost") -> HTTPServer:
    """Start HTTP server for documentation"""
    
def generate_interactive_docs(config: dict) -> str:
    """Generate interactive documentation HTML"""
    
def watch_config_changes(callback) -> Observer:
    """Watch for configuration changes"""
```

#### New Command in git_defaults.json
```json
{
  "docs": {
    "description": "Start documentation server",
    "help_text": "Host documentation for your current configuration",
    "usage": "mel docs [--port PORT] [--no-open]",
    "examples": [
      "mel docs",
      "mel docs --port 3000",
      "mel docs --no-open"
    ],
    "mode": "advanced",
    "commands": [
      "python -c \"import mel.docs; mel.docs.serve()\""
    ],
    "parameters": {
      "port": {
        "type": "integer",
        "default": 8080,
        "description": "Port to serve documentation on"
      },
      "no_open": {
        "type": "boolean",
        "default": false,
        "description": "Don't open browser automatically"
      }
    }
  }
}
```

## Conclusion

### Parameter System Recommendation

**Align closely with npm scripts standards** while adding enhancements:

1. **Support npm's `--` separator** for maximum compatibility
2. **Support npm's environment variable patterns** (`npm_config_*`)
3. **Add parameter validation and documentation** on top of npm standards
4. **Maintain backward compatibility** with existing npm scripts

### Mel Docs Recommendation

**Implement as MVP** (low complexity):
- Basic HTTP server serving generated docs
- Port and host configuration
- Auto-open browser option
- Real-time config monitoring (optional)

This provides immediate value while keeping implementation simple and maintainable.

The combination of npm-compatible parameters and hosted documentation creates a powerful, user-friendly system that feels familiar to developers while providing the transparency and ease-of-use that makes Mel special.
