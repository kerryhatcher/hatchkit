# hatchkit

> A tool to help with AI driven development.

[![PyPI](https://img.shields.io/pypi/v/hatchkit)](https://pypi.org/project/hatchkit/)
[![Python](https://img.shields.io/pypi/pyversions/hatchkit)](https://pypi.org/project/hatchkit/)
[![License](https://img.shields.io/github/license/kerryhatcher/hatchkit)](LICENSE)

---

## ⚡ Get Started

### Option 1 — Persistent installation (recommended)

```bash
uv tool install hatchkit
```

Then use `hatchkit` anywhere:

```bash
hatchkit init my-project --ai copilot
hatchkit check
```

### Option 2 — Run once without installing

```bash
uvx hatchkit init my-project --ai claude
```

### Upgrade

```bash
uv tool upgrade hatchkit
```

---

## 🔧 CLI Reference

### `hatchkit init [PROJECT_NAME]`

Initialise a new hatchkit project with AI agent configuration files.

| Argument / Option | Description |
|---|---|
| `PROJECT_NAME` | New project directory name (omit to use `--here` or `.`) |
| `--here` | Initialise in the current directory |
| `--force` | Overwrite existing files without prompting |
| `--ai` | AI agent to configure: `claude`, `copilot`, `cursor`, `gemini`, `codex`, `generic` |

**Examples**

```bash
# Create a new project directory
hatchkit init my-project

# Initialise in the current directory with Claude Code support
hatchkit init --here --ai claude

# Initialise with GitHub Copilot support
hatchkit init . --ai copilot
```

### `hatchkit check`

Check whether the required tools and AI agents are installed on your system.

```bash
hatchkit check
```

### `hatchkit version`

Print the installed hatchkit version.

```bash
hatchkit version
```

---

## 📦 Development

This project uses [uv](https://docs.astral.sh/uv/) for environment and package management.

```bash
# Clone and set up
git clone https://github.com/kerryhatcher/hatchkit.git
cd hatchkit
uv sync

# Run the CLI from source
uv run hatchkit --help

# Run tests
uv run pytest

# Lint
uv run ruff check .
```

### Publishing to PyPI

```bash
uv build
uv publish
```

---

## License

[MIT](LICENSE)
