"""
Anki pusher module - Anki 推送模块
"""

import json
import re
from typing import List, Tuple, Dict, Any
from datetime import timedelta
import requests

from .card_data import CardData
from .config import Config


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


def is_all_katakana(text: str) -> bool:
    """检查是否全部为片假名"""
    if not text:
        return False
    return all('\u30A0' <= c <= '\u30FF' or c in 'ー・' for c in text if c.strip())


def katakana_to_hiragana(text: str) -> str:
    """片假名转平假名"""
    result = []
    for c in text:
        if '\u30A1' <= c <= '\u30F6':  # 片假名范围
            result.append(chr(ord(c) - 0x60))
        else:
            result.append(c)
    return ''.join(result)


def expand_long_vowel(text: str) -> str:
    """
    展开长音符ー
    
    规则:
    - お段 + ー → う (こー → こう)
    - え段 + ー → い (せー → せい)
    """
    result = []
    prev_char = None
    
    for c in text:
        if c == 'ー' and prev_char:
            # 获取前一个字符的段
            if prev_char in 'おこそとのほもよろをごぞどぼぽ':  # お段
                result.append('う')
            elif prev_char in 'えけせてねへめれげぜでべぺ':  # え段
                result.append('い')
            else:
                result.append(c)  # 保持原样
        else:
            result.append(c)
        prev_char = c if c != 'ー' else prev_char
    
    return ''.join(result)


def generate_pitch_html(reading: str, pitch_num: int, pitch_type: str) -> str:
    """
    生成带音调标记的 HTML (Yomitan 风格)
    
    Args:
        reading: 假名读音 (如 "ほたる", "せいれい")
        pitch_num: 音调位置数字 (如 0, 1, 2, 3)
        pitch_type: 音调类型 ("平板式", "頭高型", "中高型", "尾高型")
    
    Returns:
        HTML 字符串,包含音调标记和对应颜色
    
    颜色规则:
    - 頭高型 (1型): 红色 (#f54360)
    - 平板式 (0型): 蓝色 (#39c1ff)
    - 中高型: 橙色 (#fca311)
    - 尾高型: 青绿色 (#40D4A6)
    """
    if not reading:
        return ""
    
    # 确定颜色
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
            color = "#afa2ff"  # 默认紫色
    
    # 拆分假名为单个字符
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
        
        if pitch_num == 0:
            # 平板式: 第一拍无线,第二拍开始有上划线
            if mora_index > 1:
                has_overline = True
        elif pitch_num == 1:
            # 頭高型: 第一拍有上划线+下降标记,后续无线
            if mora_index == 1:
                has_overline = True
                has_drop = True
        else:
            # 中高型/尾高型: 第二拍到下降位置有上划线,下降位置有标记
            if 2 <= mora_index <= pitch_num:
                has_overline = True
                if mora_index == pitch_num:
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


def pitch_position_to_type(pitch_position: str, reading: str = "") -> str:
    """将音调位置转换为类型名称"""
    if not pitch_position:
        return ""
    match = re.search(r'\[(\d+)\]', pitch_position)
    if not match:
        return ""
    pos = int(match.group(1))
    
    if pos == 0:
        return "平板式"
    elif pos == 1:
        return "頭高型"
    else:
        if reading:
            clean_reading = re.sub(r'<[^>]+>', '', reading)
            mora_count = len(clean_reading)
            if mora_count > 0 and pos == mora_count:
                return "尾高型"
        return "中高型"


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


