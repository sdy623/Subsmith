# MDX Utils 使用指南

## 📦 模块说明

`mdx_utils` 提供符合 **Yomitan 浏览器插件标准**的 MDX 词典查询功能,可直接用于 AnkiConnect 的 `definition`/`glossary` 字段。

**核心功能:**
- ✅ Yomitan 格式的释义查询 (`MeaningsLookup`)
- ✅ 音频和音调信息提取 (`AudioLookup`)
- ✅ 多词典联合查询
- ✅ CSS 命名空间隔离

---

## 🚀 快速开始

### 1. 基础导入 - 推荐方式

```python
from pathlib import Path
from mdx_utils import MeaningsLookup

# 使用 from_dirs 初始化(推荐)
lookup = MeaningsLookup.from_dirs(
    primary_dir=Path("dicts/primary"),      # 主词典目录
    secondary_dir=Path("dicts/secondary"),  # 次词典目录
    dict_names={                            # 词典显示名称
        "DJS.mdx": "大辞泉 第二版",
        "日汉双解词典_20231101.mdx": "明鏡日汉双解辞典",
        "xsjrihanshuangjie.mdx": "新世纪日汉双解词典",
    }
)

# 查询单词(联合所有词典)
html = lookup.lookup("政権")
print(html)  # Yomitan 格式的 HTML,包含所有匹配词典
```

---

## 📚 详细用法

### 2. 初始化方式

#### 方式1: 从目录初始化(推荐)

```python
lookup = MeaningsLookup.from_dirs(
    primary_dir=Path("dicts/primary"),
    secondary_dir=Path("dicts/secondary"),
    dict_names={
        "DJS.mdx": "大辞泉 第二版",
        "meikyou.mdx": "明鏡日汉双解辞典",
    },
    use_jamdict=True  # 启用 JMDict fallback(默认 True)
)
```

#### 方式2: 直接指定词典列表

```python
lookup = MeaningsLookup([
    (Path("dict1.mdx"), "大辞泉 第二版"),
    (Path("dict2.mdx"), "明鏡日汉双解辞典"),
    (Path("dict3.mdx"), "新世纪日汉双解词典"),
])
```

### 3. 查询单词(联合查询)

```python
# 联合查询所有词典
definition_html = lookup.lookup("政権")

# 未找到时返回空字符串
if definition_html:
    print("✅ 找到释义")
else:
    print("❌ 未找到")

# 禁用 JMDict fallback(单次查询)
html = lookup.lookup("単語", fallback_to_jamdict=False)
```

### 4. 集成到 AnkiConnect

```python
import requests

# 查询单词
definition = lookup.lookup("政権")

# 构建 AnkiConnect payload
payload = {
    "action": "addNote",
    "version": 6,
    "params": {
        "note": {
            "deckName": "Japanese",
            "modelName": "Japanese (recognition)",
            "fields": {
                "word": "政権",
                "definition": definition,  # 直接使用 Yomitan 格式
                "glossary": definition,    # 可选: 同时填充 glossary 字段
            },
            "tags": ["anime", "auto"],
        }
    }
}

# 发送到 Anki
response = requests.post("http://localhost:8765", json=payload)
print(response.json())
```

---

## 🎨 输出格式说明

### Yomitan 标准格式

```html
<div style="text-align: left;" class="yomitan-glossary">
  <ol>
    <!-- 词典1 -->
    <li data-dictionary="大辞泉 第二版">
      <i>(大辞泉 第二版)</i> 
      <span>
        <!-- MDX 词典原始 HTML -->
        <div>せい‐けん［政権］⟨名⟩</div>
        <div>政策を実行し、統治機構を動かす権力。</div>
      </span>
    </li>
    <style>
      /* 词典1的命名空间化 CSS */
      .yomitan-glossary [data-dictionary="大辞泉 第二版"] .word { 
        font-weight: bold; 
      }
    </style>
    
    <!-- 词典2 -->
    <li data-dictionary="明鏡日汉双解辞典">
      <i>(明鏡日汉双解辞典)</i> 
      <span>
        <!-- 词典2 HTML -->
      </span>
    </li>
    <style>
      /* 词典2的命名空间化 CSS */
      .yomitan-glossary [data-dictionary="明鏡日汉双解辞典"] .dfcn { 
        color: dodgerblue; 
      }
    </style>
  </ol>
</div>
```

