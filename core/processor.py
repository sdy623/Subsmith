"""
Main processing module - 核心处理逻辑
"""

import json
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import asdict

try:
    import pandas as pd
except ImportError:
    pd = None

from .config import Config
from .card_data import CardData
from .media_handler import MediaHandler
from .subtitle_handler import SubtitleHandler
from .word_processor import WordProcessor
from .frequency import FrequencyIndex
from .csv_exporter import CSVExporter
from .anki_pusher import AnkiPusher
from .logger import ProcessLogger

from mdx_utils import MeaningsLookup, AudioLookup, get_all_audio_info_from_mdx


class MiningProcessor:
    """主处理器 - 协调所有模块完成挖矿任务"""
    
    def __init__(self, config: Config):
        self.config = config
        self.word_processor = WordProcessor()
        self.media_handler = MediaHandler()
        self.subtitle_handler = SubtitleHandler()
        self.logger = ProcessLogger(verbose=not config.quiet, quiet=config.quiet)
        
        # 初始化词典查询
        self.meanings_lookup = None
        self.audio_lookup = None
        self.freq_index = FrequencyIndex()
        
    def initialize(self) -> bool:
        """初始化所有模块"""
        print("\n" + "=" * 60)
        print("JP Media Mining (模块化版本)")
        print("=" * 60)
        
        # 验证配置
        errors = self.config.validate()
        if errors:
            print("\n❌ 配置错误:")
            for err in errors:
                print(f"   - {err}")
            return False
        
        # 加载释义查询
        if self.config.primary_mdx or self.config.secondary_mdx or self.config.tertiary_mdx:
            print("\n📖 初始化释义查询...")
            self.meanings_lookup = MeaningsLookup.from_dirs(
                primary_dir=self.config.primary_mdx,
                secondary_dir=self.config.secondary_mdx,
                tertiary_dir=self.config.tertiary_mdx,
                use_jamdict=self.config.use_jamdict
            )
            if self.meanings_lookup and self.meanings_lookup.all_dicts:
                print(f"   ✅ 加载词典: {len(self.meanings_lookup.all_dicts)} 个")
        
        # 加载音频查询
        if self.config.nhk_old or self.config.nhk_new or self.config.djs:
            print("\n🎵 初始化音频查询...")
            self.audio_lookup = AudioLookup.from_dirs(
                nhk_old_dir=self.config.nhk_old,
                nhk_new_dir=self.config.nhk_new,
                djs_dir=self.config.djs
            )
            audio_count = len(self.audio_lookup.audio_dicts) if self.audio_lookup and self.audio_lookup.audio_dicts else 0
            print(f"   ✅ 音频词典: {audio_count} 个")
        
        # 加载频率数据
        if self.config.freq:
            print("\n📊 加载频率数据...")
            self.freq_index = FrequencyIndex(self.config.freq)
            if self.freq_index.idx:
                print(f"   ✅ 已加载 {len(self.freq_index.idx)} 条频率数据")
        
        print("\n✅ 初始化完成\n")
        return True
    
    def process(self) -> List[CardData]:
        """执行挖矿处理流程"""
        # 加载字幕
        print(f"📄 加载字幕: {self.config.subs.name}")
        subs = self.subtitle_handler.load_subs(self.config.subs)
        print(f"   ✅ 共 {len(subs)} 行字幕")
        
        # 加载单词
        print(f"\n📝 加载目标单词: {self.config.words.name}")
        words = self.word_processor.load_words(self.config.words)
        print(f"   ✅ 共 {len(words)} 个单词")
        
        # 提取媒体信息
        print(f"\n📺 提取媒体信息...")
        anime_name, episode = self.subtitle_handler.extract_episode_info(
            self.config.video, self.config.words
        )
        print(f"   动漫名: {anime_name}")
        print(f"   集数: {episode}")
        
        # 查找匹配
        print(f"\n🔍 开始处理字幕...")
        cards = self._find_hits(
            words=words,
            subs=subs,
            video=self.config.video,
            outdir=self.config.outdir,
            anime_name=anime_name,
            episode=episode,
            pad=self.config.pad,
            vf=self.config.vf,
            verbose=not self.config.quiet
        )
        
        print(f"\n✅ 处理完成! 共生成 {len(cards)} 张卡片")
        return cards
    
    def _find_hits(
        self,
        words: List[tuple],
        subs,
        video: Path,
        outdir: Path,
        anime_name: str,
        episode: str,
        pad: float,
        vf: Optional[str],
        verbose: bool
    ) -> List[CardData]:
        """查找字幕中的目标单词并生成卡片数据"""
        MediaHandler.ensure_dir(outdir)
        cards: List[CardData] = []
        
        word_to_reading = {word: reading for word, reading, _ in words}
        word_to_lookup_form = {word: lookup_form for word, _, lookup_form in words}
        wset = set(word_to_reading.keys())
        
        # 输出处理摘要
        self.logger.log_processing_summary(len(words), len(subs))
        
        for idx, line in enumerate(subs, 1):
            sent = self.subtitle_handler.normalize_sub_text(line.text)
            if not sent:
                continue
            
            # 分词并检查匹配
            lemmas = self.word_processor.lemmatize(sent)
            tokens_set = set(lemmas)
            
            matched_by_lemma = wset.intersection(tokens_set)
            matched_by_string = {word for word, _, _ in words if word in sent}
            matched = matched_by_lemma | matched_by_string
            
            if not matched:
                continue
            
            # 记录字幕匹配
            self.logger.log_subtitle_match(idx, len(subs), list(matched), sent)
            
            # 生成带假名的句子
            furig = self.word_processor.tokens_furigana(sent)
            
            # 计算时间和生成媒体
            start = max(0.0, MediaHandler.ms_to_s(line.start) - pad)
            end = MediaHandler.ms_to_s(line.end) + pad
            mid = (start + end) / 2
            
            base = f"{video.stem}_{int(line.start)}_{int(line.end)}"
            img_path = outdir / f"{base}.jpg"
            aud_path = outdir / f"{base}.m4a"
            
            try:
                MediaHandler.screenshot(video, mid, img_path, vf)
                MediaHandler.cut_audio(video, start, end, aud_path)
            except Exception as e:
                self.logger.log_media_processing_error(e)
                continue
            
            # 为每个匹配的单词创建卡片
            for word in matched:
                card = self._create_card(
                    word=word,
                    sent=sent,
                    furig=furig,
                    start=start,
                    end=end,
                    img_path=img_path,
                    aud_path=aud_path,
                    word_to_reading=word_to_reading,
                    word_to_lookup_form=word_to_lookup_form,
                    anime_name=anime_name,
                    episode=episode,
                    verbose=verbose
                )
                if card:
                    cards.append(card)
        
        return cards
    
    def _create_card(
        self,
        word: str,
        sent: str,
        furig: str,
        start: float,
        end: float,
        img_path: Path,
        aud_path: Path,
        word_to_reading: dict,
        word_to_lookup_form: dict,
        anime_name: str,
        episode: str,
        verbose: bool
    ) -> Optional[CardData]:
        """创建单张卡片"""
        # 记录查询开始
        self.logger.log_word_query_start(word)
        
        # 获取词元
        word_lemma_parts = []
        for t in self.word_processor.tagger(word):
            part_lemma = None
            if hasattr(t.feature, 'lemma') and t.feature.lemma:
                part_lemma = t.feature.lemma
            elif hasattr(t, 'feature') and len(t.feature) > 6 and t.feature[6]:
                part_lemma = t.feature[6]
            else:
                part_lemma = t.surface
            if part_lemma:
                word_lemma_parts.append(part_lemma)
        
        word_lemma = ''.join(word_lemma_parts) if word_lemma_parts else word
        
        # 记录词元形式
        self.logger.log_lemma_form(word, word_lemma)
        
        # 检查用户指定查词形态
        user_lookup_form = word_to_lookup_form.get(word)
        if user_lookup_form:
            self.logger.log_user_lookup_form(user_lookup_form)
            word_lemma = user_lookup_form
        
        # 准备查询候选词
        is_original_katakana = WordProcessor.is_all_katakana(word)
        query_candidates = []
        
        if is_original_katakana and not user_lookup_form:
            query_candidates.append(word)
            if word_lemma != word:
                query_candidates.append(word_lemma)
        else:
            query_candidates.append(word_lemma)
            if word_lemma != word:
                query_candidates.append(word)
        
        if word_lemma.endswith('く'):
            query_candidates.append(word_lemma[:-1] + 'き')
        
        # 检查强制读音
        forced_reading = word_to_reading.get(word)
        if forced_reading:
            self.logger.log_forced_reading(forced_reading)
        
        # 1. 查询释义
        definition = ""
        successful_query_form = word
        
        if self.meanings_lookup:
            try:
                if forced_reading:
                    definition = self.meanings_lookup.lookup(forced_reading)
                    if definition:
                        self.logger.log_definition_success(definition, "假名查询")
                    else:
                        # Fallback 到词元查询
                        definition = self.meanings_lookup.lookup(word_lemma)
                        if definition:
                            successful_query_form = word_lemma
                            self.logger.log_definition_success(definition, "词元查询")
                else:
                    for idx, candidate in enumerate(query_candidates):
                        definition = self.meanings_lookup.lookup(candidate)
                        if definition:
                            successful_query_form = candidate
                            if idx > 0:  # 不是第一个候选词
                                self.logger.log_variant_query(candidate)
                            self.logger.log_definition_success(definition)
                            break
                
                if not definition:
                    self.logger.log_definition_not_found()
            except Exception as e:
                self.logger.log_query_error("释义", e)
        
        # 2. 查询音频和音调
        reading = ''
        pitch_pos = ''
        pitch_src = ''
        audio_src = ''
        all_readings_json = ''
        word_audio_b64 = ""
        audio_result = None
        
        if self.audio_lookup:
            try:
                if forced_reading:
                    audio_result = self.audio_lookup.lookup(forced_reading, verbose=False, return_all_pitches=True)
                else:
                    for idx, candidate in enumerate(query_candidates):
                        audio_result = self.audio_lookup.lookup(candidate, verbose=False, return_all_pitches=True)
                        if audio_result and audio_result.get('reading'):
                            if idx > 0:
                                self.logger.log_variant_query(candidate, "音频")
                            break
                
                if audio_result:
                    reading = audio_result.get('reading', '') or ''
                    pitch_pos = audio_result.get('pitch_position', '') or ''
                    pitch_src = audio_result.get('pitch_source', '') or ''
                    audio_src = audio_result.get('audio_source', '') or ''
                    
                    all_pitches = audio_result.get('all_pitches', [])
                    all_readings_json = json.dumps(
                        [{'reading': r, 'pitch_position': p} for r, p in all_pitches],
                        ensure_ascii=False
                    ) if all_pitches else ''
                    
                    if reading:
                        all_count = len(all_pitches) if all_pitches and len(all_pitches) > 1 else None
                        self.logger.log_reading_success(reading, pitch_pos, all_count)
                    
                    if audio_result.get('audio_base64'):
                        audio_b64 = audio_result['audio_base64']
                        audio_mime = audio_result.get('audio_mime', 'audio/mpeg')
                        word_audio_b64 = f"data:{audio_mime};base64,{audio_b64}"
                        self.logger.log_word_audio_success(audio_src)
                else:
                    self.logger.log_reading_not_found()
            except Exception as e:
                self.logger.log_query_error("音频", e)
        
        # 3. 查询频率
        freq_str, freq_rank = None, None
        for idx, candidate in enumerate(query_candidates):
            freq_str, freq_rank = self.freq_index.lookup(candidate)
            if freq_str:
                if idx > 0:
                    self.logger.log_variant_query(candidate, "频率")
                self.logger.log_frequency_success(freq_str, freq_rank)
                break
        
        if not freq_str:
            self.logger.log_frequency_not_found()
        
        # 4. 音调类型
        pitch_type = self._pitch_position_to_type(pitch_pos, reading)
        if pitch_type:
            self.logger.log_pitch_type(pitch_type)
        
        # 5. Base64 编码媒体
        self.logger.log_media_encoding()
        sentence_audio_b64 = MediaHandler.file_to_base64(aud_path)
        picture_b64 = MediaHandler.file_to_base64(img_path)
        
        return CardData(
            word=successful_query_form,
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
            lemma=word_lemma,
            all_readings=all_readings_json
        )
    
    @staticmethod
    def _pitch_position_to_type(pitch_position: str, reading: str = "") -> str:
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
                mora_count = len(clean_reading)  # 简化处理
                if mora_count > 0 and pos == mora_count:
                    return "尾高型"
            return "中高型"
