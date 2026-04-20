<h1 align="center">
  imini API Integration Skill
</h1>

<p align="center">
  <em>🚀 The official Claude Code skill for imini open platform — AIGC image & video generation APIs</em>
</p>

<p align="center">
  <a href="./README_CN.md">中文文档</a> · English
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img alt="License" src="https://img.shields.io/badge/License-MIT-blue.svg" /></a>
  <a href="https://claude.com/claude-code"><img alt="Claude Code" src="https://img.shields.io/badge/Claude-Code-8A3FFC.svg" /></a>
  <a href="https://docs.imini.ai"><img alt="Models" src="https://img.shields.io/badge/Models-7-green.svg" /></a>
  <a href="https://imini.ai"><img alt="Platform" src="https://img.shields.io/badge/Platform-imini.ai-0070F3.svg" /></a>
</p>

## ✨ What is This?

A Claude Code skill that **automatically** picks the right imini model for your image or video generation task, estimates credit cost, and generates production-ready **async** integration code (submit + poll + result extraction) in your preferred language. No model comparison, no boilerplate, no guesswork.

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

### 🎬 Video Models

| Model ID | Underlying | Strengths |
|---|---|---|
| `kling/kling-v3` | Kling 3.0 | 🎞️ Text/image to video, first-last-frame, multi-reference |
| `kling/kling-v3-omni` | Kling 3.0 Omni | 🎥 Adds **reference-video** input on top of v3, up to 1080P |
| `doubao/seedance-2.0` | Seedance 2.0 | 🧬 Multimodal reference (image + video + audio), 480P / 720P |
| `doubao/seedance-2.0-fast` | Seedance 2.0 Fast | 💸 Same features as 2.0, lower cost, 480P / 720P |

> 📡 Live catalog: https://docs.imini.ai/llms.txt

## 🚀 Quick Start

### Installation

Share this repository URL with Claude Code:

```
Install this skill: https://github.com/imini-ai/imini-api-integration-skill
```

Claude Code installs it automatically.

### Verify

Ask Claude Code:

```
What skills are available?
```

You should see `imini-api-integration` in the list.

### Basic Usage

Just ask naturally:

```
"Generate a 4K cinematic image from a prompt using imini, in Python"
"Create a 10-second 1080P video with a reference video, Node.js"
"Batch-generate 100 images with imini, concurrency 10"
```

The skill will:

1. ✅ Ask for your imini API key (if missing)
2. ✅ Fetch the latest model catalog
3. ✅ Recommend model(s) with cost estimates
4. ✅ Pull the OpenAPI spec on confirmation
5. ✅ Generate complete async integration code
6. ✅ Provide production tips (polling, backoff, concurrency)

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
imini-api-integration-skill/
├── SKILL.md                      # Main skill workflow (7 steps)
├── scripts/
│   └── fetch_imini_catalog.py    # Catalog fetcher / parser (stdlib-only)
└── references/
    ├── workflow.md               # Async task state machine + polling strategy
    ├── model_selection.md        # Decision tree + cost tables
    ├── integration_examples.md   # Python / Node.js / TypeScript / cURL templates
    └── errors.md                 # Error codes + retry policy
```

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

- 🐍 Python 3.8+ (catalog script — stdlib only)
- 🤖 [Claude Code](https://claude.com/claude-code)

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
