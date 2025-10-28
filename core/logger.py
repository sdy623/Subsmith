"""
Logger - 日志输出模块

提供统一的日志输出接口，支持详细模式和安静模式
"""

import re
from typing import Optional


class ProcessLogger:
    """处理过程日志记录器"""
    
    def __init__(self, verbose: bool = True, quiet: bool = False):
        """
        初始化日志记录器
        
        Args:
            verbose: 是否显示详细信息
            quiet: 是否安静模式（不输出任何信息）
        """
        self.verbose = verbose
        self.quiet = quiet
    
    def info(self, message: str, indent: int = 0):
        """输出普通信息"""
        if not self.quiet:
            prefix = "   " * indent
            print(f"{prefix}{message}")
    
    def verbose_info(self, message: str, indent: int = 0):
        """输出详细信息（仅在 verbose 模式下）"""
        if self.verbose and not self.quiet:
            prefix = "   " * indent
            print(f"{prefix}{message}")
    
    def warning(self, message: str, indent: int = 0):
        """输出警告信息"""
        if not self.quiet:
            prefix = "   " * indent
            print(f"{prefix}⚠️  {message}")
    
    def error(self, message: str, indent: int = 0):
        """输出错误信息"""
        if not self.quiet:
            prefix = "   " * indent
            print(f"{prefix}❌ {message}")
    
    def success(self, message: str, indent: int = 0):
        """输出成功信息"""
        if not self.quiet:
            prefix = "   " * indent
            print(f"{prefix}✅ {message}")
    
    # === 专门的处理日志方法 ===
    
    def log_subtitle_match(self, idx: int, total: int, matched_words: list, sentence: str):
        """记录字幕匹配"""
        if self.verbose and not self.quiet:
            print(f"[{idx}/{total}] 找到匹配: {', '.join(matched_words)}")
            print(f"         原句: {sentence[:50]}...")
    
    def log_word_query_start(self, word: str):
        """记录单词查询开始"""
        self.verbose_info(f"📝 查询单词: {word}", indent=1)
    
    def log_lemma_form(self, original: str, lemma: str):
        """记录词元形式"""
        if original != lemma:
            self.verbose_info(f"📖 词元形式: {original} → {lemma}", indent=2)
    
    def log_user_lookup_form(self, form: str):
        """记录用户指定的查词形态"""
        self.verbose_info(f"🎯 用户指定查词形态: {form}", indent=2)
    
    def log_forced_reading(self, reading: str):
        """记录强制读音"""
        self.verbose_info(f"🔒 强制读音: {reading}", indent=2)
    
    def log_definition_success(self, definition: str, source: Optional[str] = None):
        """记录释义查询成功"""
        plain_def = re.sub(r'<[^>]+>', '', definition)[:100]
        if source:
            self.verbose_info(f"✅ 释义 ({source}): {plain_def}...", indent=2)
        else:
            self.verbose_info(f"✅ 释义: {plain_def}...", indent=2)
    
    def log_definition_not_found(self):
        """记录未找到释义"""
        self.verbose_info("⚠️  未找到释义", indent=2)
    
    def log_variant_query(self, variant: str, query_type: str = ""):
        """记录使用变体查询"""
        if query_type:
            self.verbose_info(f"🔄 使用变体查询{query_type}: {variant}", indent=2)
        else:
            self.verbose_info(f"🔄 使用变体查询: {variant}", indent=2)
    
    def log_reading_success(self, reading: str, pitch_pos: str, all_count: Optional[int] = None):
        """记录读音查询成功"""
        plain_reading = re.sub(r'<[^>]+>', '', reading)
        self.verbose_info(f"🎵 读音: {plain_reading} [{pitch_pos}]", indent=2)
        if all_count and all_count > 1:
            self.verbose_info(f"📋 共 {all_count} 个候选读音", indent=2)
    
    def log_reading_not_found(self):
        """记录未找到读音"""
        self.verbose_info("⚠️  未找到音频/音调", indent=2)
    
    def log_frequency_success(self, freq_str: str, freq_rank: float):
        """记录频率查询成功"""
        self.verbose_info(f"📊 频率: {freq_str} (排序值: {freq_rank})", indent=2)
    
    def log_frequency_not_found(self):
        """记录未找到频率"""
        self.verbose_info("⚠️  未找到频率数据", indent=2)
    
    def log_pitch_type(self, pitch_type: str):
        """记录音调类型"""
        self.verbose_info(f"🎼 声调类型: {pitch_type}", indent=2)
    
    def log_media_encoding(self):
        """记录媒体编码"""
        self.verbose_info("📦 编码媒体文件...", indent=2)
    
    def log_word_audio_success(self, source: str):
        """记录单词音频成功"""
        self.verbose_info(f"✅ 单词音频: {source}", indent=3)
    
    def log_media_processing_error(self, error: Exception):
        """记录媒体处理错误"""
        self.warning(f"媒体处理失败: {error}", indent=1)
    
    def log_query_error(self, query_type: str, error: Exception):
        """记录查询错误"""
        self.verbose_info(f"⚠️  {query_type}查询失败: {error}", indent=2)
    
    def log_processing_summary(self, word_count: int, subtitle_count: int):
        """记录处理摘要"""
        if not self.quiet:
            print(f"\n🔍 开始处理字幕...")
            print(f"   目标单词: {word_count} 个")
            print(f"   字幕行数: {subtitle_count} 行\n")
