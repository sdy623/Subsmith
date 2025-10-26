# 快速开始 - 一键导入 Anki

## 🚀 一键完成流程

从视频提取单词到 Anki 卡片,一条命令搞定!

### 前置准备

#### 1. 安装 AnkiConnect

在 Anki 中安装 AnkiConnect 插件:

1. 打开 Anki
2. **工具** → **插件** → **获取插件**
3. 输入代码: **2055492159**
4. 重启 Anki

#### 2. 确保 Anki 正在运行

使用 `--anki` 参数时,Anki 必须在后台运行。

#### 3. (可选) 创建笔记类型

如果你没有 "Senren" 笔记类型,可以:
- 使用 `--anki-model` 参数指定已有的笔记类型
- 或在 Anki 中手动创建 (详见 [ANKI_IMPORT_GUIDE.md](ANKI_IMPORT_GUIDE.md))

---

## 📖 使用方法

### 方式 1: 一键推送到 Anki (推荐)

```bash
python jp_media_mining_refactored.py \
  --video "[BeanSub] Kimetsu no Yaiba [01].mp4" \
  --subs "Ep01.ja.srt" \
  --words "S01E01_words.txt" \
  --primary-mdx "dicts/primary" \
  --nhk-old "dicts/NHK_Old" \
  --nhk-new "dicts/NHK_New" \
  --djs "dicts/DJS" \
  --freq "dicts/term_meta_bank_1.json" \
  --outdir "out/S01E01" \
  --csv "out/S01E01/cards.csv" \
  --anki \
  --anki-deck "Japanese::Kimetsu_no_Yaiba" \
  --anki-tags anime kimetsu S01E01
```

**效果**: 
- ✅ 自动提取单词信息
- ✅ 生成截图和音频
- ✅ 查询词典释义和读音
- ✅ 导出 CSV 文件
- ✅ **直接推送到 Anki**

### 方式 2: 仅生成 CSV (不推送)

```bash
python jp_media_mining_refactored.py \
  --video "Ep01.mp4" \
  --subs "Ep01.ja.srt" \
  --words "words.txt" \
  --primary-mdx "dicts/primary" \
  --nhk-old "dicts/NHK_Old" \
  --outdir "out/Ep01" \
  --csv "out/Ep01/cards.csv"
```

CSV 确认无误后,可以单独推送:

```bash
python import_to_anki.py \
  --csv "out/Ep01/cards.csv" \
  --deck "Japanese::Anime"
```

---

## 🎯 参数说明

### 必需参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--video` | 视频文件 | `"Ep01.mp4"` |
| `--subs` | 字幕文件 | `"Ep01.ja.srt"` |
| `--words` | 单词列表 | `"words.txt"` |
| `--outdir` | 输出目录 | `"out/Ep01"` |
| `--csv` | CSV 路径 | `"out/Ep01/cards.csv"` |

### Anki 相关参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--anki` | 启用 Anki 推送 | (标志) |
| `--anki-deck` | 牌组名称 | `Japanese::Anime` |
| `--anki-model` | 笔记类型 | `Senren` |
| `--anki-tags` | 标签 (多个) | `anime mining` |
| `--anki-allow-duplicates` | 允许重复 | (标志) |
| `--ankiconnect-url` | API 地址 | `http://localhost:8765` |

### 词典参数

| 参数 | 说明 | 用途 |
|------|------|------|
| `--primary-mdx` | 主要词典目录 | 释义 (如明鏡、大辞泉) |
| `--secondary-mdx` | 次要词典目录 | 释义备选 |
| `--tertiary-mdx` | 第三级词典目录 | 释义最终备选 |
| `--nhk-old` | NHK 旧版目录 | 音调信息 |
| `--nhk-new` | NHK 新版目录 | 音频 (AAC) |
| `--djs` | 大辞泉目录 | 音频备选 |
| `--freq` | 频率数据 | BCCWJ JSON 文件 |

---

## 💡 实用技巧

### 1. 自动提取动漫名和集数

文件命名规范:

