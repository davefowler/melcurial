# Mel Docs Dependency Analysis

## Current Documentation System

### Dependencies
- **Jinja2**: Template engine (already in pyproject.toml)
- **Python stdlib**: `pathlib`, `shutil`, `importlib` (no extra deps)
- **Templates**: 5 Jinja2 templates + assets

### Current Build Process
```python
# scripts/build_docs.py (66 lines)
- Loads mel module to get help constants
- Uses Jinja2 to render templates
- Copies assets directory
- Generates 4 HTML files
```

## Mel Docs Implementation Options

### Option 1: Built-in (Recommended)
**Dependencies**: Only Jinja2 (already required)

#### Implementation
```python
# ~150 lines of Python
def cmd_docs(port=8080, host="localhost", open_browser=True):
    """Start documentation server"""
    
    # Generate HTML from current config (reuse existing logic)
    html = generate_docs_html(load_merged_config(detect_vcs()))
    
    # Start simple HTTP server (stdlib only)
    import http.server
    import socketserver
    
    class DocsHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(html.encode())
            else:
                super().do_GET()
    
    with socketserver.TCPServer((host, port), DocsHandler) as httpd:
        if open_browser:
            open_url(f"http://{host}:{port}")
        print(f"📚 Documentation at http://{host}:{port}")
        httpd.serve_forever()
```

#### Pros
- **Zero additional dependencies** (Jinja2 already required)
- **Simple implementation** (~150 lines)
- **Always available** - no separate install
- **Fast startup** - no package downloads

#### Cons
- **Slightly larger mel binary** (+~150 lines)
- **All users get docs code** (even if they don't use it)

### Option 2: Optional Add-on (`mel upgrade:docs`)
**Dependencies**: Jinja2 + additional packages

#### Implementation
```python
# Separate package: mel-docs
def install_docs_extension():
    """Install mel docs extension"""
    # Download and install mel-docs package
    # Add docs command to mel
```

#### Pros
- **Smaller core mel** - only essential functionality
- **Optional feature** - users choose to install
- **Can have more dependencies** - could use Flask, etc.

#### Cons
- **Additional complexity** - package management
- **Installation friction** - extra step for users
- **Dependency management** - version conflicts
- **More maintenance** - separate package to maintain

## Dependency Analysis

### Current Mel Dependencies
```toml
dependencies = [
  "Jinja2>=3.1",  # Already required for current docs
]
```

### For Built-in Mel Docs
```toml
dependencies = [
  "Jinja2>=3.1",  # Same as current - no change
]
```

### For Optional Mel Docs
```toml
# mel package
dependencies = [
  "Jinja2>=3.1",
]

# mel-docs package (separate)
dependencies = [
  "Jinja2>=3.1",
  "watchdog>=2.0",  # For file watching
  "flask>=2.0",     # For better web server
]
```

## Code Size Analysis

### Current Documentation System
- **build_docs.py**: 66 lines
- **Templates**: 5 files (~200 lines total)
- **Assets**: 1 image file

### Built-in Mel Docs Addition
- **docs_server.py**: ~150 lines
- **Reuse existing templates**: 0 additional lines
- **Reuse existing assets**: 0 additional files
- **Total addition**: ~150 lines

### Optional Mel Docs Package
- **docs_server.py**: ~150 lines
- **package management**: ~100 lines
- **install/uninstall logic**: ~50 lines
- **Total**: ~300 lines across multiple files

## Recommendation: Built-in Implementation

### Why Built-in is Better

#### 1. **Zero Additional Dependencies**
- Jinja2 is already required
- No new packages to install
- No version conflicts

#### 2. **Simpler User Experience**
```bash
# Built-in - works immediately
mel docs

# vs Optional - requires extra step
mel upgrade:docs
mel docs
```

#### 3. **Lower Maintenance Burden**
- Single package to maintain
- No separate versioning
- No installation issues

#### 4. **Better Integration**
- Can access mel internals directly
- No import/plugin complexity
- Seamless configuration access

### Implementation Strategy

#### Phase 1: Basic Server (MVP)
```python
# Add to core/runner.py
def cmd_docs(port=8080, host="localhost", open_browser=True):
    """Start documentation server for current configuration"""
    
    # Generate HTML from current config
    config = load_merged_config(detect_vcs())
    html = generate_docs_html(config)
    
    # Start simple HTTP server
    start_docs_server(html, port, host, open_browser)
```

#### Phase 2: Enhanced Features
```python
# Add file watching (optional dependency)
def cmd_docs_watch(port=8080, host="localhost"):
    """Start docs server with auto-reload on config changes"""
    
    # Only import watchdog if user requests watch mode
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        # Implement file watching
    except ImportError:
        print("⚠️  File watching requires 'pip install watchdog'")
        print("   Falling back to basic docs server")
        cmd_docs(port, host, True)
```

### Template Reuse Strategy

#### Reuse Existing Templates
```python
def generate_docs_html(config: dict) -> str:
    """Generate HTML using existing templates"""
    
    # Load existing Jinja2 environment
    env = Environment(
        loader=FileSystemLoader("templates/"),
        autoescape=select_autoescape(["html", "xml"])
    )
    
    # Use existing base template
    template = env.get_template("base.html.j2")
    
    # Generate content from config
    content = generate_content_from_config(config)
    
    return template.render(
        title="Mel Documentation",
        content=content,
        config=config
    )
```

#### Minimal Template Changes
- **Reuse**: `base.html.j2`, `assets/`
- **Modify**: `index.html.j2` to be config-driven
- **Add**: Dynamic content generation

### File Structure
```
mel (executable)
├── core/
│   ├── runner.py          # Add cmd_docs()
│   ├── config.py          # Existing
│   └── docs_server.py     # New (~150 lines)
├── templates/             # Existing (reuse)
│   ├── base.html.j2
│   ├── index.html.j2
│   └── assets/
└── configs/               # Existing
    ├── git_defaults.json
    └── config_schema.json
```

## Alternative: Hybrid Approach

### Core + Optional Enhancement
```python
def cmd_docs(port=8080, host="localhost", open_browser=True, watch=False):
    """Start documentation server"""
    
    if watch:
        # Try enhanced version with file watching
        try:
            cmd_docs_enhanced(port, host, open_browser)
        except ImportError:
            print("⚠️  Enhanced docs (--watch) requires 'pip install watchdog'")
            print("   Starting basic docs server...")
            cmd_docs_basic(port, host, open_browser)
    else:
        cmd_docs_basic(port, host, open_browser)
```

### Benefits
- **Basic functionality**: Always available
- **Enhanced features**: Optional with extra dependencies
- **Graceful degradation**: Falls back to basic if enhanced not available

## Conclusion

### **Recommendation: Built-in Implementation**

**Why:**
1. **Zero additional dependencies** (Jinja2 already required)
2. **Simpler user experience** (no separate install)
3. **Lower maintenance burden** (single package)
4. **Better integration** (direct access to mel internals)

**Implementation:**
- **~150 lines** of additional code
- **Reuse existing templates** and assets
- **Simple HTTP server** using Python stdlib
- **Optional enhancements** (file watching) with graceful fallback

**User Experience:**
```bash
# Works immediately - no setup required
mel docs

# Optional enhancement (if user wants it)
pip install watchdog
mel docs --watch
```

This approach gives us the best of both worlds: a simple, always-available docs server with the option to enhance it for users who want more features.
