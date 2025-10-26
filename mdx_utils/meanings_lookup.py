"""
Meanings Lookup Module - Yomitan Format
为 jp_media_mining 提供支持 Yomitan 格式的词典查询功能
"""

from pathlib import Path
from typing import Optional, List, Dict, Tuple

from .yomitan_formatter import query_multiple_dicts_yomitan

# 可选依赖
try:
    from jamdict import Jamdict
    JAMDICT = Jamdict()
except ImportError:
    JAMDICT = None


def _collect_mdx_paths(dir_or_file: Optional[Path]) -> List[Path]:
    """收集 MDX 文件路径
    
    Args:
        dir_or_file: 目录路径或单个 MDX 文件路径
        
    Returns:
        MDX 文件路径列表
    """
    if dir_or_file is None:
        return []
    
    p = Path(dir_or_file)
    
    if not p.exists():
        return []
    
    if p.is_file() and p.suffix.lower() == '.mdx':
        return [p]
    
    if p.is_dir():
        return sorted(p.glob("*.mdx"))
    
    return []


class MeaningsLookup:
    """词典查询类 - 支持 Yomitan 格式输出(分级查询)
    
    支持三级词典查询:
    1. Primary: 主词典(联合查询所有)
    2. Secondary: 次词典(仅当 Primary 无结果时查询)
    3. Tertiary: 第三级词典(仅当 Secondary 无结果时查询)
    4. JMDict: 最后的 fallback
    
    Attributes:
        all_dicts: 所有词典的 [(Path, 显示名称)] 列表
        primary_dicts: 主词典列表
        secondary_dicts: 次词典列表
        tertiary_dicts: 第三级词典列表
        use_jamdict: 是否启用 JMDict fallback
        
    Example:
        >>> # 使用目录初始化(自动扫描 .mdx 文件)
        >>> lookup = MeaningsLookup.from_dirs(
        ...     primary_dir=Path("dicts/primary"),
        ...     secondary_dir=Path("dicts/secondary"),
        ...     tertiary_dir=Path("dicts/tertiary"),
        ...     dict_names={
        ...         "DJS.mdx": "大辞泉 第二版",
        ...         "meikyou.mdx": "明鏡日汉双解辞典",
        ...     }
        ... )
        >>> 
        >>> # 查询单词(分级查询)
        >>> html = lookup.lookup("政権")
        >>> # 返回第一个有结果的级别的 Yomitan 格式 HTML
    """
    
    def __init__(
        self, 
        mdx_list: List[Tuple[Path, str]] = None,
        primary_dicts: List[Tuple[Path, str]] = None,
        secondary_dicts: List[Tuple[Path, str]] = None,
        tertiary_dicts: List[Tuple[Path, str]] = None,
        use_jamdict: bool = True
    ):
        """初始化词典查询器
        
        Args:
            mdx_list: [(mdx_path, 显示名称), ...] 词典列表 (兼容旧版本,作为 primary)
            primary_dicts: 主词典列表
            secondary_dicts: 次词典列表
            tertiary_dicts: 第三级词典列表
            use_jamdict: 是否启用 JMDict fallback(默认 True)
        """
        # 兼容旧版本: mdx_list 作为 primary_dicts
        if mdx_list and not primary_dicts:
            primary_dicts = mdx_list
        
        self.primary_dicts = primary_dicts or []
        self.secondary_dicts = secondary_dicts or []
        self.tertiary_dicts = tertiary_dicts or []
        self.all_dicts = self.primary_dicts + self.secondary_dicts + self.tertiary_dicts
        self.use_jamdict = use_jamdict
    
    @classmethod
    def from_dirs(
        cls,
        primary_dir: Optional[Path] = None,
        secondary_dir: Optional[Path] = None,
        tertiary_dir: Optional[Path] = None,
        dict_names: Optional[Dict[str, str]] = None,
        use_jamdict: bool = True
    ) -> "MeaningsLookup":
        """从目录初始化词典查询器(推荐方式)
        
        Args:
            primary_dir: 主词典目录(或单个 .mdx 文件)
            secondary_dir: 次词典目录(或单个 .mdx 文件)
            tertiary_dir: 第三级词典目录(或单个 .mdx 文件)
            dict_names: {文件名: 显示名称} 映射字典(可选)
            use_jamdict: 是否启用 JMDict fallback(默认 True)
            
        Returns:
            MeaningsLookup 实例
            
        Example:
            >>> lookup = MeaningsLookup.from_dirs(
            ...     primary_dir=Path("dicts/primary"),
            ...     secondary_dir=Path("dicts/secondary"),
            ...     tertiary_dir=Path("dicts/tertiary"),
            ...     dict_names={
            ...         "DJS.mdx": "大辞泉 第二版",
            ...         "日汉双解词典_20231101.mdx": "明鏡日汉双解辞典",
            ...     }
            ... )
        """
        # 收集所有 MDX 文件
        primary_mdxs = _collect_mdx_paths(primary_dir)
        secondary_mdxs = _collect_mdx_paths(secondary_dir)
        tertiary_mdxs = _collect_mdx_paths(tertiary_dir)
        
        # 构建分级词典列表
        def build_dict_list(mdxs):
            result = []
            for mdx_file in mdxs:
                if dict_names and mdx_file.name in dict_names:
                    display_name = dict_names[mdx_file.name]
                else:
                    display_name = mdx_file.stem
                result.append((mdx_file, display_name))
            return result
        
        primary_list = build_dict_list(primary_mdxs)
        secondary_list = build_dict_list(secondary_mdxs)
        tertiary_list = build_dict_list(tertiary_mdxs)
        
        return cls(
            primary_dicts=primary_list,
            secondary_dicts=secondary_list,
            tertiary_dicts=tertiary_list,
            use_jamdict=use_jamdict
        )
    
    def lookup(self, query: str, fallback_to_jamdict: Optional[bool] = None) -> str:
        """查询单词并返回 Yomitan 格式的 HTML(整合查询)
        
        **整合查询策略**:
        1. 联合查询 Primary + Secondary 词典(全部整合到一个结果)
        2. 如果 Primary + Secondary 都无结果,查询 Tertiary 词典
        3. 如果都没找到,fallback 到 JMDict(如果启用)
        
        Args:
            query: 要查询的单词
            fallback_to_jamdict: 是否使用 JMDict fallback,None 时使用初始化设置
            
        Returns:
            Yomitan 格式的 HTML 字符串,未找到时返回空字符串
            
        Example:
            >>> html = lookup.lookup("政権")
            >>> # 返回整合了 Primary + Secondary 的 Yomitan 格式 HTML
            >>> if html:
            ...     note_fields["definition"] = html
        """
        # 确定是否使用 JMDict fallback
        use_jmd = fallback_to_jamdict if fallback_to_jamdict is not None else self.use_jamdict
        
        # 1. 联合查询 Primary + Secondary 词典(整合结果)
        combined_dicts = self.primary_dicts + self.secondary_dicts
        if combined_dicts:
            html = query_multiple_dicts_yomitan(combined_dicts, query)
            if html:
                return html
        
        # 2. 如果 Primary + Secondary 都无结果,查询 Tertiary 词典
        if self.tertiary_dicts:
            html = query_multiple_dicts_yomitan(self.tertiary_dicts, query)
            if html:
                return html
        
        # 4. Fallback 到 JMDict（如果启用且可用）
        if use_jmd and JAMDICT is not None:
            try:
                res = JAMDICT.lookup(query)
                parts = []
                for e in res.entries[:3]:  # 最多3条
                    glosses = "; ".join(g.text for g in e.gloss)
                    kanji = ", ".join(k.text for k in e.kana) or ", ".join(k.text for k in e.kanji)
                    parts.append(f"<div class='entry'><b>{kanji}</b>: {glosses}</div>")
                if parts:
                    # JMDict 也包装成 Yomitan 格式（无 CSS）
                    jmdict_html = "\n".join(parts)
                    return f'<div style="text-align: left;" class="yomitan-glossary"><ol><li data-dictionary="JMDict"><i>(JMDict)</i> <span>{jmdict_html}</span></li></ol></div>'
            except Exception:
                pass
        
        # 3. 未找到任何结果
        return ""