```
视频文件: [BeanSub] Kimetsu no Yaiba [01].mp4
单词文件: S01E01_words.txt
```

脚本会自动提取:
- **动漫名**: `Kimetsu no Yaiba` (去除方括号内容)
- **集数**: `S01E01` (从单词文件名提取)

这些信息会填充到 Anki 卡片的 `miscInfo` 字段。

### 2. 强制指定读音

在单词文件中使用方括号指定读音:

```
精霊[せいれい]
己[おのれ]
空模様
```

脚本会:
- 优先使用指定的读音查询词典和音频
- 未指定的单词会自动匹配最佳读音

### 3. 批量处理多集

PowerShell 脚本:

```powershell
# 处理 S01E01 到 S01E12
1..12 | ForEach-Object {
    $ep = "S01E{0:D2}" -f $_
    python jp_media_mining_refactored.py `
      --video "videos/$ep.mp4" `
      --subs "subs/$ep.srt" `
      --words "words/$ep.txt" `
      --primary-mdx "dicts/primary" `
      --nhk-old "dicts/NHK_Old" `
      --nhk-new "dicts/NHK_New" `
      --outdir "out/$ep" `
      --csv "out/$ep/cards.csv" `
      --anki `
      --anki-deck "Japanese::Anime" `
      --anki-tags anime $ep
}
```

Bash 脚本:

```bash
#!/bin/bash
for i in {01..12}; do
  ep="S01E$i"
  python jp_media_mining_refactored.py \
    --video "videos/$ep.mp4" \
    --subs "subs/$ep.srt" \
    --words "words/$ep.txt" \
    --primary-mdx "dicts/primary" \
    --nhk-old "dicts/NHK_Old" \
    --nhk-new "dicts/NHK_New" \
    --outdir "out/$ep" \
    --csv "out/$ep/cards.csv" \
    --anki \
    --anki-deck "Japanese::Anime" \
    --anki-tags anime $ep
done
```

### 4. 仅 CSV 模式 (快速测试)

先生成 CSV 确认结果:

```bash
python jp_media_mining_refactored.py \
  --video "Ep01.mp4" \
  --subs "Ep01.ja.srt" \
  --words "words.txt" \
  --primary-mdx "dicts/primary" \
  --nhk-old "dicts/NHK_Old" \
  --outdir "out/test" \
  --csv "out/test/cards.csv"
```

检查 CSV 无误后,再用 `--anki` 参数重新运行。

---

## 🐛 常见问题

### 1. AnkiConnect 连接失败

**错误信息**: `❌ AnkiConnect 连接失败`

**解决方案**:
1. 确认 Anki 正在运行
2. 检查 AnkiConnect 插件是否安装 (代码: 2055492159)
3. 重启 Anki
4. 检查防火墙设置 (允许端口 8765)

### 2. 笔记类型不存在

**错误信息**: `model was not found`

**解决方案**:
- 方案 A: 在 Anki 中手动创建 "Senren" 笔记类型 (参考 ANKI_IMPORT_GUIDE.md)
- 方案 B: 使用已有笔记类型: `--anki-model "你的笔记类型"`

### 3. 卡片重复

**错误信息**: `cannot create note because it is a duplicate`

**解决方案**:
使用 `--anki-allow-duplicates` 参数允许重复卡片。

### 4. 媒体文件缺失

CSV 和 Anki 都会创建媒体文件:
- CSV 模式: 文件保存在 `outdir/media/` 目录
- Anki 模式: 文件直接上传到 Anki 的媒体目录

如果媒体处理失败,检查:
- FFmpeg 是否安装并在 PATH 中
- 视频和字幕文件路径是否正确
- 磁盘空间是否充足

---

## 📝 输出文件

### 目录结构

```
out/S01E01/
├── cards.csv                           # CSV 数据文件
├── media/                              # 媒体文件目录
│   ├── 荷車_1_pic.jpg                  # 截图
│   ├── 荷車_1_word.aac                # 单词音频
│   ├── 荷車_1_sent.m4a                # 句子音频
│   ├── 空模様_2_pic.jpg
│   └── ...
└── [原始临时文件]                      # 视频帧和音频片段
```

### CSV 字段

| 字段 | 说明 | 示例 |
|------|------|------|
| `word` | 单词 | `荷車` |
| `duplicate_count` | 重复次数 | `1` |
| `sentence` | 原句 | `きょうは荷車を引いていけないから` |
| `sentence_furigana` | 带假名 | `きょうは荷車[にぐるま]を引い[ひい]て...` |
| `definition` | 释义 (HTML) | `<div>人・馬が引くなどして...</div>` |
| `reading` | 读音 (HTML) | `ニ<span>ク</span>ルマ` |
| `pitch_position` | 音调位置 | `[2]` |
| `pitch_type` | 音调类型 | `中高型` |
| `picture_file` | 截图路径 | `media/荷車_1_pic.jpg` |
| `word_audio_file` | 单词音频 | `media/荷車_1_word.aac` |
| `sentence_audio_file` | 句子音频 | `media/荷車_1_sent.m4a` |
| `bccwj_frequency` | 频率 | `2万` |
| `anime_name` | 动漫名 | `Kimetsu no Yaiba` |
| `episode` | 集数 | `S01E01` |
| `start_time` | 开始时间 | `105.523` |

---

## ✨ 高级用法

### 自定义牌组层级

```bash
--anki-deck "Japanese::Anime::鬼灭之刃::S01"
```

Anki 会自动创建层级结构:
```
Japanese/
  └── Anime/
      └── 鬼灭之刃/
          └── S01/
