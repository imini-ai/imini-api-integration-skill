<h1 align="center">
  imini API 集成 Skill
</h1>

<p align="center">
  <em>🚀 imini 开放平台 AIGC 图像/视频生成 API 的官方 Claude Code skill</em>
</p>

<p align="center">
  中文文档 · <a href="./README.md">English</a>
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img alt="License" src="https://img.shields.io/badge/License-MIT-blue.svg" /></a>
  <a href="https://claude.com/claude-code"><img alt="Claude Code" src="https://img.shields.io/badge/Claude-Code-8A3FFC.svg" /></a>
  <a href="https://docs.imini.ai"><img alt="Models" src="https://img.shields.io/badge/Models-7-green.svg" /></a>
  <a href="https://imini.ai"><img alt="Platform" src="https://img.shields.io/badge/Platform-imini.ai-0070F3.svg" /></a>
</p>

## ✨ 这是什么

一个 Claude Code skill，**自动**为你的图像/视频生成需求挑对 imini 模型、估算积分成本，并以你选择的语言生成可直接投产的**异步任务**代码（提交 + 轮询 + 结果提取）。无需对比模型、无需写样板代码、无需猜测最佳参数。

## 🎯 核心能力

- 🧠 **自动选型** — 描述你要生成的内容，skill 挑对 imini 模型
- 🔄 **始终最新** — 模型清单实时从 `docs.imini.ai/llms.txt` 拉取，**上新模型你无需重装 skill**
- ⚡ **完整异步流程** — 提交函数 + 轮询循环 + 结果提取 + 超时保护，不只一个 POST
- 💻 **多语言输出** — Python（同步 + 异步）/ Node.js / TypeScript / cURL
- 💰 **成本估算** — 运行前告诉你大约消耗多少积分
- 🛡️ **内置错误处理** — 429 / 5xx 指数退避重试，4xx 完整暴露错误信息
- 🎨 **零 context 浪费** — 用脚本解析目录，不把整份文档塞进对话

## 🤖 支持的模型

### 🖼️ 图像模型

| 模型 ID | 底层 | 特点 |
|---|---|---|
| `google/nano-banana` | Gemini 2.5 Flash Image | 🏃 快速、低成本，1K |
| `google/nano-banana-pro` | Gemini 3 Pro Image | 🎯 最高 4K，最多 14 张参考图，支持 asset / style 两种参考模式 |
| `google/nano-banana-2` | Gemini 3.1 Flash Image | 🎚️ 512 / 1K / 2K / 4K 多档位，最多 14 张参考图 |

### 🎬 视频模型

| 模型 ID | 底层 | 特点 |
|---|---|---|
| `kling/kling-v3` | 可灵 3.0 | 🎞️ 文/图生视频、首尾帧、多参考图 |
| `kling/kling-v3-omni` | 可灵 3.0 Omni | 🎥 在 v3 基础上新增**参考视频**输入，最高 1080P |
| `doubao/seedance-2.0` | Seedance 2.0 | 🧬 多模态参考（图 + 视频 + 音频），480P / 720P |
| `doubao/seedance-2.0-fast` | Seedance 2.0 Fast | 💸 能力与 2.0 一致，成本更低，480P / 720P |

> 📡 实时清单：https://docs.imini.ai/llms.txt

## 🚀 快速上手

### 安装

把仓库 URL 发给 Claude Code：

```
Install this skill: https://github.com/imini-ai/imini-api-integration-skill
```

Claude Code 会自动识别并安装。

### 验证

```
What skills are available?
```

列表中应能看到 `imini-api-integration`。

### 基本用法

自然语言提需求即可：

```
"用 imini 生成一张 4K 电影质感的图，Python 代码"
"用参考视频引导，生成 10 秒 1080P 视频，Node.js 代码"
"用 imini 并发生成 100 张图，并发数 10"
```

Skill 会自动：

1. ✅ 检查/询问你的 imini API Key
2. ✅ 拉取最新模型清单
3. ✅ 推荐合适模型并给出成本估算
4. ✅ 确认后拉取 OpenAPI spec
5. ✅ 生成完整的异步调用代码
6. ✅ 附赠生产实践建议（轮询策略、退避、并发）

