# 快速参考: mdx_utils 音频和音调提取

## 🚀 快速开始

```python
from pathlib import Path
from mdx_utils import AudioLookup

# 初始化
lookup = AudioLookup.from_dirs(
    nhk_old_dir=Path("NHK_Old"),
    djs_dir=Path("DJS"),
)

# 查询单词 (自动智能匹配读音)
result = lookup.lookup("精霊", verbose=True)

# 使用结果
print(result['reading'])         # セイレイ (HTML标记)
print(result['pitch_position'])  # [0]
print(result['audio_base64'])    # base64音频数据
print(result['audio_source'])    # NHK旧版
```

---

## 📋 返回值字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `audio_base64` | str | Base64编码的音频 | "UklGRhQF..." |
| `audio_mime` | str | MIME类型 | "audio/ogg" |
| `audio_source` | str | 来源词典 | "NHK旧版" |
| `reading` | str | 假名读音(HTML) | "セ<u>イレイ</u>" |
| `pitch_position` | str | 音调位置 | "[0]" |
| `pitch_source` | str | 音调来源 | "NHK旧版" |
| `all_pitches` | list | 所有读音(可选) | [("セイレイ","[0]")] |

---

## 🎯 常见用法

### 1. 基础查询

```python
result = lookup.lookup("政権")
```

### 2. 详细输出

```python
result = lookup.lookup("精霊", verbose=True)
# 输出:
# ✅ 音频: NHK旧版 (audio/ogg)
# ✅ 音调: NHK旧版 找到 3 个读音,智能选择: セイレイ [0]
```

### 3. 查看所有候选读音

```python
result = lookup.lookup("精霊", return_all_pitches=True)
for reading, pitch in result['all_pitches']:
    print(f"{reading} {pitch}")
```

### 4. 转换为 Anki 格式

```python
anki_fields = lookup.format_for_anki(result)
# 返回:
# {
#     'reading': 'セ<u>イレイ</u>',
#     'pitchPosition': '[0]',
#     'audio': {
#         'data': 'UklGRhQF...',
#         'filename': '精霊_NHK旧版.ogg',
#         'fields': ['Audio']
#     }
# }
```

---

## 🤖 智能读音匹配

**自动启用:** 安装 fugashi 后自动使用

```bash
pip install fugashi unidic-lite
```

**工作原理:**
1. 从NHK提取所有候选读音
2. 用fugashi获取实际读音
3. 自动匹配最接近的
4. Fallback: 返回最后一个(通常是最常用的)

**示例:**
```python
# 精霊 有 3 个候选读音
result = lookup.lookup("精霊")
# 自动选择: セイレイ [0] ✅ (最常用)
```

---

## 🎵 音调标记含义

| 类型 | 标记 | 说明 | 示例 |
|------|------|------|------|
| 平板型 | [0] | 第1拍高,后续都高 | あめ [0] (雨) |
| 头高型 | [1] | 第1拍高,第2拍降 | あめ [1] (飴) |
| 中高型 | [2] | 第2拍降 | おとこ [2] (男) |
| 尾高型 | [n] | 最后1拍降 | おんな [3] (女) |

**HTML 标记:**
- 低音: 无标记
- 高音/下降: `<span style="text-decoration: overline;">文字</span>`

---

## 📦 底层 API

### 单独提取音频

```python
from mdx_utils import extract_audio_from_mdx

audio_b64, mime, source = extract_audio_from_mdx(
    mdx_file=Path("DJS.mdx"),
    word="政権",
    dict_name="大辞泉"
)
```

### 单独提取音调

```python
from mdx_utils import extract_pitch_info_nhk_old

# 智能匹配最佳
reading, pitch = extract_pitch_info_nhk_old(
    mdx_file=Path("NHK_Old.mdx"),
    word="精霊"
)

# 获取所有候选
all_pitches = extract_pitch_info_nhk_old(
    mdx_file=Path("NHK_Old.mdx"),
    word="精霊",
    return_all=True
)
```

### 获取所有音频信息

```python
from mdx_utils import get_all_audio_info_from_mdx

audio_infos = get_all_audio_info_from_mdx(
    mdx_file=Path("NHK_Old.mdx"),
    word="精霊",
    dict_name="NHK"
)

for info in audio_infos:
    print(info.audio_path)
    print(info.mime_type)
    print(len(info.audio_data))
```

---

## ⚙️ 自定义配置

### 指定词典名称

```python
lookup = AudioLookup.from_dirs(
    nhk_old_dir=Path("NHK_Old"),
    djs_dir=Path("DJS"),
    dict_names={
        "DJS.mdx": "大辞泉 第二版",
        "NHKJPVDL.mdx": "NHK日本語発音アクセント辞典",
    }
)
```

### 手动指定词典列表

```python
lookup = AudioLookup(
    audio_dicts=[
        (Path("NHK_New/NHK2016.mdx"), "NHK新版"),
        (Path("NHK_Old/NHKJPVDL.mdx"), "NHK旧版"),
        (Path("DJS/DJS.mdx"), "大辞泉"),
    ],
    pitch_dict=Path("NHK_Old/NHKJPVDL.mdx")
)
```

---

## 🐛 故障排查

### 问题1: 找不到音频

**检查:**
1. MDX 文件路径是否正确
2. 词典是否包含该词条
3. 是否有对应的 .mdd 文件

```python
result = lookup.lookup("测试词", verbose=True)
# 查看详细输出
```

### 问题2: Fugashi 不工作

**解决:**
```bash
# 安装
pip install fugashi unidic-lite

# 测试
python -c "import fugashi; print(fugashi.Tagger()('精霊')[0].feature)"
```

### 问题3: 读音选择不正确

**调试:**
```python
# 查看所有候选
result = lookup.lookup("精霊", return_all_pitches=True)
print(result['all_pitches'])

# 查看 fugashi 读音
from mdx_utils import get_word_reading_with_fugashi
print(get_word_reading_with_fugashi("精霊"))
```

---

## 📚 文档链接

- [完整文档 (README.md)](./README.md)
- [Fugashi集成说明 (FUGASHI_INTEGRATION.md)](./FUGASHI_INTEGRATION.md)
- [多读音支持 (MULTI_PITCH_SUPPORT.md)](./MULTI_PITCH_SUPPORT.md)
- [音频功能总结 (AUDIO_FEATURE_SUMMARY.md)](./AUDIO_FEATURE_SUMMARY.md)

---

**版本**: 1.0  
**最后更新**: 2025-10-19
