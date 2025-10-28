"""
GUI 配置管理器
持久化保存用户设置
"""

import json
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """GUI 配置管理"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.config_dir = Path.home() / '.config' / 'JA-Mining'
        self.config_file = self.config_dir / 'gui_config.json'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 默认配置
        self.default_config = {
            # 文件路径
            'video_file': '',
            'subtitle_file': '',
            'words_file': '',
            'output_dir': '',
            'primary_mdx': '',
            'secondary_mdx': '',
            'tertiary_mdx': '',
            'nhk_old': '',
            'nhk_new': '',
            'djs': '',
            'freq': '',
            
            # 主处理参数
            'min_freq': 1,
            'max_freq': 99999,
            'min_sentence_length': 5,
            'max_sentence_length': 30,
            
            # Anki 连接
            'anki_url': 'http://127.0.0.1:8765',
            'anki_deck': 'Japanese::Mining',
            'anki_model': 'Japanese Mining',
            'anki_tags': '',
            
            # Anki 字段映射
            'field_word': 'word',
            'field_sentence': 'sentence',
            'field_reading': 'reading',
            'field_definition': 'definition',
            'field_pitch': 'pitch',
            'field_audio': 'wordAudio',
            'field_picture': 'picture',
            
            # 其他选项
            'verbose': True,
            'push_to_anki': False,
        }
        
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # 合并默认配置（处理新增的配置项）
                    config = self.default_config.copy()
                    config.update(loaded)
                    return config
            except Exception as e:
                print(f"加载配置失败: {e}")
                return self.default_config.copy()
        return self.default_config.copy()
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get(self, key: str, default=None) -> Any:
        """获取配置项"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        self.config[key] = value
    
    def update(self, data: Dict[str, Any]):
        """批量更新配置"""
        self.config.update(data)
