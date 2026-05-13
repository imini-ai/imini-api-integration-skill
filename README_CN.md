<h1 align="center">
  imini API 集成 Skill
</h1>

<p align="center">
  <em>🚀 imini 开放平台的官方 skill —— 覆盖 55+ agent（Claude Code、Codex、Cursor、OpenCode、OpenClaw、Hermes 等），通过开放的 <a href="https://github.com/vercel-labs/skills">skills</a> 生态发布</em>
</p>

<p align="center">
  中文文档 · <a href="./README.md">English</a> · <a href="./INSTALL.md">安装</a>
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

## ✨ 这是什么

一个跨 agent 的 skill，**自动**为你的图像/视频生成需求挑对 imini 模型、估算积分成本，并根据使用场景**直接调用预置脚本**（一次性生成）或**生成可投产的异步代码**（集成进你的项目）。无需对比模型、无需写样板代码、无需猜测最佳参数。

支持任何加载 Markdown skill 的 agent —— Claude Code、Codex、Cursor 等等。一行命令跨 agent 安装见 [INSTALL.md](./INSTALL.md)。

## 🎯 核心能力

- 🧠 **自动选型** — 描述你要生成的内容，skill 挑对 imini 模型
- 🔄 **始终最新** — 模型清单实时从 `docs.imini.ai/llms.txt` 拉取，**上新模型你无需重装 skill**
- ⚡ **两条路并存** — Path A 一次性生成（直接调脚本）/ Path B 集成代码生成（产出模板）
- 💻 **多语言输出**（Path B） — Python（同步 + 异步）/ Node.js / TypeScript / cURL
- 💰 **成本估算** — 运行前告诉你大约消耗多少积分
- 🛡️ **内置错误处理** — 429 / 5xx 指数退避 + 抖动，4xx 完整暴露 `error.code` / `message` / `request_id`
- 🎨 **零 context 浪费** — Path A 走脚本时不再把代码模板载入对话

## 🤖 支持的模型

### 🖼️ 图像模型

| 模型 ID | 底层 | 特点 |
|---|---|---|
| `google/nano-banana` | Gemini 2.5 Flash Image | 🏃 快速、低成本，1K |
| `google/nano-banana-pro` | Gemini 3 Pro Image | 🎯 最高 4K，最多 14 张参考图，支持 asset / style 两种参考模式 |
| `google/nano-banana-2` | Gemini 3.1 Flash Image | 🎚️ 512 / 1K / 2K / 4K 多档位，最多 14 张参考图 |
| `openai/gpt-image-2` | OpenAI gpt-image-2 | 🎛️ 1K / 2K / 4K × low / medium / high 质量两维独立 |

### 🎬 视频模型

| 模型 ID | 底层 | 特点 |
|---|---|---|
| `kling/kling-v3` | 可灵 3.0 | 🎞️ 文/图生视频、首尾帧、多参考图 |
| `kling/kling-v3-omni` | 可灵 3.0 Omni | 🎥 在 v3 基础上新增**参考视频**输入，最高 1080P |
| `kling/kling-v3-motion-control` | 可灵 3.0 Motion Control | 🕺 用参考视频的动作驱动一个角色 |
| `doubao/seedance-2.0` | Seedance 2.0 | 🧬 多模态参考（图 + 视频 + 音频），480P / 720P |
| `doubao/seedance-2.0-fast` | Seedance 2.0 Fast | 💸 能力与 2.0 一致，成本更低，480P / 720P |
| `dashscope/happyhorse-1.0` | HappyHorse 1.0 | ✂️ 文/图/参考生视频 **+ 视频编辑**，一个模型搞定 |

> 📡 实时清单（永远是最新）：https://docs.imini.ai/llms.txt —— 由 `fetch_imini_catalog.py` 在脚本里实时拉取，**生产环境清单永不过期**。

## 🚀 快速上手

### 安装

详见 [INSTALL.md](./INSTALL.md) 中四种安装方式。最快的是跨 agent 一行命令：

```bash
npx skills add imini-ai/imini-api-integration-skill
```

支持 Claude Code、Codex、Cursor、OpenCode、OpenClaw、Hermes 等 50+ agent —— `npx skills` 会自动检测你装的是哪个 agent，把 skill 放到对应的 skills 目录里。

或者如果你用 Claude Code、习惯它原生的 plugin 流程：

```
/plugin marketplace add imini-ai/imini-api-integration-skill
/plugin install imini@imini
```

### 验证

两条路径，对应不同使用场景：

**Path A · 🏃 一次性生成（NEW）** —— 直接说：

```
"用 imini nano-banana 帮我生成一张测试图"
"用 kling-v3 生成一段 5 秒 1080P 的无人机航拍山脉视频"
```

