
# Subsmith —— 一个日语视频字幕词汇挖掘工具

> **🎯 Version 0.9** - GUI 界面 + 强化 CLI 工具

一套完整的日语学习卡片生成工具，从视频和字幕中自动提取目标单词，生成包含释义、读音、音调、音频和截图的 Anki 卡片。

---

## 🚀 快速开始

### 前置准备

1. **安装 FFmpeg**（必需）
   
   - 下载：https://ffmpeg.org/download.html
   - 添加到系统 PATH
   - 验证：运行 `ffmpeg -version`

2. **安装 Anki 和模板**（推荐）
   
   - 下载 Anki：https://apps.ankiweb.net/
   - 安装 AnkiConnect 插件（代码：`2055492159`）
   - 下载 Senren 模板：https://github.com/SenrenNagasaki/senren-anki-note-types

3. **安装 Python 依赖**
   
   ```bash
   pip install -r requirements.txt
   ```

### 方式一：GUI 应用（推荐新手）⭐

```bash
python app.py
```

**GUI 特性：**
- ✅ **可视化参数配置** - 拖拽文件、浏览目录
- ✅ **实时词典查询** - 独立查询界面
- ✅ **配置自动保存** - 关闭后自动恢复设置
- ✅ **进度监控** - 实时日志输出和进度条
- ✅ **Anki 推送** - 一键推送到 Anki

**使用步骤：**
1. 启动 `python app.py`
2. 在主界面配置视频、字幕、单词表路径
3. 设置词典路径（Primary/Secondary/Tertiary MDX + NHK）
4. 配置 Anki 设置（URL、牌组、模型）
5. 点击"开始处理"

### 方式二：CLI 工具（推荐自动化）⭐

```bash
# 基本用法
python cli.py \
  --video "episodes/S01E01.mp4" \
  --subs "subs/S01E01.ja.srt" \
  --words "words/S01E01.txt" \
  --primary-mdx "dicts/Primary_MDX" \
  --nhk-new "dicts/NHK_New" \
  --freq "dicts/term_meta_bank_1.json" \
  --outdir "output/S01E01" \
  --csv "output/S01E01/cards.csv"

# 推送到 Anki
python cli.py \
  --video "episodes/S01E01.mp4" \
  --subs "subs/S01E01.ja.srt" \
  --words "words/S01E01.txt" \
  --primary-mdx "dicts/Primary_MDX" \
  --secondary-mdx "dicts/Secondary_MDX" \
  --tertiary-mdx "dicts/Tertiary_MDX" \
  --nhk-old "dicts/NHK_Old" \
  --nhk-new "dicts/NHK_New" \
  --djs "dicts/DJS_N" \
  --freq "dicts/term_meta_bank_1.json" \
  --outdir "output/S01E01" \
  --csv "output/S01E01/cards.csv" \
  --anki \
  --anki-deck "Japanese::Anime::MyShow" \
  --anki-model "Senren" \
  --anki-tags anime myshow S01E01
```

📖 **详细指南：**
- **[GUI 使用指南](GUI_GUIDE.md)** - 图形界面完整教程 ⭐
- **[快速开始](QUICK_START.md)** - 5分钟上手
- **[Anki 导入指南](ANKI_IMPORT_GUIDE.md)** - 卡片导入和模板配置

---

## ✨ 核心特性

### 1. 🎨 现代化 GUI 界面（Version 2.0 新增）

基于 **PySide6-Fluent-Widgets** 的 Fluent Design 风格界面：

#### 📋 主界面 - 参数配置
- **拖拽文件支持** - 直接拖拽视频、字幕、单词表文件
- **三级词典配置** - Primary → Secondary → Tertiary 词典架构
- **音调词典配置** - NHK 新版/旧版、大辞泉
- **实时进度显示** - 进度条 + 详细日志输出
- **控制按钮** - 开始处理、停止处理、清空日志
- **标签配置** - 空格分隔的 Anki 标签
- **一键推送** - 勾选即可推送到 Anki

#### 📖 词典查询界面
- **实时查询** - 输入单词即时查询
- **6种词典支持** - Primary/Secondary/Tertiary + NHK×2 + DJS
- **HTML格式化** - Yomitan 风格的释义显示
- **词元推导** - 自动尝试词元形式和变体

#### ⚙️ Anki 设置界面
- **连接测试** - 测试 AnkiConnect 连接状态
- **牌组配置** - 设置目标牌组名称
- **模型配置** - 设置笔记类型（推荐 Senren）
- **URL配置** - 自定义 AnkiConnect 地址

