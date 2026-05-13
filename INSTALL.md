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

It recursively scans this repo for `SKILL.md` and writes a symlink (or `--copy`) at `~/.<agent>/skills/imini-generate/`. Update with the same command.

Useful flags:

```bash
npx skills add imini-ai/imini-api-integration-skill --list                    # preview what would be installed
npx skills add imini-ai/imini-api-integration-skill -a claude-code -a codex   # install to multiple specific agents
npx skills add imini-ai/imini-api-integration-skill --copy                    # copy instead of symlink
npx skills add imini-ai/imini-api-integration-skill -g                        # global (~/.<agent>/) vs project (.<agent>/)
```

### Troubleshooting: `npx` fails with `EEXIST` / npm cache error

If you see something like:

```
npm error code EEXIST
npm error syscall rename
npm error path ...
```

That's a stale npm cache, unrelated to this repo. Clean it and retry:

```bash
npm cache clean --force
npx skills add imini-ai/imini-api-integration-skill
```

If you still want a Node-free path, jump to **#3 `./setup`** below.

### Codex fallback: bundled installer (`install-skill-from-github.py`)

If you're on Codex and your Agent falls back to Codex's bundled installer at `~/.codex/skills/.system/skill-installer/`, it requires the skill path **explicitly** — it does not auto-discover `SKILL.md` outside the repo root. Tell it (or paste this when prompted):

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
    --repo imini-ai/imini-api-integration-skill \
    --path skills/imini-generate
```

The `--path` is the same value declared as `skills` in our `.codex-plugin/plugin.json`, so a Codex Agent that reads that manifest first should already derive this command without you typing it. Result lands at `~/.codex/skills/imini-generate/`. Restart Codex to pick it up.

## 2. Claude Code marketplace (native flow)

Inside Claude Code:

```
/plugin marketplace add imini-ai/imini-api-integration-skill
/plugin install imini@imini
/reload-plugins
```

The repo's `.claude-plugin/marketplace.json` is read directly from GitHub — no Anthropic-side publishing required. The skill invokes as `/imini:imini-generate`. Update later with `/plugin update imini@imini`.

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
./setup --name <name>     # customize install directory name (default: imini-generate)
./setup --dry-run         # preview without modifying anything
./setup --help            # full options
```

It symlinks `skills/imini-generate` into the host's standalone skills directory. Idempotent — re-run any time. Existing real directories are backed up to `*.bak.<timestamp>` before being replaced.

### ⚠ Important: don't clone INTO the install target

If you clone the repo directly into `~/.claude/skills/imini-generate/` (or the equivalent Codex / Cursor path), `setup` will refuse to run because the source and target would be the same directory. Clone to a separate location (for example `~/projects/imini-api-integration-skill/`) and run `./setup` from there.

## 4. Manual symlink

```bash
git clone --depth 1 https://github.com/imini-ai/imini-api-integration-skill.git ~/projects/imini-api-integration-skill
ln -s ~/projects/imini-api-integration-skill/skills/imini-generate ~/.claude/skills/imini-generate
```

Substitute `~/.claude/` with `~/.codex/`, `~/.cursor/`, or your agent's home directory as needed. See the full agent list in [`vercel-labs/skills`](https://github.com/vercel-labs/skills#supported-agents).

## Verify

The skill has two operating modes — both should work after install.

### Path A — one-shot generation (bundled scripts)

For "generate me an image / video right now" the skill ships executable scripts. Quickest possible smoke test (after `export IMINI_API_KEY='sk-...'`):

```bash
# Sanity check: list available models (works offline after first 24h cache hit)
python3 ~/.<agent>/skills/imini-generate/scripts/generate_image.py --list-models

# Generate a 1K image (~50 credits, fastest model)
python3 ~/.<agent>/skills/imini-generate/scripts/generate_image.py \
    --model google/nano-banana \
    --prompt "a tiny test image" \
    --output ./test.png
```

Substitute `<agent>` with `claude` / `codex` / `cursor` as appropriate. In conversation, just ask:

> "Generate a test image with imini, nano-banana."

The agent should detect Path A (one-shot) and run the bundled script directly — no Python codegen.

### Path B — integration code for your project

Ask:

> "How do I generate a 4K image with imini using `google/nano-banana-pro` from my Python app?"

The agent should detect Path B (codegen) and produce a Python/Node/TS/cURL snippet that:

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
| `./setup` | `rm ~/.<agent>/skills/imini-generate` (only removes the symlink) |
| Manual symlink | same |

## Layout reference

```
imini-api-integration-skill/         # repo root = marketplace root AND plugin root
├── .claude-plugin/
│   ├── marketplace.json             # marketplace catalog, source: "./" (self-marketplace)
│   └── plugin.json                  # Claude Code plugin manifest (name: "imini")
├── .codex-plugin/
│   └── plugin.json                  # Codex Agent-readable manifest (skills hint + install command)
├── .cursor-plugin/
│   └── plugin.json                  # Cursor manifest (skills path hint)
├── skills/
│   └── imini-generate/             # the skill itself — installed at ~/.<agent>/skills/imini-generate/
│       ├── SKILL.md                 # main workflow
│       ├── references/              # decision tree, error guide, code templates
│       └── scripts/                 # live catalog fetcher + Path A generate/poll scripts
├── setup                            # universal bash installer
├── INSTALL.md
├── README.md
├── README_CN.md
├── VERSION
└── LICENSE
```

After install, `skills/imini-generate/` is placed at `~/.<agent>/skills/imini-generate/` (via symlink or copy depending on the install method). The four manifest files at the repo root tell each agent's loader (Claude Code marketplace, Codex bundled installer, Cursor) where to find the skill.

The `.codex-plugin/` and `.cursor-plugin/` manifests don't currently have known deterministic consumers (Codex's bundled `install-skill-from-github.py` ignores them, and `cursor.com/schemas/cursor-plugin/plugin.json` returns HTTP 500). They are kept as **AI-Agent-readable hints** — Codex Agents that inspect the repo before running the bundled installer will see `"skills": "./skills"` and the `install.command` example, and can derive the correct `--path` argument without listing the tree first.
