"""
Audio Lookup Module - 音频和音调信息提取
从多个 MDX 词典中提取音频和音调信息

复用 mdxscraper.core.audio 模块的功能
"""

from pathlib import Path
from typing import Optional, List, Tuple, Dict
from bs4 import BeautifulSoup
import re

from mdxscraper import Dictionary

# 导入 mdxscraper 的音频处理模块
try:
    from mdxscraper.core.audio import (
        AudioInfo,
        get_audio_info,
        extract_audio_paths_from_html,
        lookup_audio,
        embed_audio_in_html,
    )
    AUDIO_MODULE_AVAILABLE = True
except ImportError:
    AUDIO_MODULE_AVAILABLE = False
    AudioInfo = None

# 导入 fugashi 用于获取实际读音
try:
    import fugashi
    FUGASHI_AVAILABLE = True
except ImportError:
    FUGASHI_AVAILABLE = False


def extract_audio_from_mdx(mdx_file: Path, word: str, dict_name: str = None) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """从 MDX 词典中提取音频 (使用 mdxscraper.core.audio)
    
    Args:
        mdx_file: MDX 词典文件路径
        word: 要查询的单词
        dict_name: 词典名称
        
    Returns:
        (audio_base64, mime_type, source_dict) 元组
        - audio_base64: base64 编码的音频数据
        - mime_type: 音频类型 (audio/aac, audio/mpeg, audio/wav 等)
        - source_dict: 来源词典名称
    """
    if type(mdx_file) is not Path:
        mdx_file = Path(mdx_file)
    
    if dict_name is None:
        dict_name = mdx_file.stem
    
    if not AUDIO_MODULE_AVAILABLE:
        return None, None, None
    
    with Dictionary(mdx_file) as dict_obj:
        html_content = dict_obj.lookup_html(word)
        
        if not html_content:
            return None, None, None
        
        # 使用 mdxscraper.core.audio.get_audio_info 提取音频
        try:
            audio_infos = get_audio_info(dict_obj.impl, word, html_content)
            
            if audio_infos and len(audio_infos) > 0:
                # 返回第一个音频文件
                first_audio = audio_infos[0]
                
                # AudioInfo 包含 data_uri: "data:audio/mpeg;base64,..."
                # 解析出 base64 数据
                data_uri = first_audio.data_uri
                if data_uri.startswith('data:'):
                    match = re.match(r'data:([^;]+);base64,(.+)', data_uri)
                    if match:
                        mime_type, audio_base64 = match.groups()
                        return audio_base64, mime_type, dict_name
        
        except Exception:
            pass
        
        return None, None, None


def get_all_audio_info_from_mdx(mdx_file: Path, word: str, dict_name: str = None) -> List:
    """获取词条的所有音频信息 (复用 mdxscraper.core.audio.get_audio_info)
    
    Args:
        mdx_file: MDX 词典文件路径
        word: 要查询的单词
        dict_name: 词典名称
        
    Returns:
        AudioInfo 列表,每个包含:
        - word: 词条
        - audio_path: 音频路径
        - audio_data: 音频二进制数据
        - mime_type: MIME 类型
        - data_uri: base64 data URI
        - format: 文件格式
    """
    if type(mdx_file) is not Path:
        mdx_file = Path(mdx_file)
    
    if dict_name is None:
        dict_name = mdx_file.stem
    
    if not AUDIO_MODULE_AVAILABLE:
        return []
    
    with Dictionary(mdx_file) as dict_obj:
        html_content = dict_obj.lookup_html(word)
        
        if not html_content:
            return []
        
        try:
            # 直接返回 mdxscraper 的 AudioInfo 列表
            audio_infos = get_audio_info(dict_obj.impl, word, html_content)
            return audio_infos
        
        except Exception:
            return []