#### ℹ️ 关于界面
- **版本信息** - 当前版本和更新日志
- **技术栈** - 使用的技术和库
- **功能特性** - 所有功能说明

**💾 配置持久化：** 所有设置自动保存到 `~/.config/JA-Mining/gui_config.json`

### 2. 📚 智能词典查询系统

**三级词典架构：**

```
Primary MDX (核心词典，如大辞林)
    ↓ 未找到
Secondary MDX (补充词典，如大辞泉)
    ↓ 未找到  
Tertiary MDX (备用词典，如新明解)
    ↓ 未找到
JMDict Fallback (可选)
```

**自动回退查询策略：**

1. **词元形式**：食べた → 食べる
2. **表面形式**：原始输入
3. **く→き 变体**：狂い咲く → 狂い咲き（复合词）
4. **片假名→平假名**：ピン → ぴん
5. **长音展开**：こー → こう、せー → せい

**输出格式：** Yomitan 兼容的 HTML，包含词性、释义、例句等完整信息

### 3. 🎵 高级音频和音调系统

**三级音频源（优先级递减）：**

1. **NHK 新版** - 最新发音，高音质
2. **NHK 旧版** - 备用音频
3. **大辞泉 MDX** - 第三选择

**多音调支持：**

- 自动获取单词的**所有可能读音和音调型**
- 每个读音都有独立的音调信息

**音调可视化（Yomitan 风格）：**

- 🔴 **头高型** - 红色上划线
- 🔵 **平板式** - 蓝色上划线
- 🟠 **中高型** - 橙色上划线
- 🟢 **尾高型** - 青绿色上划线
- ⬇️ **下降标记** - 音调下降位置竖线

### 4. 🔤 分词和假名注音

**技术栈：** Fugashi + UniDic（日本国立国语研究所标准）

**智能送假名处理：**

```
间違い → 間違[まちが]い   (不是 間違い[まちがい])
食べた → 食[た]べた        (不是 食べた[たべた])
```

**空格分隔输出：**

```
間違[まちが]い 今[いま]は 重度[じゅうど]の
```

**长音智能转换：**

- お段：こー → こう（不是 こお）
- え段：せー → せい（不是 せえ）
- 片假名：コー → コー（保持原样）

### 5. 📝 单词表高级语法

**灵活的单词表格式：**

```text
# 基本格式
精霊                           # 自动查词、自动读音、自动音调
食べた                         # 自动推导词元（食べる）

# 圆括号 () = 强制读音
精霊(せいれい)                 # 强制使用这个读音（多音字）
走った(はしった)               # 指定读音为「はしった」

# 方括号 [] = 强制查词形态
食べた[食べる]                 # 用「食べる」查词典
狂い咲く[狂い咲き]             # 用「狂い咲き」查（复合词）

# 组合使用
走った(はしった)[走る]         # 读音 + 查词形态都指定
生贄(いけにえ)[生け贄]         # 强制读音 + 查词形态
```

**语法规则：**

- `()` = 强制读音（覆盖自动提取）
- `[]` = 强制查词典形态（覆盖词元推导）
- 可以单独使用，也可以组合使用
- 注释用 `#` 开头（会被忽略）

### 6. 🎬 媒体处理

**视频截图：**

- 自动在句子时间点截图
- 可配置 FFmpeg 滤镜（如裁剪、调色）
- 支持高分辨率截图

**音频裁剪：**

- 精确裁剪句子音频
- 可配置前后填充时间（`--pad`）
- 自动音量归一化

**媒体编码：**

- 所有媒体转为 Base64 嵌入 CSV
- 一键导入 Anki，无需手动复制文件

### 7. 📊 频率数据

**支持格式：**

- BCCWJ 词频（`term_meta_bank_1.json`）
- 自定义 CSV/TSV/JSON

**输出信息：**

- 词频描述（如"上位5%"）
- 排序值（用于按频率排序学习）

### 8. 🚀 一键推送到 Anki

**AnkiConnect 集成：**

- 直接推送到 Anki，无需 CSV 导入
- 自动创建牌组
- 支持多标签（如 `anime kimetsu S01E01`）
- 可配置牌组、模型、字段映射

**推送选项：**

- 允许/禁止重复卡片
- 自定义 AnkiConnect URL
- 批量推送进度显示

---

## 📂 项目结构