```

### 多标签分类

```bash
--anki-tags anime action demon-slayer S01E01 seen
```

每张卡片会有这些标签,方便后续筛选和复习。

### 混合使用词典

```bash
# 三级词典 + JMDict 备选
python jp_media_mining_refactored.py \
  --primary-mdx "dicts/DJS" \
  --secondary-mdx "dicts/明鏡" \
  --tertiary-mdx "dicts/日中" \
  --use-jamdict \
  --anki \
  ...
```

查询顺序: Primary → Secondary → Tertiary → JMDict

---

## 🎓 完整示例

### 示例 1: 处理《鬼灭之刃》第一集

```bash
python jp_media_mining_refactored.py \
  --video "[BeanSub&FZSD] Kimetsu no Yaiba [01].mp4" \
  --subs "S01E01.ja.srt" \
  --words "S01E01_words.txt" \
  --primary-mdx "E:/dicts/DJS" \
  --secondary-mdx "E:/dicts/明鏡" \
  --nhk-old "E:/dicts/NHK_Old" \
  --nhk-new "E:/dicts/NHK_New" \
  --djs "E:/dicts/DJS" \
  --freq "E:/dicts/term_meta_bank_1.json" \
  --outdir "E:/output/kimetsu/S01E01" \
  --csv "E:/output/kimetsu/S01E01/cards.csv" \
  --anki \
  --anki-deck "Japanese::Anime::鬼灭之刃" \
  --anki-tags anime action kimetsu S01E01 \
  --anki-allow-duplicates
```

### 示例 2: 快速测试 (只查 5 个单词)

words_test.txt:
```
荷車
空模様
障子
うまいもん
己
```

```bash
python jp_media_mining_refactored.py \
  --video "Ep01.mp4" \
  --subs "Ep01.ja.srt" \
  --words "words_test.txt" \
  --primary-mdx "dicts/DJS" \
  --nhk-old "dicts/NHK_Old" \
  --outdir "test" \
  --csv "test/cards.csv" \
  --anki \
  --anki-deck "Japanese::Test"
```

---

## 📚 更多资源

- **详细文档**: [jp_media_mining_refactored_README.md](jp_media_mining_refactored_README.md)
- **Anki 导入**: [ANKI_IMPORT_GUIDE.md](ANKI_IMPORT_GUIDE.md)
- **mdx_utils**: [mdx_utils/README.md](mdx_utils/README.md)
- **问题排查**: [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)

---

**祝你学习愉快! 🎉**
