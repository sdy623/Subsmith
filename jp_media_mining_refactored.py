#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JP Media Mining → Anki Cards (重构版)

重构改进:
1. 使用 mdx_utils.MeaningsLookup 进行多词典释义查询 (Yomitan格式)
2. 使用 mdx_utils.AudioLookup 获取音频和音调信息 (支持 Fugashi 智能匹配)
3. 优化代码结构,提高可维护性
4. 集成 AnkiConnect API,一键推送到 Anki

依赖安装:
  pip install pysubs2 fugashi[unidic-lite] requests pandas

使用示例 (生成 CSV):
  python jp_media_mining_refactored.py \
    --video "episodes/Ep01.mp4" \
    --subs  "subs/Ep01.ja.srt" \
    --words "unknown/Ep01_words.txt" \
    --primary-mdx   "dicts/primary_mdx_dir" \
    --secondary-mdx "dicts/secondary_mdx_dir" \
    --tertiary-mdx  "dicts/tertiary_mdx_dir" \
    --nhk-old "dicts/NHK_Old" \
    --nhk-new "dicts/NHK_New" \
    --djs     "dicts/DJS" \
    --freq    "dicts/term_meta_bank_1.json" \
    --outdir  "out/Ep01" \
    --csv     "out/Ep01/cards.csv"

使用示例 (一键推送到 Anki):
  python jp_media_mining_refactored.py \
    --video "episodes/Ep01.mp4" \
    --subs  "subs/Ep01.ja.srt" \
    --words "unknown/Ep01_words.txt" \
    --primary-mdx "dicts/primary" \
    --nhk-old "dicts/NHK_Old" \
    --nhk-new "dicts/NHK_New" \
    --djs "dicts/DJS" \
    --freq "dicts/term_meta_bank_1.json" \
    --outdir "out/Ep01" \
    --csv "out/Ep01/cards.csv" \
    --anki \
    --anki-deck "Japanese::Kimetsu_no_Yaiba" \
    --anki-tags anime kimetsu S01E01

注意事项:
  - 使用 --anki 参数需要先安装 AnkiConnect 插件 (代码: 2055492159)
  - 确保 Anki 正在运行
  - 笔记类型 (--anki-model) 必须包含以下字段:
    word, sentence, sentenceFurigana, sentenceEng, reading, sentenceCard,
    audioCard, notes, picture, wordAudio, sentenceAudio, selectionText,
    definition, glossary, pitchPosition, pitch, frequency, freqSort,
    miscInfo, dictionaryPreference
