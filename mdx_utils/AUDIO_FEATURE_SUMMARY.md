# 音频和音调提取功能 - 实现总结

## ✅ 已完成功能

### 1. 核心模块: `mdx_utils/audio_lookup.py`

**功能:**
- ✅ 从多个 MDX 词典提取音频 (支持 AAC, MP3, WAV 等)
- ✅ 从旧版 NHK 提取音调信息 (tune-0/tune-1/tune-2 标签)
- ✅ 多词典按优先级联合查询
- ✅ 生成 Anki 字段格式

**核心类:**
- `AudioLookup`: 音频和音调查询主类
  - `from_dirs()`: 从目录初始化
  - `lookup()`: 查询音频和音调
  - `format_for_anki()`: 转换为 Anki 格式

**辅助函数:**
- `extract_audio_from_mdx()`: 从单个词典提取音频
- `extract_pitch_info_nhk_old()`: 从旧版 NHK 提取音调

---

## 📖 使用示例

### 示例 1: 基础使用 (audio_extraction_test.ipynb)

```python
from pathlib import Path
from mdx_utils import AudioLookup

# 初始化
audio_lookup = AudioLookup.from_dirs(
    nhk_new_dir=Path("dicts/NHK_New"),  # 新版 NHK (AAC 音频)
    nhk_old_dir=Path("dicts/NHK_Old"),  # 旧版 NHK (完整音调)
    djs_dir=Path("dicts/DJS"),          # 大辞泉
)

# 查询
result = audio_lookup.lookup("精霊", verbose=True)
# 输出:
# ✅ 音频: NHK新版 (audio/aac)
# ✅ 音调: NHK旧版 [2]

# 结果包含:
result['audio_base64']    # base64 音频数据
result['audio_mime']      # audio/aac
result['audio_source']    # "NHK新版"
result['reading']         # '<span style="text-decoration: overline;">せいれい</span>'
result['pitch_position']  # "[2]"
result['pitch_source']    # "NHK旧版"
```

### 示例 2: Anki 卡片集成

```python
# 转换为 Anki 格式
anki_fields = audio_lookup.format_for_anki(result)

# AnkiConnect payload
note = {
    "deckName": "日语",
    "modelName": "Japanese",
    "fields": {
        "Word": "精霊",
        "Reading": anki_fields['reading'],          # せ̄いれい̄ (带上划线)
        "PitchPosition": anki_fields['pitchPosition'], # [2]
    },
    "audio": [anki_fields['audio']]  # {'data': base64, 'filename': 'audio_xxx.aac'}
}
```

### 示例 3: 只使用特定词典

```python
# 直接指定词典列表
audio_lookup = AudioLookup(
    audio_dicts=[
        (Path("dicts/nhk_new.mdx"), "NHK新版"),
        (Path("dicts/djs.mdx"), "大辞泉"),
    ],
    pitch_dict=Path("dicts/nhk_old.mdx")
)
```

---

## 🎵 音调标记系统

### 旧版 NHK HTML 标签

```html
<span class="tune-0">せ</span>    <!-- 低音 -->
<span class="tune-1">いれ</span>  <!-- 高音,添加上划线 -->
<span class="tune-2">い</span>    <!-- 下降音,添加上划线并记录位置 -->
```

### 转换为 Anki 格式

**reading 字段 (HTML):**
```html
せ<span style="text-decoration: overline;">いれい</span>
```

**pitchPosition 字段:**
```
[2]  # 表示第2个音后下降
```

### 音调类型说明

| pitchPosition | 名称 | 说明 | 示例 |
|---------------|------|------|------|
| [0] | 平板型 | 第1音低,其余高 | あめ̄ (雨) |
| [1] | 头高型 | 第1音高,其余低 | あ̄め (飴) |
| [2] | 中高型 | 第2音后下降 | はし̄ (箸) |
| [N] | 尾高型 | 最后一音下降 | - |

---

## 📁 文件结构

```
mdx_utils/
├── __init__.py              # 模块入口,导出 AudioLookup
├── audio_lookup.py          # ✨ 新增: 音频和音调提取
├── yomitan_formatter.py     # Yomitan 格式查询
├── meanings_lookup.py       # 释义查询
└── README.md               # 使用文档 (已更新)

audio_extraction_test.ipynb  # ✨ 新增: 音频提取测试 Notebook
```

---

## 🔧 词典优先级

### 音频提取优先级
1. **新版 NHK** (NHKJPVDL.mdx)
   - ✅ AAC 音频,音质最好
   - ❌ 音调标记不完整

2. **旧版 NHK** (NHK旧版.mdx)
   - ✅ 完整的音调标记 (tune-0/1/2)
   - ✅ MP3 音频

3. **大辞泉 第二版** (DJS.mdx)
   - ✅ 有音频
   - ⚠️ 只有下降位置标记

### 音调提取
- **始终使用旧版 NHK** (最完整的音调标记)

---

## 📝 测试 Notebook

`audio_extraction_test.ipynb` 包含完整的测试示例:

1. **Cell 1-2**: 导入和基础函数
2. **Cell 3**: `extract_audio_from_mdx()` - 单词典音频提取
3. **Cell 4**: `extract_pitch_info_nhk_old()` - 旧版NHK音调提取
4. **Cell 5**: `query_audio_and_pitch()` - 联合查询函数
5. **Cell 6**: 配置词典路径
6. **Cell 7**: 批量测试多个单词
7. **Cell 8**: 在 Notebook 中预览音频播放
8. **Cell 9**: 生成 Anki 字段格式

---

## 🚀 下一步

### 集成到 jp_media_mining

1. **导入模块:**
```python
from mdx_utils import AudioLookup, MeaningsLookup
```

2. **初始化:**
```python
# 释义查询
meanings = MeaningsLookup.from_dirs(...)

# 音频查询
audio = AudioLookup.from_dirs(
    nhk_new_dir=Path("dicts/NHK_New"),
    nhk_old_dir=Path("dicts/NHK_Old"),
    djs_dir=Path("dicts/DJS"),
)
```

3. **查询和组合:**
```python
# 查询释义
definition = meanings.lookup(word)

# 查询音频和音调
audio_result = audio.lookup(word)
anki_audio = audio.format_for_anki(audio_result)

# 构建 AnkiConnect payload
note = {
    "fields": {
        "Word": word,
        "Definition": definition,              # Yomitan 格式 HTML
        "Reading": anki_audio['reading'],      # 带上划线的假名
        "PitchPosition": anki_audio['pitchPosition'],  # [0], [1], [2]...
    },
    "audio": [anki_audio['audio']] if anki_audio['audio'] else []
}
```

---

## ✅ 功能验证清单

- [x] 从新版 NHK 提取 AAC 音频
- [x] 从旧版 NHK 提取 MP3 音频
- [x] 从大辞泉提取音频
- [x] 从旧版 NHK 提取音调标记 (tune-0/1/2)
- [x] 转换音调标记为 HTML 上划线格式
- [x] 计算音调下降位置 [0], [1], [2]...
- [x] 多词典按优先级联合查询
- [x] 生成 Anki 字段格式
- [x] base64 音频编码
- [x] 支持 AAC/MP3/WAV 等多种音频格式
- [x] Notebook 中预览音频播放
- [x] 完整的类型提示
- [x] 详细的文档和示例

---

**完成日期**: 2025-10-19  
**作者**: GitHub Copilot