```
Japanese-Anime-Mining-Tool/
├── app.py                          # 🎨 GUI 应用入口 ⭐
├── cli.py                          # 💻 CLI 工具入口 ⭐
├── jp_media_mining_refactored.py   # 📦 旧版主程序（已废弃）
├── converage123.py                 # 🧪 词典查询测试工具
│
├── core/                           # 🧠 核心模块（重构版）⭐
│   ├── __init__.py
│   ├── config.py                   # 配置管理（dataclass）
│   ├── card_data.py                # 卡片数据模型
│   ├── logger.py                   # 日志模块（详细输出）
│   ├── media_handler.py            # 媒体处理（FFmpeg）
│   ├── subtitle_handler.py         # 字幕解析（pysubs2）
│   ├── word_processor.py           # 词汇处理（Fugashi）
│   ├── processor.py                # 主处理器（协调者）
│   ├── frequency.py                # 频率数据查询
│   ├── csv_exporter.py             # CSV 导出
│   └── anki_pusher.py              # Anki 推送（AnkiConnect）
│
├── gui/                            # 🎨 GUI 界面（PySide6）⭐
│   ├── __init__.py
│   ├── config_manager.py           # GUI 配置持久化
│   ├── main_window.py              # 主窗口（FluentWindow）
│   ├── home_interface.py           # 主界面（参数配置）
│   ├── dict_query_interface.py     # 词典查询界面
│   ├── anki_settings_interface.py  # Anki 设置界面
│   └── about_interface.py          # 关于界面
│
├── mdx_utils/                      # 📖 词典查询模块
│   ├── __init__.py
│   ├── meanings_lookup.py          # 释义查询（三级词典 + 回退）
│   ├── audio_lookup.py             # 音频/音调查询（Fugashi 集成）
│   └── yomitan_formatter.py        # Yomitan 格式化
│
├── README.md                       # 📚 本文档
├── GUI_GUIDE.md                    # 🎨 GUI 使用指南 ⭐
├── QUICK_START.md                  # 🚀 快速开始指南
├── ANKI_IMPORT_GUIDE.md            # 📥 Anki 导入指南
├── requirements.txt                # 📦 Python 依赖
│
├── test_out/                       # 🧪 测试输出目录
│   ├── cards.csv                   # 测试生成的卡片
│   └── media/                      # 测试媒体文件
│
└── examples/                       # 🎓 示例文件
    ├── example_words.txt           # 单词表示例
    └── example_output.csv          # 输出示例

```

---

## 🔧 安装依赖

### 系统要求

#### 必需软件

1. **Python 3.10+**（推荐 3.11）