## 💡 使用示例

### 示例 1 · 🎨 Python 文生 4K 高保真图

**你**：*"用 imini 最好的图像模型生成一张 4K 电影质感的图，Python 代码。"*

**Claude Code**（装了本 skill 后）：

- 选中 `google/nano-banana-pro` — 支持 4K 输出和 style 参考
- 成本估算：**约 200 积分/张**
- 生成 Python 代码，包含 `IMINI_API_KEY` 环境变量鉴权、提交函数、指数退避轮询、结果提取

### 示例 2 · 🎥 参考视频生成 10 秒 1080P 视频（Node.js）

**你**：*"用一段参考视频引导风格，生成 10 秒 1080P 视频，Node.js 代码。"*

**Claude Code**：

- 选中 `kling/kling-v3-omni` — **唯一支持 1080P + 参考视频的模型**
- 成本估算：**约 2,200 积分**（10 秒 × 220 积分/秒）
- 💡 提示：若可接受 720P，`doubao/seedance-2.0-fast` 带参考视频会便宜很多，可让 skill 对比价格再决定

### 示例 3 · ⚡ 并发批量生成

**你**：*"用 imini 并发生成 100 张图，最多 10 个并发。"*

**Claude Code**：

- 生成异步 Python 代码（`aiohttp` + 信号量）
- 内置限流重试的轮询循环
- 记录每次提交的 `task_id` 和估算成本

## 🛠️ 进阶特性

### 🔍 目录脚本

直接使用解析器：

```bash
# 列全部
python3 scripts/fetch_imini_catalog.py

# 按类型筛选
python3 scripts/fetch_imini_catalog.py --type video

# 查单个模型
python3 scripts/fetch_imini_catalog.py --model google/nano-banana-pro

# JSON 输出给工具链用
python3 scripts/fetch_imini_catalog.py --json
```

### 📦 零外部依赖

目录脚本仅用 Python 标准库，**无需 `pip install`**。

## 📚 目录结构

```
imini-api-integration-skill/
├── SKILL.md                      # 主指令（7 步工作流）
├── scripts/
│   └── fetch_imini_catalog.py    # 目录拉取与解析（纯标准库）
└── references/
    ├── workflow.md               # 异步任务状态机 + 轮询策略
    ├── model_selection.md        # 选型决策树 + 成本表
    ├── integration_examples.md   # Python / Node.js / TypeScript / cURL 模板
    └── errors.md                 # 错误码 + 重试策略
```

## 🔑 API Key

到以下地址创建 API Key（所有模型共用一把）：

🔗 https://imini.ai/zh/api-keys

> 🛡️ **安全提示**：skill 生成的代码**始终从环境变量 `IMINI_API_KEY` 读取 Key**，不会硬编码。

## 🎨 支持的输出语言

- 🐍 **Python** — 同步（`urllib`）+ 异步（`aiohttp`）
- 📜 **Node.js** — 原生 `fetch`
- 📘 **TypeScript** — 原生 `fetch`，带完整类型
- 🔧 **cURL** — 两步式提交 + 轮询脚本

## 🌟 为什么用它

<table>
<tr>
<td width="50%" valign="top">

### 😵 以前（手工集成）

```
1. 在 imini 文档对比图像/视频模型
2. 理解异步任务模式
3. 手写提交 + 轮询循环
4. 处理 429 / 5xx 重试
5. 设计超时和并发
6. 估算积分预算
⏱️ 耗时：30–60 分钟
```

</td>
<td width="50%" valign="top">

### 🎉 现在（使用本 skill）

```
1. 自然语言告诉 Claude Code
2. 拿到生产级异步代码
⏱️ 耗时：2–3 分钟
```

</td>
</tr>
</table>

## ✅ 依赖

- 🐍 Python 3.8+（目录脚本 — 纯标准库）
- 🤖 [Claude Code](https://claude.com/claude-code)

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
