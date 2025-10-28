"""
Card data model
"""

from dataclasses import dataclass


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
    
    # 额外信息
    lemma: str                   # 词元
    all_readings: str            # 所有候选读音 (JSON)
