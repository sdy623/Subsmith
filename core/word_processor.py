"""
Word processing module
"""

import re
from pathlib import Path
from typing import List, Tuple, Optional
import fugashi

try:
    import jaconv
except ImportError:
    jaconv = None


class WordProcessor:
    """词汇处理器"""
    
    def __init__(self):
        self.tagger = fugashi.Tagger()
    
    @staticmethod
    def load_words(path: Path) -> List[Tuple[str, Optional[str], Optional[str]]]:
        """从文件加载目标单词列表
        
        支持格式:
        - 普通单词: 精霊
        - 指定读音: 精霊(せいれい)
        - 指定查词形态: 食べた[食べる]
        - 同时指定: 食べた(たべた)[食べる]
        
        Returns:
            [(单词, 读音或None, 查词形态或None), ...]
        """
        txt = path.read_text(encoding='utf-8')
        words_with_reading = []
        
        for w in re.split(r"[\n,\t]", txt):
            w = w.strip()
            if not w:
                continue
            
            lookup_form = None
            reading = None
            
            # 检查方括号(查词形态)
            dict_match = re.search(r'\[([^\]]+)\]', w)
            if dict_match:
                lookup_form = dict_match.group(1).strip()
                w = w.replace(dict_match.group(0), '')
            
            # 检查圆括号(读音)
            reading_match = re.search(r'\(([^\)]+)\)', w)
            if reading_match:
                reading = reading_match.group(1).strip()
                w = w.replace(reading_match.group(0), '')
            
            word = w.strip()
            words_with_reading.append((word, reading, lookup_form))
        
        return words_with_reading
    
    def tokens_furigana(self, text: str) -> str:
        """为文本添加假名注音(平假名)"""
        if not text:
            return ""
        out = []
        for t in self.tagger(text):
            surf = t.surface
            # 获取读音(片假名) - 使用 lForm
            yomi = None
            if hasattr(t.feature, 'lForm') and t.feature.lForm is not None:
                yomi = t.feature.lForm
            elif hasattr(t.feature, 'kana') and t.feature.kana is not None:
                yomi = t.feature.kana
            elif hasattr(t, 'feature') and len(t.feature) > 7:
                yomi = t.feature[7]
            
            # 转换为平假名
            if yomi:
                yomi = self.katakana_to_hiragana(yomi)
            
            # 如果有汉字且读音不同,添加假名
            if yomi and yomi != surf and re.search(r"[一-龯々〆ヵヶ]", surf):
                # 分离汉字部分和送り仮名
                kanji_end = 0
                for i, char in enumerate(surf):
                    if re.match(r"[一-龯々〆ヵヶ]", char):
                        kanji_end = i + 1
                
                if kanji_end < len(surf):
                    kanji_part = surf[:kanji_end]
                    okurigana = surf[kanji_end:]
                    yomi_kanji = yomi
                    if okurigana and yomi.endswith(okurigana):
                        yomi_kanji = yomi[:-len(okurigana)]
                    out.append(f"{kanji_part}[{yomi_kanji}]{okurigana}")
                else:
                    out.append(f"{surf}[{yomi}]")
            else:
                out.append(surf)
        
        return ' '.join(out)
    
    def lemmatize(self, text: str) -> List[str]:
        """获取文本中所有词的词元形式"""
        if not text:
            return []
        lemmas = []
        for t in self.tagger(text):
            lemma = None
            if hasattr(t.feature, 'lemma'):
                lemma = t.feature.lemma
            elif hasattr(t, 'feature') and len(t.feature) > 6:
                lemma = t.feature[6]
            lemmas.append(lemma or t.surface)
        return lemmas
    
    @staticmethod
    def katakana_to_hiragana(text: str) -> str:
        """将片假名转换为平假名"""
        if not text:
            return ""
        
        if jaconv:
            return jaconv.kata2hira(text)
        
        # 降级方案
        result = []
        for char in text:
            code = ord(char)
            if 0x30A1 <= code <= 0x30F6:
                result.append(chr(code - 0x60))
            else:
                result.append(char)
        return ''.join(result)
    
    @staticmethod
    def is_all_katakana(text: str) -> bool:
        """检测文本是否全是片假名"""
        if not text:
            return False
        for char in text:
            code = ord(char)
            if not (0x30A1 <= code <= 0x30F6 or code == 0x30FC or code == 0x30FB):
                return False
        return True
