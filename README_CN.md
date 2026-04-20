# imini API 集成 Skill

> imini 开放平台 AIGC 图像/视频生成 API 的官方 Claude Code skill。

帮助开发者将 imini 的图像/视频生成 API 快速集成到项目中。自动挑选合适的模型、估算积分成本、生成可直接运行的**异步任务**代码（提交 + 轮询 + 结果提取），而不是简单的 HTTP 代码片段。

[English README](./README.md)

## 安装

把仓库 URL 发给 Claude Code：

```
https://github.com/imini-ai/imini-api-integration-skill
```

Claude Code 会自动识别并安装。安装后确认：

```
What skills are available?
```

## 能做什么

- **自动选型** — 描述你要生成什么，skill 挑对 imini 模型
- **始终最新** — 模型清单从 `docs.imini.ai/llms.txt` 实时拉取，**imini 上新模型时你无需重装 skill**
- **完整异步流程** — 提交函数 + 轮询循环 + 结果提取 + 超时，不只一个 POST
- **多语言输出** — Python（同步 + 异步）/ Node.js / TypeScript / cURL
- **成本估算** — 运行前告诉你这次大约要消耗多少积分
- **内置错误处理** — 429 / 5xx 指数退避重试，4xx 完整暴露错误信息

## 支持的模型

| 模型 ID | 类型 | 底层 | 特点 |
|---|---|---|---|
| `google/nano-banana` | 图像 | Gemini 2.5 Flash Image | 快速、低成本，1K |
| `google/nano-banana-pro` | 图像 | Gemini 3 Pro Image | 最高 4K，最多 14 张参考图，asset/style 两种参考模式 |
| `google/nano-banana-2` | 图像 | Gemini 3.1 Flash Image | 512 / 1K / 2K / 4K 多档位，最多 14 张参考图 |
| `kling/kling-v3` | 视频 | 可灵 3.0 | 文/图生视频、首尾帧、多参考图 |
| `kling/kling-v3-omni` | 视频 | 可灵 3.0 Omni | 在 v3 基础上新增参考视频输入 |
| `doubao/seedance-2.0` | 视频 | Seedance 2.0 | 多模态参考（图 + 视频 + 音频） |
| `doubao/seedance-2.0-fast` | 视频 | Seedance 2.0 Fast | 能力与 2.0 一致，成本更低 |

实时清单：https://docs.imini.ai/llms.txt

## 典型用法示例

### Python 文生高保真图

> "用 imini 最好的图像模型生成一张 4K 电影质感的图，Python 代码。"

Skill：选中 `google/nano-banana-pro`，拉取 spec，生成一份包含环境变量鉴权、提交函数、指数退避轮询、结果提取的完整 Python 代码。

### Node.js 参考视频生成 10 秒 1080P 视频

> "用一段参考视频引导风格，生成 10 秒 1080P 视频，Node.js 代码。"

Skill：选中 `kling/kling-v3-omni`（或提供 `doubao/seedance-2.0` / `seedance-2.0-fast` 作为更便宜的多模态替代），估算积分成本，生成 Node.js 代码。

### 并发批量生成

> "批量生成 100 张图，最多 10 个并发。"

Skill：生成异步 Python（`aiohttp` + 信号量），包含轮询、限流重试、超时。

## API Key

到以下地址创建 API Key（所有模型共用一把）：

- https://imini.ai/zh/api-keys（中文）
- https://imini.ai/api-keys（英文）

**安全提示**：生成的代码**始终从环境变量 `IMINI_API_KEY` 读取 Key**，不会硬编码。

## 依赖

- Python 3.8+（目录解析脚本仅用标准库，**无需 `pip install`**）
- Claude Code

## 相关链接

- 平台：https://imini.ai
- API 文档：https://docs.imini.ai
- 价格：https://docs.imini.ai/zh/guide/pricing
- 更新公告：https://docs.imini.ai/zh/changelog
- 技术支持：support@imini.com

## License

MIT — 详见 [LICENSE](./LICENSE)。