def get_word_reading_with_fugashi(word: str) -> Optional[str]:
    """使用 fugashi 获取单词的读音
    
    Args:
        word: 日语单词
        
    Returns:
        读音 (片假名),如果无法获取则返回 None
    """
    if not FUGASHI_AVAILABLE:
        return None
    
    try:
        tagger = fugashi.Tagger()
        result = tagger(word)
        
        if not result:
            return None
        
        # 取第一个词的读音
        first_token = result[0]
        
        # 尝试多种方式获取读音
        reading = None
        
        # 方法1: UniDic 的 lForm 字段 (最准确的片假名读音)
        if hasattr(first_token.feature, 'lForm') and first_token.feature.lForm is not None:
            reading = first_token.feature.lForm
        
        # 方法2: UniDic 的 kana 字段 (备选)
        elif hasattr(first_token.feature, 'kana') and first_token.feature.kana is not None:
            reading = first_token.feature.kana
        
        # 方法3: 直接访问 feature 列表 (IPADic)
        # IPADic: [品詞, 品詞細分類1, 品詞細分類2, 品詞細分類3, 活用型, 活用形, 原形, 読み, 発音]
        elif hasattr(first_token, 'feature') and len(first_token.feature) > 7:
            reading = first_token.feature[7]  # 读音字段
        
        # 方法4: 使用 features 属性 (备选)
        elif hasattr(first_token, 'features'):
            features = first_token.features
            if len(features) > 7:
                reading = features[7]
        
        # 如果读音是 "*" 或空,返回 None
        if reading and reading != '*' and reading.strip():
            return reading
        
        return None
        
    except Exception as e:
        # 调试时可以打印错误
        # print(f"Fugashi 错误: {e}")
        return None


def normalize_reading(reading: str) -> str:
    """标准化读音格式用于匹配
    
    移除 HTML 标签,转换为片假名,统一长音符号
    
    Args:
        reading: 读音字符串 (可能包含 HTML)
        
    Returns:
        标准化后的读音
    """
    # 移除 HTML 标签
    plain = re.sub(r'<[^>]+>', '', reading)
    
    # 统一长音符号 (全角)
    plain = plain.replace('ー', 'ー')
    
    # 转换平假名到片假名 (简单映射)
    hiragana_to_katakana = str.maketrans(
        'ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをんゔゕゖ',
        'ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶ'
    )
    plain = plain.translate(hiragana_to_katakana)
    
    return plain.upper()


def match_best_pitch(all_pitches: List[Tuple[str, str]], word: str) -> Tuple[str, str]:
    """从多个音调选项中选择最匹配的
    
    使用 fugashi 获取词语的实际读音,然后匹配最接近的音调信息
    
    Args:
        all_pitches: 所有音调信息列表 [(reading_html, pitch_pos), ...]
        word: 原始单词
        
    Returns:
        最匹配的 (reading_html, pitch_pos) 元组
    """
    if not all_pitches:
        return (None, None)
    
    if len(all_pitches) == 1:
        return all_pitches[0]
    
    # 尝试用 fugashi 获取实际读音
    actual_reading = get_word_reading_with_fugashi(word)
    
    if not actual_reading:
        # 无法获取实际读音,返回最后一个 (通常是最常用的)
        return all_pitches[-1]
    
    # 标准化实际读音
    normalized_actual = normalize_reading(actual_reading)
    
    # 计算每个候选读音与实际读音的相似度
    best_match = all_pitches[-1]  # 默认最后一个
    best_score = 0
    
    for reading_html, pitch_pos in all_pitches:
        normalized_candidate = normalize_reading(reading_html)
        
        # 完全匹配
        if normalized_candidate == normalized_actual:
            return (reading_html, pitch_pos)
        
        # 计算相似度 (简单的字符匹配比例)
        matches = sum(1 for a, b in zip(normalized_candidate, normalized_actual) if a == b)
        max_len = max(len(normalized_candidate), len(normalized_actual))
        score = matches / max_len if max_len > 0 else 0
        
        if score > best_score:
            best_score = score
            best_match = (reading_html, pitch_pos)
    
    return best_match