"""

import argparse
import base64
import csv
import json
import re
import subprocess
import zipfile
from dataclasses import dataclass, asdict
from datetime import timedelta
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

import pysubs2
import requests
from fugashi import Tagger

try:
    import pandas as pd
except ImportError:
    pd = None

# 导入 mdx_utils 模块
from mdx_utils import MeaningsLookup, AudioLookup, get_all_audio_info_from_mdx

# ----------------------- AnkiConnect API -----------------------

class AnkiConnect:
    """AnkiConnect API 封装"""
    
    def __init__(self, url: str = "http://localhost:8765"):
        self.url = url
    
    def invoke(self, action: str, **params) -> Any:
        """调用 AnkiConnect API"""
        payload = {
            "action": action,
            "version": 6,
            "params": params
        }
        
        response = requests.post(self.url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        if len(result) != 2:
            raise Exception('AnkiConnect 响应格式错误')
        
        if result['error'] is not None:
            raise Exception(f'AnkiConnect 错误: {result["error"]}')
        
        return result['result']
    
    def check_connection(self) -> bool:
        """检查 AnkiConnect 是否可用"""
        try:
            version = self.invoke('version')
            print(f"   ✅ AnkiConnect 已连接 (版本: {version})")
            return True
        except Exception as e:
            print(f"   ❌ AnkiConnect 连接失败: {e}")
            print("      请确保 Anki 正在运行且已安装 AnkiConnect 插件")
            return False
    
    def create_deck(self, deck_name: str) -> None:
        """创建牌组 (如果不存在)"""
        self.invoke('createDeck', deck=deck_name)
    
    def add_note(self, note: Dict[str, Any]) -> int:
        """添加笔记,返回笔记 ID"""
        return self.invoke('addNote', note=note)
    
    def store_media_file(self, filename: str, data: str) -> str:
        """
        存储媒体文件到 Anki
        
        Args:
            filename: 文件名
            data: Base64 编码的数据 (不需要 data URI 前缀)
        
        Returns:
            文件名 (用于 [sound:...] 或 <img> 标签)
        """
        self.invoke('storeMediaFile', filename=filename, data=data)
        return filename


def format_time_hhmmss(seconds: float) -> str:
    """
    将秒数格式化为 (h:)mm:ss
    
    示例:
    - 65.5 → "01:05"
    - 3665.5 → "1:01:05"
    """
    if not seconds or seconds < 0:
        return "00:00"
    
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


# ----------------------- Data Types -----------------------

@dataclass
class CardData:
    """Anki 卡片数据"""
    # 基础字段
    word: str                    # 目标单词
    sentence: str                # 原句
    sentence_furigana: str       # 带假名的原句
    
    # 释义
    definition: str              # HTML 格式释义 (Yomitan)
    
    # 音调信息
    reading: str                 # 假名读音 (带上划线标记)
    pitch_position: str          # 音调位置 [0], [1], [2] 等
    pitch_type: str              # 音调类型 (平板式/頭高型/中高型/尾高型)
    pitch_source: str            # 音调来源词典
    
    # 音频 (Base64)
    sentence_audio_base64: str   # 句子音频 Base64
    word_audio_base64: str       # 单词音频 Base64
    word_audio_source: str       # 单词音频来源
    
    # 图片 (Base64)
    picture_base64: str          # 截图 Base64
    
    # 频率
    bccwj_frequency: str         # 频率显示值
    bccwj_freq_sort: str         # 频率排序值
    
    # 媒体信息
    anime_name: str              # 动漫名称
    episode: str                 # 集数 (如 S01E05)
    
    # 时间信息
    start_time: float            # 字幕开始时间
    end_time: float              # 字幕结束时间
    end_time: float              # 字幕结束时间
    
    # 额外信息
    lemma: str                   # 词元
    all_readings: str            # 所有候选读音 (JSON)


# ----------------------- 音调类型转换 -----------------------

def count_kana_length(text: str) -> int:
    """
    计算假名的拍数(モーラ数)
    
    Args:
        text: 假名文本 (平假名或片假名)
    
    Returns:
        拍数
    
    规则:
    - 普通假名: 1拍 (あ、か、さ...)
    - 小写假名: 0拍,与前面的假名组成1拍 (ゃ、ゅ、ょ、ァ、ィ、ゥ...)
    - 促音(っ/ッ): 1拍
    - 长音(ー): 1拍
    """
    if not text:
        return 0
    
    # 小写假名(拗音、小写片假名)
    small_kana = set('ぁぃぅぇぉゃゅょゎァィゥェォヵヶャュョヮ')
    
    count = 0
    for char in text:
        # 小写假名不单独计数
        if char in small_kana:
            continue
        # 假名范围: 平假名(0x3040-0x309F) 或 片假名(0x30A0-0x30FF)
        code = ord(char)
        if (0x3040 <= code <= 0x309F) or (0x30A0 <= code <= 0x30FF):
            count += 1
    
    return count


def pitch_position_to_type(pitch_position: str, reading: str = "") -> str:
    """
    将音调位置转换为日语声调类型名称
    
    Args:
        pitch_position: 音调位置,如 "[0]", "[1]", "[2]" 等
        reading: 假名读音 (用于计算拍数)
    
    Returns:
        声调类型: 平板式/頭高型/中高型/尾高型
    
    规则:
    - [0]: 平板式 (へいばんしき) - 第一拍低,后续高且不降
    - [1]: 頭高型 (あたまだかがた) - 第一拍高,第二拍降
    - [2]~[N-1]: 中高型 (なかだかがた) - 中间某处降调
    - [N]: 尾高型 (おだかがた) - 最后一拍高,助词处降
    
    示例:
    - にぐるま [2], 拍数=4 → 中高型 (2 < 4)
    - そら [2], 拍数=2 → 尾高型 (2 == 2)
    - そらもよう [0], 拍数=5 → 平板式
    """
    if not pitch_position:
        return ""
    
    # 提取数字
    import re
    match = re.search(r'\[(\d+)\]', pitch_position)
    if not match:
        return ""
    
    pos = int(match.group(1))
    
    if pos == 0:
        return "平板式"
    elif pos == 1:
        return "頭高型"
    else:
        # 需要根据假名长度判断是中高型还是尾高型
        if reading:
            # 去除 HTML 标签和上划线标记
            clean_reading = re.sub(r'<[^>]+>', '', reading)
            mora_count = count_kana_length(clean_reading)
            
            if mora_count > 0 and pos == mora_count:
                return "尾高型"
        
        return "中高型"


def generate_pitch_html(reading: str, pitch_position: int, pitch_type: str) -> str:
    """
    生成带音调标记的 HTML (Yomitan 风格)
    
    Args:
        reading: 假名读音 (如 "ほたる", "せいれい")
        pitch_position: 音调位置数字 (如 0, 1, 2, 3)
        pitch_type: 音调类型 ("平板式", "頭高型", "中高型", "尾高型")
    
    Returns:
        HTML 字符串,包含音调标记和对应颜色
    
    颜色规则:
    - 頭高型 (1型): 红色 (#f54360 或 red)
    - 平板式 (0型): 蓝色 (#39c1ff 或 blue)
    - 中高型/尾高型: 绿色 (#93c47d 或 green)
    
    示例:
    - ほたる [1]: 红色, 第一拍后下降
    - せいれい [0]: 蓝色, 第一拍低后续高
    - にぐるま [2]: 绿色, 第二拍后下降
    """
    if not reading:
        return ""
    
    # 确定颜色 (使用 match-case 语法, Python 3.10+)
    match pitch_type:
        case "頭高型":
            color = "#f54360"  # 红色 (atamadaka)
        case "平板式":
            color = "#39c1ff"  # 蓝色 (heiban)
        case "中高型":
            color = "#fca311"  # 橙色 (nakadaka)
        case "尾高型":
            color = "#40D4A6"  # 青绿色 (odaka)
        case _:
            color = "#afa2ff"  # 默认绿色
    
    # 拆分假名为单个字符(处理小写假名)
    chars = list(reading)
    
    # 生成每个假名的 HTML
    spans = []
    for i, char in enumerate(chars):
        mora_index = i + 1  # 拍数从 1 开始
        
        # 基础样式
        char_html = f'<span style="display:inline;">{char}</span>'
        
        # 判断是否需要上划线和下降标记
        has_overline = False
        has_drop = False
        
        if pitch_position == 0:
            # 平板式: 第一拍无线,第二拍开始有上划线
            if mora_index > 1:
                has_overline = True
        elif pitch_position == 1:
            # 頭高型: 第一拍有上划线+下降标记,后续无线
            if mora_index == 1:
                has_overline = True
                has_drop = True
        else:
            # 中高型/尾高型: 第二拍到下降位置有上划线,下降位置有标记
            if 2 <= mora_index <= pitch_position:
                has_overline = True
                if mora_index == pitch_position:
                    has_drop = True
        
        # 构建标记 HTML
        mark_style_parts = [
            f'border-color:{color}',
        ]
        
        if has_overline or has_drop:
            mark_style_parts.extend([
                'display:block',
                'user-select:none',
                'pointer-events:none',
                'position:absolute',
                'top:0.1em',
                'left:0',
                'right:0',
                'height:0',
                'border-top-width:0.1em',
                'border-top-style:solid',
            ])
        
        if has_drop:
            # 下降标记: 右侧竖线
            mark_style_parts.extend([
                'right:-0.1em',
                'height:0.4em',
                'border-right-width:0.1em',
                'border-right-style:solid',
            ])
        
        mark_html = f'<span style="{";".join(mark_style_parts)};"></span>'
        
        # 包装容器
        container_style_parts = [
            'display:inline-block',
            'position:relative',
        ]
        
        if has_drop:
            # 下降位置需要右边距和内边距
            container_style_parts.extend([
                'padding-right:0.1em',
                'margin-right:0.1em',
            ])
        
        container_html = f'<span style="{";".join(container_style_parts)};">{char_html}{mark_html}</span>'
        spans.append(container_html)
    
    # 组合所有假名
    full_html = '<span style="display:inline;">' + ''.join(spans) + '</span>'
    
    return full_html


def file_to_base64(file_path: Path) -> str:
    """
    将文件转换为 Base64 编码字符串
    
    Args:
        file_path: 文件路径
    
    Returns:
        Base64 编码的字符串,如果文件不存在返回空字符串
    """
    import base64
    
    if not file_path or not file_path.exists():
        return ""
    
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
            b64 = base64.b64encode(data).decode('utf-8')
            
            # 添加 data URI scheme
            ext = file_path.suffix.lower()
            if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                mime_type = f"image/{ext[1:]}"
                if ext == '.jpg':
                    mime_type = "image/jpeg"
                return f"data:{mime_type};base64,{b64}"
            elif ext in ['.mp3', '.m4a', '.ogg', '.wav']:
                mime_type = f"audio/{ext[1:]}"
                if ext == '.m4a':
                    mime_type = "audio/mp4"
                return f"data:{mime_type};base64,{b64}"
            else:
                return f"data:application/octet-stream;base64,{b64}"
    except Exception as e:
        print(f"   ⚠️  读取文件失败 {file_path}: {e}")
        return ""


# ----------------------- FFmpeg 辅助函数 -----------------------

def ms_to_s(ms: int) -> float:
    """毫秒转秒"""
    return ms / 1000.0


def ensure_dir(p: Path) -> None:
    """确保目录存在"""
    p.mkdir(parents=True, exist_ok=True)


def run_ffmpeg(cmd: List[str]) -> None:
    """执行 FFmpeg 命令"""
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed: {' '.join(cmd)}\n{proc.stderr.decode('utf-8', 'ignore')}"
        )


def screenshot(video: Path, t: float, out_jpg: Path, vf: Optional[str] = None) -> None:
    """截取视频帧并保存为 JPG (95% 质量)"""
    cmd = ["ffmpeg", "-y", "-ss", f"{t:.3f}", "-i", str(video)]
    if vf:
        cmd += ["-vf", vf]
    # 使用 JPEG 编码器,qscale:v 2 约等于 95% 质量
    # qscale:v 范围: 2-31, 2=最高质量, 31=最低质量
    cmd += ["-vframes", "1", "-c:v", "mjpeg", "-q:v", "2", str(out_jpg)]
    run_ffmpeg(cmd)


def cut_audio(video: Path, start: float, end: float, out_audio: Path) -> None:
    """裁剪音频片段"""
    dur = max(0.01, end - start)
    cmd = [
        "ffmpeg", "-y", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}",
        "-i", str(video), "-vn", "-ac", "2", "-ar", "48000",
        "-c:a", "aac", "-b:a", "192k", str(out_audio)
    ]
    run_ffmpeg(cmd)


# ----------------------- 字幕和文本处理 -----------------------

def katakana_to_hiragana(text: str) -> str:
    """将片假名转换为平假名"""
    if not text:
        return ""
    result = []
    for char in text:
        code = ord(char)
        # 片假名范围: 0x30A0-0x30FF
        # 平假名范围: 0x3040-0x309F
        # 偏移量: 0x60
        if 0x30A1 <= code <= 0x30F6:  # カ-ヶ
            result.append(chr(code - 0x60))
        else:
            result.append(char)
    return ''.join(result)


def is_all_katakana(text: str) -> bool:
    """检测文本是否全是片假名(允许长音符、促音等)
    
    Args:
        text: 要检测的文本
        
    Returns:
        True 如果全是片假名字符
        
    Example:
        >>> is_all_katakana("コーヒー")
        True
        >>> is_all_katakana("コーヒーを飲む")
        False
    """
    if not text:
        return False
    # 片假名范围: ァ-ヶ (0x30A1-0x30F6) + 长音符 ー (0x30FC) + 中点 ・ (0x30FB)
    for char in text:
        code = ord(char)
        if not (0x30A1 <= code <= 0x30F6 or code == 0x30FC or code == 0x30FB):
            return False
    return True


def expand_long_vowel(text: str) -> str:
    """展开长音符(ー)为完整假名
    
    Args:
        text: 平假名文本 (可能包含长音符)
        
    Returns:
        展开后的平假名 (无长音符)
        
    规则:
    - あー → あa
    - いー → いi
    - うー → うu
    - えー → ええ/えい (根据前字判断)
    - おー → うo (お段长音通常用 う)
    
    Example:
        >>> expand_long_vowel("こーひー")
        "こうひい"
        >>> expand_long_vowel("せんせー")
        "せんせい"
    """
    if not text or 'ー' not in text:
        return text
    
    # 母音映射 (平假名行的代表字符)
    vowel_map = {
        'あ': 'あ', 'か': 'あ', 'さ': 'あ', 'た': 'あ', 'な': 'あ', 
        'は': 'あ', 'ま': 'あ', 'や': 'あ', 'ら': 'あ', 'わ': 'あ', 'が': 'あ', 'ざ': 'あ', 'だ': 'あ', 'ば': 'あ', 'ぱ': 'あ',
        'い': 'い', 'き': 'い', 'し': 'い', 'ち': 'い', 'に': 'い', 
        'ひ': 'い', 'み': 'い', 'り': 'い', 'ゐ': 'い', 'ぎ': 'い', 'じ': 'い', 'ぢ': 'い', 'び': 'い', 'ぴ': 'い',
        'う': 'う', 'く': 'う', 'す': 'う', 'つ': 'う', 'ぬ': 'う', 
        'ふ': 'う', 'む': 'う', 'ゆ': 'う', 'る': 'う', 'ぐ': 'う', 'ず': 'う', 'づ': 'う', 'ぶ': 'う', 'ぷ': 'う',
        'え': 'い', 'け': 'い', 'せ': 'い', 'て': 'い', 'ね': 'い', 
        'へ': 'い', 'め': 'い', 'れ': 'い', 'ゑ': 'い', 'げ': 'い', 'ぜ': 'い', 'で': 'い', 'べ': 'い', 'ぺ': 'い',
        'お': 'う', 'こ': 'う', 'そ': 'う', 'と': 'う', 'の': 'う', 
        'ほ': 'う', 'も': 'う', 'よ': 'う', 'ろ': 'う', 'を': 'う', 'ご': 'う', 'ぞ': 'う', 'ど': 'う', 'ぼ': 'う', 'ぽ': 'う',
        'ん': 'ん',
    }
    
    result = []
    for i, char in enumerate(text):
        if char == 'ー' and i > 0:
            # 长音符: 重复前一个字符的母音
            prev_char = result[-1] if result else 'あ'
            vowel = vowel_map.get(prev_char, 'う')  # 默认 u 音
            result.append(vowel)
        else:
            result.append(char)
    
    return ''.join(result)


def normalize_sub_text(s: str) -> str:
    """标准化字幕文本,去除样式标签"""
    if not s:
        return ""
    s = re.sub(r"\{[^}]*\}", "", s)  # ASS 标签
    s = re.sub(r"<[^>]+>", "", s)    # HTML 标签
    s = s.replace("\\N", "\n")       # ASS 换行标记 -> 真实换行
    s = s.replace("\u3000", " ")     # 全角空格
    s = re.sub(r"\s+", " ", s).strip()
    return s


def extract_episode_info(video_path: Path, words_path: Path) -> tuple[str, str]:
    """从文件名提取动漫名和集数信息
    
    Args:
        video_path: 视频文件路径
        words_path: 单词文件路径
        
    Returns:
        (anime_name, episode): 动漫名和集数 (如 "鬼灭之刃", "S01E05")
    """
    # 从视频文件名提取动漫名 (去掉扩展名和集数信息)
    video_stem = video_path.stem  # 例如: "[BeanSub&FZSD&VCB-Studio] Kimetsu no Yaiba [01][Ma10p 1080p][x265 flac aac]"
    
    # 从单词文件名提取集数 (匹配 S_E 或 SE 格式)
    words_stem = words_path.stem  # 例如: "S1_E2_words" 或 "S01E05_words"
    
    # 尝试多种格式匹配
    episode_code = None
    
    # 1. 匹配 Sx_Ex 格式 (S1_E2, S01_E05 等，用下划线分隔)
    episode_match = re.search(r'S(\d+)_E(\d+)', words_stem, re.IGNORECASE)
    if episode_match:
        season = episode_match.group(1)
        episode = episode_match.group(2)
        episode_code = f"S{season.zfill(2)}E{episode.zfill(2)}"
    
    # 2. 匹配 SxEx 格式 (S1E2, S01E05 等，无下划线)
    if not episode_code:
        episode_match = re.search(r'S(\d+)E(\d+)', words_stem, re.IGNORECASE)
        if episode_match:
            season = episode_match.group(1)
            episode = episode_match.group(2)
            episode_code = f"S{season.zfill(2)}E{episode.zfill(2)}"
    
    # 3. 如果没找到,尝试匹配 Ep01 格式
    if not episode_code:
        ep_match = re.search(r'Ep(\d+)', words_stem, re.IGNORECASE)
        if ep_match:
            episode_code = f"S01E{ep_match.group(1).zfill(2)}"
    
    # 4. 如果还是没找到,尝试从视频文件名提取
    if not episode_code:
        video_episode_match = re.search(r'S(\d+)E(\d+)', video_stem, re.IGNORECASE)
        if video_episode_match:
            season = video_episode_match.group(1)
            episode = video_episode_match.group(2)
            episode_code = f"S{season.zfill(2)}E{episode.zfill(2)}"
        else:
            # 尝试匹配方括号中的数字 [01]
            bracket_match = re.search(r'\[(\d{1,2})\]', video_stem)
            if bracket_match:
                episode_code = f"S01E{bracket_match.group(1).zfill(2)}"
            else:
                episode_code = "S01E01"  # 默认值
    
    # 从视频文件名提取动漫名
    # 1. 移除所有方括号及其内容 (如 [BeanSub&FZSD&VCB-Studio], [01], [Ma10p 1080p] 等)
    anime_name = re.sub(r'\[[^\]]*\]', '', video_stem)
    
    # 2. 移除集数部分 (S01E05 或 Ep01 格式)
    anime_name = re.sub(r'[_\s]*S\d+E\d+.*', '', anime_name, flags=re.IGNORECASE)
    anime_name = re.sub(r'[_\s]*Ep\d+.*', '', anime_name, flags=re.IGNORECASE)
    
    # 3. 下划线转空格,清理多余空白
    anime_name = anime_name.replace('_', ' ').strip()
    anime_name = re.sub(r'\s+', ' ', anime_name)  # 多个空格合并为一个
    
    if not anime_name:
        anime_name = video_stem  # 如果提取失败,使用完整文件名
    
    return anime_name, episode_code


def load_words(path: Path) -> List[Tuple[str, Optional[str], Optional[str]]]:
    """从文件加载目标单词列表
    
    支持格式:
    - 普通单词: 精霊
    - 单圆括号指定读音: 精霊(せいれい)
    - 单方括号指定查词形态: 食べた[食べる] 或 狂い咲く[狂い咲き]
    - 同时指定读音和查词形态: 食べた(たべた)[食べる]
    
    语法规则:
    - () 圆括号 = 强制读音
    - [] 方括号 = 强制查词形态
    
    Returns:
        List[Tuple[str, Optional[str], Optional[str]]]: [(单词, 读音或None, 查词形态或None), ...]
    """
    txt = path.read_text(encoding='utf-8')
    words_with_reading = []
    
    for w in re.split(r"[\n,\t]", txt):
        w = w.strip()
        if not w:
            continue
        
        lookup_form = None
        reading = None
        original_w = w
        
        # 检查方括号(查词形态): 食べた[食べる]
        dict_match = re.search(r'\[([^\]]+)\]', w)
        if dict_match:
            lookup_form = dict_match.group(1).strip()
            # 移除方括号部分
            w = w.replace(dict_match.group(0), '')
        
        # 检查圆括号(读音): 精霊(せいれい)
        reading_match = re.search(r'\(([^\)]+)\)', w)
        if reading_match:
            reading = reading_match.group(1).strip()
            # 移除圆括号部分
            w = w.replace(reading_match.group(0), '')
        
        # 剩下的就是单词本身
        word = w.strip()
        
        words_with_reading.append((word, reading, lookup_form))
    
    return words_with_reading


def tokens_furigana(text: str, tagger: Tagger) -> str:
    """为文本添加假名注音(平假名)
    
    格式规则:
    - 有汉字的词添加假名标注: 間違[まちが]
    - 送り仮名不包含在方括号内: 間違[まちが]い (不是 間違い[まちがい])
    - 从第二个token开始,每个token前加空格: 間違[まちが]い 今[いま]は
    
    示例:
        間違[まちが]い 今[いま]は 重度[じゅうど]の 飢餓[きが]状態[じょうたい]
    """
    if not text:
        return ""
    out = []
    for t in tagger(text):
        surf = t.surface
        # 获取读音(片假名)
        yomi = None
        if hasattr(t.feature, 'kana'):
            yomi = t.feature.kana
        elif hasattr(t, 'feature') and len(t.feature) > 7:
            yomi = t.feature[7]
        
        # 转换为平假名
        if yomi:
            yomi = katakana_to_hiragana(yomi)
        
        # 如果有汉字且读音不同,添加假名
        if yomi and yomi != surf and re.search(r"[一-龯々〆ヵヶ]", surf):
            # 分离汉字部分和送り仮名
            # 找到最后一个汉字的位置
            kanji_end = 0
            for i, char in enumerate(surf):
                if re.match(r"[一-龯々〆ヵヶ]", char):
                    kanji_end = i + 1
            
            if kanji_end < len(surf):
                # 有送り仮名: 間違い -> 間違[まちが]い
                kanji_part = surf[:kanji_end]
                okurigana = surf[kanji_end:]
                
                # 假名也要对应截取(去掉送り仮名对应的部分)
                # 简单处理: 假设送り仮名的假名就是它本身
                yomi_kanji = yomi
                if okurigana and yomi.endswith(okurigana):
                    yomi_kanji = yomi[:-len(okurigana)]
                
                out.append(f"{kanji_part}[{yomi_kanji}]{okurigana}")
            else:
                # 全是汉字: 間違 -> 間違[まちがい]
                out.append(f"{surf}[{yomi}]")
        else:
            out.append(surf)
    
    # 从第二个token开始,每个前面加空格
    return ' '.join(out)


def lemmatize(text: str, tagger: Tagger) -> List[str]:
    """获取文本中所有词的词元形式"""
    if not text:
        return []
    lemmas = []
    for t in tagger(text):
        # 尝试多种方式获取词元
        lemma = None
        if hasattr(t.feature, 'lemma'):
            lemma = t.feature.lemma
        elif hasattr(t, 'feature') and len(t.feature) > 6:
            lemma = t.feature[6]  # IPADic 格式
        
        lemmas.append(lemma or t.surface)
    return lemmas


# ----------------------- 频率索引 -----------------------

class FrequencyIndex:
    """频率数据索引 (支持 CSV/TSV/JSON 格式)"""
    
    def __init__(self, path: Optional[Path] = None):
        self.idx: Dict[str, Tuple[str, float]] = {}
        if not path:
            return
        
        try:
            if path.suffix.lower() == '.json':
                self._load_from_json(path)
            elif path.suffix.lower() == '.zip':
                self._load_from_zip(path)
            else:
                self._load_from_file(path)
        except Exception as e:
            print(f"⚠️  加载频率数据失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_from_json(self, path: Path):
        """从 Yomichan term_meta_bank JSON 文件加载
        
        格式示例:
        ["具体的検討", "freq", {"reading": "ぐたいてきけんとう", "frequency": {"value": 108366, "displayValue": "10万"}}]
        或简单格式:
        ["単語", "freq", 数值]
        ["単語", "freq", {"value": 数值, "displayValue": "显示"}]
        """
        import json
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print(f"   ⚠️  JSON 格式不正确,期望列表")
            return
        
        loaded = 0
        for entry in data:
            if not isinstance(entry, list) or len(entry) < 3:
                continue
            
            term = entry[0]  # 单词
            meta_type = entry[1]  # 通常是 "freq"
            meta_value = entry[2]  # 频率值或对象
            
            # 只处理频率数据
            if meta_type != "freq":
                continue
            
            # 提取数值
            rank = None
            display = None
            
            if isinstance(meta_value, (int, float)):
                # 简单数值格式
                rank = float(meta_value)
                display = f"{int(rank)}"
            elif isinstance(meta_value, dict):
                # 对象格式 - 检查是否有嵌套的 frequency 字段
                if 'frequency' in meta_value and isinstance(meta_value['frequency'], dict):
                    # 嵌套格式: {"reading": "...", "frequency": {"value": ..., "displayValue": "..."}}
                    freq_obj = meta_value['frequency']
                    rank = float(freq_obj.get('value', 0))
                    display = f"{freq_obj.get('displayValue', str(int(rank)))}"
                elif 'value' in meta_value:
                    # 直接格式: {"value": ..., "displayValue": "..."}
                    rank = float(meta_value.get('value', 0))
                    display = f"{meta_value.get('displayValue', str(int(rank)))}"
                else:
                    continue
            else:
                continue
            
            if rank is not None and display:
                # 存储: term -> (display_string, numeric_rank)
                self.idx.setdefault(term, (display, rank))
                loaded += 1
        
        if loaded > 0:
            print(f"   ✅ 加载频率数据: {loaded} 条")
        else:
            print(f"   ⚠️  未找到任何频率数据")
    
    def _load_from_zip(self, path: Path):
        """从 ZIP 文件加载"""
        if pd is None:
            return
        
        with zipfile.ZipFile(path) as z:
            cand = [n for n in z.namelist() 
                   if n.lower().endswith(('.csv', '.tsv'))]
            if not cand:
                return
            
            with z.open(cand[0]) as f:
                sep = ',' if cand[0].lower().endswith('.csv') else '\t'
                df = pd.read_csv(f, sep=sep)
                self._load_dataframe(df)
    
    def _load_from_file(self, path: Path):
        """从 CSV/TSV 文件加载"""
        if pd is None:
            return
        
        sep = ',' if path.suffix.lower() == '.csv' else '\t'
        df = pd.read_csv(path, sep=sep)
        self._load_dataframe(df)
    
    def _load_dataframe(self, df: pd.DataFrame):
        """从 DataFrame 加载数据"""
        cols = {c.lower(): c for c in df.columns}
        
        # 查找词条列
        term_c = next((cols[k] for k in ['term', 'lemma', 'word', '表記', '語彙', '語'] 
                      if k in cols), None)
        # 查找频率列
        rank_c = next((cols[k] for k in ['rank', 'freq_rank', 'harmonic_rank', 
                                         'frequency', '頻度', '出現度'] 
                      if k in cols), None)
        
        if term_c is None or rank_c is None:
            return
        
        for _, row in df[[term_c, rank_c]].dropna().iterrows():
            term = str(row[term_c])
            try:
                rank = float(row[rank_c])
                self.idx.setdefault(term, (str(rank), rank))
            except (ValueError, TypeError):
                continue
    
    def lookup(self, key: str) -> Tuple[Optional[str], Optional[float]]:
        """查询词的频率"""
        return self.idx.get(key, (None, None))


# ----------------------- 核心处理逻辑 -----------------------

def find_hits(
    words: List[Tuple[str, Optional[str]]],  # 修改: 现在包含可选读音
    subs: pysubs2.SSAFile,
    tagger: Tagger,
    video: Path,
    outdir: Path,
    meanings_lookup: MeaningsLookup,
    audio_lookup: AudioLookup,
    freq_index: FrequencyIndex,
    anime_name: str = "",
    episode: str = "",
    dicts_dir: Optional[Path] = None,
    pad: float = 0.0,
    vf: Optional[str] = None,
    verbose: bool = True
) -> List[CardData]:
    """
    查找字幕中的目标单词并生成卡片数据
    
    Args:
        words: 目标单词列表 (单词, 可选读音)
        subs: 字幕文件
        tagger: Fugashi 分词器
        video: 视频文件路径
        outdir: 输出目录
        meanings_lookup: 释义查询对象
        audio_lookup: 音频查询对象
        freq_index: 频率索引
        anime_name: 动漫名称
        episode: 集数信息 (如 S01E05)
        dicts_dir: 词典目录路径 (用于 DJS_N 备选音频)
        pad: 音频裁剪前后填充时间(秒)
        vf: FFmpeg 视频滤镜
        verbose: 是否显示详细信息
    
    Returns:
        卡片数据列表
    """
    ensure_dir(outdir)
    cards: List[CardData] = []
    
    # 创建单词集合和映射
    word_to_reading = {word: reading for word, reading, _ in words}
    word_to_lookup_form = {word: lookup_form for word, _, lookup_form in words}
    wset = set(word_to_reading.keys())
    
    print(f"\n🔍 开始处理字幕...")
    print(f"   目标单词: {len(words)} 个")
    print(f"   字幕行数: {len(subs)} 行\n")
    
    for idx, line in enumerate(subs, 1):
        # 标准化字幕文本
        sent = normalize_sub_text(line.text)
        if not sent:
            continue
        
        # 分词并获取词元
        lemmas = lemmatize(sent, tagger)
        tokens_set = set(lemmas)
        
        # 检查是否包含目标单词 (使用两种方式: 词元匹配 + 字符串匹配)
        # 1. 词元匹配: 检查分词后的词元
        matched_by_lemma = wset.intersection(tokens_set)
        
        # 2. 字符串匹配: 直接在句子中查找 (处理分词失败的情况)
        matched_by_string = {word for word, _, _ in words if word in sent}
        
        # 合并两种匹配结果
        matched = matched_by_lemma | matched_by_string
        
        if not matched:
            continue
        
        if verbose:
            print(f"[{idx}/{len(subs)}] 找到匹配: {', '.join(matched)}")
            print(f"         原句: {sent[:50]}...")
        
        # 生成带假名的句子
        furig = tokens_furigana(sent, tagger)
        
        # 计算时间范围
        start = max(0.0, ms_to_s(line.start) - pad)
        end = ms_to_s(line.end) + pad
        mid = (start + end) / 2
        
        # 生成文件名 (使用 JPG 格式)
        base = f"{video.stem}_{int(line.start)}_{int(line.end)}"
        img_path = outdir / f"{base}.jpg"
        aud_path = outdir / f"{base}.m4a"
        
        # 截图和裁剪音频
        try:
            screenshot(video, mid, img_path, vf)
            cut_audio(video, start, end, aud_path)
        except Exception as e:
            print(f"   ⚠️  媒体处理失败: {e}")
            continue
        
        # 为每个匹配的单词创建卡片
        for word in matched:
            if verbose:
                print(f"   📝 查询单词: {word}")
            
            # 记录原始单词(可能是片假名)
            original_word = word
            is_original_katakana = is_all_katakana(word)
            
            # 获取单词的词元形式 (原形) - 用于词典查询
            # 例如: 食べた → 食べる, 見ている → 見る
            # 注意: Fugashi 将会把词拆成多个 token, 每个 token 有自己的 lemma
            # 对于复合词(例如 空模様)我们需要把所有 token 的 lemma 拼接起来, 而不是只取第一个
            word_lemma_parts: List[str] = []
            for t in tagger(word):
                part_lemma = None
                if hasattr(t.feature, 'lemma') and t.feature.lemma:
                    part_lemma = t.feature.lemma
                elif hasattr(t, 'feature') and len(t.feature) > 6 and t.feature[6]:
                    part_lemma = t.feature[6]  # IPADic 格式
                else:
                    part_lemma = t.surface
                # 保证不是空字符串
                if part_lemma:
                    word_lemma_parts.append(part_lemma)

            # 将各 token 的 lemma 拼接回完整词元
            word_lemma = ''.join(word_lemma_parts) if word_lemma_parts else word
            
            # 如果词元和原词不同,显示提示
            if word_lemma != word and verbose:
                print(f"      📖 词元形式: {word} → {word_lemma}")
            
            # 检查是否有用户指定的查词形态 (方括号语法)
            user_lookup_form = word_to_lookup_form.get(word)
            if user_lookup_form:
                if verbose:
                    print(f"      🎯 用户指定查词形态: {user_lookup_form}")
                # 使用用户指定的形态作为首选查询词
                word_lemma = user_lookup_form
            
            # 准备查询候选词列表 (用于回退查询)
            # 对于片假名词汇: 原片假名 → 词元(平假名) → く→き变体
            # 对于其他词汇: 词元 → 原词 → く→き变体
            query_candidates = []
            
            if is_original_katakana and not user_lookup_form:
                # 片假名词汇优先用原片假名查询
                query_candidates.append(original_word)
                if word_lemma != original_word:
                    query_candidates.append(word_lemma)  # 平假名作为备选
            else:
                # 其他情况按正常顺序
                query_candidates.append(word_lemma)
                if word_lemma != word:
                    query_candidates.append(word)
            
            # 对于以く结尾的动词,添加き变体 (复合词常见形式)
            if word_lemma.endswith('く'):
                ki_variant = word_lemma[:-1] + 'き'
                query_candidates.append(ki_variant)
            
            # 获取强制读音 (如果有的话)
            forced_reading = word_to_reading.get(word)
            if forced_reading and verbose:
                print(f"      🔒 强制读音: {forced_reading}")
            
            # 1. 查询释义 (使用候选词回退查询)
            definition = ""
            successful_query_form = word  # 记录成功查询的形态,用于更新卡片显示
            
            if meanings_lookup:
                try:
                    # 如果有强制读音,用假名查询
                    if forced_reading:
                        definition = meanings_lookup.lookup(forced_reading)
                        if definition and verbose:
                            # 检查结果是否包含原汉字和假名
                            if word_lemma in definition or word in definition:
                                plain_def = re.sub(r'<[^>]+>', '', definition)[:100]
                                print(f"      ✅ 释义 (假名查询): {plain_def}...")
                            else:
                                print(f"      ⚠️  假名查询结果中未找到原词 '{word}',结果可能不准确")
                        elif verbose:
                            print(f"      ⚠️  假名 '{forced_reading}' 未找到释义,尝试用词元查询")
                            # 假名查询失败,回退到词元查询
                            definition = meanings_lookup.lookup(word_lemma)
                            if definition:
                                successful_query_form = word_lemma
                                plain_def = re.sub(r'<[^>]+>', '', definition)[:100]
                                print(f"      ✅ 释义 (词元查询): {plain_def}...")
                    else:
                        # 没有强制读音,使用候选词回退查询
                        # 对于片假名词汇: 候选词列表已包含 [片假名, 平假名, ...]
                        # 对于其他词汇: 候选词列表包含 [词元, 原词, く→き变体]
                        for candidate in query_candidates:
                            definition = meanings_lookup.lookup(candidate)
                            if definition:
                                successful_query_form = candidate  # 记录成功的查询形态
                                if candidate != query_candidates[0] and verbose:
                                    print(f"      🔄 使用变体查询: {candidate}")
                                plain_def = re.sub(r'<[^>]+>', '', definition)[:100]
                                print(f"      ✅ 释义: {plain_def}...")
                                break
                    
                    if not definition and verbose:
                        print(f"      ⚠️  未找到释义")
                except Exception as e:
                    if verbose:
                        print(f"      ⚠️  释义查询失败: {e}")
                    definition = ""
            else:
                if verbose:
                    print(f"      ⚠️  释义查询未初始化,跳过")
            
            # 2. 查询音频和音调 (支持多读音)
            reading = ''
            pitch_pos = ''
            pitch_src = ''
            audio_src = ''
            all_readings_json = ''
            audio_result = None  # 初始化 audio_result,确保作用域正确
            
            if audio_lookup:
                try:
                    # 如果有强制读音,直接用假名查询
                    if forced_reading:
                        audio_result = audio_lookup.lookup(forced_reading, verbose=False, return_all_pitches=True)
                        if verbose and audio_result and audio_result.get('reading'):
                            print(f"      ✅ 使用强制读音查询: {forced_reading}")
                    else:
                        # 没有强制读音,使用候选词回退查询
                        for candidate in query_candidates:
                            audio_result = audio_lookup.lookup(candidate, verbose=False, return_all_pitches=True)
                            if audio_result and audio_result.get('reading'):
                                if candidate != word_lemma and verbose:
                                    print(f"      🔄 使用变体查询音频: {candidate}")
                                break
                    
                    if audio_result:
                        reading = audio_result.get('reading', '') or ''
                        pitch_pos = audio_result.get('pitch_position', '') or ''
                        pitch_src = audio_result.get('pitch_source', '') or ''
                        audio_src = audio_result.get('audio_source', '') or ''
                        
                        # 获取所有候选读音
                        all_pitches = audio_result.get('all_pitches', [])
                        
                        all_readings_json = json.dumps(
                            [{'reading': r, 'pitch_position': p} for r, p in all_pitches],
                            ensure_ascii=False
                        ) if all_pitches else ''
                        
                        if verbose and reading:
                            plain_reading = re.sub(r'<[^>]+>', '', reading)
                            print(f"      🎵 读音: {plain_reading} {pitch_pos}")
                            if not forced_reading and len(all_pitches) > 1:
                                print(f"      📋 共 {len(all_pitches)} 个候选读音")
                        elif verbose:
                            print(f"      ⚠️  未找到音频/音调")
                    else:
                        if verbose:
                            print(f"      ⚠️  未找到音频/音调")
                except Exception as e:
                    if verbose:
                        print(f"      ⚠️  音频查询失败: {e}")
                    audio_result = None  # 确保异常时 audio_result 为 None
            else:
                if verbose:
                    print(f"      ⚠️  音频查询未初始化,跳过")
            
            # 3. 查询频率 (使用候选词回退查询)
            freq_str, freq_rank = None, None
            for candidate in query_candidates:
                freq_str, freq_rank = freq_index.lookup(candidate)
                if freq_str:
                    if candidate != word_lemma and verbose:
                        print(f"      🔄 使用变体查询频率: {candidate}")
                    break
            
            if verbose:
                if freq_str:
                    print(f"      📊 频率: {freq_str} (排序值: {freq_rank})")
                else:
                    print(f"      ⚠️  未找到频率数据")
            
            # 4. 转换音调类型 (使用假名读音长度)
            pitch_type = pitch_position_to_type(pitch_pos, reading)
            if verbose and pitch_type:
                print(f"      🎼 声调类型: {pitch_type}")
            
            # 5. Base64 编码媒体文件
            if verbose:
                print(f"      📦 编码媒体文件...")
            
            sentence_audio_b64 = file_to_base64(aud_path)
            picture_b64 = file_to_base64(img_path)
            
            # 获取单词音频 (AudioLookup 直接返回 Base64 data URI)
            word_audio_b64 = ""
            if audio_result and audio_result.get('audio_base64'):
                # AudioLookup 返回的是纯 Base64 数据,需要转换为 data URI
                audio_b64 = audio_result['audio_base64']
                audio_mime = audio_result.get('audio_mime', 'audio/mpeg')
                word_audio_b64 = f"data:{audio_mime};base64,{audio_b64}"
                if verbose:
                    print(f"         ✅ 单词音频: {audio_src}")
            
            # 如果 AudioLookup 没找到音频,尝试从 DJS_N (大辞泉第二版) 获取 (使用候选词回退查询)
            # 注意: DJS 可能已经在 AudioLookup 中,所以这个是真正的备选
            if not word_audio_b64 and dicts_dir:
                djs_mdx = dicts_dir / "DJS_N" / "DJS.mdx"
                if djs_mdx.exists():
                    try:
                        for candidate in query_candidates:
                            audio_infos = get_all_audio_info_from_mdx(djs_mdx, candidate, "大辞泉")
                            if audio_infos:
                                if candidate != word_lemma and verbose:
                                    print(f"         🔄 使用变体查询大辞泉音频: {candidate}")
                                # 使用第一个音频
                                first_audio = audio_infos[0]
                                if first_audio.data_uri:
                                    word_audio_b64 = first_audio.data_uri
                                    audio_src = "大辞泉"
                                    if verbose:
                                        print(f"         ✅ 单词音频 (大辞泉): {first_audio.format}")
                                break
                    except Exception as e:
                        if verbose:
                            print(f"         ⚠️  大辞泉音频查询失败: {e}")
            
            # 创建卡片数据
            # 注意: word 字段使用成功查询到的形态,这样显示的是词典中真实存在的词条
            # 例如: 狂い咲く[[狂い咲き]] 会显示为 "狂い咲き"
            card = CardData(
                word=successful_query_form,  # 使用成功查询的形态而非原始输入
                sentence=sent,
                sentence_furigana=furig,
                definition=definition,
                reading=reading,
                pitch_position=pitch_pos,
                pitch_type=pitch_type,
                pitch_source=pitch_src,
                sentence_audio_base64=sentence_audio_b64,
                word_audio_base64=word_audio_b64,
                word_audio_source=audio_src,
                picture_base64=picture_b64,
                bccwj_frequency=freq_str or '',
                bccwj_freq_sort=str(freq_rank) if freq_rank is not None else '',
                anime_name=anime_name,
                episode=episode,
                start_time=start,
                end_time=end,
                lemma=word_lemma,  # 存储词元形式
                all_readings=all_readings_json
            )
            
            cards.append(card)
            if verbose:
                print()
    
    return cards


# ----------------------- 路径处理工具 -----------------------

def normalize_path(path_str: str) -> Path:
    """
    规范化路径字符串,处理 Unicode 字符
    
    常见问题:
    - 全角空格 (U+3000) 被识别为 \\u3000
    - 日语文件名编码问题
    """
    if not path_str:
        return None
    
    # 处理 Unicode 转义序列
    try:
        # 如果字符串包含 \u 转义,尝试解码
        if '\\u' in path_str:
            path_str = path_str.encode().decode('unicode-escape')
    except Exception:
        pass
    
    # 创建 Path 对象
    path = Path(path_str)
    
    # 处理全角空格和其他全角字符
    path_str = str(path)
    path_str = path_str.replace('\u3000', ' ')  # 全角空格 → 半角空格
    
    return Path(path_str)


def safe_path_from_args(arg_value) -> Optional[Path]:
    """
    安全地从命令行参数获取 Path 对象
    
    Args:
        arg_value: argparse 解析的参数值
    
    Returns:
        规范化的 Path 对象,或 None
    """
    if arg_value is None:
        return None
    
    if isinstance(arg_value, Path):
        # 已经是 Path,但仍需规范化
        return normalize_path(str(arg_value))
    
    return normalize_path(str(arg_value))


# ----------------------- CSV 导出 -----------------------

def write_csv(cards: List[CardData], csv_path: Path, outdir: Path) -> None:
    """将卡片数据写入 CSV (包含 Base64 编码的媒体) 并导出独立媒体文件
    
    使用 DataFrame 管理数据:
    1. 统计重复单词出现次数
    2. 去重保留第一次出现的数据
    3. 添加 duplicate_count 字段标记重复次数
    """
    if not pd:
        print("\n❌ pandas 未安装,无法导出 CSV")
        return
    
    ensure_dir(csv_path.parent)
    
    # 创建媒体文件目录
    media_dir = outdir / "media"
    ensure_dir(media_dir)
    
    print(f"\n📊 使用 DataFrame 处理数据...")
    
    # 转换为 DataFrame
    df = pd.DataFrame([asdict(card) for card in cards])
    
    print(f"   原始卡片数: {len(df)}")
    
    # 统计每个单词的重复次数
    word_counts = df['word'].value_counts().to_dict()
    df['duplicate_count'] = df['word'].map(word_counts)
    
    # 找出重复的单词
    duplicates = df[df['duplicate_count'] > 1]['word'].unique()
    if len(duplicates) > 0:
        print(f"   发现重复单词: {len(duplicates)} 个")
        print(f"   示例: {', '.join(list(duplicates)[:5])}")
    
    # 去重 (保留第一次出现)
    df_dedup = df.drop_duplicates(subset=['word'], keep='first').copy()
    removed = len(df) - len(df_dedup)
    
    if removed > 0:
        print(f"   去重后卡片数: {len(df_dedup)} (移除 {removed} 张重复)")
    
    # 先导出媒体文件,获取文件路径
    print(f"\n📦 导出独立媒体文件到: {media_dir}")
    
    media_stats = {
        'pictures': 0,
        'sentence_audio': 0,
        'word_audio': 0
    }
    
    # 添加媒体文件路径列
    df_dedup['picture_file'] = ''
    df_dedup['sentence_audio_file'] = ''
    df_dedup['word_audio_file'] = ''
    
    # 遍历去重后的数据,导出媒体文件并记录路径
    for idx in df_dedup.index:
        i = idx + 1
        card_word = df_dedup.at[idx, 'word']
        
        # 导出图片 (JPG 格式)
        picture_b64 = df_dedup.at[idx, 'picture_base64']
        if picture_b64:
            try:
                if picture_b64.startswith('data:'):
                    header, b64_data = picture_b64.split(';base64,', 1)
                    import base64
                    img_data = base64.b64decode(b64_data)
                    
                    # 判断原始格式,统一保存为 JPG
                    img_filename = f"{card_word}_{i}_pic.jpg"
                    img_path = media_dir / img_filename
                    with open(img_path, 'wb') as f:
                        f.write(img_data)
                    
                    # 记录相对路径
                    df_dedup.at[idx, 'picture_file'] = f"media/{img_filename}"
                    media_stats['pictures'] += 1
            except Exception as e:
                print(f"   ⚠️  导出图片失败 ({card_word}): {e}")
        
        # 导出句子音频
        sentence_audio_b64 = df_dedup.at[idx, 'sentence_audio_base64']
        if sentence_audio_b64:
            try:
                if sentence_audio_b64.startswith('data:'):
                    header, b64_data = sentence_audio_b64.split(';base64,', 1)
                    mime = header.split(':')[1]
                    ext = 'mp3' if 'mpeg' in mime else 'mp4' if 'mp4' in mime else mime.split('/')[-1]
                    
                    import base64
                    audio_data = base64.b64decode(b64_data)
                    
                    audio_filename = f"{card_word}_{i}_sent.{ext}"
                    audio_path = media_dir / audio_filename
                    with open(audio_path, 'wb') as f:
                        f.write(audio_data)
                    
                    df_dedup.at[idx, 'sentence_audio_file'] = f"media/{audio_filename}"
                    media_stats['sentence_audio'] += 1
            except Exception as e:
                print(f"   ⚠️  导出句子音频失败 ({card_word}): {e}")
        
        # 导出单词音频
        word_audio_b64 = df_dedup.at[idx, 'word_audio_base64']
        if word_audio_b64:
            try:
                if word_audio_b64.startswith('data:'):
                    header, b64_data = word_audio_b64.split(';base64,', 1)
                    mime = header.split(':')[1]
                    ext = 'mp3' if 'mpeg' in mime else 'aac' if 'aac' in mime else mime.split('/')[-1]
                    
                    import base64
                    audio_data = base64.b64decode(b64_data)
                    
                    audio_filename = f"{card_word}_{i}_word.{ext}"
                    audio_path = media_dir / audio_filename
                    with open(audio_path, 'wb') as f:
                        f.write(audio_data)
                    
                    df_dedup.at[idx, 'word_audio_file'] = f"media/{audio_filename}"
                    media_stats['word_audio'] += 1
            except Exception as e:
                print(f"   ⚠️  导出单词音频失败 ({card_word}): {e}")
    
    print(f"   ✅ 图片: {media_stats['pictures']} 个")
    print(f"   ✅ 句子音频: {media_stats['sentence_audio']} 个")
    print(f"   ✅ 单词音频: {media_stats['word_audio']} 个")
    
    # 定义 CSV 字段顺序 (不包含 Base64 数据,只包含文件路径)
    csv_fields = [
        'word', 'duplicate_count', 'sentence', 'sentence_furigana', 'definition',
        'reading', 'pitch_position', 'pitch_type', 'pitch_source',
        'sentence_audio_file', 'word_audio_file', 'word_audio_source',
        'picture_file',
        'bccwj_frequency', 'bccwj_freq_sort', 
        'anime_name', 'episode',
        'start_time', 'end_time',
        'lemma', 'all_readings'
    ]

    # 确保所有字段都存在
    for field in csv_fields:
        if field not in df_dedup.columns:
            df_dedup[field] = ''
    
    try:
        # 导出 CSV (只包含文本和文件路径)
        df_dedup[csv_fields].to_csv(csv_path, index=False, encoding='utf-8')
        
        print(f"\n✅ CSV 已生成: {csv_path}")
        print(f"   总卡片数: {len(df_dedup)}")
        print(f"   ℹ️  CSV 包含媒体文件路径,不含 Base64 数据")
        
    except Exception as e:
        print(f"\n❌ CSV 写入失败: {e}")
        raise


# ----------------------- Anki 推送 -----------------------

def push_to_anki(
    cards: List[CardData],
    anki: AnkiConnect,
    deck_name: str,
    model_name: str,
    tags: List[str],
    allow_duplicates: bool = False,
    verbose: bool = True
) -> Tuple[int, int]:
    """
    将卡片推送到 Anki
    
    Args:
        cards: 卡片数据列表
        anki: AnkiConnect 实例
        deck_name: 牌组名称
        model_name: 笔记类型
        tags: 标签列表
        allow_duplicates: 是否允许重复
        verbose: 是否显示详细信息
    
    Returns:
        (成功数, 失败数)
    """
    print(f"\n🚀 开始推送到 Anki...")
    print(f"   牌组: {deck_name}")
    print(f"   笔记类型: {model_name}")
    print(f"   标签: {', '.join(tags)}")
    print(f"   卡片数: {len(cards)}")
    print()
    
    success_count = 0
    error_count = 0
    word_counter = {}  # 用于生成唯一文件名
    
    for idx, card in enumerate(cards, 1):
        word = card.word
        word_counter[word] = word_counter.get(word, 0) + 1
        card_index = word_counter[word]
        
        try:
            # 1. 准备媒体文件
            picture_filename = ""
            word_audio_filename = ""
            sentence_audio_filename = ""
            
            # 图片
            if card.picture_base64:
                try:
                    # 提取 Base64 数据
                    if card.picture_base64.startswith('data:'):
                        _, b64_data = card.picture_base64.split(';base64,', 1)
                    else:
                        b64_data = card.picture_base64
                    
                    picture_filename = f"{word}_{card_index}_pic.jpg"
                    anki.store_media_file(picture_filename, b64_data)
                except Exception as e:
                    if verbose:
                        print(f"   ⚠️  [{idx}/{len(cards)}] {word}: 图片上传失败: {e}")
            
            # 单词音频
            if card.word_audio_base64:
                try:
                    if card.word_audio_base64.startswith('data:'):
                        header, b64_data = card.word_audio_base64.split(';base64,', 1)
                        # 从 MIME 类型推断扩展名
                        mime = header.split(':')[1]
                        ext = 'mp3' if 'mpeg' in mime else 'aac' if 'aac' in mime else 'mp3'
                    else:
                        b64_data = card.word_audio_base64
                        ext = 'mp3'
                    
                    word_audio_filename = f"{word}_{card_index}_word.{ext}"
                    anki.store_media_file(word_audio_filename, b64_data)
                except Exception as e:
                    if verbose:
                        print(f"   ⚠️  [{idx}/{len(cards)}] {word}: 单词音频上传失败: {e}")
            
            # 句子音频
            if card.sentence_audio_base64:
                try:
                    if card.sentence_audio_base64.startswith('data:'):
                        header, b64_data = card.sentence_audio_base64.split(';base64,', 1)
                        mime = header.split(':')[1]
                        ext = 'mp3' if 'mpeg' in mime else 'mp4' if 'mp4' in mime else 'm4a'
                    else:
                        b64_data = card.sentence_audio_base64
                        ext = 'm4a'
                    
                    sentence_audio_filename = f"{word}_{card_index}_sent.{ext}"
                    anki.store_media_file(sentence_audio_filename, b64_data)
                except Exception as e:
                    if verbose:
                        print(f"   ⚠️  [{idx}/{len(cards)}] {word}: 句子音频上传失败: {e}")
            
            # 2. 准备字段
            # 高亮单词
            sentence_html = card.sentence
            if word in sentence_html:
                sentence_html = sentence_html.replace(word, f'<span class="highlight">{word}</span>')
            
            # 读音格式化为 HTML 列表 (带音调标记)
            reading_html = ''
            if card.reading:
                all_readings = []
                if card.all_readings:
                    try:
                        readings_list = json.loads(card.all_readings)
                        all_readings = readings_list  # 保留完整信息
                    except:
                        # 降级: 只有基础读音
                        all_readings = [{'reading': card.reading, 'pitch_position': card.pitch_position}]
                else:
                    all_readings = [{'reading': card.reading, 'pitch_position': card.pitch_position}]
                
                reading_html = '<ol>'
                for r_info in all_readings:
                    # 提取读音和音调信息
                    if isinstance(r_info, dict):
                        r_reading = r_info.get('reading', '')
                        r_pitch = r_info.get('pitch_position', '')
                    else:
                        # 字符串格式(降级处理)
                        r_reading = str(r_info)
                        r_pitch = card.pitch_position
                    
                    # 去除 HTML 标签,获取纯假名
                    clean_reading = re.sub(r'<[^>]+>', '', r_reading)
                    
                    # 处理长音符: 根据原词类型决定如何处理
                    if is_all_katakana(word):
                        # 原词是全片假名 (如 コーヒー): 保持原样,不转换
                        # clean_reading 保持原来的片假名或平假名
                        pass
                    else:
                        # 原词不是全片假名 (如 精霊, 学校): 转为平假名并展开长音
                        clean_reading = katakana_to_hiragana(clean_reading)
                        clean_reading = expand_long_vowel(clean_reading)
                    
                    # 提取音调位置数字
                    pitch_num = None
                    if r_pitch:
                        match = re.search(r'\[?(\d+)\]?', str(r_pitch))
                        if match:
                            pitch_num = int(match.group(1))
                    
                    # 生成带音调标记的 HTML
                    if pitch_num is not None and clean_reading:
                        # 根据音调位置判断类型
                        r_pitch_type = pitch_position_to_type(f"[{pitch_num}]", clean_reading)
                        pitch_html = generate_pitch_html(clean_reading, pitch_num, r_pitch_type)
                        reading_html += f'<li>{pitch_html}</li>'
                    else:
                        # 无音调信息,直接显示读音
                        reading_html += f'<li>{r_reading}</li>'
                
                reading_html += '</ol>'
            
            # 音调位置格式化
            pitch_position_html = ''
            if card.pitch_position:
                pos_num = card.pitch_position.strip('[]')
                pitch_position_html = f'<ol><li><span style="display:inline;"><span>[</span><span>{pos_num}</span><span>]</span></span></li></ol>'
            
            # 频率格式化
            frequency_html = ''
            if card.bccwj_frequency:
                frequency_html = f'<ul style="text-align: left;"><li>BCCWJ: {card.bccwj_frequency}</li></ul>'
            
            # miscInfo: 动漫名|集数|时间戳
            misc_info_parts = []
            if card.anime_name:
                misc_info_parts.append(card.anime_name)
            if card.episode:
                misc_info_parts.append(card.episode)
            if card.start_time:
                time_str = format_time_hhmmss(card.start_time)
                misc_info_parts.append(time_str)
            misc_info = ' | '.join(misc_info_parts)
            
            # 3. 构建 Anki 笔记
            fields = {
                'word': word,
                'sentence': sentence_html,
                'sentenceFurigana': card.sentence_furigana,
                'sentenceEng': '',
                'reading': reading_html,
                'sentenceCard': '',
                'audioCard': '',
                'notes': '',
                'picture': f'<img src="{picture_filename}" />' if picture_filename else '',
                'wordAudio': f'[sound:{word_audio_filename}]' if word_audio_filename else '',
                'sentenceAudio': f'[sound:{sentence_audio_filename}]' if sentence_audio_filename else '',
                'selectionText': '',
                'definition': card.definition,
                'glossary': card.definition,
                'pitchPosition': pitch_position_html,
                'pitch': card.pitch_type,
                'frequency': frequency_html,
                'freqSort': card.bccwj_freq_sort,
                'miscInfo': misc_info,
                'dictionaryPreference': ''
            }
            
            note = {
                'deckName': deck_name,
                'modelName': model_name,
                'fields': fields,
                'tags': tags,
                'options': {
                    'allowDuplicate': allow_duplicates,
                    'duplicateScope': 'collection'
                }
            }
            
            # 4. 添加到 Anki
            note_id = anki.add_note(note)
            
            if verbose:
                print(f"   ✅ [{idx}/{len(cards)}] {word} (ID: {note_id})")
            
            success_count += 1
            
        except Exception as e:
            if verbose:
                print(f"   ❌ [{idx}/{len(cards)}] {word}: {e}")
            error_count += 1
    
    return success_count, error_count


# ----------------------- 主程序 -----------------------

def main():
    ap = argparse.ArgumentParser(
        description='JP Media Mining → Anki Cards (重构版)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python jp_media_mining_refactored.py \\
    --video "episodes/Ep01.mp4" \\
    --subs  "subs/Ep01.ja.srt" \\
    --words "unknown/Ep01_words.txt" \\
    --primary-mdx   "dicts/primary" \\
    --secondary-mdx "dicts/secondary" \\
    --tertiary-mdx  "dicts/tertiary" \\
    --nhk-old "dicts/NHK_Old" \\
    --nhk-new "dicts/NHK_New" \\
    --djs     "dicts/DJS" \\
    --outdir  "out/Ep01" \\
    --csv     "out/Ep01/cards.csv"
        """
    )
    
    # 必需参数
    ap.add_argument('--video', required=True, type=Path, help='视频文件路径')
    ap.add_argument('--subs', required=True, type=Path, help='字幕文件路径 (.srt/.ass/.vtt)')
    ap.add_argument('--words', required=True, type=Path, help='目标单词列表文件')
    ap.add_argument('--outdir', required=True, type=Path, help='输出目录')
    
    # MDX 词典 (释义)
    ap.add_argument('--primary-mdx', type=Path, 
                   help='主要释义词典目录 (包含 .mdx 文件)')
    ap.add_argument('--secondary-mdx', type=Path,
                   help='次要释义词典目录')
    ap.add_argument('--tertiary-mdx', type=Path,
                   help='第三级释义词典目录 (仅当 secondary 无结果时查询)')
    ap.add_argument('--use-jamdict', action='store_true',
                   help='启用 JMDict 作为最后的 fallback')
    
    # MDX 词典 (音频和音调)
    ap.add_argument('--nhk-old', type=Path,
                   help='NHK 旧版词典目录 (音调信息)')
    ap.add_argument('--nhk-new', type=Path,
                   help='NHK 新版词典目录 (音频)')
    ap.add_argument('--djs', type=Path,
                   help='大辞泉词典目录 (音频)')
    
    # 频率数据
    ap.add_argument('--freq', type=Path,
                   help='频率数据文件 (JSON/ZIP/CSV/TSV), 如 BCCWJ term_meta_bank_1.json')
    
    # 媒体处理选项
    ap.add_argument('--pad', type=float, default=0.0,
                   help='音频裁剪前后填充时间(秒), 默认 0')
    ap.add_argument('--vf', type=str, default=None,
                   help='FFmpeg 视频滤镜, 如 "scale=1280:-1"')
    
    # 输出选项
    ap.add_argument('--csv', type=Path, required=True,
                   help='CSV 输出路径')
    ap.add_argument('--quiet', action='store_true',
                   help='安静模式,减少输出')
    
    # Anki 推送选项
    ap.add_argument('--anki', action='store_true',
                   help='推送到 Anki (需要 AnkiConnect 插件)')
    ap.add_argument('--anki-deck', type=str, default='Japanese::Anime',
                   help='Anki 牌组名称 (默认: Japanese::Anime)')
    ap.add_argument('--anki-model', type=str, default='Senren',
                   help='Anki 笔记类型 (默认: Senren)')
    ap.add_argument('--anki-tags', type=str, nargs='+', default=['anime', 'mining'],
                   help='Anki 卡片标签 (默认: anime mining)')
    ap.add_argument('--anki-allow-duplicates', action='store_true',
                   help='允许重复卡片')
    ap.add_argument('--ankiconnect-url', type=str, default='http://localhost:8765',
                   help='AnkiConnect API 地址 (默认: http://localhost:8765)')
    
    args = ap.parse_args()
    
    # ==================== 规范化路径参数 ====================
    
    print("=" * 60)
    print("JP Media Mining (重构版)")
    print("=" * 60)
    
    print("\n🔧 规范化路径参数...")
    
    # 转换所有路径参数
    video_path = safe_path_from_args(args.video)
    subs_path = safe_path_from_args(args.subs)
    words_path = safe_path_from_args(args.words)
    outdir_path = safe_path_from_args(args.outdir)
    csv_path = safe_path_from_args(args.csv)
    
    primary_mdx_path = safe_path_from_args(args.primary_mdx)
    secondary_mdx_path = safe_path_from_args(args.secondary_mdx)
    tertiary_mdx_path = safe_path_from_args(args.tertiary_mdx)
    nhk_old_path = safe_path_from_args(args.nhk_old)
    nhk_new_path = safe_path_from_args(args.nhk_new)
    djs_path = safe_path_from_args(args.djs)
    freq_path = safe_path_from_args(args.freq)
    
    print(f"   ✅ 路径规范化完成")
    
    # 推导词典根目录 (用于查找 DJS_N)
    dicts_dir = None
    if djs_path and djs_path.exists():
        # djs_path 通常是 .../dicts/DJS/DJS.mdx
        # 我们需要获取 .../dicts
        dicts_dir = djs_path.parent.parent
        if not dicts_dir.is_dir():
            dicts_dir = None
    
    # ==================== 初始化 ====================
    
    # 1. 加载 Fugashi 分词器
    print("\n📚 初始化分词器...")
    try:
        tagger = Tagger()
        print("   ✅ Fugashi (UniDic) 已加载")
    except Exception as e:
        print(f"   ❌ Fugashi 初始化失败: {e}")
        return 1
    
    # 2. 加载字幕
    print(f"\n📄 加载字幕: {subs_path.name}")
    try:
        subs = pysubs2.load(str(subs_path))
        print(f"   ✅ 共 {len(subs)} 行字幕")
    except Exception as e:
        print(f"   ❌ 加载失败: {e}")
        return 1
    
    # 3. 加载目标单词
    print(f"\n📝 加载目标单词: {words_path.name}")
    try:
        words = load_words(words_path)
        print(f"   ✅ 共 {len(words)} 个单词")
        if not args.quiet and len(words) <= 100:
            # 显示格式: word, word(reading), word[lookup_form], word(reading)[lookup_form]
            word_list_display = []
            for w, r, l in words[:100]:
                parts = [w]
                if r:
                    parts.append(f"({r})")
                if l:
                    parts.append(f"[{l}]")
                word_list_display.append(''.join(parts))
            print(f"   单词列表: {', '.join(word_list_display)}")
    except Exception as e:
        print(f"   ❌ 加载失败: {e}")
        return 1
    
    # 3.5 提取动漫名和集数信息
    print(f"\n📺 提取媒体信息...")
    anime_name, episode = extract_episode_info(video_path, words_path)
    print(f"   动漫名: {anime_name}")
    print(f"   集数: {episode}")
    
    # 4. 初始化释义查询
    print(f"\n📖 初始化释义查询 (MeaningsLookup)...")
    print(f"   📂 Primary MDX: {primary_mdx_path}")
    print(f"   📂 Secondary MDX: {secondary_mdx_path}")
    print(f"   📂 Tertiary MDX: {tertiary_mdx_path}")
    try:
        meanings_lookup = MeaningsLookup.from_dirs(
            primary_dir=primary_mdx_path,
            secondary_dir=secondary_mdx_path,
            tertiary_dir=tertiary_mdx_path,
            use_jamdict=args.use_jamdict
        )
        if meanings_lookup and meanings_lookup.all_dicts:
            print(f"   ✅ 加载词典: {len(meanings_lookup.all_dicts)} 个")
            
            # 显示各级词典
            if meanings_lookup.primary_dicts:
                print(f"      📘 Primary: {len(meanings_lookup.primary_dicts)} 个")
                for mdx_path, display_name in meanings_lookup.primary_dicts[:3]:
                    print(f"         - {display_name}")
                if len(meanings_lookup.primary_dicts) > 3:
                    print(f"         ... 还有 {len(meanings_lookup.primary_dicts) - 3} 个")
            
            if meanings_lookup.secondary_dicts:
                print(f"      📙 Secondary: {len(meanings_lookup.secondary_dicts)} 个")
                for mdx_path, display_name in meanings_lookup.secondary_dicts[:3]:
                    print(f"         - {display_name}")
                if len(meanings_lookup.secondary_dicts) > 3:
                    print(f"         ... 还有 {len(meanings_lookup.secondary_dicts) - 3} 个")
            
            if meanings_lookup.tertiary_dicts:
                print(f"      📗 Tertiary: {len(meanings_lookup.tertiary_dicts)} 个")
                for mdx_path, display_name in meanings_lookup.tertiary_dicts[:3]:
                    print(f"         - {display_name}")
                if len(meanings_lookup.tertiary_dicts) > 3:
                    print(f"         ... 还有 {len(meanings_lookup.tertiary_dicts) - 3} 个")
        else:
            print(f"   ⚠️  未加载任何词典")
        
        if args.use_jamdict:
            print(f"   ✅ JMDict Fallback: 已启用")
    except Exception as e:
        print(f"   ⚠️  初始化失败: {e}")
        import traceback
        traceback.print_exc()
        meanings_lookup = None
    
    # 5. 初始化音频查询
    print(f"\n🎵 初始化音频查询 (AudioLookup)...")
    try:
        audio_lookup = AudioLookup.from_dirs(
            nhk_old_dir=nhk_old_path,
            nhk_new_dir=nhk_new_path,
            djs_dir=djs_path
        )
        audio_count = len(audio_lookup.audio_dicts) if audio_lookup.audio_dicts else 0
        print(f"   ✅ 音频词典: {audio_count} 个")
        if audio_lookup.pitch_dict:
            print(f"   ✅ 音调词典: {audio_lookup.pitch_dict.name}")
    except Exception as e:
        print(f"   ⚠️  初始化失败: {e}")
        audio_lookup = None
    
    # 6. 加载频率数据
    print(f"\n📊 加载频率数据...")
    try:
        freq_index = FrequencyIndex(freq_path)
        if freq_index.idx:
            print(f"   ✅ 已加载 {len(freq_index.idx)} 条频率数据")
        else:
            print(f"   ℹ️  未加载频率数据")
    except Exception as e:
        print(f"   ⚠️  加载失败: {e}")
        freq_index = FrequencyIndex()
    
    # ==================== 处理 ====================
    
    print("\n" + "=" * 60)
    print("开始处理")
    print("=" * 60)
    
    try:
        cards = find_hits(
            words=words,
            subs=subs,
            tagger=tagger,
            video=video_path,
            outdir=outdir_path,
            meanings_lookup=meanings_lookup,
            audio_lookup=audio_lookup,
            freq_index=freq_index,
            anime_name=anime_name,
            episode=episode,
            dicts_dir=dicts_dir,
            pad=args.pad,
            vf=args.vf,
            verbose=not args.quiet
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        return 1
    except Exception as e:
        print(f"\n\n❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # ==================== 输出 ====================
    
    if not cards:
        print("\n⚠️  未找到任何匹配的单词")
        return 0
    
    print("\n" + "=" * 60)
    print("导出结果")
    print("=" * 60)
    
    # 导出 CSV
    try:
        write_csv(cards, csv_path, outdir_path)
    except Exception as e:
        print(f"\n❌ CSV 导出失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # 推送到 Anki (如果启用)
    if args.anki:
        print("\n" + "=" * 60)
        print("推送到 Anki")
        print("=" * 60)
        
        try:
            # 连接 AnkiConnect
            print(f"\n🔌 连接 AnkiConnect ({args.ankiconnect_url})...")
            anki = AnkiConnect(args.ankiconnect_url)
            
            if not anki.check_connection():
                print("\n⚠️  无法连接到 Anki,跳过推送")
                print("   请确保:")
                print("   1. Anki 正在运行")
                print("   2. 已安装 AnkiConnect 插件 (代码: 2055492159)")
                print("   3. AnkiConnect 设置正确")
            else:
                # 创建牌组
                print(f"\n📚 准备牌组: {args.anki_deck}")
                try:
                    anki.create_deck(args.anki_deck)
                    print(f"   ✅ 牌组已就绪")
                except Exception as e:
                    print(f"   ⚠️  创建牌组失败: {e}")
                
                # 推送卡片
                success, failed = push_to_anki(
                    cards=cards,
                    anki=anki,
                    deck_name=args.anki_deck,
                    model_name=args.anki_model,
                    tags=args.anki_tags,
                    allow_duplicates=args.anki_allow_duplicates,
                    verbose=not args.quiet
                )
                
                print(f"\n📊 推送统计:")
                print(f"   成功: {success} 张")
                print(f"   失败: {failed} 张")
                print(f"   总计: {len(cards)} 张")
                
                if success > 0:
                    print(f"\n✅ 卡片已添加到 Anki 牌组: {args.anki_deck}")
        
        except Exception as e:
            print(f"\n❌ Anki 推送失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ 完成!")
    print("=" * 60)
    print(f"\n📊 统计:")
    print(f"   处理字幕: {len(subs)} 行")
    print(f"   目标单词: {len(words)} 个")
    print(f"   生成卡片: {len(cards)} 张")
    print(f"   输出目录: {outdir_path}")
    print(f"   CSV 文件: {csv_path}")
    if args.anki:
        print(f"   Anki 牌组: {args.anki_deck}")
    
    return 0


if __name__ == '__main__':
    exit(main())
