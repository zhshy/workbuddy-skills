---
name: read-book
description: Read a book and extract structured notes — PDF, EPUB, MOBI, markdown, .txt, pasted text, or URL to a public-domain work. Reads in chunks (by chapter when a TOC exists, by 50-page blocks otherwise), extracts per-chapter TL;DR + key concepts + quotes + action items + frameworks. Four modes — notes (default, chapter-by-chapter), summary (whole-book TL;DR + 3–5 takeaways), quotes (pull-quote highlights only), study (notes + Q&A spaced-rep cards). Trigger on "读这本书", "帮我读这本书做笔记", "提取这本书的笔记", "总结这本书", "摘录金句", "read this book", "extract notes from this PDF", "summarize this ebook". Adapted for WorkBuddy on Windows from coreyhaines31/makerskills (MIT).
metadata:
  version: 0.2.0-wb
  source: https://github.com/coreyhaines31/makerskills (skills/read-book, MIT)
---

# /read-book — 从书籍和长 PDF 中提取结构化笔记

流程：接入 → 分块 → 逐块提取 → 汇总成笔记文件。

## Step 1 — 识别输入

接受以下输入：
- **PDF**：文件路径。用原生 Read 工具分页读取（每次最多约 10 页，用 pages 参数指定范围）
- **EPUB / MOBI**：文件路径。需要 `pandoc` 或 Calibre 的 `ebook-convert` 先转文本（见 `references/sources.md`）。本机未装时告诉用户如何安装，或建议改用 PDF/txt 版本
- **Markdown / .txt**：文件路径，直接读取
- **粘贴的文本**：直接用粘贴内容
- **URL**（公版书全文）：用 WebFetch 拉取（古腾堡计划、archive.org 等）

根据扩展名判断类型；不明确时先问用户。

## Step 2 — 识别模式

| 用户调用 | 模式 | 产出 |
|---|---|---|
| `读这本书 <输入>` / `/read-book <输入>` | **notes**（默认） | 逐章：TL;DR + 核心概念 + 金句 + 行动项 + 框架 |
| `… summary` | summary | 全书一段话 TL;DR + 3–5 个要点 + 适合谁读 |
| `… quotes` | quotes | 仅金句，带章节上下文和页码 |
| `… study` | study | notes 模式 + 10–20 张间隔重复问答卡 |

书很长（>200 页）且未指定模式时，默认 `notes` 但提醒用户会消耗较多轮次。

## Step 3 — 获取文本并分块

按 `references/sources.md` 的方式接入。本步产出：文本内容 + 分块计划。

**分块策略**（混合，按优先级）：

1. **按章节**（有目录时）
   - PDF：先用 Read 读取第 1–5 页找目录页；目录明确则按章节划分页码范围
   - EPUB/MOBI：pandoc 转出的 markdown 里 `# Chapter X`（或中文 `# 第X章`）标题即分块点
2. **按页数**：PDF 无目录时，每 50 页一块
3. **按字符数**：纯文本/markdown 每 30,000 字符一块（约 7,500 词）

分块计划保存为 `~/Documents/books/<作者>-<书名slug>-<YYYY-MM-DD>/chunks.json`：

```json
{
  "source": "<路径>",
  "title": "<书名>",
  "author": "<作者>",
  "type": "pdf",
  "total_pages": 287,
  "chunking": "by-chapter",
  "chunks": [
    {"i": 0, "label": "Introduction", "pages": "1-12"},
    {"i": 1, "label": "Chapter 1", "pages": "13-32"}
  ]
}
```

## Step 4 — 逐块读取并提取

循环：
1. 读取第 N 块（PDF 用 Read 的 pages 参数，文本/MD 直接读）
2. 按所选模式提取（模板见 `references/output-modes.md`）
3. 把该块笔记追加写入工作目录

PDF **不要一次读完整本**——原生 Read 每次约 10 页上限，必须按块处理。