def extract_pitch_info_nhk_old(mdx_file: Path, word: str, return_all: bool = False) -> Tuple[Optional[str], Optional[str]] | List[Tuple[str, str]]:
    """从旧版 NHK 提取音调信息 (带 Fugashi 读音验证)
    
    旧版 NHK 使用 tune-0/tune-1/tune-2 标记音高:
    - tune-0: 低音
    - tune-1: 高音 (添加上划线)
    - tune-2: 下降音 (添加上划线,并记录下降位置)
    
    ⚠️  NHK 词典特殊标记处理:
    - 鼻浊音标记 (゜): 如 カ゜ク (家具的特殊读音)
    - 此函数会自动使用 Fugashi 的 lForm 验证读音
    - 如果 NHK 读音与 Fugashi 不一致,自动使用 Fugashi 的标准读音
    - 保留 NHK 的音调位置信息
    
    Args:
        mdx_file: 旧版 NHK MDX 文件路径
        word: 要查询的单词
        return_all: 是否返回所有读音的音调信息 (默认 False,只返回第一个)
        
    Returns:
        如果 return_all=False:
            (reading_with_marks, pitch_position) 元组
        如果 return_all=True:
            [(reading_with_marks, pitch_position), ...] 列表
        
        - reading_with_marks: 带上划线标记的假名 (HTML) - 已修正为标准读音
        - pitch_position: 音调类型 [0], [1], [2] 等
    
    Example:
        >>> # 家具 - NHK: カ゜ク [1] (鼻浊音) → 自动修正为: カグ [1]
        >>> reading, pitch = extract_pitch_info_nhk_old(nhk_path, "家具")
        >>> # reading: "カグ" (标准读音), pitch: "[1]"
    """
    if type(mdx_file) is not Path:
        mdx_file = Path(mdx_file)
    
    with Dictionary(mdx_file) as dict_obj:
        html_content = dict_obj.lookup_html(word)
        
        if not html_content:
            return [] if return_all else (None, None)
        
        soup = BeautifulSoup(html_content, 'lxml')
        
        # 查找所有包含音调信息的容器 (可能有多个读音)
        # 旧版 NHK 将每个读音放在单独的 <p> 标签中
        # 每个 <p> 有两部分: 发音図 (单词) 和 助詞付 (带助词),只取第一部分
        all_pitch_infos = []
        
        # 策略: 找到所有包含 tune-* 类的 <p> 标签
        # 每个 <p> 标签代表一个独立的读音
        pitch_paragraphs = soup.find_all('p')
        
        for p_tag in pitch_paragraphs:
            # 在这个 <p> 中查找所有 <a> 标签 (音频链接)
            # 通常有两个: 発音図 和 助詞付
            # 我们只需要第一个 (発音図) 后面的 tune 元素
            audio_links = p_tag.find_all('a', class_='aud-btn')
            
            if not audio_links:
                continue
            
            # 找到第一个音频链接 (発音図) 后面的 tune 元素
            # 方法: 从第一个 <a> 标签开始,找到下一个 <br> 或第二个 <a> 之前的所有 tune-* 元素
            first_link = audio_links[0]
            
            # 收集第一个音频链接后的 tune 元素
            reading_parts = []
            drop_position = 0
            current_pos = 0
            
            # 遍历第一个链接之后的兄弟节点
            # 在遇到 <br> 之前的所有 tune-* 元素
            for sibling in first_link.next_siblings:
                # 如果遇到 <br> 标签,停止 (第一部分结束)
                if hasattr(sibling, 'name') and sibling.name == 'br':
                    break
                
                # 检查是否是 tune-* 元素
                if hasattr(sibling, 'get') and sibling.get('class'):
                    classes = sibling.get('class', [])
                    if any(c.startswith('tune-') for c in classes):
                        text = sibling.get_text()
                        
                        if 'tune-0' in classes:
                            reading_parts.append(text)
                        elif 'tune-1' in classes:
                            reading_parts.append(f'<span style="text-decoration: overline;">{text}</span>')
                        elif 'tune-2' in classes:
                            reading_parts.append(f'<span style="text-decoration: overline;">{text}</span>')
                            drop_position = current_pos + len(text)
                        
                        current_pos += len(text)
            
            if reading_parts:
                reading_html = ''.join(reading_parts)
                pitch_pos = f"[{drop_position}]"
                all_pitch_infos.append((reading_html, pitch_pos))
        
        # 去重 (可能有重复的)
        unique_infos = []
        seen_readings = set()
        for reading, pitch in all_pitch_infos:
            # 移除 HTML 标签用于比较
            plain_reading = re.sub(r'<[^>]+>', '', reading)
            key = (plain_reading, pitch)
            if key not in seen_readings:
                seen_readings.add(key)
                unique_infos.append((reading, pitch))
        
        # 🔧 新增: 使用 Fugashi 验证和修正读音 (处理 NHK 鼻浊音等特殊标记)
        if unique_infos and FUGASHI_AVAILABLE:
            verified_infos = []
            fugashi_reading = get_word_reading_with_fugashi(word)
            
            if fugashi_reading:
                # 将 Fugashi 读音转换为平假名用于比较
                try:
                    import jaconv
                    fugashi_hira = jaconv.kata2hira(fugashi_reading)
                except (ImportError, Exception):
                    # 简单转换
                    fugashi_hira = fugashi_reading
                    for char in fugashi_reading:
                        code = ord(char)
                        if 0x30A1 <= code <= 0x30F6:
                            fugashi_hira = fugashi_hira.replace(char, chr(code - 0x60))
                
                for reading_html, pitch_pos in unique_infos:
                    # 提取纯文本读音
                    plain_reading = re.sub(r'<[^>]+>', '', reading_html)
                    
                    # 移除 NHK 特殊标记 (鼻浊音 ゜、长音 ー 等)
                    clean_reading = plain_reading.replace('゜', '').replace('◌゚', '')
                    
                    # 转换为平假名用于比较
                    try:
                        import jaconv
                        clean_hira = jaconv.kata2hira(clean_reading)
                    except:
                        clean_hira = clean_reading
                        for char in clean_reading:
                            code = ord(char)
                            if 0x30A1 <= code <= 0x30F6:
                                clean_hira = clean_hira.replace(char, chr(code - 0x60))
                    
                    # 比较读音
                    if clean_hira != fugashi_hira:
                        # 读音不匹配 (如 NHK 的鼻浊音 カ゜ク vs Fugashi 的 カグ)
                        # 使用 Fugashi 的读音，保留 NHK 的音调位置
                        
                        # 将 Fugashi 读音转换为片假名
                        fugashi_kata = fugashi_reading
                        
                        # 根据音调位置重建 HTML
                        # 提取音调位置数字
                        pitch_num = 0
                        pitch_match = re.search(r'\[(\d+)\]', pitch_pos)
                        if pitch_match:
                            pitch_num = int(pitch_match.group(1))
                        
                        # 重建带音调标记的 HTML
                        new_reading_parts = []
                        for i, char in enumerate(fugashi_kata):
                            pos = i + 1
                            
                            if pitch_num == 0:
                                # 平板式: 第一拍无线,第二拍开始有上划线
                                if pos > 1:
                                    new_reading_parts.append(f'<span style="text-decoration: overline;">{char}</span>')
                                else:
                                    new_reading_parts.append(char)
                            elif pitch_num == 1:
                                # 頭高型: 第一拍有上划线,后续无线
                                if pos == 1:
                                    new_reading_parts.append(f'<span style="text-decoration: overline;">{char}</span>')
                                else:
                                    new_reading_parts.append(char)
                            else:
                                # 中高型/尾高型: 第二拍到下降位置有上划线
                                if 2 <= pos <= pitch_num:
                                    new_reading_parts.append(f'<span style="text-decoration: overline;">{char}</span>')
                                else:
                                    new_reading_parts.append(char)
                        
                        corrected_reading_html = ''.join(new_reading_parts)
                        verified_infos.append((corrected_reading_html, pitch_pos))
                        
                        # 可选: 打印警告 (调试时使用)
                        # print(f"⚠️  NHK 读音修正: {word} - NHK:{plain_reading} → Fugashi:{fugashi_kata}")
                    else:
                        # 读音一致,保留原样
                        verified_infos.append((reading_html, pitch_pos))
                
                unique_infos = verified_infos if verified_infos else unique_infos
        
        if return_all:
            return unique_infos
        else:
            # 使用 fugashi 智能匹配最合适的读音
            return match_best_pitch(unique_infos, word)


