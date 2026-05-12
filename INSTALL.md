# Install imini API Integration Skill

This skill ships **one** capability — generating production-ready async code that integrates imini Open Platform image and video generation into any project. It works with Claude Code, Codex, Cursor, and any other agent that loads Markdown-based skills.

## Quick decision

| You are... | Recommended install |
|---|---|
| Claude Code user, want it as a plugin | **#1 below** — `/plugin marketplace add` |
| Cross-agent user, prefer one command | **#2 below** — `npx skills add` |
| Codex / Cursor user, or no Node | **#3 below** — `./setup` |
| Long-time standalone user, want to stay simple | **#4 below** — manual symlink |

## Prerequisites

- Get an imini API key: https://imini.ai/api-keys — one key works for every model.
- (Optional, only for some install paths) Node.js 18+ for `npx skills add`.

---

## 1. Claude Code marketplace

Inside Claude Code:

```
/plugin marketplace add imini-ai/imini-api-integration-skill
/plugin install imini@imini
/reload-plugins
```

Invokes as `/imini:api-integration`. Update later with `/plugin update imini@imini`.

This reads `.claude-plugin/marketplace.json` from the repo — no Anthropic-side publishing required, the repo IS the marketplace.

## 2. `npx skills add` (cross-agent)

[`vercel-labs/skills`](https://github.com/vercel-labs/skills) auto-detects whether you're on Claude Code, Codex, or Cursor and writes the skill to the right path:

```bash
npx skills add imini-ai/imini-api-integration-skill
```

Update with the same command.

## 3. Setup script (universal fallback)

If you can't or don't want to use `/plugin` or `npx`:

```bash
git clone --depth 1 https://github.com/imini-ai/imini-api-integration-skill.git
cd imini-api-integration-skill
./setup
```

Flags:

```bash
./setup --host claude        # force Claude Code install path
./setup --host codex         # force Codex install path
./setup --host cursor        # force Cursor install path
./setup --name my-imini      # customize install dir name
./setup --dry-run            # preview without modifying anything
./setup --help               # full options
```

The script symlinks `skills/api-integration/` into your agent's standalone skills directory (`~/.<agent>/skills/imini-api-integration/`). Idempotent — re-run any time. Existing real directories are backed up to `*.bak.<timestamp>` before being replaced.

### ⚠ Important: don't clone INTO the install target

If you clone the repo directly into `~/.claude/skills/imini-api-integration/` (or the equivalent Codex / Cursor path), setup will refuse to run because the source and target would be the same directory. Clone to a separate location (e.g. `~/projects/imini-api-integration-skill/`) and run `./setup` from there.

## 4. Manual symlink (legacy standalone path)

For users who want the absolute minimum:

```bash
git clone --depth 1 https://github.com/imini-ai/imini-api-integration-skill.git ~/projects/imini-api-integration-skill
ln -s ~/projects/imini-api-integration-skill/skills/api-integration ~/.claude/skills/imini-api-integration
```

(Replace `~/.claude/skills/` with `~/.codex/skills/` or `~/.cursor/skills/` as needed.)

## Verify

In your agent, ask:

> "How do I generate a 4K image with imini using google/nano-banana-pro?"

The agent should consult the skill, ask for your API key (or detect `$IMINI_API_KEY`), fetch the OpenAPI spec, and produce a Python/Node/TypeScript/cURL snippet that:

- Submits to `/v1/images/generate`
- Polls `/v1/images/tasks/{task_id}` with jittered backoff, checking for `succeeded` / `failed` (NOT `completed` / `running`)
- Iterates `images[]` for the URL (not just `[0]`)
- Surfaces structured errors (`error.code` / `error.message` / `error.request_id`)

## Updating

| Install method | Update command |
|---|---|
| `/plugin marketplace add` | `/plugin update imini@imini` inside Claude Code |
| `npx skills add` | re-run the same `npx skills add ...` |
| `./setup` | `cd <repo> && git pull && ./setup` |
| Manual symlink | `cd <repo> && git pull` (the symlink picks up changes automatically) |

## Uninstall

| Install method | Uninstall command |
|---|---|
| `/plugin marketplace add` | `/plugin uninstall imini@imini` inside Claude Code |
| `npx skills add` | `npx skills remove imini-ai/imini-api-integration-skill` |
| `./setup` | `rm ~/.<agent>/skills/imini-api-integration` (only removes the symlink) |
| Manual symlink | same |

## Layout reference

If you're curious what each path means:

```
imini-api-integration-skill/
├── SKILL.md                     # Single source of truth (root, for legacy standalone use)
├── references/                  # Decision tree, error guide, integration templates
├── scripts/                     # Live catalog fetcher
├── .claude-plugin/
│   ├── plugin.json              # Claude Code single-plugin manifest
│   └── marketplace.json         # /plugin marketplace add entry
├── .codex-plugin/plugin.json    # Codex manifest
├── .cursor-plugin/plugin.json   # Cursor manifest
├── skills/
│   └── api-integration/         # Plugin-style skill path (symlinks back to root)
│       ├── SKILL.md             # → ../../SKILL.md
│       ├── references           # → ../../references
│       └── scripts              # → ../../scripts
├── setup                        # Universal install script (symlink-based)
├── VERSION
└── INSTALL.md                   # This file
```

Two valid skill paths coexist for backward compatibility:

- `SKILL.md` at root — original standalone layout (still works for users who manually cloned into `~/.claude/skills/<name>/`)
- `skills/api-integration/SKILL.md` — required by Claude Code's plugin format and used by all four install methods above

Both resolve to the same content via symlinks.
