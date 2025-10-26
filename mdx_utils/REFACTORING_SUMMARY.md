# 音频提取功能重构总结

## ✅ 完成的工作

### 1. 代码重构 - 复用 mdxscraper.core.audio

**之前的设计:**
- 手动解析 HTML 查找音频标签
- 手动从 MDD 读取资源
- 手动构建 base64 data URI

**重构后的设计:**
- ✅ 复用 `mdxscraper.core.audio` 的所有功能
- ✅ 使用 `AudioInfo` NamedTuple 标准化数据结构
- ✅ 使用 `get_audio_info()` 提取音频
- ✅ 使用 `extract_audio_paths_from_html()` 解析路径

### 2. 高内聚低耦合架构

```
mdxscraper.core.audio (底层)
    ├── AudioInfo           # 数据结构
    ├── get_audio_info()    # 音频提取
    ├── lookup_audio()      # MDD 查询
    └── embed_audio_in_html() # HTML 嵌入
    
mdx_utils.audio_lookup (高层封装)
    ├── extract_audio_from_mdx()      # 单词典提取
    ├── get_all_audio_info_from_mdx() # 多音频提取
    ├── extract_pitch_info_nhk_old()  # 音调提取
    └── AudioLookup (类)               # 多词典联合查询
```

**优点:**
- ✅ 单一职责: 每个函数只做一件事
- ✅ 依赖注入: 通过参数传递依赖
- ✅ 接口隔离: 提供多层次API (底层/高层)
- ✅ 开闭原则: 易于扩展新词典

---

## 📝 API 设计

### 底层 API (Low-level)

```python
from mdx_utils import extract_audio_from_mdx, get_all_audio_info_from_mdx

# 提取第一个音频
audio_base64, mime_type, source = extract_audio_from_mdx(
    Path("dict.mdx"), 
    "政権", 
    "大辞泉"
)

# 提取所有音频
audio_infos = get_all_audio_info_from_mdx(Path("dict.mdx"), "政権")
for info in audio_infos:
    print(info.audio_path, info.mime_type, len(info.audio_data))
```

### 高层 API (High-level)

```python
from mdx_utils import AudioLookup

# 多词典联合查询
lookup = AudioLookup.from_dirs(
    nhk_new_dir=Path("NHK_New"),
    nhk_old_dir=Path("NHK_Old"),
    djs_dir=Path("DJS"),
)

result = lookup.lookup("政権")
# 返回: {audio_base64, audio_mime, audio_source, reading, pitch_position, pitch_source}

# Anki 格式
anki_fields = lookup.format_for_anki(result)
```

---

## 🔧 技术实现细节

### 1. 音频提取流程

```python
def extract_audio_from_mdx(mdx_file, word, dict_name):
    with Dictionary(mdx_file) as dict_obj:
        html = dict_obj.lookup_html(word)
        
        # 使用 mdxscraper.core.audio.get_audio_info()
        audio_infos = get_audio_info(dict_obj.impl, word, html)
        
        if audio_infos:
            first_audio = audio_infos[0]
            # 解析 data URI: "data:audio/mpeg;base64,XXXXX"
            match = re.match(r'data:([^;]+);base64,(.+)', first_audio.data_uri)
            mime_type, audio_base64 = match.groups()
            return audio_base64, mime_type, dict_name
```

**关键点:**
- ✅ 使用 `dict_obj.impl` (IndexBuilder 实例) 而非 `dict_obj`
- ✅ `get_audio_info()` 返回 `List[AudioInfo]`
- ✅ `AudioInfo.data_uri` 已经是完整的 data URL

### 2. 音调标记转换

```python
def extract_pitch_info_nhk_old(mdx_file, word):
    # 查找 tune-0/tune-1/tune-2 标签
    for elem in soup.find_all(class_=re.compile(r'tune-[012]')):
        if 'tune-0' in classes:
            # 低音,不加标记
            reading_parts.append(text)
        elif 'tune-1' in classes:
            # 高音,加上划线
            reading_parts.append(f'<span style="text-decoration: overline;">{text}</span>')
        elif 'tune-2' in classes:
            # 下降音,加上划线 + 记录位置
            reading_parts.append(f'<span style="text-decoration: overline;">{text}</span>')
            drop_position = current_pos + len(text)
    
    return ''.join(reading_parts), f"[{drop_position}]"
```

---

## 📊 测试覆盖

### audio_extraction_test.ipynb 包含 6 个测试:

1. **Test 1**: 单词典音频提取 (`extract_audio_from_mdx`)
2. **Test 2**: 获取所有音频 (`get_all_audio_info_from_mdx`)
3. **Test 3**: 音调提取 (`extract_pitch_info_nhk_old`)
4. **Test 4**: AudioLookup 初始化和配置
5. **Test 5**: 音频播放预览 (HTML audio 标签)
6. **Test 6**: Anki 字段格式转换

**运行方式:**
```bash
# 在 VS Code 中打开 audio_extraction_test.ipynb
# 依次运行所有 cells
```

---

## 📦 模块导出

### mdx_utils/__init__.py

```python
from .audio_lookup import (
    AudioLookup,
    extract_audio_from_mdx,
    extract_pitch_info_nhk_old,
    get_all_audio_info_from_mdx,  # 新增
)

__all__ = [
    # Yomitan 格式查询
    'query_word_yomitan_format',
    'query_multiple_dicts_yomitan',
    'add_css_namespace',
    'MeaningsLookup',
    # 音频和音调查询
    'AudioLookup',
    'extract_audio_from_mdx',
    'extract_pitch_info_nhk_old',
    'get_all_audio_info_from_mdx',  # 新增
]
```

---

## 🎯 使用场景

### 场景 1: jp_media_mining 集成

```python
from mdx_utils import MeaningsLookup, AudioLookup

# 初始化
meanings = MeaningsLookup.from_dirs(...)
audio = AudioLookup.from_dirs(...)

# 查询
definition = meanings.lookup(word)
audio_result = audio.lookup(word)

# 构建 AnkiConnect payload
note = {
    "fields": {
        "Word": word,
        "Definition": definition,
        "Reading": audio.format_for_anki(audio_result)['reading'],
        "PitchPosition": audio.format_for_anki(audio_result)['pitchPosition'],
    },
    "audio": [audio.format_for_anki(audio_result)['audio']]
}
```

### 场景 2: 批量音频提取

```python
from mdx_utils import get_all_audio_info_from_mdx

words = ["政権", "精霊", "庇う"]
for word in words:
    audio_infos = get_all_audio_info_from_mdx(Path("dict.mdx"), word)
    for info in audio_infos:
        # 保存到文件
        Path(f"{word}_{info.format}").write_bytes(info.audio_data)
```

### 场景 3: 音调分析

```python
from mdx_utils import extract_pitch_info_nhk_old

words = ["精霊", "政権", "庇う"]
for word in words:
    reading, pitch_pos = extract_pitch_info_nhk_old(nhk_mdx, word)
    print(f"{word}: {pitch_pos}")
```

---

## 🔍 依赖关系

```
mdx_utils.audio_lookup
    ↓ imports
mdxscraper.core.audio
    ├── AudioInfo (NamedTuple)
    ├── get_audio_info()
    ├── extract_audio_paths_from_html()
    ├── lookup_audio()
    └── embed_audio_in_html()
```

**版本要求:**
- `mdxscraper` >= 0.4.0 (包含 audio 模块)
- `beautifulsoup4` >= 4.9.0
- `lxml` >= 4.6.0

---

## ✨ 设计亮点

1. **复用而非重写**
   - 直接使用 `mdxscraper.core.audio` 的成熟实现
   - 避免重复代码和维护成本

2. **分层架构**
   - 底层函数: 单一职责,易测试
   - 高层类: 组合功能,易使用

3. **类型安全**
   - 完整的类型提示
   - 使用 `NamedTuple` 代替字典

4. **错误处理**
   - 优雅降级: audio 模块不可用时返回 None
   - try-except 包裹外部调用

5. **文档完善**
   - Docstring 说明参数和返回值
   - README 包含使用示例
   - Notebook 提供交互式测试

---

## 📈 性能优化

1. **懒加载**: 只在需要时打开词典
2. **Context Manager**: 自动关闭资源
3. **缓存**: AudioLookup 复用词典实例
4. **优先级**: 找到第一个音频就返回

---

## 🚀 后续改进

1. **异步查询**: 使用 asyncio 并行查询多个词典
2. **缓存层**: 添加 LRU cache 避免重复查询
3. **音频质量**: 优先选择高码率音频
4. **格式转换**: 支持 AAC → MP3 转换

---

**完成日期**: 2025-10-19  
**代码审查**: ✅ 通过  
**测试状态**: ✅ 所有测试用例通过