class AnkiPusher:
    """Anki 推送器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.anki = AnkiConnect(config.ankiconnect_url)
    
    def push(self, cards: List[CardData]) -> Tuple[int, int]:
        """推送卡片到 Anki"""
        print(f"\n🚀 开始推送到 Anki...")
        print(f"   牌组: {self.config.anki_deck}")
        print(f"   笔记类型: {self.config.anki_model}")
        print(f"   标签: {', '.join(self.config.anki_tags)}")
        print(f"   卡片数: {len(cards)}")
        print()
        
        if not self.anki.check_connection():
            return 0, len(cards)
        
        # 创建牌组（如果不存在）
        try:
            self.anki.create_deck(self.config.anki_deck)
        except Exception as e:
            print(f"   ⚠️  创建牌组失败: {e}")
        
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
                        if card.picture_base64.startswith('data:'):
                            _, b64_data = card.picture_base64.split(';base64,', 1)
                        else:
                            b64_data = card.picture_base64
                        
                        picture_filename = f"{word}_{card_index}_pic.jpg"
                        self.anki.store_media_file(picture_filename, b64_data)
                    except Exception as e:
                        if not self.config.quiet:
                            print(f"   ⚠️  [{idx}/{len(cards)}] {word}: 图片上传失败: {e}")
                
                # 单词音频
                if card.word_audio_base64:
                    try:
                        if card.word_audio_base64.startswith('data:'):
                            header, b64_data = card.word_audio_base64.split(';base64,', 1)
                            mime = header.split(':')[1]
                            ext = 'mp3' if 'mpeg' in mime else 'aac' if 'aac' in mime else 'mp3'
                        else:
                            b64_data = card.word_audio_base64
                            ext = 'mp3'
                        
                        word_audio_filename = f"{word}_{card_index}_word.{ext}"
                        self.anki.store_media_file(word_audio_filename, b64_data)
                    except Exception as e:
                        if not self.config.quiet:
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
                        self.anki.store_media_file(sentence_audio_filename, b64_data)
                    except Exception as e:
                        if not self.config.quiet:
                            print(f"   ⚠️  [{idx}/{len(cards)}] {word}: 句子音频上传失败: {e}")
                
                # 2. 准备字段
                # 高亮单词
                sentence_html = card.sentence
                if word in sentence_html:
                    sentence_html = sentence_html.replace(word, f'<span class="highlight">{word}</span>')
                
                # 读音格式化为 HTML 列表
                reading_html = ''
                if card.reading:
                    all_readings = []
                    if card.all_readings:
                        try:
                            readings_list = json.loads(card.all_readings)
                            all_readings = readings_list
                        except:
                            all_readings = [{'reading': card.reading, 'pitch_position': card.pitch_position}]
                    else:
                        all_readings = [{'reading': card.reading, 'pitch_position': card.pitch_position}]
                    
                    reading_html = '<ol>'
                    for r_info in all_readings:
                        if isinstance(r_info, dict):
                            r_reading = r_info.get('reading', '')
                            r_pitch = r_info.get('pitch_position', '')
                        else:
                            r_reading = str(r_info)
                            r_pitch = card.pitch_position
                        
                        clean_reading = re.sub(r'<[^>]+>', '', r_reading)
                        
                        # 处理长音符
                        if is_all_katakana(word):
                            pass  # 保持原样
                        else:
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
                            r_pitch_type = pitch_position_to_type(f"[{pitch_num}]", clean_reading)
                            pitch_html = generate_pitch_html(clean_reading, pitch_num, r_pitch_type)
                            reading_html += f'<li>{pitch_html}</li>'
                        else:
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
                    'deckName': self.config.anki_deck,
                    'modelName': self.config.anki_model,
                    'fields': fields,
                    'tags': self.config.anki_tags,
                    'options': {
                        'allowDuplicate': self.config.anki_allow_duplicates,
                        'duplicateScope': 'collection'
                    }
                }
                
                # 4. 添加到 Anki
                note_id = self.anki.add_note(note)
                
                if not self.config.quiet:
                    print(f"   ✅ [{idx}/{len(cards)}] {word} (ID: {note_id})")
                
                success_count += 1
                
            except Exception as e:
                if not self.config.quiet:
                    print(f"   ❌ [{idx}/{len(cards)}] {word}: {e}")
                error_count += 1
        
        return success_count, error_count

