# WorkBuddy Skills

一组 WorkBuddy / Claude Agent Skills，含读书工具、旅游攻略、高考真题获取。

> 语文教学相关的 7 个技能已独立成库，见文末[相关仓库](#相关仓库)。

## 技能清单

| 技能 | 说明 | 来源 |
|---|---|---|
| [`read-book`](read-book/) | 从 PDF/EPUB/MOBI/Markdown/txt 或公版书 URL 中提取结构化笔记。四种模式：章节笔记、全书摘要、金句摘录、学习卡片 | 改编自 [coreyhaines31/makerskills](https://github.com/coreyhaines31/makerskills)（MIT） |
| [`reading-companion`](reading-companion/) | 管理读书笔记：提取核心观点、跨书籍主题关联、生成复习卡片 | 改编自 [malue-ai/dazee-small](https://github.com/malue-ai/dazee-small)（MIT） |
| [`in-china-travel-guide`](in-china-travel-guide/) | 中国境内旅行攻略生成，含目的地档案、行程定制、主题编辑风格与响应式前端资源 | 原创 |
| [`gaokao-yuwen-paper-sourcing`](gaokao-yuwen-paper-sourcing/) | 高考语文真题获取：源站定位、URL 规律、编码处理、内容层核验 | 原创 |

## 安装

把需要的技能目录复制到 WorkBuddy 用户级技能目录：

```bash
git clone https://github.com/zhshy/workbuddy-skills.git

# Windows
xcopy /E /I workbuddy-skills\read-book "%USERPROFILE%\.workbuddy\skills\read-book"

# macOS / Linux
cp -r workbuddy-skills/read-book ~/.workbuddy/skills/
```

重启 WorkBuddy 后生效。

## 什么是 Skill

Skill 是给 AI 助手加载的专业知识包：一个 `SKILL.md` 定义触发条件与工作流程，`references/` 存放按需加载的细节文件。加载后助手会按既定流程工作，而不是即兴发挥。

本仓库技能遵循 Agent Skills 规范：YAML frontmatter + Markdown 正文 + 渐进式披露的 references。

## 外部依赖

| 技能 | 依赖 | 说明 |
|---|---|---|
| `read-book` | `pandoc` 或 Calibre（`ebook-convert`） | 仅解析 EPUB/MOBI 时需要；PDF 与文本格式无需额外依赖 |

Windows 安装：`winget install --id JohnMacFarlane.Pandoc`

## 授权说明

本仓库中改编自第三方开源项目的技能保留原作者署名与 MIT 协议，详见各技能目录下的 `LICENSE`：

- `read-book` — 改编自 coreyhaines31/makerskills
- `reading-companion` — 改编自 malue-ai/dazee-small

两者均为 MIT 协议，允许修改与再分发，要求保留原始版权声明。

其余技能为原创，同样以 MIT 协议发布。

## 相关仓库

语文教学方向的技能已独立成库（连同编排层共 7 个）：

| 仓库 | 说明 |
|---|---|
| [gaozhong-yuwen-design-orchestrator](https://github.com/zhshy/gaozhong-yuwen-design-orchestrator) | **总控**：把下面五个串成六步工作流 |
| [gaozhong-yuwen-kebiao](https://github.com/zhshy/gaozhong-yuwen-kebiao) | 《普通高中语文课程标准》知识库 |
| [sunshaozhen-text-analysis](https://github.com/zhshy/sunshaozhen-text-analysis) | 孙绍振文本微观分析（还原—比较—矛盾） |
| [wang-rongsheng-reading-design](https://github.com/zhshy/wang-rongsheng-reading-design) | 王荣生阅读教学设计 + 检测设计 |
| [xiaopeidong-qianqian-teaching](https://github.com/zhshy/xiaopeidong-qianqian-teaching) | 肖培东"浅浅地教语文"课堂艺术 |
| [gaoyi-chinese-lesson-design](https://github.com/zhshy/gaoyi-chinese-lesson-design) | 高一语文教学设计（统编版必修上下册） |
| [gaoyi-writing-coach](https://github.com/zhshy/gaoyi-writing-coach) | 高中作文批改与升格 |

## 许可

MIT License，见 [LICENSE](LICENSE)。