2. **FFmpeg**（音视频处理）
   
   - **下载：** [FFmpeg Official Site](https://ffmpeg.org/download.html)
   - **Windows:** 下载后添加到 PATH 环境变量
   - **Linux:** `sudo apt install ffmpeg` / `sudo yum install ffmpeg`
   - **macOS:** `brew install ffmpeg`
   - **验证安装：** 运行 `ffmpeg -version`

3. **Anki + AnkiConnect 插件**（可选，用于直接推送）
   
   - **Anki 下载：** [Anki Official Site](https://apps.ankiweb.net/)
   - **AnkiConnect 插件代码：** `2055492159`

#### Anki 笔记类型（必需）

本工具需要专门的 Anki 笔记类型来正确显示所有字段：

- **推荐模板：[Senren Anki 模板库](https://brenoaqua.github.io/Senren/setup_overview/)**
  - 完整支持音调显示、音频播放、释义格式化
  - 包含精美的卡片样式
  - 支持 Yomitan 格式的 HTML 释义

**安装 Senren 模板：**

1. 访问 [Senren Note Types GitHub](https://github.com/BrenoAqua/Senren/releases/)
2. 下载 `.apkg` 模板包
3. 在 Anki 中双击导入
4. 使用模板中的笔记类型名称（默认 `Senren`）

### Python 依赖安装

```bash
# 方式1：直接安装（推荐）
pip install -r requirements.txt

# 方式2：手动安装核心依赖
pip install pysubs2 fugashi[unidic-lite] requests pandas PySide6 PySide6-Fluent-Widgets mdxscraper
```

### 依赖清单

**核心库：**

- `pysubs2` - 字幕解析
- `fugashi` + `unidic-lite` - 日语分词和词元推导
- `requests` - HTTP 请求（AnkiConnect）
- `pandas` - CSV 导出
- `mdxscraper` - MDX 词典查询

**GUI 库（仅 GUI 版本需要）：**

- `PySide6` ≥ 6.6.0 - Qt6 Python 绑定
- `PySide6-Fluent-Widgets` - Fluent Design 组件库

**可选库：**

- `jamdict` - JMDict 字典 fallback（`--use-jamdict`）

### 词典文件准备（不包含在本仓库）

需要自行准备以下词典文件：

#### 必需词典

1. **Primary MDX** - 核心释义词典
   - 推荐：大辞林、新明解国語辞典
2. **NHK 音调词典** - 音调和音频
   - NHK 新版（带音频，优先）
   - NHK 旧版（备用）

#### 可选词典

3. **Secondary MDX** - 补充释义词典
4. **Tertiary MDX** - 第三级词典
5. **大辞泉 MDX (DJS)** - 备用音频源
6. **BCCWJ 频率数据** - 词频统计
   - 文件名：`term_meta_bank_1.json`

**词典目录示例：**

```
~/Japanese_Dicts/
├── Primary_MDX/
│   └── 大辞林.mdx
├── Secondary_MDX/
│   └── 大辞泉.mdx
├── Tertiary_MDX/
│   └── 新明解.mdx
├── NHK_New/
│   ├── NHK.mdx
│   └── NHK.mdd  # 音频文件
├── NHK_Old/
│   ├── NHK_Old.mdx
│   └── NHK_Old.mdd
├── DJS_N/
│   ├── DJS.mdx
│   └── DJS.mdd
└── term_meta_bank_1.json
```

---

## 📖 使用方法

### GUI 模式（推荐新手）🎨

#### 1. 启动应用
```bash
python app.py
```

#### 2. 配置参数（主界面）

**基本素材：**
- **视频文件：** 拖拽或点击浏览按钮选择 `.mp4` / `.mkv` 等视频
- **字幕文件：** 选择日语字幕文件 `.srt` / `.ass`
- **单词表：** 选择包含目标单词的 `.txt` 文件
- **输出目录：** 选择卡片输出目录

**词典配置：**
- **Primary MDX：** 核心释义词典（如大辞林）
- **Secondary MDX：** 补充释义词典（可选）
- **Tertiary MDX：** 第三级词典（可选）
- **NHK 旧版：** NHK 旧版音调词典
- **NHK 新版：** NHK 新版音调词典（优先）
- **大辞泉 (DJS)：** 备用音频源（可选）
- **频率数据：** BCCWJ 词频文件（可选）

**Anki 推送：**
- 勾选"推送到 Anki"复选框
- 输入标签（空格分隔，如 `anime season1 ep01`）

#### 3. 配置 Anki 设置（Anki 设置界面）
- **AnkiConnect URL：** 默认 `http://127.0.0.1:8765`
- **牌组名称：** 如 `Japanese::Anime::MyShow`
- **笔记类型：** 推荐 `Senren`
- **测试连接：** 点击测试按钮验证连接

#### 4. 开始处理
- 点击"开始处理"按钮（宽度 150px，绿色）
- 实时查看进度条和日志输出
- 需要停止时点击"停止处理"（红色）
- 处理完成后查看输出目录的 CSV 文件

#### 5. 词典查询（词典查询界面）
- 输入单词进行实时查询
- 查看 Yomitan 格式的释义
- 测试词典配置是否正确

**💡 提示：** 所有配置会自动保存到 `~/.config/JA-Mining/gui_config.json`，下次启动自动恢复。

---

### CLI 模式（推荐批量处理）💻

#### 基本用法

```bash
python cli.py \
  --video "episodes/S01E01.mp4" \
  --subs "subs/S01E01.ja.srt" \
  --words "words/S01E01.txt" \
  --primary-mdx "dicts/Primary_MDX" \
  --nhk-new "dicts/NHK_New" \
  --freq "dicts/term_meta_bank_1.json" \
  --outdir "output/S01E01" \
  --csv "output/S01E01/cards.csv"
```

#### 推送到 Anki

```bash
python cli.py \
  --video "episodes/S01E01.mp4" \
  --subs "subs/S01E01.ja.srt" \
  --words "words/S01E01.txt" \
  --primary-mdx "dicts/Primary_MDX" \
  --secondary-mdx "dicts/Secondary_MDX" \
  --tertiary-mdx "dicts/Tertiary_MDX" \
  --nhk-old "dicts/NHK_Old" \
  --nhk-new "dicts/NHK_New" \
  --djs "dicts/DJS_N" \
  --freq "dicts/term_meta_bank_1.json" \
  --outdir "output/S01E01" \
  --csv "output/S01E01/cards.csv" \
  --anki \
  --anki-deck "Japanese::Anime::MyShow" \
  --anki-model "Senren" \
  --anki-tags anime myshow S01E01
```

#### 批量处理脚本（PowerShell）

```powershell
# 处理整季动画
1..12 | ForEach-Object {
    $ep = "{0:D2}" -f $_
    python cli.py `
      --video "episodes/S01E$ep.mp4" `
      --subs "subs/S01E$ep.ja.srt" `
      --words "words/S01E$ep.txt" `
      --primary-mdx "dicts/Primary_MDX" `
      --nhk-new "dicts/NHK_New" `
      --freq "dicts/term_meta_bank_1.json" `
      --outdir "output/S01E$ep" `
      --csv "output/S01E$ep/cards.csv" `
      --anki `
      --anki-deck "Japanese::MyAnime" `
      --anki-model "Senren" `
      --anki-tags anime season1 "ep$ep"
}
```

---

## ⚙️ 命令行参数详解

### 必需参数

| 参数         | 说明       | 示例                        |
| ---------- | -------- | ------------------------- |
| `--video`  | 视频文件路径   | `episodes/S01E01.mp4`     |
| `--subs`   | 字幕文件路径   | `subs/S01E01.ja.srt`      |
| `--words`  | 单词列表文件   | `words/S01E01.txt`        |
| `--outdir` | 输出目录     | `output/S01E01`           |
| `--csv`    | CSV 输出路径 | `output/S01E01/cards.csv` |

### 词典参数

| 参数                | 说明                 | 是否必需 |
| ----------------- | ------------------ | ---- |
| `--primary-mdx`   | Primary 释义词典       | 推荐   |
| `--secondary-mdx` | Secondary 释义词典     | 可选   |
| `--tertiary-mdx`  | Tertiary 释义词典      | 可选   |
| `--nhk-old`       | NHK 旧版音调词典         | 推荐   |
| `--nhk-new`       | NHK 新版音调词典         | 推荐   |
| `--djs`           | 大辞泉词典（备用音频）        | 可选   |
| `--freq`          | 频率数据文件             | 可选   |
| `--use-jamdict`   | 启用 JMDict fallback | 可选   |

### 媒体处理参数

| 参数      | 说明          | 默认值   |
| ------- | ----------- | ----- |
| `--pad` | 音频裁剪前后填充（秒） | `0.0` |
| `--vf`  | FFmpeg 视频滤镜 | 无     |

**常用滤镜示例：**

```bash
# 裁剪字幕区域
--vf "crop=iw:ih*0.5:0:ih*0.5"

# 调整亮度和对比度
--vf "eq=brightness=0.1:contrast=1.2"

# 组合滤镜
--vf "crop=iw:ih*0.5:0:ih*0.5,eq=brightness=0.1"
```

### Anki 推送参数

| 参数             | 说明                  | 默认值                     |
| -------------- | ------------------- | ----------------------- |
| `--anki`       | 启用推送到 Anki          | `False`                 |
| `--anki-url`   | AnkiConnect API 地址  | `http://localhost:8765` |
| `--anki-deck`  | 目标牌组名称              | `Japanese::Anime`       |
| `--anki-model` | 笔记类型名称（推荐 `Senren`） | `JP_Mining_Note`        |
| `--anki-tags`  | 标签列表（空格分隔）          | 无                       |

### 其他参数

| 参数        | 说明         |
| --------- | ---------- |
| `--quiet` | 安静模式（减少输出） |
| `--help`  | 显示帮助信息     |

---

## 📤 输出格式

### CSV 字段说明

| 字段名                     | 说明               | 示例                              |
| ----------------------- | ---------------- | ------------------------------- |
| `word`                  | 单词（查询成功的形态）      | `食べる`                           |
| `sentence`              | 例句（原始字幕）         | `美味しいご飯を食べた`                    |
| `sentence_furigana`     | 例句假名注音           | `美味[おい]しい ご 飯[はん]を 食[た]べた`      |
| `definition`            | 释义（Yomitan HTML） | `<div class="dict">...</div>`   |
| `reading`               | 单词读音             | `たべる`                           |
| `pitch_position`        | 音调位置（数字）         | `3`                             |
| `pitch_type`            | 音调类型             | `中高型`                           |
| `pitch_source`          | 音调来源             | `NHK_New`                       |
| `sentence_audio_base64` | 句子音频（Base64）     | `data:audio/mp3;base64,...`     |
| `word_audio_base64`     | 单词音频（Base64）     | `data:audio/mp3;base64,...`     |
| `word_audio_source`     | 单词音频来源           | `NHK_New`                       |
| `picture_base64`        | 截图（Base64）       | `data:image/jpeg;base64,...`    |
| `bccwj_frequency`       | BCCWJ 频率描述       | `上位 5%（高频）`                     |
| `bccwj_freq_sort`       | BCCWJ 排序值        | `5000`                          |
| `anime_name`            | 动漫名称             | `MyAnime`                       |
| `episode`               | 集数               | `S01E01`                        |
| `start_time`            | 字幕起始时间           | `00:05:23.450`                  |
| `end_time`              | 字幕结束时间           | `00:05:26.120`                  |
| `lemma`                 | 词元形式             | `食べる`                           |
| `all_readings`          | 所有读音（JSON）       | `[{"reading":"たべる","pitch":3}]` |

### Anki 字段映射
> ⚠️ **Warning：MiscInfo 字段的集数抽取依赖于文件名格式，当前仅支持如 `S01E01`、`E01` 等标准格式。若视频文件名未包含集数信息，或格式不符，MiscInfo 字段可能无法正确生成集数部分，导致卡片信息不完整。开发时未对无集数场景进行充分验证，建议手动检查文件名或在批量处理前统一命名。**
>
> 参考：[ANKI_IMPORT_GUIDE.md](ANKI_IMPORT_GUIDE.md) 字段映射说明。
推送到 Anki 时，CSV 字段映射到笔记类型字段：

```
word → word
sentence → sentence
sentenceFurigana → sentenceFurigana
reading → reading
definition → definition
pitch → pitch
pitchPosition → pitchPosition
wordAudio → wordAudio (音频文件名)
sentenceAudio → sentenceAudio (音频文件名)
picture → picture (图片文件名)
frequency → frequency
```

**注意：** 字段名采用 **小驼峰命名**（camelCase），需要在 Anki 中创建对应的笔记类型。

---

## 🔧 技术细节

### 词元推导（Lemmatization）

使用 **Fugashi + UniDic** 进行日语词元推导：

```
食べた → 食べる    (动词过去式 → 基本形)
見ている → 見る    (动词进行时 → 基本形)
走った → 走る      (动词过去式 → 基本形)
美しかった → 美しい (形容词过去式 → 基本形)
```

### 复合词回退（く→き Variant）

日语复合词常以**连用形（き结尾）**出现在词典中，但 Fugashi 返回**词典形（く结尾）**：

```
狂い咲く → 查询顺序：
  1. 狂い咲く（Fugashi 返回的词元）
  2. 狂い咲き（き变体）← 词典中的实际形态
```

### 片假名处理

全片假名词汇（外来语、拟声词）优先用原形查询：

```
ピン → 查询顺序：
  1. ピン（原始片假名）← 可能是专有名词
  2. ぴん（转换为平假名）← 通用查询
```

### 长音展开

**仅对非片假名词汇**展开长音符号：

```
# 展开规则
こー → こう   (お段 + 长音 = う)
せー → せい   (え段 + 长音 = い)
そー → そう   (お段 + 长音 = う)
けー → けい   (え段 + 长音 = い)

# 片假名保持原样
コー → コー   (不展开)
セー → セー   (不展开)
```

### 音调类型判定

根据**音调位置**和**假名长度**判断：

```python
if pitch == 0:
    → 平板式（全部高音，无下降）
elif pitch == 1:
    → 头高型（第一拍高，之后下降）
elif pitch == len(kana):
    → 尾高型（最后一拍后下降）
else:
    → 中高型（中间某处下降）
```

### 音调 HTML 生成（Yomitan 风格）

```python
# 示例：たべる（音调3，中高型）
<span style="display:inline-block;position:relative;padding-top:0.25em;">
  <span style="color:#fca311;">た</span>  # 橙色
  <span style="color:#fca311;">べ</span>  # 橙色
  <span style="color:#fca311;">る</span>  # 橙色
  <span style="display:inline-block;border-top:2px solid #fca311;">  # 上划线
    <span>たべる</span>
  </span>
  <span style="border-left:2px solid #fca311;"></span>  # 下降标记
</span>
```

---

## ❓ 常见问题

### Q1: FFmpeg 未找到或无法运行？

**A:** 解决步骤：

1. 访问 https://ffmpeg.org/download.html 下载
2. 解压到合适位置（如 `C:\ffmpeg`）
3. 添加到系统 PATH 环境变量：
   - Windows: 系统属性 → 环境变量 → Path → 新建 → 添加 `C:\ffmpeg\bin`
4. 重启命令行/PowerShell
5. 验证：运行 `ffmpeg -version`

### Q2: 为什么有些单词查不到释义？

**A:** 可能原因和解决方案：

| 原因       | 解决方案                   |
| -------- | ---------------------- |
| 词典中没有该词条 | 使用 `[]` 指定查词形态，或添加更多词典 |
| 活用形未正确推导 | 使用 `食べた[食べる]` 强制指定     |
| 复合词形态差异  | 程序会自动尝试 `く→き` 变体       |
| 片假名外来语   | 程序会自动尝试平假名转换           |

### Q3: 读音不正确怎么办？

**A:** 使用圆括号强制指定：

```
精霊(せいれい)   # 强制使用「せいれい」而不是「しょうりょう」
生贄(いけにえ)   # 强制使用「いけにえ」而不是「せいぎせい」
```

### Q5: AnkiConnect 连接失败？

**A:** 检查清单：

1. ✅ Anki 是否正在运行
2. ✅ AnkiConnect 插件是否已安装（代码：`2055492159`）
3. ✅ 防火墙是否允许 `127.0.0.1:8765`
4. ✅ URL 是否正确（默认 `http://127.0.0.1:8765`）

**测试方法：**

```bash
# PowerShell
Invoke-WebRequest -Uri http://127.0.0.1:8765 -Method Post -Body '{"action":"version","version":6}' -ContentType "application/json"

# 应该返回版本号
```

### Q6: GUI 的配置文件保存在哪里？

**A:** 配置文件路径：
- **Windows:** `C:\Users\<用户名>\.config\JA-Mining\gui_config.json`
- **Linux/Mac:** `~/.config/JA-Mining/gui_config.json`

可以手动编辑此文件修改默认配置。

### Q7: Senren 模板和工具默认字段不匹配？

**A:** 本工具输出字段完全兼容 Senren 模板。如果使用其他模板：

1. 在 Anki 中创建自定义笔记类型
2. 添加对应字段（参考"输出格式"章节）
3. 使用 `--anki-model` 指定你的笔记类型名称

### Q8: 如何批量处理多集动画？

**A:** 使用 CLI + 脚本循环：

**PowerShell 示例：**

```powershell
1..12 | ForEach-Object {
    $ep = "E{0:D2}" -f $_
    python cli.py `
      --video "episodes/$ep.mp4" `
      --subs "subs/$ep.ja.srt" `
      --words "words/$ep.txt" `
      --primary-mdx "dicts/primary.mdx" `
      --nhk-new "dicts/nhk_new.mdx" `
      --freq "dicts/term_meta_bank_1.json" `
      --outdir "output/$ep" `
      --csv "output/$ep/cards.csv" `
      --anki `
      --anki-deck "Japanese::MyAnime" `
      --anki-tags anime "s01$ep"
}
```

**Bash 示例：**

**Bash 示例：**
```bash
for i in {1..12}; do
  ep=$(printf "E%02d" $i)
  python cli.py \
    --video "episodes/$ep.mp4" \
    --subs "subs/$ep.ja.srt" \
    --words "words/$ep.txt" \
    --primary-mdx "dicts/Primary_MDX" \
    --nhk-new "dicts/NHK_New" \
    --freq "dicts/term_meta_bank_1.json" \
    --outdir "output/$ep" \
    --csv "output/$ep/cards.csv" \
    --anki \
    --anki-deck "Japanese::MyAnime" \
    --anki-model "Senren" \
    --anki-tags anime "s01$ep"
done
```

---

## 🔄 版本历史

### Version 1.0 (当前版本) - 初始发布

**核心功能：**

- ✅ 基础字幕词汇挖掘功能
- ✅ 词典查询和释义提取
- ✅ 音调标注和音频提取
- ✅ 视频截图和音频裁剪
- ✅ CSV 导出
- ✅ AnkiConnect 推送集成
- ✅ 命令行工具（CLI）

**技术实现：**

- ✅ 单文件主程序（`jp_media_mining_refactored.py`）
- ✅ MDX 词典集成
- ✅ Fugashi 分词
- ✅ FFmpeg 媒体处理
- ✅ 基础词典查询策略

**已知限制：**

- ⚠️ 代码未模块化（所有功能在单文件中）
  
  

### 未来计划（Version 2.0）

**架构重构：**

- 🔄 模块化设计（core/ + gui/ + mdx_utils/）
- 🔄 配置类和数据模型
- 🔄 日志系统增强

**新功能：**

- 🔄 GUI 应用（PySide6 + Fluent Design）
- 🔄 配置持久化
- 🔄 实时词典查询界面
- 🔄 拖拽文件支持
- 🔄 三级词典架构（Primary/Secondary/Tertiary）
- 🔄 进度监控和停止控制

---

## 📜 许可证

**GNU General Public License v3.0 (GPL-3.0)**

Copyright (c) 2025 Subsmith

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

---

## 🙏 致谢

**必需软件：**

- **[FFmpeg](https://ffmpeg.org/)** - 强大的音视频处理工具
  - 项目地址：https://ffmpeg.org/
  - 许可证：LGPL / GPL
- **[Anki](https://apps.ankiweb.net/)** - 开源间隔重复学习软件
  - 项目地址：https://apps.ankiweb.net/
  - 许可证：AGPL-3.0

**Anki 模板：**

- **[Senren Anki Note Types](https://github.com/SenrenNagasaki/senren-anki-note-types)** - 专业的日语学习卡片模板
  - 作者：SenrenNagasaki
  - 项目地址：https://github.com/SenrenNagasaki/senren-anki-note-types
  - 特性：完整支持音调显示、音频播放、Yomitan 格式释义
  - 本工具默认输出字段完全兼容此模板

**开源库：**

- **[Fugashi](https://github.com/polm/fugashi)** - 高性能日语分词（MeCab Python 绑定）
  - 作者：Paul O'Leary McCann
  - 许可证：MIT
- **[UniDic](https://clrd.ninjal.ac.jp/unidic/)** - 日本国立国语研究所标准词典
  - 提供准确的词元推导和词性标注
- **[pysubs2](https://github.com/tkarabela/pysubs2)** - 字幕解析库
  - 许可证：MIT
- **[PySide6-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)** - Fluent Design 组件库
  - 作者：zhiyiYo
  - 许可证：GPL-3.0
- **[MDXScraper](https://github.com/VimWei/MdxScraper)** - MDX 词典查询库
  - 许可证：GPL-3.0

**插件和工具：**

- **[AnkiConnect](https://github.com/FooSoft/anki-connect.git)** - Anki 的 HTTP API 插件
  - 作者：Alex Yatskov
  - 插件代码：2055492159
  - 许可证：GPL-3.0
- **[Yomitan](https://github.com/themoeway/yomitan)** - 浏览器日语词典扩展
  - 格式标准参考

**词典资源：**

- **NHK 日本語発音アクセント辞典** - 音调和发音标准
- **大辞林 / 大辞泉 / 新明解国語辞典** - 释义词典
- **BCCWJ (Balanced Corpus of Contemporary Written Japanese)** - 日语语料库词频数据

**社区：**

- **FreeMdict Forum** 的所有贡献者和支持者
- **Anki 中文社区** 的测试和反馈
- **MDX 词典制作者们** 的辛勤工作

---

## 🤝 贡献

欢迎提交 **Issue** 和 **Pull Request**！

**贡献指南：**

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

**开发计划：**

### TODO（功能冻结，待后续解锁）

 - [ ] 词典系统分组重构（命名优化，避免 Primary/Secondary/Tertiary 迷惑性）：
   - Jp-Jp：日语-日语词典（如大辞林/新明解），支持多文件
   - Jp-Target：日语-目标语言词典（如日英、日中等），支持多文件
   - Jp-Target-Extra：目标语言补充词典（如日英补充、日中补充等），支持多文件
  - Jp-Target-Extra：语音/音调词典（如 NHK、DJS 等），支持多文件（用于音频和音调信息补充）
  - GUI/CLI 参数选择均需支持每组任意数量词典
  - TODO：所有相关参数、界面、文档需同步采用新命名，彻底弃用 Primary/Secondary/Tertiary 关键词，避免用户理解混淆
- [ ] 词典组内可动态添加/删除词典文件（GUI/CLI）
- [ ] 词典优先级和分组逻辑调整
- [ ] 相关参数和界面设计同步升级

**注意：本月所有代码开发和特性升级已冻结，避免破坏现有稳定性。**

[ ] CLI 批量推送优化（连接池）
[ ] 更多词典格式支持
[ ] 导出为 Anki 模板包
[ ] 多语言界面支持
[ ] 云端词典查询

---

## 📧 联系方式

如有问题或建议，请通过以下方式联系：

- **GitHub Issues:** [提交 Issue](https://github.com/yourusername/Japanese-Anime-Mining-Tool/issues)
- **Discussions:** [参与讨论](https://github.com/yourusername/Japanese-Anime-Mining-Tool/discussions)

---

**⭐ 如果这个工具对你有帮助，请给个 Star！**
