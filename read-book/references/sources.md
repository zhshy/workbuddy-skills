# 各类来源的文本接入方式

按文件扩展名或 URL 特征选择接入方式。

---

## PDF

**原生路径** — WorkBuddy 的 Read 工具直接读 PDF：

```
Read 工具，file_path="<pdf>"，用 offset/limit 或 pages 参数读 "1-10"
```

每次最多约 10 页。长书按分块计划逐块处理。

**先拿目录和页数：**

```bash
# 首选：直接读前 5 页找目录（Contents / 目录 / Table of Contents）
# 用 Read 工具读第 1-5 页
```

无 python 环境限制时，也可用 PyPDF 类库获取书签，但通常读前 5 页已足够。

**扫描版 PDF（无文字层）：**

读 1–2 页发现只有图片、无文字时即为扫描版，需先 OCR：

```bash
# Windows 安装（可选）
winget install OCRmyPDF
ocrmypdf "<pdf>" "<pdf-ocr.pdf>"
# 然后改用 OCR 后的版本
```

无法本地 OCR 时，告知用户需要寻找文字版或使用在线 OCR 服务。

---

## EPUB

用 pandoc 转 markdown（保留章节结构）：

```bash
# 一次性安装：winget install --id JohnMacFarlane.Pandoc
pandoc "<book.epub>" -o "<workdir>/book.md" --wrap=none
```

输出中的 `# Chapter X`（或 `# 第X章`）标题即分块点。

备选：Calibre 的 `ebook-convert`（到 calibre-ebook.com 下载安装，命令行工具位于 `C:\Program Files\Calibre2\`）：

```bash
ebook-convert "<book.epub>" "<workdir>/book.txt"
```

---

## MOBI / AZW3

用 `ebook-convert`（pandoc 对 MOBI 支持不好）：

```bash
ebook-convert "<book.mobi>" "<workdir>/book.txt"
```

本机未装 Calibre 且用户不愿安装时，建议改用 PDF 或 txt 版本。

---

## Markdown / .txt

直接 Read，无需转换。按 30K 字符一块分块。

---

## 粘贴的文本

直接使用粘贴内容。短于 30K 字符视为单块；长文本按字符数分块。

用户只粘贴了书中某一节（"帮我读这一章"）时，按单块处理，跳过逐章汇总。

---

## URL（公版书全文）

```bash
# 用 WebFetch 拉取
# 古腾堡计划格式：https://www.gutenberg.org/files/<id>/<id>-0.txt
# archive.org 格式：https://archive.org/stream/<id>/<id>_djvu.txt
```

古腾堡计划优先取 `.txt` 链接而非 HTML——纯文本便于分块。

---

## 元数据提取

每个来源都把以下信息写入工作目录的 `metadata.json`：

```json
{
  "title": "<书名>",
  "author": "<作者>",
  "year": "<年份，如有>",
  "source": "<原始路径或 URL>",
  "type": "pdf | epub | mobi | markdown | text | url",
  "page_count": 287,
  "word_count": 95000,
  "has_toc": true,
  "captured_at": "YYYY-MM-DD"
}
```

- PDF：从封面/版权页和目录页读取；缺失时直接问用户
- EPUB：pandoc 转出的 md 开头或问用户
- markdown/text：文件名没有书名作者时，问用户