某一块提取不出有效内容（如图表为主、版权页）时，记录跳过原因，继续下一块，不让整个任务失败。

## Step 5 — 汇总为最终笔记

把所有块笔记合并为单个 `~/Documents/books/<工作目录>/notes.md`，结构按所选模式的全书模板（见 `references/output-modes.md`）。

文件顶部固定为元数据块：

```markdown
source: <文件路径或 URL>
captured: YYYY-MM-DD
type: book
book_title: <书名>
author: <作者>
mode: notes
chunks: <块数>
chunking: <策略>

# <书名> — <作者>

## TL;DR
<2–3 句>

## 关键要点
1. ...

## 章节笔记
...

## 交叉引用建议
- 可关联《<相关书>》（第 X 章讨论了……）
```

交叉引用是建议性的，列在文末即可，不自动展开。

## Step 6 — 可选：归档到阅读笔记库

完成后询问用户：

> "要不要把这份笔记归入你的阅读笔记库（~/Documents/reading-notes/）？我可以提取核心要点生成一页书摘，供跨书主题关联使用。"

默认**询问**，绝不自动写入。用户同意后：
1. 按 reading-companion 技能的笔记模板，在 `~/Documents/reading-notes/books/<书名slug>.md` 生成书摘页
2. 告知用户保存路径

用户不需要归档时，notes.md 已在工作目录，随时可取。

## Step 7 — 汇报

在对话中给出：
- 一行摘要：`<书名> · <作者> · <总页数或字数> · <模式> · <已处理块数>`
- 工作目录路径
- TL;DR 全文
- notes/study 模式：前 3 条要点
- quotes 模式：前 3 条金句
- 如已归档：归档路径

## 快速调用一览

| 调用 | 模式 | 行为 |
|---|---|---|
| `读这本书 <输入>` | notes | 完整流程，默认模式 |
| `… summary` | summary | 只要 TL;DR + 要点（>100 页的书抽读导言+2–3 个中间章+结尾） |
| `… quotes` | quotes | 逐章但只输出金句 |
| `… study` | study | 笔记 + 问答卡 |
| `… --render html` | 任意 | 用 pandoc 把 notes.md 渲染成 HTML（本机需装 pandoc，未装则跳过并说明） |

## 与其他技能协作

- **reading-companion**：本技能产出 notes.md 后，可提取要点归入 `~/Documents/reading-notes/` 书摘库，再做跨书主题关联和复习卡
- **作文批改/备课场景**：教育类书籍的"框架"条目（如孙绍振的还原法、王荣生的教学设计流程）可直接被后续备课引用

## 错误处理

| 情况 | 处理 |
|---|---|
| EPUB/MOBI 但未装 pandoc / Calibre | 告诉用户：`winget install --id JohnMacFarlane.Pandoc` 或到 calibre-ebook.com 下载安装（自带 ebook-convert）；或建议改用 PDF/txt 版本 |
| PDF 是扫描件（无文字层） | 先检查：读 1–2 页发现是图片即提示用户需要 OCR 版本；可选 `winget install OCRmyPDF` 或使用在线 OCR |
| PDF 无可识别目录 | 回退到 50 页分块，在元数据中注明 |
| 书超长（>500 页） | 提醒耗时，询问是否改用 summary 模式 |
| 某块提取为空 | 跳过该块、记录、继续，不中断整个任务 |

## 质量要求

- **不要压缩到失真。** 30 页的章节应产出 8–15 行笔记，而不是 3 行。压缩是好的，压扁是错的。
- **保留具体信息。** 人名、数字、日期、金句都保留。目的在于日后用户能检索到"某人说过的某句话"。
- **金句是神圣的。** 标记为金句的内容必须逐字照录，尽量注页码。
- **行动项要显式。** 书让你产生"我应该做 X"的念头时，明确写成一条行动项。这是产出中杠杆最高的部分。
- **框架单独列条目。** 作者命名的框架（如"还原—比较"分析法、"四步习惯回路"）在笔记中单独点名列出。
