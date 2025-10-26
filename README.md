# 日语动漫字幕挖矿工具 (Japanese Anime Mining Tool)

一套完整的日语学习卡片生成工具,从动漫视频和字幕中自动提取目标单词,生成包含释义、读音、音调、音频和截图的 Anki 卡片。

## 核心特性

### 1. 智能词典查询系统
- **三级词典架构**: Primary (核心词典) → Secondary (补充词典) → Tertiary (备用词典)
- **自动回退查询**: 
  - 词元形式 (食べた → 食べる)
  - 表面形式 (原始输入)
  - く→き 变体 (狂い咲く → 狂い咲き)
  - 片假名→平假名转换 (ピン → ぴん)
- **Yomitan 格式输出**: 完整的 HTML 释义,包含词性、例句等

### 2. 高级音频和音调系统
- **多音调支持**: 自动获取单词的所有可能读音和音调型
- **三级音频源**:
  1. NHK 新版 (第一优先)
  2. NHK 旧版 (第二优先)
  3. 大辞泉 MDX (备用音频)
- **音调类型可视化**: 
  - 平板式 (🔵 蓝色)
  - 头高型 (🔴 红色)
  - 中高型 (🟠 橙色)
  - 尾高型 (🟢 青色)

### 3. 分词和假名注音
- **Fugashi + UniDic**: 高精度日语分词
- **智能送假名处理**: `間違[まちが]い` (不是 `間違い[まちがい]`)
- **空格分隔**: `間違[まちが]い 今[いま]は 重度[じゅうど]の`
- **长音转换**: 
  - お段: こー → こう (不是 こお)
  - え段: せー → せい (不是 せえ)

### 4. 单词表高级语法

支持灵活的单词表格式:

```
# 基本格式
精霊                           # 普通单词,自动提取一切
食べた                         # 自动推导词元 (食べる)

# 圆括号 () = 强制读音
精霊(せいれい)                 # 强制使用这个读音
走った(はしった)               # 指定读音

# 方括号 [] = 强制查词形态
食べた[食べる]                 # 用 食べる 查词典
狂い咲く[狂い咲き]             # 用 狂い咲き 查词典 (复合词)

# 组合使用
走った(はしった)[走る]         # 读音 + 查词形态都指定
```

**语法规则:**
- `()` = 强制读音 (覆盖自动提取)
- `[]` = 强制查词典形态 (覆盖词元推导)
- 可以单独使用,也可以组合使用

### 5. 片假名词汇智能处理

对于全片假名词汇 (如 `ピン`):
1. **优先用片假名查询** (可能词典里有片假名词条)
2. **查不到才转平假名** (ピン → ぴん)
3. 自动记录使用的查询形态

### 6. 媒体处理
- **视频截图**: 自动在句子时间点截图 (可配置滤镜)
- **音频裁剪**: 精确裁剪句子音频 (可配置前后填充)
- **Base64 编码**: 所有媒体嵌入 CSV,一键导入 Anki

### 7. 频率数据
- **BCCWJ 词频**: 显示单词在日语语料库中的频率
- **排序值**: 便于按频率排序学习

### 8. 一键推送到 Anki
- **AnkiConnect 集成**: 直接推送到 Anki,无需手动导入
- **自动创建卡组**: 指定卡组名自动创建
- **标签系统**: 支持多标签 (如 `anime kimetsu S01E01`)

## 文件结构

```
Japanese-Anime-Mining-Tool/
├── jp_media_mining_refactored.py    # 主程序 (核心工具)
├── converage123.py                   # MDX 词典查询测试工具
├── mdx_utils/                        # 词典查询模块
│   ├── __init__.py
│   ├── meanings_lookup.py           # 释义查询 (三级词典)
│   ├── audio_lookup.py              # 音频/音调查询 (Fugashi 集成)
│   └── yomitan_formatter.py         # Yomitan 格式化工具
├── README.md                         # 本文档
├── requirements.txt                  # Python 依赖
└── examples/                         # 示例文件
    ├── example_words.txt            # 单词表示例
    └── example_output.csv           # 输出示例
```

## 安装依赖

### Python 包

```bash
pip install pysubs2 fugashi[unidic-lite] requests pandas
```

### 必需词典文件 (不包含在本仓库)

需要自行准备以下词典:

1. **Primary MDX** (核心词典,如 大辞林、新明解)
2. **Secondary MDX** (补充词典,如 大辞泉)
3. **Tertiary MDX** (备用词典)
4. **NHK 音调词典**:
   - NHK 新版 (带音频)
   - NHK 旧版 (备用)
5. **大辞泉 MDX** (DJS_N,用于备用音频)
6. **BCCWJ 频率数据** (`term_meta_bank_1.json`)

**词典目录结构示例:**
```
dicts/
├── Primary_MDX/
│   └── 大辞林.mdx
├── Secondary_MDX/
│   └── 大辞泉.mdx
├── Tertiary_MDX/
│   └── 新明解.mdx
├── NHK_New/
│   └── NHK.mdx
├── NHK_Old/
│   └── NHK.mdx
├── DJS_N/
│   └── DJS.mdx
└── term_meta_bank_1.json
```

## 使用方法

### 1. 生成 CSV 文件

```bash
python jp_media_mining_refactored.py \
  --video "episodes/S01E01.mp4" \
  --subs "subs/S01E01.ja.srt" \
  --words "words/S01E01_words.txt" \
  --primary-mdx "dicts/Primary_MDX" \
  --secondary-mdx "dicts/Secondary_MDX" \
  --tertiary-mdx "dicts/Tertiary_MDX" \
  --nhk-old "dicts/NHK_Old" \
  --nhk-new "dicts/NHK_New" \
  --djs "dicts/DJS_N" \
  --freq "dicts/term_meta_bank_1.json" \
  --outdir "output/S01E01" \
  --csv "output/S01E01/cards.csv"
```

### 2. 直接推送到 Anki (需要 AnkiConnect)

```bash
python jp_media_mining_refactored.py \
  --video "episodes/S01E01.mp4" \
  --subs "subs/S01E01.ja.srt" \
  --words "words/S01E01_words.txt" \
  --primary-mdx "dicts/Primary_MDX" \
  --nhk-old "dicts/NHK_Old" \
  --nhk-new "dicts/NHK_New" \
  --djs "dicts/DJS_N" \
  --freq "dicts/term_meta_bank_1.json" \
  --outdir "output/S01E01" \
  --csv "output/S01E01/cards.csv" \
  --anki \
  --anki-deck "Japanese::Anime::MyAnime" \
  --anki-tags anime myshow S01E01
```

### 3. 测试词典查询 (converage123.py)

```bash
python converage123.py
```

这个工具用于测试 MDX 词典的查询功能,可以验证:
- 词典是否正确加载
- 查询结果是否为 Yomitan 格式
- HTML 输出是否正确

## 单词表格式详解

### 基本格式

```
精霊
食べる
走る
```

### 指定读音 (圆括号)

```
精霊(せいれい)
生贄(いけにえ)
```

用途: 当词典有多个读音,但你想强制使用特定读音时

### 指定查词形态 (方括号)

```
食べた[食べる]
狂い咲く[狂い咲き]
すばしっこかった[素早い]
```

用途: 
- 活用形无法自动推导时
- 复合词词典中使用不同形态 (く→き)
- 强制使用特定词条

### 组合使用

```
走った(はしった)[走る]
食べた(たべた)[食べる]
```

## 命令行参数

### 必需参数

| 参数 | 说明 |
|------|------|
| `--video` | 视频文件路径 |
| `--subs` | 字幕文件路径 (.srt/.ass) |
| `--words` | 单词列表文件路径 |
| `--primary-mdx` | Primary 词典目录 |
| `--nhk-old` | NHK 旧版词典目录 |
| `--nhk-new` | NHK 新版词典目录 |
| `--djs` | 大辞泉词典目录 (DJS_N) |
| `--freq` | 频率数据 JSON 文件 |
| `--outdir` | 输出目录 |

### 可选参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--secondary-mdx` | Secondary 词典目录 | 无 |
| `--tertiary-mdx` | Tertiary 词典目录 | 无 |
| `--csv` | CSV 输出路径 | `{outdir}/cards.csv` |
| `--pad` | 音频裁剪前后填充(秒) | 0.3 |
| `--vf` | FFmpeg 视频滤镜 | `crop=iw:ih*0.5:0:ih*0.5` |
| `--verbose` | 显示详细日志 | False |
| `--quiet` | 安静模式 | False |