class AudioLookup:
    """音频和音调信息查询类
    
    按优先级从多个词典中提取音频和音调信息:
    1. 新版 NHK (AAC 音频,音调标记不完整)
    2. 旧版 NHK (完整音调标记)
    3. 大辞泉 第二版 (有音频和下降位置标记)
    
    Attributes:
        audio_dicts: 音频词典列表 [(Path, 显示名称)]
        pitch_dict: 音调词典路径 (旧版 NHK)
        
    Example:
        >>> audio_lookup = AudioLookup(
        ...     audio_dicts=[
        ...         (Path("nhk_new.mdx"), "NHK新版"),
        ...         (Path("nhk_old.mdx"), "NHK旧版"),
        ...         (Path("djs.mdx"), "大辞泉"),
        ...     ],
        ...     pitch_dict=Path("nhk_old.mdx")
        ... )
        >>> 
        >>> result = audio_lookup.lookup("政権")
        >>> print(result['audio_source'])  # "NHK新版"
        >>> print(result['pitch_position'])  # "[2]"
    """
    
    def __init__(
        self,
        audio_dicts: List[Tuple[Path, str]],
        pitch_dict: Optional[Path] = None
    ):
        """初始化音频查询器
        
        Args:
            audio_dicts: [(mdx_path, 显示名称), ...] 按优先级排列
            pitch_dict: 音调词典路径 (通常是旧版 NHK)
        """
        self.audio_dicts = audio_dicts
        self.pitch_dict = pitch_dict
    
    @classmethod
    def from_dirs(
        cls,
        nhk_new_dir: Optional[Path] = None,
        nhk_old_dir: Optional[Path] = None,
        djs_dir: Optional[Path] = None,
        dict_names: Optional[Dict[str, str]] = None
    ) -> "AudioLookup":
        """从目录初始化音频查询器
        
        Args:
            nhk_new_dir: 新版 NHK 目录 (或 .mdx 文件)
            nhk_old_dir: 旧版 NHK 目录 (或 .mdx 文件)
            djs_dir: 大辞泉目录 (或 .mdx 文件)
            dict_names: {文件名: 显示名称} 映射
            
        Returns:
            AudioLookup 实例
        """
        audio_dicts = []
        pitch_dict = None
        
        dict_names = dict_names or {}
        
        # 新版 NHK
        if nhk_new_dir:
            nhk_new_path = Path(nhk_new_dir)
            if nhk_new_path.is_file():
                mdx_file = nhk_new_path
            else:
                mdx_files = list(nhk_new_path.glob("*.mdx"))
                mdx_file = mdx_files[0] if mdx_files else None
            
            if mdx_file and mdx_file.exists():
                display_name = dict_names.get(mdx_file.name, "NHK新版")
                audio_dicts.append((mdx_file, display_name))
        
        # 旧版 NHK
        if nhk_old_dir:
            nhk_old_path = Path(nhk_old_dir)
            if nhk_old_path.is_file():
                mdx_file = nhk_old_path
            else:
                mdx_files = list(nhk_old_path.glob("*.mdx"))
                mdx_file = mdx_files[0] if mdx_files else None
            
            if mdx_file and mdx_file.exists():
                display_name = dict_names.get(mdx_file.name, "NHK旧版")
                audio_dicts.append((mdx_file, display_name))
                pitch_dict = mdx_file  # 用于音调提取
        
        # 大辞泉
        if djs_dir:
            djs_path = Path(djs_dir)
            if djs_path.is_file():
                mdx_file = djs_path
            else:
                mdx_files = list(djs_path.glob("*.mdx"))
                mdx_file = mdx_files[0] if mdx_files else None
            
            if mdx_file and mdx_file.exists():
                display_name = dict_names.get(mdx_file.name, "大辞泉")
                audio_dicts.append((mdx_file, display_name))
        
        return cls(audio_dicts, pitch_dict)
    
    def lookup(self, word: str, verbose: bool = False, return_all_pitches: bool = False) -> Dict:
        """查询单词的音频和音调信息
        
        Args:
            word: 要查询的单词
            verbose: 是否打印详细信息
            return_all_pitches: 是否返回所有可能的音调信息 (默认 False,只返回第一个)
            
        Returns:
            {
                'audio_base64': str,  # base64 音频数据
                'audio_mime': str,    # 音频类型
                'audio_source': str,  # 来源词典
                'reading': str,       # 带标记的假名读音(HTML) - 第一个
                'pitch_position': str,# 音调类型 [0], [1] 等 - 第一个
                'pitch_source': str,  # 音调来源
                'all_pitches': list,  # 所有音调信息 [(reading, position), ...] (仅当 return_all_pitches=True)
            }
        """
        result = {
            'audio_base64': None,
            'audio_mime': None,
            'audio_source': None,
            'reading': None,
            'pitch_position': None,
            'pitch_source': None,
        }
        
        if return_all_pitches:
            result['all_pitches'] = []
        
        # 1. 按优先级查找音频
        for mdx_path, dict_name in self.audio_dicts:
            audio_data, mime_type, source = extract_audio_from_mdx(mdx_path, word, dict_name)
            if audio_data:
                result['audio_base64'] = audio_data
                result['audio_mime'] = mime_type
                result['audio_source'] = source
                if verbose:
                    print(f"✅ 音频: {source} ({mime_type})")
                break  # 找到第一个就停止
        
        # 2. 从音调词典提取音调信息
        if self.pitch_dict and self.pitch_dict.exists():
            if return_all_pitches:
                # 获取所有音调信息
                all_pitch_infos = extract_pitch_info_nhk_old(self.pitch_dict, word, return_all=True)
                
                if all_pitch_infos:
                    result['all_pitches'] = all_pitch_infos
                    # 第一个作为默认值
                    result['reading'] = all_pitch_infos[0][0]
                    result['pitch_position'] = all_pitch_infos[0][1]
                    result['pitch_source'] = 'NHK旧版'
                    
                    if verbose:
                        print(f"✅ 音调: NHK旧版 找到 {len(all_pitch_infos)} 个读音")
                        for i, (reading, pitch) in enumerate(all_pitch_infos, 1):
                            # 移除 HTML 标签用于显示
                            plain_reading = re.sub(r'<[^>]+>', '', reading)
                            print(f"   {i}. {plain_reading} {pitch}")
            else:
                # 只获取第一个音调信息
                reading, pitch_pos = extract_pitch_info_nhk_old(self.pitch_dict, word, return_all=False)
                if reading:
                    result['reading'] = reading
                    result['pitch_position'] = pitch_pos
                    result['pitch_source'] = 'NHK旧版'
                    if verbose:
                        print(f"✅ 音调: NHK旧版 {pitch_pos}")
        
        return result
    
    def format_for_anki(self, result: Dict) -> Dict:
        """将查询结果格式化为 Anki 字段
        
        Args:
            result: lookup() 的返回值
            
        Returns:
            {
                'audio': dict,  # {'data': base64, 'filename': str}
                'reading': str,  # 带标记的假名
                'pitchPosition': str,  # [0], [1] 等
            }
        """
        anki_fields = {
            'audio': None,
            'reading': result.get('reading', ''),
            'pitchPosition': result.get('pitch_position', ''),
        }
        
        # 音频字段
        if result.get('audio_base64'):
            # 扩展名根据 MIME 类型确定
            mime_to_ext = {
                'audio/mpeg': 'mp3',
                'audio/aac': 'aac',
                'audio/wav': 'wav',
                'audio/ogg': 'ogg',
            }
            ext = mime_to_ext.get(result['audio_mime'], 'mp3')
            
            # AnkiConnect 音频格式
            anki_fields['audio'] = {
                'data': result['audio_base64'],
                'filename': f"audio_{hash(result['audio_base64'][:100])}.{ext}",
                'fields': ['audio']  # 要添加到的字段名
            }
        
        return anki_fields