Agent 会**直接调用预置的 Python 脚本** —— 不再每次生成新代码、不再每次 burn token 重新推导 submit/poll 逻辑。几秒后生成的文件就落到你当前目录。

**Path B · 🛠️ 集成代码** —— 想把 imini 写进你自己的项目时：

```
"我的 Django 应用要调 imini 的 google/nano-banana-pro 生成 4K 图，怎么写？"
"用 TypeScript 写一个批量调 imini 生成 100 张图的脚本，并发 10"
```

Agent 会生成完整的异步 submit/poll 代码模板，语言你来选。

### 基本用法

Skill 会根据你的意图自动路由：

| 你说的话 | 路径 | 实际发生 |
|---|---|---|
| "生成 / 制作 / 画一张 ..." | **A** | 跑 `scripts/generate_image.py` 或 `generate_video.py` |
| "把 imini 加到我项目 / 写代码调 imini" | **B** | 用你指定的语言生成模板 |
| 表达模糊 | Agent 会主动问一句 |

无论走哪条路径，skill 都会：

1. ✅ 检测环境（Path A 需要 Python 3.8+；Path B 视语言而定 Node 18+ / Python / cURL）
2. ✅ 从你 shell 的 `$IMINI_API_KEY` 读取密钥 —— **不会让你把 key 贴进对话**
3. ✅ 实时拉取 `docs.imini.ai/llms.txt` 模型清单（24 小时本地缓存兜底）
4. ✅ 推荐模型 + 成本估算，明确得到你确认后再执行
5. ✅ Path A 跑脚本 / Path B 生成代码 —— 都内置抖动、429 退避、结构化错误处理、多结果迭代

## 💡 使用示例

### 示例 1 · 🎨 Path A 一次性生成 4K 图

**你**：*"用 imini 最好的图像模型生成一张 4K 电影质感的图。"*

**Agent**（装了本 skill 后）：

- 选中 `google/nano-banana-pro` —— 支持 4K + style 参考
- 成本估算：**约 200 积分/张**
- **直接调** `python3 scripts/generate_image.py --model google/nano-banana-pro --prompt "..." --resolution 4K --output ./out.png`
- 几十秒后给你文件路径

### 示例 2 · 🎥 Path A 生成 1080P 视频

**你**：*"用一段参考视频引导风格，生成 10 秒 1080P 视频。"*

**Agent**：

- 选中 `kling/kling-v3-omni` —— **唯一支持 1080P + 参考视频**
- 成本估算：**约 2,200 积分**（10 秒 × 220 积分/秒）
- 直接调 `generate_video.py --model kling/kling-v3-omni --reference-video ./ref.mp4 --duration 10 --resolution 1080P --output ./out.mp4`
- 💡 提示：若可接受 720P，`doubao/seedance-2.0-fast` 配合参考视频会便宜很多，可让 skill 对比价格再决定

### 示例 3 · ⚡ Path B 批量集成代码

**你**：*"用 Python 异步并发生成 100 张图，最多 10 并发，把代码加到我项目里。"*

**Agent**：

- 识别为 Path B（集成进项目）
- 生成异步 Python 代码（`aiohttp` + 信号量），按 `references/integration_examples.md` 模板
- 内置 ±20% 抖动、429 退避、结构化错误处理、`images[]` 迭代提取
- 记录每次提交的 `task_id` + 估算积分

## 🛠️ 进阶特性

### 🔍 模型清单脚本

直接使用解析器：

```bash
# 列全部
python3 skills/imini-generate/scripts/fetch_imini_catalog.py

# 按类型筛选
python3 .../scripts/fetch_imini_catalog.py --type video

# 查单个模型（含定价）
python3 .../scripts/fetch_imini_catalog.py --model google/nano-banana-pro

# JSON 输出给工具链用
python3 .../scripts/fetch_imini_catalog.py --json
```

Path A 的 generate 脚本内置 `--list-models` 子命令，效果等同。

### 🛡️ --print-request 调试模式

Path A 脚本支持 `--print-request` —— **不打 API、不需要 Key**，先看会发什么 JSON 出去：

```bash
python3 .../scripts/generate_image.py \
    --model google/nano-banana-pro \
    --prompt "test" --resolution 4K \
    --print-request

# 输出:
# {
#   "model": "google/nano-banana-pro",
#   "prompt": "test",
#   "resolution": "4K"
# }
```

base64 编码的本地图片自动截断显示（不会刷屏）。

### ⏱️ --async + poll 接力

长视频可以 `--async` 提交后立即返回 task_id，关电脑或换会话后再用 `poll_video_task.py` 续：

```bash
TASK_ID=$(python3 .../scripts/generate_video.py \
    --model doubao/seedance-2.0 \
    --prompt "..." --duration 15 --reference-video ./ref.mp4 \
    --async)

# 过一会儿...
python3 .../scripts/poll_video_task.py --task-id "$TASK_ID" --output ./out.mp4
```

