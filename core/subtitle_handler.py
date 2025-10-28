"""
Subtitle handling module
"""

import re
from pathlib import Path
from typing import Tuple
import pysubs2


class SubtitleHandler:
    """字幕处理器"""
    
    @staticmethod
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
    
    @staticmethod
    def extract_episode_info(video_path: Path, words_path: Path) -> Tuple[str, str]:
        """从文件名提取动漫名和集数信息
        
        Returns:
            (anime_name, episode): 动漫名和集数 (如 "鬼灭之刃", "S01E05")
        """
        video_stem = video_path.stem
        words_stem = words_path.stem
        
        # 尝试多种格式匹配集数
        episode_code = None
        
        # 1. 匹配 Sx_Ex 格式
        episode_match = re.search(r'S(\d+)_E(\d+)', words_stem, re.IGNORECASE)
        if episode_match:
            season = episode_match.group(1)
            episode = episode_match.group(2)
            episode_code = f"S{season.zfill(2)}E{episode.zfill(2)}"
        
        # 2. 匹配 SxEx 格式
        if not episode_code:
            episode_match = re.search(r'S(\d+)E(\d+)', words_stem, re.IGNORECASE)
            if episode_match:
                season = episode_match.group(1)
                episode = episode_match.group(2)
                episode_code = f"S{season.zfill(2)}E{episode.zfill(2)}"
        
        # 3. 匹配 Ep01 格式
        if not episode_code:
            ep_match = re.search(r'Ep(\d+)', words_stem, re.IGNORECASE)
            if ep_match:
                episode_code = f"S01E{ep_match.group(1).zfill(2)}"
        
        # 4. 从视频文件名提取
        if not episode_code:
            video_episode_match = re.search(r'S(\d+)E(\d+)', video_stem, re.IGNORECASE)
            if video_episode_match:
                season = video_episode_match.group(1)
                episode = video_episode_match.group(2)
                episode_code = f"S{season.zfill(2)}E{episode.zfill(2)}"
            else:
                bracket_match = re.search(r'\[(\d{1,2})\]', video_stem)
                if bracket_match:
                    episode_code = f"S01E{bracket_match.group(1).zfill(2)}"
                else:
                    episode_code = "S01E01"
        
        # 提取动漫名
        anime_name = re.sub(r'\[[^\]]*\]', '', video_stem)
        anime_name = re.sub(r'[_\s]*S\d+E\d+.*', '', anime_name, flags=re.IGNORECASE)
        anime_name = re.sub(r'[_\s]*Ep\d+.*', '', anime_name, flags=re.IGNORECASE)
        anime_name = anime_name.replace('_', ' ').strip()
        anime_name = re.sub(r'\s+', ' ', anime_name)
        
        if not anime_name:
            anime_name = video_stem
        
        return anime_name, episode_code
    
    @staticmethod
    def load_subs(path: Path) -> pysubs2.SSAFile:
        """加载字幕文件"""
        return pysubs2.load(str(path))
