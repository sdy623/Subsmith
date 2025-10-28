"""
Configuration module for Subsmith
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List


@dataclass
class Config:
    """配置类 - 所有参数的集中管理"""
    
    # 必需参数
    video: Path
    subs: Path
    words: Path
    outdir: Path
    csv: Path
    
    # 词典路径
    primary_mdx: Optional[Path] = None
    secondary_mdx: Optional[Path] = None
    tertiary_mdx: Optional[Path] = None
    nhk_old: Optional[Path] = None
    nhk_new: Optional[Path] = None
    djs: Optional[Path] = None
    
    # 频率数据
    freq: Optional[Path] = None
    
    # 媒体处理选项
    pad: float = 0.0
    vf: Optional[str] = None
    
    # 输出选项
    quiet: bool = False
    
    # Anki 选项
    anki: bool = False
    anki_deck: str = "Japanese::Anime"
    anki_model: str = "Senren"
    anki_tags: List[str] = field(default_factory=lambda: ['anime', 'mining'])
    anki_allow_duplicates: bool = False
    ankiconnect_url: str = "http://localhost:8765"
    
    # JMDict fallback
    use_jamdict: bool = False
    
    @classmethod
    def from_args(cls, args):
        """从 argparse 参数创建配置"""
        return cls(
            video=Path(args.video),
            subs=Path(args.subs),
            words=Path(args.words),
            outdir=Path(args.outdir),
            csv=Path(args.csv),
            primary_mdx=Path(args.primary_mdx) if args.primary_mdx else None,
            secondary_mdx=Path(args.secondary_mdx) if args.secondary_mdx else None,
            tertiary_mdx=Path(args.tertiary_mdx) if args.tertiary_mdx else None,
            nhk_old=Path(args.nhk_old) if args.nhk_old else None,
            nhk_new=Path(args.nhk_new) if args.nhk_new else None,
            djs=Path(args.djs) if args.djs else None,
            freq=Path(args.freq) if args.freq else None,
            pad=args.pad,
            vf=args.vf,
            quiet=args.quiet,
            anki=args.anki,
            anki_deck=args.anki_deck,
            anki_model=args.anki_model,
            anki_tags=args.anki_tags,
            anki_allow_duplicates=args.anki_allow_duplicates,
            ankiconnect_url=args.ankiconnect_url,
            use_jamdict=args.use_jamdict,
        )
    
    def validate(self) -> List[str]:
        """验证配置，返回错误列表"""
        errors = []
        
        # 检查必需文件
        if not self.video.exists():
            errors.append(f"视频文件不存在: {self.video}")
        if not self.subs.exists():
            errors.append(f"字幕文件不存在: {self.subs}")
        if not self.words.exists():
            errors.append(f"单词列表不存在: {self.words}")
        
        # 检查词典目录
        if self.primary_mdx and not self.primary_mdx.exists():
            errors.append(f"Primary 词典不存在: {self.primary_mdx}")
        if self.nhk_old and not self.nhk_old.exists():
            errors.append(f"NHK 旧版词典不存在: {self.nhk_old}")
        if self.nhk_new and not self.nhk_new.exists():
            errors.append(f"NHK 新版词典不存在: {self.nhk_new}")
        if self.djs and not self.djs.exists():
            errors.append(f"大辞泉词典不存在: {self.djs}")
        
        # 检查频率文件
        if self.freq and not self.freq.exists():
            errors.append(f"频率数据不存在: {self.freq}")
        
        return errors