### 📦 零外部依赖

所有脚本仅用 Python 3.8+ 标准库：`urllib` / `json` / `argparse` / `base64` / `mimetypes` / `pathlib`。**无需 `pip install` 任何东西**。

## 📚 目录结构

```
imini-api-integration-skill/
├── .claude-plugin/
│   ├── marketplace.json             # Claude Code marketplace 目录
│   └── plugin.json                  # Claude Code plugin manifest
├── .codex-plugin/plugin.json        # Codex Agent 可读的 manifest
├── .cursor-plugin/plugin.json       # Cursor manifest
├── skills/
│   └── imini-generate/             # skill 本体 —— 装到 ~/.<agent>/skills/imini-generate/
│       ├── SKILL.md                 # 工作流入口（Path A 跑脚本 / Path B 生代码）
│       ├── references/              # Path B（生代码）专用
│       │   ├── workflow.md            # 异步任务状态机 + 轮询策略
│       │   ├── model_selection.md     # 选型决策树
│       │   ├── integration_examples.md  # Python / Node.js / TS / cURL 模板
│       │   └── errors.md              # 超时表 + 错误码 + 重试策略
│       └── scripts/                 # Path A（直接生成）+ catalog 脚本
│           ├── _imini_common.py      # submit/poll/上传/下载/错误处理 共享内核
│           ├── generate_image.py     # CLI：图像生成
│           ├── generate_video.py     # CLI：视频生成
│           ├── poll_image_task.py    # CLI：用 task_id 续 poll 图
│           ├── poll_video_task.py    # CLI：用 task_id 续 poll 视频
│           └── fetch_imini_catalog.py  # 实时拉取并解析 llms.txt（纯标准库）
├── setup                            # 通用 bash 安装脚本
├── INSTALL.md
├── README.md, README_CN.md
├── VERSION
└── LICENSE
```

## 🔑 API Key

到以下地址创建 API Key（所有模型共用一把）：

🔗 https://imini.ai/zh/api-keys

> 🛡️ **安全提示**：在 shell 里 `export IMINI_API_KEY='sk-...'`，**不要把 Key 贴进对话** —— 对话日志会被记录。skill 生成的代码同样始终从环境变量读取，不会硬编码。

## 🎨 Path B 支持的输出语言

- 🐍 **Python** —— 同步（`urllib`，零依赖）+ 异步（`aiohttp ≥ 3.9`）
- 📜 **Node.js** —— 原生 `fetch`（**需要 Node 18+**）
- 📘 **TypeScript** —— 原生 `fetch`，带完整类型（需要 Node 18+）
- 🔧 **cURL** —— 两步式提交 + 轮询脚本

## 🌟 为什么用它

<table>
<tr>
<td width="50%" valign="top">

### 😵 以前（手工集成或裸 codegen）

```
1. 在 imini 文档对比图像/视频模型
2. 理解异步任务模式
3. 手写 submit + 轮询循环
4. 处理 429 / 5xx 重试 + 抖动
5. 调试 status enum
   (succeeded vs completed)
6. 调试结果迭代
   (images[] vs images[0])
7. 估算积分预算
⏱️ 耗时：30–60 分钟
🔁 每次会话还要重复 codegen
```

</td>
<td width="50%" valign="top">

### 🎉 现在（使用本 skill）

```
1. 自然语言告诉 agent
2. 一次性生成 → 直接跑预置脚本
   集成进项目 → 拿到生产级模板
⏱️ 耗时：
   Path A 一次性：< 1 分钟
   Path B 集成：  2–3 分钟
🚀 不再每次会话重写
   submit/poll boilerplate
```

</td>
</tr>
</table>

## ✅ 依赖

- 🐍 Python 3.8+ —— Path A 脚本必备（仅标准库，无需 `pip install`）
- 🤖 任意加载 Markdown skill 的 agent —— [Claude Code](https://claude.com/claude-code) / Codex / Cursor / OpenCode / OpenClaw / Hermes / [其他 50+](https://github.com/vercel-labs/skills#supported-agents)
- （Path B 生成 JS/TS 代码时）Node.js 18+ —— 原生 `fetch`

## 🔗 相关链接

- 🌐 **imini 平台**：https://imini.ai
- 📖 **API 文档**：https://docs.imini.ai
- 💰 **价格**：https://docs.imini.ai/zh/guide/pricing
- 📰 **更新公告**：https://docs.imini.ai/zh/changelog

## 💬 技术支持

- 📧 **邮箱**：support@imini.com

## 📝 License

遵循 [MIT License](./LICENSE)。

---

<div align="center">

**⭐ 觉得有用欢迎 Star！**

[快速上手](#-快速上手) · [示例](#-使用示例) · [文档](#-目录结构)

为与 imini 合作的开发者用心打造 ❤️

</div>
