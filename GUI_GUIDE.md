# GUI 使用指南

## 🚀 快速开始

### 1. 安装依赖

```bash
# 激活虚拟环境
.\test1\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动 GUI 应用

```bash
python app.py
```

或使用 CLI 工具：

```bash
python cli.py --help
```

## 📋 界面功能

### 主页（Home）

主页是核心功能界面，用于配置参数并执行挖掘任务。

**素材文件：**
- **视频文件**: 选择动漫视频文件（支持 mp4, mkv, avi）
- **字幕文件**: 选择对应的字幕文件（支持 srt, ass, vtt）
- **单词列表**: 选择包含目标单词的文本文件（每行一个单词）
- **输出目录**: 选择输出文件的保存位置

**词典目录：**
- **Primary 词典**: 主要 MDX 词典目录
- **NHK 旧版**: NHK 日本語発音アクセント辞典（旧版）
- **NHK 新版**: NHK 日本語発音アクセント辞典（新版）
- **大辞泉 (DJS)**: 大辞泉词典目录
- **频率数据**: 词频数据文件（支持 JSON/ZIP/CSV/TSV）

**导出选项：**
- ☑️ **导出 CSV**: 将生成的卡片导出为 CSV 文件
- ☑️ **推送到 Anki**: 将卡片推送到 Anki（需先配置 Anki 设置）

**处理流程：**
1. 选择所有必需的文件和目录
2. 配置导出选项
3. 点击"开始处理"按钮
4. 查看进度条和日志输出
5. 处理完成后会显示统计信息

### 词典查询（Dict Query）

词典查询界面用于快速查询日语单词。

**使用方法：**
1. 选择词典类型（Primary MDX / NHK 旧版 / NHK 新版 / 大辞泉）
2. 输入日语单词
3. 点击"查询"按钮或按回车键
4. 查看词典释义（HTML 格式）

**Fallback 机制：**
如果在选择的词典中未找到结果，系统会自动尝试其他词典，并显示提示信息。

### Anki 设置（Anki Settings）

配置 Anki 推送相关参数。

**Anki-Connect 配置：**
- **URL**: Anki-Connect 服务地址（默认：http://127.0.0.1:8765）
- **测试连接**: 点击按钮测试与 Anki 的连接状态

**牌组配置：**
- **牌组**: Anki 牌组名称（例如：Japanese::Mining）
- **模型**: Anki 笔记模型名称（例如：Japanese Mining）
- **标签**: 添加到卡片的标签（多个标签用空格分隔）

**字段映射：**
系统会自动映射以下字段：
- Word → 单词
- Sentence → 句子
- Reading → 读音
- Definition → 释义
- Pitch → 音调
- Audio → 音频
- Picture → 图片
- Frequency → 频率

**注意事项：**
- 确保 Anki 正在运行
- 确保已安装 Anki-Connect 插件
- 确保牌组和模型已在 Anki 中创建

### 关于（About）

显示项目信息、版本号、技术栈、许可证等。

## 🔧 CLI 工具

如果你更喜欢命令行工具，可以使用 `cli.py`：

```bash
python cli.py \
    --video "path/to/video.mp4" \
    --subs "path/to/subs.srt" \
    --words "path/to/words.txt" \
    --outdir "path/to/output" \
    --primary-mdx "path/to/primary_mdx" \
    --nhk-old "path/to/nhk_old" \
    --csv \
    --anki
```

查看所有选项：

```bash
python cli.py --help
```

## 💡 使用技巧

### 1. 单词列表准备

单词列表是文本文件，每行一个单词：

```
家具
勉強
大学
```

### 2. 词典目录结构

词典目录应包含 `.mdx` 和对应的 `.mdd` 文件：

```
primary_mdx/
├── primary.mdx
└── primary.mdd
```

### 3. 频率数据格式

支持以下格式：
- **JSON**: Yomichan 格式的频率数据
- **ZIP**: 包含 JSON 的压缩包
- **CSV/TSV**: 第一列为单词，第二列为频率

### 4. Anki 模型准备

在 Anki 中创建笔记模型，包含以下字段：
- Word
- Sentence
- Reading
- Definition
- Pitch
- Audio
- Picture
- Frequency
- Episode（可选）
- Position（可选）

### 5. FFmpeg 安装

确保已安装 FFmpeg 并添加到系统 PATH：

```bash
# Windows
choco install ffmpeg

# Linux
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

验证安装：

```bash
ffmpeg -version
```

## ⚠️ 常见问题

### Q: 无法连接到 Anki

**A**: 确保：
1. Anki 正在运行
2. 已安装 Anki-Connect 插件（代码：2055492159）
3. URL 正确（默认：http://127.0.0.1:8765）

### Q: 词典查询失败

**A**: 检查：
1. 词典目录路径是否正确
2. 词典文件是否完整（.mdx 和 .mdd）
3. 是否有读取权限

### Q: FFmpeg 错误

**A**: 确保：
1. FFmpeg 已正确安装
2. 已添加到系统 PATH
3. 视频文件格式受支持

### Q: 读音显示错误

**A**: 系统已修复鼻浊音问题，优先使用 Fugashi 的 lForm。如果仍有问题，请检查 UniDic 版本。

## 📚 参考资料

- [Anki-Connect GitHub](https://github.com/FooSoft/anki-connect)
- [Fugashi Documentation](https://github.com/polm/fugashi)
- [PySide6-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
