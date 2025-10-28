"""
Frequency data handling module
"""

import json
import zipfile
from pathlib import Path
from typing import Optional, Tuple, Dict

try:
    import pandas as pd
except ImportError:
    pd = None


class FrequencyIndex:
    """频率数据索引"""
    
    def __init__(self, path: Optional[Path] = None):
        self.idx: Dict[str, Tuple[str, float]] = {}
        if not path:
            return
        
        try:
            if path.suffix.lower() == '.json':
                self._load_from_json(path)
            elif path.suffix.lower() == '.zip':
                self._load_from_zip(path)
            else:
                self._load_from_file(path)
        except Exception as e:
            print(f"⚠️  加载频率数据失败: {e}")
    
    def _load_from_json(self, path: Path):
        """从 Yomichan term_meta_bank JSON 文件加载"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            return
        
        loaded = 0
        for entry in data:
            if not isinstance(entry, list) or len(entry) < 3:
                continue
            
            term = entry[0]
            meta_type = entry[1]
            meta_value = entry[2]
            
            if meta_type != "freq":
                continue
            
            rank = None
            display = None
            
            if isinstance(meta_value, (int, float)):
                rank = float(meta_value)
                display = f"{int(rank)}"
            elif isinstance(meta_value, dict):
                if 'frequency' in meta_value and isinstance(meta_value['frequency'], dict):
                    freq_obj = meta_value['frequency']
                    rank = float(freq_obj.get('value', 0))
                    display = f"{freq_obj.get('displayValue', str(int(rank)))}"
                elif 'value' in meta_value:
                    rank = float(meta_value.get('value', 0))
                    display = f"{meta_value.get('displayValue', str(int(rank)))}"
                else:
                    continue
            else:
                continue
            
            if rank is not None and display:
                self.idx.setdefault(term, (display, rank))
                loaded += 1
        
        if loaded > 0:
            print(f"   ✅ 加载频率数据: {loaded} 条")
    
    def _load_from_zip(self, path: Path):
        """从 ZIP 文件加载"""
        if pd is None:
            return
        
        with zipfile.ZipFile(path) as z:
            cand = [n for n in z.namelist() if n.lower().endswith(('.csv', '.tsv'))]
            if not cand:
                return
            
            with z.open(cand[0]) as f:
                sep = ',' if cand[0].lower().endswith('.csv') else '\t'
                df = pd.read_csv(f, sep=sep)
                self._load_dataframe(df)
    
    def _load_from_file(self, path: Path):
        """从 CSV/TSV 文件加载"""
        if pd is None:
            return
        
        sep = ',' if path.suffix.lower() == '.csv' else '\t'
        df = pd.read_csv(path, sep=sep)
        self._load_dataframe(df)
    
    def _load_dataframe(self, df):
        """从 DataFrame 加载数据"""
        cols = {c.lower(): c for c in df.columns}
        
        term_c = next((cols[k] for k in ['term', 'lemma', 'word', '表記', '語彙', '語'] 
                      if k in cols), None)
        rank_c = next((cols[k] for k in ['rank', 'freq_rank', 'harmonic_rank', 
                                         'frequency', '頻度', '出現度'] 
                      if k in cols), None)
        
        if term_c is None or rank_c is None:
            return
        
        for _, row in df[[term_c, rank_c]].dropna().iterrows():
            term = str(row[term_c])
            try:
                rank = float(row[rank_c])
                self.idx.setdefault(term, (str(rank), rank))
            except (ValueError, TypeError):
                continue
    
    def lookup(self, key: str) -> Tuple[Optional[str], Optional[float]]:
        """查询词的频率"""
        return self.idx.get(key, (None, None))
