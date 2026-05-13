<h1 align="center">
  imini API Integration Skill
</h1>

<p align="center">
  <em>🚀 The official skill for imini open platform — works with 55+ agents (Claude Code, Codex, Cursor, OpenCode, OpenClaw, Hermes, …) via the open <a href="https://github.com/vercel-labs/skills">skills</a> ecosystem</em>
</p>

<p align="center">
  <a href="./README_CN.md">中文文档</a> · English · <a href="./INSTALL.md">Install</a>
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img alt="License" src="https://img.shields.io/badge/License-MIT-blue.svg" /></a>
  <a href="https://github.com/vercel-labs/skills"><img alt="Agents" src="https://img.shields.io/badge/Agents-55%2B-blueviolet.svg" /></a>
  <a href="https://claude.com/claude-code"><img alt="Claude Code" src="https://img.shields.io/badge/Claude_Code-supported-8A3FFC.svg" /></a>
  <a href="#"><img alt="Codex" src="https://img.shields.io/badge/Codex-supported-10A37F.svg" /></a>
  <a href="#"><img alt="Cursor" src="https://img.shields.io/badge/Cursor-supported-000000.svg" /></a>
  <a href="https://docs.imini.ai"><img alt="Models" src="https://img.shields.io/badge/Models-10-green.svg" /></a>
  <a href="https://imini.ai"><img alt="Platform" src="https://img.shields.io/badge/Platform-imini.ai-0070F3.svg" /></a>
</p>

## ✨ What is This?

A cross-agent skill that **automatically** picks the right imini model for your image or video generation task, estimates credit cost, and generates production-ready **async** integration code (submit + poll + result extraction) in your preferred language. No model comparison, no boilerplate, no guesswork.

Works in any agent that loads Markdown skills — Claude Code, Codex, Cursor, and others. See [INSTALL.md](./INSTALL.md) for one-line install across all of them.

## 🎯 Key Features

- 🧠 **Smart Model Selection** — describe what you want to generate; the skill picks the right imini model
- 🔄 **Always Up-to-Date** — model catalog fetched live from `docs.imini.ai/llms.txt`, no reinstall when new models ship
- ⚡ **Complete Async Flow** — submit function + polling loop + result extraction + timeout, not just a POST call
- 💻 **Multi-Language Output** — Python (sync + async), Node.js, TypeScript, cURL
- 💰 **Cost Estimation** — credit estimate before you run
- 🛡️ **Built-in Error Handling** — exponential backoff on 429 / 5xx, full error surfacing on 4xx
- 🎨 **Zero Context Waste** — script-based catalog parsing keeps your conversation small

## 🤖 Supported Models

### 🖼️ Image Models

| Model ID | Underlying | Strengths |
|---|---|---|
| `google/nano-banana` | Gemini 2.5 Flash Image | 🏃 Fast, low-cost, 1K |
| `google/nano-banana-pro` | Gemini 3 Pro Image | 🎯 Up to 4K, 14 reference images, asset / style refs |
| `google/nano-banana-2` | Gemini 3.1 Flash Image | 🎚️ 512 / 1K / 2K / 4K tiers, 14 reference images |
| `openai/gpt-image-2` | OpenAI gpt-image-2 | 🎛️ 1K / 2K / 4K × low / medium / high quality (orthogonal) |

### 🎬 Video Models

| Model ID | Underlying | Strengths |
|---|---|---|
| `kling/kling-v3` | Kling 3.0 | 🎞️ Text/image to video, first-last-frame, multi-reference |
| `kling/kling-v3-omni` | Kling 3.0 Omni | 🎥 Adds **reference-video** input on top of v3, up to 1080P |
| `kling/kling-v3-motion-control` | Kling 3.0 Motion Control | 🕺 Replicate motion from a reference video onto a character |
| `doubao/seedance-2.0` | Seedance 2.0 | 🧬 Multimodal reference (image + video + audio), 480P / 720P |
| `doubao/seedance-2.0-fast` | Seedance 2.0 Fast | 💸 Same features as 2.0, lower cost, 480P / 720P |
| `dashscope/happyhorse-1.0` | HappyHorse 1.0 | ✂️ Text/image/reference-to-video AND **video editing** in one model |

