"""
MDX Dictionary Query Utilities
提供 MDX 词典查询、格式化和音频/音调提取功能
"""

from .yomitan_formatter import (
    query_word_yomitan_format,
    query_multiple_dicts_yomitan,
    add_css_namespace,
)

from .meanings_lookup import MeaningsLookup

from .audio_lookup import (
    AudioLookup,
    extract_audio_from_mdx,
    extract_pitch_info_nhk_old,
    get_all_audio_info_from_mdx,
    get_word_reading_with_fugashi,
    match_best_pitch,
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
    'get_all_audio_info_from_mdx',
    'get_word_reading_with_fugashi',
    'match_best_pitch',
]
