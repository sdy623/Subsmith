# Anki 导入指南

## 功能概述

`import_to_anki.py` 脚本可以将 `jp_media_mining_refactored.py` 生成的 CSV 数据直接导入到 Anki,无需手动操作。

## 前置准备

### 1. 安装 AnkiConnect 插件

1. 打开 Anki
2. 工具 → 插件 → 获取插件
3. 输入代码: `2055492159`
4. 重启 Anki

### 2. 创建 Senren 笔记类型

在 Anki 中创建名为 "Senren" 的笔记类型,包含以下字段:

**字段列表:**
- `word` - 单词
- `sentence` - 原句 (带高亮)
- `sentenceFurigana` - 带假名的句子
- `sentenceEng` - 英文翻译 (可选)
- `reading` - 读音 (带音调标记)
- `sentenceCard` - 句子卡片内容 (可选)
- `audioCard` - 音频卡片 (可选)
- `notes` - 笔记 (可选)
- `picture` - 截图
- `wordAudio` - 单词音频
- `sentenceAudio` - 句子音频
- `selectionText` - 选中文本 (可选)
- `definition` - 释义 (HTML)
- `glossary` - 词汇表 (与 definition 相同)
- `pitchPosition` - 音调位置 ([0], [1], [2] 等)
- `pitch` - 音调类型 (平板式/頭高型/中高型/尾高型)
- `frequency` - 频率信息
- `freqSort` - 频率排序值
- `miscInfo` - 附加信息 (动漫名|集数|时间戳)
- `dictionaryPreference` - 词典偏好 (可选)

### 3. 安装 Python 依赖

```bash
pip install requests pandas
```

## 使用方法

### 基础用法

```bash
python import_to_anki.py --csv "out/Ep01/cards.csv"
```

### 完整用法

```bash
python import_to_anki.py \
  --csv "out/Ep01/cards.csv" \
  --deck "Japanese::Anime" \
  --model "Senren" \
  --tags anime mining \
  --allow-duplicates
```

### 参数说明

- `--csv` (必需): CSV 文件路径
- `--deck`: Anki 牌组名称 (默认: `Japanese::Anime`)
- `--model`: Anki 笔记类型 (默认: `Senren`)
- `--tags`: 卡片标签 (默认: `anime mining`)
- `--allow-duplicates`: 允许重复卡片
- `--ankiconnect-url`: AnkiConnect API 地址 (默认: `http://localhost:8765`)

## 工作流程

### 完整流程示例

```bash
# 1. 生成 CSV 数据
python jp_media_mining_refactored.py \
  --video "[BeanSub] Kimetsu no Yaiba [01].mp4" \
  --subs "Ep01.ja.srt" \
  --words "S01E01_words.txt" \
  --primary-mdx "dicts/primary" \
  --secondary-mdx "dicts/secondary" \
  --nhk-old "dicts/NHK_Old" \
  --nhk-new "dicts/NHK_New" \
  --djs "dicts/DJS" \
  --freq "dicts/term_meta_bank_1.json" \
  --outdir "out/S01E01" \
  --csv "out/S01E01/cards.csv"

# 2. 导入到 Anki
python import_to_anki.py \
  --csv "out/S01E01/cards.csv" \
  --deck "Japanese::Kimetsu_no_Yaiba" \
  --tags anime kimetsu S01E01
```

## 字段映射详解

### CSV → Anki 字段映射

| CSV 字段 | Anki 字段 | 说明 |
|---------|----------|------|
| `word` | `word` | 单词 |
| `sentence` | `sentence` | 原句 (高亮显示单词) |
| `sentence_furigana` | `sentenceFurigana` | 带假名的句子 |
| `definition` | `definition`, `glossary` | HTML 格式释义 |
| `reading` | `reading` | 读音 (HTML 格式,带音调标记) |
| `pitch_position` | `pitchPosition` | 音调位置 |
| `pitch_type` | `pitch` | 音调类型 |
| `picture_file` | `picture` | 截图 (自动上传) |
| `word_audio_file` | `wordAudio` | 单词音频 (自动上传) |
| `sentence_audio_file` | `sentenceAudio` | 句子音频 (自动上传) |
| `bccwj_frequency` | `frequency` | 频率显示值 |
| `bccwj_freq_sort` | `freqSort` | 频率排序值 |
| `anime_name` + `episode` + `start_time` | `miscInfo` | 格式: "动漫名 \| S01E01 \| 01:23" |

### miscInfo 字段格式

```
Kimetsu no Yaiba | S01E05 | 01:45
```

包含三部分,使用 `|` 分隔:
1. **动漫名**: 从视频文件名提取
2. **集数**: 从单词文件名提取 (S01E05 格式)
3. **时间戳**: 字幕开始时间 ((h:)mm:ss 格式)