### Anki 相关参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--anki` | 启用 AnkiConnect 推送 | False |
| `--anki-url` | AnkiConnect URL | `http://localhost:8765` |
| `--anki-deck` | 目标卡组名称 | `Japanese::Anime` |
| `--anki-model` | 笔记类型名称 | `JP_Mining_Note` |
| `--anki-tags` | 标签列表(空格分隔) | 无 |

## 输出格式

### CSV 字段

| 字段 | 说明 |
|------|------|
| `word` | 单词 (显示成功查询的形态) |
| `sentence` | 例句 (原始字幕) |
| `sentence_furigana` | 例句假名注音 |
| `definition` | 释义 (Yomitan HTML 格式) |
| `reading` | 单词读音 (假名) |
| `pitch_position` | 音调位置 (数字) |
| `pitch_type` | 音调类型 (平板/头高/中高/尾高) |
| `pitch_source` | 音调来源 (NHK_New/NHK_Old) |
| `sentence_audio_base64` | 句子音频 (Base64) |
| `word_audio_base64` | 单词音频 (Base64) |
| `word_audio_source` | 单词音频来源 |
| `picture_base64` | 截图 (Base64) |
| `bccwj_frequency` | BCCWJ 频率描述 |
| `bccwj_freq_sort` | BCCWJ 排序值 |
| `anime_name` | 动漫名称 |
| `episode` | 集数 |
| `start_time` | 字幕起始时间 |
| `end_time` | 字幕结束时间 |
| `lemma` | 词元形式 |
| `all_readings` | 所有读音 (JSON) |

## 技术细节

### 词元推导 (Lemmatization)

使用 Fugashi + UniDic 进行词元推导:

```
食べた → 食べる
見ている → 見る
走った → 走る
```

### 复合词回退 (く→き Variant)

日语复合词常以 き 结尾 (連用形),但 Fugashi 返回 く 形式:

```
狂い咲く → 尝试查询:
  1. 狂い咲く (词元)
  2. 狂い咲き (き 变体) ← 词典中的形态
```

### 片假名处理

全片假名词汇优先查询原形:

```
ピン → 尝试查询:
  1. ピン (原始片假名)
  2. ぴん (转换后平假名)
```

### 长音展开

仅对非片假名词汇展开长音符:

```
こー → こう   (お段 + 长音 = う)
せー → せい   (え段 + 长音 = い)
コー → コー   (片假名保持原样)
```

### 音调类型判定

根据音调位置和假名长度判断:

- **平板式**: pitch = 0
- **头高型**: pitch = 1
- **尾高型**: pitch = 假名长度
- **中高型**: 1 < pitch < 假名长度

## 常见问题

### Q: 为什么有些单词查不到释义?

A: 可能原因:
1. 词典中没有该词条 → 尝试用方括号指定查词形态
2. 活用形未正确推导 → 使用 `[]` 强制指定
3. 复合词形态差异 → 程序会自动尝试 く→き 变体

### Q: 读音不正确怎么办?

A: 使用圆括号强制指定: `単語(たんご)`

### Q: AnkiConnect 连接失败?

A: 检查:
1. Anki 是否正在运行
2. AnkiConnect 插件是否已安装 (代码: 2055492159)
3. 防火墙是否阻止连接

### Q: 如何批量处理多集?

A: 写一个简单的 bash/PowerShell 脚本循环调用主程序:

```bash
for i in {1..12}; do
  python jp_media_mining_refactored.py \
    --video "episodes/S01E$(printf %02d $i).mp4" \
    --subs "subs/S01E$(printf %02d $i).ja.srt" \
    --words "words/S01E$(printf %02d $i).txt" \
    # ... 其他参数 ...
done
```

## 更新日志

### 最新版本特性

- ✅ 三级词典架构
- ✅ 自动回退查询 (词元/变体/片假名)
- ✅ 单词表高级语法 (圆括号/方括号)
- ✅ 片假名智能处理
- ✅ 长音正确转换 (お→う, え→い)
- ✅ 多音调支持和可视化
- ✅ Yomitan 格式输出
- ✅ AnkiConnect 集成
- ✅ 词元推导 (Fugashi)
- ✅ 复合词 く→き 回退

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request!

## 致谢

- **Fugashi**: 高性能日语分词
- **UniDic**: 日语词典
- **MDX 词典社区**: 提供丰富的词典资源
- **Yomitan**: 格式标准参考