> 📡 Live catalog (always current): https://docs.imini.ai/llms.txt — fetched by the bundled `fetch_imini_catalog.py` script so this list never goes stale in production.

## 🚀 Quick Start

### Installation

See [INSTALL.md](./INSTALL.md) for all four supported paths. The fastest is the cross-agent one-liner:

```bash
npx skills add imini-ai/imini-api-integration-skill
```

This works on Claude Code, Codex, Cursor, OpenCode, OpenClaw, Hermes, and 50+ other agents — `npx skills` auto-detects which one you have and installs the skill into its conventional skills directory.

Or if you're a Claude Code user and prefer the native plugin flow:

```
/plugin marketplace add imini-ai/imini-api-integration-skill
/plugin install imini@imini
```

### Verify

Two paths — each works for a different use case:

**Path A · 🏃 One-shot generation (NEW)** — Just say:

```
"Generate a test image with imini, nano-banana"
"Make a 5-second 1080p video with kling-v3 of a drone over mountains"
```

The agent runs the **bundled Python script** directly — no codegen, no per-session boilerplate. Result file lands in your cwd in seconds.

**Path B · 🛠️ Integration code** — When you want imini *in your project*:

```
"How do I generate a 4K image with imini's google/nano-banana-pro from my Django app?"
"Write TypeScript that batches 100 imini image jobs with concurrency=10"
```

The agent generates a complete async submit/poll snippet in your language of choice.

### Basic Usage

The skill auto-routes based on intent:

| You say | Path | What happens |
|---|---|---|
| "Generate / make / draw …" | **A** | Run `scripts/generate_image.py` or `generate_video.py` |
| "Add imini to / write code for my project" | **B** | Codegen in your chosen language |
| Ambiguous | Agent asks which |

Either way, the skill will:

1. ✅ Detect environment (Python 3.8+ for Path A; Node 18+ / Python / cURL for Path B)
2. ✅ Read `$IMINI_API_KEY` from your shell — never asks you to paste it
3. ✅ Pull the live model catalog from `docs.imini.ai/llms.txt` (24h cache)
4. ✅ Recommend model + cost estimate, get explicit confirmation
5. ✅ Run a script (A) or generate code (B) with proper async handling, jitter, 429 backoff, structured errors, multi-output iteration

## 💡 Usage Examples

### Example 1 · 🎨 Text-to-Image, 4K quality in Python

**You**: *"I want to generate a 4K cinematic image from a prompt using imini's best image model, in Python."*

**Claude Code** (with this skill):

- Picks `google/nano-banana-pro` — supports 4K and style references
- Estimates: **~200 credits per image**
- Generates Python with `IMINI_API_KEY` env var, submit function, polling loop with exponential backoff, and result extraction

### Example 2 · 🎥 Reference-video to 1080P video in Node.js

**You**: *"Generate a 10-second 1080P video guided by a reference video, using imini in Node.js."*

**Claude Code**:

- Picks `kling/kling-v3-omni` — the only model that supports 1080P with reference-video input
- Estimates: **~2,200 credits** (10 s × 220 credits/s)
- 💡 Tip: if dropping to 720P is acceptable, `doubao/seedance-2.0-fast` with reference video can cut the cost substantially — ask the skill to show the comparison

### Example 3 · ⚡ Batch generation with concurrency control

**You**: *"Generate 100 images in parallel with imini, cap concurrency at 10."*

**Claude Code**:

- Generates async Python with `aiohttp` + a semaphore
- Polling loop with rate-limit retry built in
- Logs `task_id` and estimated credit cost per submission

## 🛠️ Advanced Features

### 🔍 Catalog Script

Direct use of the parser:

```bash
# List everything
python3 scripts/fetch_imini_catalog.py

# Filter by type
python3 scripts/fetch_imini_catalog.py --type video

# One specific model
python3 scripts/fetch_imini_catalog.py --model google/nano-banana-pro

# JSON for tooling
python3 scripts/fetch_imini_catalog.py --json
```

### 📦 Zero External Dependencies

The catalog script uses only the Python standard library — no `pip install` required.

## 📚 Documentation Structure

