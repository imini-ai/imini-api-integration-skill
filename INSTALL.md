# Install imini API Integration Skill

This skill ships **one** capability — generating production-ready async code that integrates imini Open Platform image and video generation into any project. It works with Claude Code, Codex, Cursor, OpenCode, OpenClaw, Hermes, and 50+ other agents that load Markdown-based skills.

## Quick decision

| You are... | Recommended install |
|---|---|
| Any agent (Claude Code, Codex, Cursor, OpenCode, …) | **#1 below** — `npx skills add` |
| Claude Code user, prefer the native plugin flow | **#2 below** — `/plugin marketplace add` |
| No Node, or want a single bash command | **#3 below** — `./setup` |
| Want full manual control | **#4 below** — manual symlink |

## Prerequisites

- Get an imini API key: https://imini.ai/api-keys — one key works for every model.
- (Only for path #1) Node.js for `npx`.

---

## 1. `npx skills add` (recommended — works on 55+ agents)

[`vercel-labs/skills`](https://github.com/vercel-labs/skills) auto-detects the active agent (Claude Code / Codex / Cursor / OpenCode / OpenClaw / Hermes / Junie / Augment / … 55 total) and installs the skill into its conventional skills directory:

```bash
npx skills add imini-ai/imini-api-integration-skill
```

It recursively scans this repo for `SKILL.md` and writes a symlink (or `--copy`) at `~/.<agent>/skills/api-integration/`. Update with the same command.

Useful flags:

```bash
npx skills add imini-ai/imini-api-integration-skill --list                    # preview what would be installed
npx skills add imini-ai/imini-api-integration-skill -a claude-code -a codex   # install to multiple specific agents
npx skills add imini-ai/imini-api-integration-skill --copy                    # copy instead of symlink
npx skills add imini-ai/imini-api-integration-skill -g                        # global (~/.<agent>/) vs project (.<agent>/)
```

## 2. Claude Code marketplace (native flow)

Inside Claude Code:

```
/plugin marketplace add imini-ai/imini-api-integration-skill
/plugin install imini@imini
/reload-plugins
```

The repo's `.claude-plugin/marketplace.json` is read directly from GitHub — no Anthropic-side publishing required. The skill invokes as `/imini:api-integration`. Update later with `/plugin update imini@imini`.

## 3. Setup script (universal bash fallback)

When you can't or don't want to use Node:

```bash
git clone --depth 1 https://github.com/imini-ai/imini-api-integration-skill.git
cd imini-api-integration-skill
./setup
```

Flags:

```bash
./setup --host claude     # force install for Claude Code (~/.claude/skills/)
./setup --host codex      # force install for Codex (~/.codex/skills/)
./setup --host cursor     # force install for Cursor (~/.cursor/skills/)
./setup --name <name>     # customize install directory name (default: imini-api-integration)
./setup --dry-run         # preview without modifying anything
./setup --help            # full options
```

It symlinks `plugins/imini/skills/api-integration` into the host's standalone skills directory. Idempotent — re-run any time. Existing real directories are backed up to `*.bak.<timestamp>` before being replaced.

### ⚠ Important: don't clone INTO the install target

If you clone the repo directly into `~/.claude/skills/imini-api-integration/` (or the equivalent Codex / Cursor path), `setup` will refuse to run because the source and target would be the same directory. Clone to a separate location (for example `~/projects/imini-api-integration-skill/`) and run `./setup` from there.

## 4. Manual symlink

```bash
git clone --depth 1 https://github.com/imini-ai/imini-api-integration-skill.git ~/projects/imini-api-integration-skill
ln -s ~/projects/imini-api-integration-skill/plugins/imini/skills/api-integration ~/.claude/skills/imini-api-integration
```

Substitute `~/.claude/` with `~/.codex/`, `~/.cursor/`, or your agent's home directory as needed. See the full agent list in [`vercel-labs/skills`](https://github.com/vercel-labs/skills#supported-agents).

## Verify

In your agent, ask:

> "How do I generate a 4K image with imini using `google/nano-banana-pro`?"

The agent should consult the skill, ask for your API key (or detect `$IMINI_API_KEY`), fetch the OpenAPI spec, and produce a Python/Node/TypeScript/cURL snippet that:

- Submits to `/v1/images/generate`
- Polls `/v1/images/tasks/{task_id}` with jittered backoff, checking for `succeeded` / `failed` (NOT `completed` / `running`)
- Iterates `images[]` for the URL (not just `[0]`)
- Surfaces structured errors (`error.code` / `error.message` / `error.request_id`)

## Updating

| Install method | Update command |
|---|---|
| `npx skills add` | re-run the same `npx skills add ...` |
| `/plugin marketplace add` | `/plugin update imini@imini` inside Claude Code |
| `./setup` | `cd <repo> && git pull && ./setup` |
| Manual symlink | `cd <repo> && git pull` (the symlink follows the new content automatically) |

## Uninstall

| Install method | Uninstall command |
|---|---|
| `npx skills add` | `npx skills remove imini-ai/imini-api-integration-skill` |
| `/plugin marketplace add` | `/plugin uninstall imini@imini` inside Claude Code |
| `./setup` | `rm ~/.<agent>/skills/imini-api-integration` (only removes the symlink) |
| Manual symlink | same |

## Layout reference

```
imini-api-integration-skill/         # repo root = marketplace root
├── .claude-plugin/
│   └── marketplace.json             # Claude Code marketplace entry, source: "./plugins/imini"
├── plugins/
│   └── imini/                       # the imini plugin (plugin name = "imini")
│       ├── .claude-plugin/
│       │   └── plugin.json          # Claude Code plugin manifest
│       └── skills/
│           └── api-integration/     # the skill itself
│               ├── SKILL.md         # main workflow
│               ├── references/      # decision tree, error guide, code templates
│               └── scripts/         # live catalog fetcher
├── setup                            # universal bash installer
├── INSTALL.md
├── README.md
├── README_CN.md
├── VERSION
└── LICENSE
```

This layout matches the canonical Claude Code plugin marketplace structure (compare with Anthropic's own `claude-plugins-official` repo). `npx skills` recursively discovers `SKILL.md` inside the repo regardless of nesting, so the same layout serves both the Claude Code marketplace path and every other agent `npx skills` supports.