示例:
- `105.5` 秒 → `01:45`
- `3665.5` 秒 → `1:01:05`

## 特殊功能

### 1. 自动去重

脚本会自动为同一单词的多次出现生成唯一的媒体文件名:
- `荷車_1_pic.jpg`
- `荷車_1_word.aac`
- `荷車_1_sent.m4a`

### 2. 媒体文件处理

媒体文件会自动:
1. 从 `media/` 目录读取
2. 转换为 Base64 编码
3. 通过 AnkiConnect 上传到 Anki
4. 生成正确的 `[sound:...]` 或 `<img>` 标签

### 3. 读音格式化

读音字段会自动格式化为 HTML 列表:
```html
<ol>
  <li>ニ<span style="text-decoration: overline;">ク</span>ルマ</li>
</ol>
```

### 4. 高亮显示

原句中的目标单词会自动高亮:
```html
きょうは<span class="highlight">荷車</span>を引いていけないから
```

## 常见问题

### 1. 连接失败

**错误**: `❌ AnkiConnect 连接失败`

**解决**:
1. 确保 Anki 正在运行
2. 确认已安装 AnkiConnect 插件
3. 检查防火墙设置
4. 重启 Anki

### 2. 笔记类型不存在

**错误**: `model was not found`

**解决**:
1. 在 Anki 中手动创建 "Senren" 笔记类型
2. 或者使用 `--model` 参数指定已存在的笔记类型

### 3. 媒体文件缺失

**错误**: `⚠️ 媒体目录不存在`

**解决**:
确保 CSV 文件和 `media/` 目录在同一父目录下:
```
out/S01E01/
├── cards.csv
└── media/
    ├── 荷車_1_pic.jpg
    ├── 荷車_1_word.aac
    └── 荷車_1_sent.m4a
```

### 4. 重复卡片

**错误**: `cannot create note because it is a duplicate`

**解决**:
使用 `--allow-duplicates` 参数允许重复卡片

## 批量导入

### 导入整季动漫

```bash
# 假设有 S01E01 到 S01E12
for i in {01..12}; do
  python import_to_anki.py \
    --csv "out/S01E$i/cards.csv" \
    --deck "Japanese::Kimetsu_no_Yaiba" \
    --tags anime kimetsu S01E$i
done
```

### PowerShell 批量导入

```powershell
# 导入所有 CSV 文件
Get-ChildItem -Path "out" -Filter "cards.csv" -Recurse | ForEach-Object {
    $episode = $_.Directory.Name
    python import_to_anki.py `
      --csv $_.FullName `
      --deck "Japanese::Anime" `
      --tags anime $episode
}
```

## 卡片模板建议

### 正面模板

```html
<div class="word">{{word}}</div>
<div class="sentence">{{sentence}}</div>
<div class="picture">{{picture}}</div>
{{sentenceAudio}}
```

### 背面模板

```html
{{FrontSide}}
<hr id="answer">
<div class="reading">{{reading}}</div>
<div class="pitch">{{pitch}} {{pitchPosition}}</div>
<div class="definition">{{definition}}</div>
<div class="word-audio">{{wordAudio}}</div>
<div class="misc-info">{{miscInfo}}</div>
```

### CSS 样式

```css
.card {
  font-family: "Yu Gothic", "Hiragino Kaku Gothic Pro", sans-serif;
  font-size: 20px;
  text-align: center;
}

.word {
  font-size: 32px;
  font-weight: bold;
  margin: 20px;
}

.sentence {
  font-size: 24px;
  margin: 15px;
}

.highlight {
  color: #ff6b6b;
  font-weight: bold;
}

.picture {
  margin: 20px auto;
  max-width: 80%;
}

.picture img {
  max-width: 100%;
  border-radius: 8px;
}

.reading {
  font-size: 28px;
  color: #4a90e2;
  margin: 15px;
}

.pitch {
  font-size: 18px;
  color: #666;
}

.definition {
  text-align: left;
  margin: 20px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 8px;
}

.misc-info {
  margin-top: 15px;
  padding: 10px;
  background: #e8f4f8;
  border-radius: 5px;
  font-size: 14px;
  color: #555;
}
```

## 性能优化

### 大批量导入

对于超过 1000 张卡片的导入:

1. 使用 `--quiet` 模式减少输出
2. 分批导入 (每批 100-200 张)
3. 确保 Anki 有足够的内存

### 加速技巧

1. **预先创建牌组**: 手动在 Anki 中创建牌组
2. **关闭同步**: 导入时暂时关闭 AnkiWeb 同步
3. **暂停插件**: 导入时禁用其他 Anki 插件

## 许可证

MIT License
