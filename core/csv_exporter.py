"""
CSV Export module - 简化版
"""

from pathlib import Path
from typing import List
from dataclasses import asdict

try:
    import pandas as pd
except ImportError:
    pd = None

from .card_data import CardData
from .config import Config


class CSVExporter:
    """CSV 导出器"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def export(self, cards: List[CardData]):
        """导出卡片数据到 CSV"""
        if not pd:
            print("❌ pandas 未安装,无法导出 CSV")
            return
        
        # 转换为 DataFrame
        df = pd.DataFrame([asdict(card) for card in cards])
        
        # 统计重复
        word_counts = df['word'].value_counts().to_dict()
        df['duplicate_count'] = df['word'].map(word_counts)
        
        # 去重
        df_dedup = df.drop_duplicates(subset=['word'], keep='first')
        removed = len(df) - len(df_dedup)
        
        print(f"   原始卡片数: {len(df)}")
        if removed > 0:
            print(f"   去重后: {len(df_dedup)} (移除 {removed} 张)")
        
        # 导出
        self.config.csv.parent.mkdir(parents=True, exist_ok=True)
        df_dedup.to_csv(self.config.csv, index=False, encoding='utf-8')
        
        print(f"   ✅ CSV 已生成: {self.config.csv}")