```
imini-api-integration-skill/         # repo root = marketplace root
├── .claude-plugin/
│   └── marketplace.json             # Claude Code marketplace entry, source: "./plugins/imini"
├── .codex-plugin/
│   └── plugin.json                  # Codex Agent-readable manifest (skills hint + install command)
├── .cursor-plugin/
│   └── plugin.json                  # Cursor manifest (skills path hint)
├── plugins/
│   └── imini/                       # the imini plugin (plugin name = "imini")
│       ├── .claude-plugin/
│       │   └── plugin.json          # Claude Code plugin manifest
│       └── skills/
│           └── api-integration/     # the skill itself — also installed as ~/.<agent>/skills/api-integration/
│               ├── SKILL.md         # Routes Path A (run script) vs Path B (codegen)
│               ├── references/      # Path B (codegen) only
│               │   ├── workflow.md            # Async task state machine + polling strategy
│               │   ├── model_selection.md     # Capability decision tree
│               │   ├── integration_examples.md  # Python (sync+async) / Node.js / TypeScript / cURL templates
│               │   └── errors.md              # Authoritative timeout table + error codes + retry policy
│               └── scripts/         # Path A (one-shot generation) + shared catalog fetcher
│                   ├── _imini_common.py        # Shared submit/poll/upload/download/error core
│                   ├── generate_image.py       # CLI: image generation across all current/future models
│                   ├── generate_video.py       # CLI: video generation across all current/future models
│                   ├── poll_image_task.py      # CLI: resume an image task_id (--async / network drop)
│                   ├── poll_video_task.py      # CLI: resume a video task_id
│                   └── fetch_imini_catalog.py  # Live catalog fetcher / parser (stdlib-only)
├── setup                            # Universal bash installer (auto-detects host)
├── INSTALL.md                       # All four install paths and update / uninstall instructions
├── README.md, README_CN.md
├── VERSION
└── LICENSE
```

This layout matches the canonical Claude Code plugin marketplace structure (compare with Anthropic's `claude-plugins-official` repo). `npx skills` recursively discovers `SKILL.md` regardless of nesting, so the same layout serves both the Claude Code marketplace path and every other agent the CLI supports.

## 🔑 API Key

Get your imini API key (one key works for every model):

🔗 https://imini.ai/api-keys

> 🛡️ **Security**: the skill always generates code that reads the key from the `IMINI_API_KEY` environment variable — never hard-coded.

## 🎨 Supported Output Languages

- 🐍 **Python** — sync (`urllib`) and async (`aiohttp`)
- 📜 **Node.js** — native `fetch`
- 📘 **TypeScript** — native `fetch` with types
- 🔧 **cURL** — two-step submit + poll script

## 🌟 Why Use This Skill?

<table>
<tr>
<td width="50%" valign="top">

### 😵 Before (Manual Integration)

```
1. Compare image / video models on imini docs
2. Learn the async task pattern
3. Write submit + polling loop boilerplate
4. Handle 429 / 5xx retry logic
5. Wire up timeouts + concurrency
6. Calculate credit budget
⏱️ Time: 30–60 minutes
```

</td>
<td width="50%" valign="top">

### 🎉 After (With This Skill)

```
1. Ask Claude Code naturally
2. Get production-ready async code
⏱️ Time: 2–3 minutes
```

</td>
</tr>
</table>

## ✅ Requirements

- 🐍 Python 3.8+ — for the catalog script (stdlib only, no `pip install`)
- 🤖 An agent that loads Markdown skills — [Claude Code](https://claude.com/claude-code), Codex, Cursor, OpenCode, OpenClaw, Hermes, or [any of 50+ others](https://github.com/vercel-labs/skills#supported-agents)
- (Generated code only) Node.js 18+ if you choose the JavaScript/TypeScript templates (native `fetch`)

## 🔗 Links

- 🌐 **imini platform**: https://imini.ai
- 📖 **API docs**: https://docs.imini.ai
- 💰 **Pricing**: https://docs.imini.ai/en/guide/pricing
- 📰 **Changelog**: https://docs.imini.ai/en/changelog

## 💬 Support

- 📧 **Email**: support@imini.com

## 📝 License

Licensed under the [MIT License](./LICENSE).

---

<div align="center">

**⭐ Star this repo if you find it useful!**

[Get Started](#-quick-start) · [View Examples](#-usage-examples) · [Read Docs](#-documentation-structure)

Made with ❤️ for developers who build with imini

</div>