### 关键特性

✅ **多词典整合** - 所有匹配词典的条目整合到一个 `<ol>` 列表  
✅ **CSS 命名空间隔离** - 每个词典的样式使用 `data-dictionary` 属性隔离  
✅ **图片 base64 嵌入** - 自动转换图片为 base64,确保离线可用  
✅ **三级查询回退** - 主词典 → 次词典 → JMDict  

---

## 🔧 高级用法

### 5. 直接使用底层函数

```python
from mdx_utils import query_multiple_dicts_yomitan
from pathlib import Path

# 手动指定词典列表
mdx_dicts = [
    (Path("dict1.mdx"), "大辞泉 第二版"),
    (Path("dict2.mdx"), "明鏡日汉双解辞典"),
]

# 查询并生成 Yomitan 格式
html = query_multiple_dicts_yomitan(
    mdx_dicts, 
    word="政権",
    output_file=Path("preview.html")  # 可选: 保存预览 HTML
)
```

### 6. 单个词典查询

```python
from mdx_utils import query_word_yomitan_format
from pathlib import Path

# 查询单个词典
html_content, css_content = query_word_yomitan_format(
    Path("dict.mdx"),
    word="政権",
    dict_name="大辞泉 第二版"
)

if html_content:
    print(f"HTML: {len(html_content)} chars")
    print(f"CSS: {len(css_content)} chars")
```

### 7. CSS 命名空间处理

```python
from mdx_utils import add_css_namespace

# 原始 CSS
css = """
.word { font-weight: bold; }
.def { color: blue; }
"""

# 添加命名空间
namespaced_css = add_css_namespace(css, "大辞泉 第二版")

print(namespaced_css)
# 输出:
# .yomitan-glossary [data-dictionary="大辞泉 第二版"] .word { font-weight: bold; }
# .yomitan-glossary [data-dictionary="大辞泉 第二版"] .def { color: blue; }
```

---

## 📁 文件结构

```
mdx_utils/
├── __init__.py              # 模块入口
├── yomitan_formatter.py     # Yomitan 格式化核心功能
├── meanings_lookup.py       # MeaningsLookup 类（高层封装）
└── README.md               # 本文档
```

---

## 🔗 相关资源

- [Yomitan GitHub](https://github.com/themoeway/yomitan)
- [AnkiConnect API](https://foosoft.net/projects/anki-connect/)
- [mdxscraper](https://github.com/xxyzz/mdxscraper)
- [Yomitan Payload 分析文档](../Yomitan_AnkiConnect_Payload_Analysis.md)

---

## 📝 完整示例

### 在 jp_media_mining 中使用

```python
from pathlib import Path
from mdx_utils import MeaningsLookup

# 初始化（在脚本开头）
meanings_lookup = MeaningsLookup.from_dirs(
    primary_dir=Path("dicts/primary"),
    secondary_dir=Path("dicts/secondary"),
    dict_names={
        "DJS.mdx": "大辞泉 第二版",
        "日汉双解词典_20231101.mdx": "明鏡日汉双解辞典",
        "xsjrihanshuangjie.mdx": "新世纪日汉双解词典",
    },
    use_jamdict=True  # 启用 JMDict fallback
)

# 在卡片生成循环中使用
for word in vocabulary_list:
    # 查询释义(联合所有词典)
    definition = meanings_lookup.lookup(word)
    
    if definition:
        # 创建 Anki 卡片
        note = {
            "word": word,
            "definition": definition,  # Yomitan 格式,包含所有匹配词典
            "glossary": definition,
            # ... 其他字段
        }
        add_note_to_anki(note)
```

---

## ⚠️ 注意事项

1. **词典文件格式** - 仅支持 `.mdx` 格式词典
2. **可选依赖** - `jamdict` 为可选依赖,未安装时跳过 JMDict 查询
3. **性能考虑** - 大量查询时建议缓存结果
4. **编码问题** - 确保 MDX 文件编码正确

---

## 🐛 故障排查

### 问题1: 样式冲突

**症状**: 多个词典样式互相覆盖

**解决**: 确保使用最新版本,CSS 命名空间功能已修复

### 问题2: 图片不显示

**症状**: 词典中的图片无法显示

**解决**: 
- 检查 MDX 文件的 .mdd 资源文件是否在同一目录
- 确保 `mdxscraper` 版本 >= 0.3.0

### 问题3: 找不到单词

**症状**: 明明词典里有,但查询返回空

**解决**:
- 检查词典文件路径是否正确
- 尝试不同的单词形式(假名/汉字)
- 查看 MDX 词典的索引是否完整

---

## 🔊 音频和音调提取

### AudioLookup 类

从多个词典中提取音频和音调信息,支持:
- 新版 NHK (AAC 音频)
- 旧版 NHK (完整音调标记 tune-0/tune-1/tune-2)
- 大辞泉 第二版 (音频 + 下降位置标记)

### 快速开始

```python
from pathlib import Path
from mdx_utils import AudioLookup

# 初始化音频查询器
audio_lookup = AudioLookup.from_dirs(
    nhk_new_dir=Path("dicts/NHK_New"),
    nhk_old_dir=Path("dicts/NHK_Old"),
    djs_dir=Path("dicts/DJS"),
    dict_names={
        "NHKJPVDL.mdx": "NHK新版",
        "NHK旧版.mdx": "NHK旧版",
        "DJS.mdx": "大辞泉",
    }
)

# 查询音频和音调 (自动智能匹配读音)
result = audio_lookup.lookup("精霊", verbose=True)

# 输出:
# ✅ 音频: NHK旧版 (audio/ogg)
# ✅ 音调: NHK旧版 找到 3 个读音,智能选择: セイレイ [0]

print(result['audio_base64'])  # base64 编码的音频
print(result['reading'])        # 带上划线的假名: セ<u>イレイ</u>
print(result['pitch_position']) # [0]

# 查看所有候选读音
result_all = audio_lookup.lookup("精霊", return_all_pitches=True)
for reading, pitch in result_all['all_pitches']:
    print(f"{reading} {pitch}")
# 输出:
# ショーリョー [2]
# ショーリョー [0]
# セイレイ [0]  ← 智能匹配选择此项
```

**🤖 智能读音匹配:**
- 使用 **fugashi** (MeCab分词器) 获取单词的实际读音
- 自动匹配最接近的音调信息
- Fallback: 如果 fugashi 不可用,返回最后一个读音(通常是最常用的)
- 需要安装: `pip install fugashi unidic-lite`

```

### Anki 字段格式

```python
# 转换为 Anki 格式
anki_fields = audio_lookup.format_for_anki(result)

# AnkiConnect payload
note = {
    "deckName": "日语",
    "modelName": "Japanese",
    "fields": {
        "Word": "精霊",
        "Reading": anki_fields['reading'],      # 带上划线的假名
        "PitchPosition": anki_fields['pitchPosition'],  # [2]
    },
    "audio": [anki_fields['audio']]  # {'data': base64, 'filename': '...'}
}
```

### 音调标记说明

**旧版 NHK HTML 标签:**
- `tune-0`: 低音
- `tune-1`: 高音 (上划线)
- `tune-2`: 下降音 (上划线 + 记录下降位置)

**转换为 Anki 格式:**
- `reading`: 假名读音,高音和下降用 `<span style="text-decoration: overline;">` 标记
- `pitchPosition`: `[0]` (平板), `[1]` (头高), `[2]` (第2音下降) 等

**示例:**

| 单词 | reading (HTML) | pitchPosition |
|------|----------------|---------------|
| 精霊 | せ<u>いれい</u> | [2] |
| 政権 | <u>せいけん</u> | [0] |

### 直接提取函数

如果只需要单个功能:

```python
from mdx_utils import extract_audio_from_mdx, extract_pitch_info_nhk_old

# 只提取音频
audio_data, mime_type, source = extract_audio_from_mdx(
    Path("dicts/NHK/nhk.mdx"),
    "精霊",
    "NHK新版"
)

# 只提取音调
reading, pitch_pos = extract_pitch_info_nhk_old(
    Path("dicts/NHK_Old/nhk_old.mdx"),
    "精霊"
)
```

---

**版本**: 1.1  
**最后更新**: 2025-10-19
