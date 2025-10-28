"""
Dict Query Interface - 词典查询界面
"""

from pathlib import Path
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from qfluentwidgets import (
    SubtitleLabel, BodyLabel, LineEdit, PrimaryPushButton,
    ComboBox, InfoBar, InfoBarPosition, FluentIcon as FIF
)


class DictQueryInterface(QWidget):
    """词典查询界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dictQueryInterface")
        self.setup_ui()
        self.dict_instances = {}  # 缓存词典实例
    
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # 标题
        title = SubtitleLabel("📖 词典查询", self)
        layout.addWidget(title)
        
        # 查询区域
        query_layout = QHBoxLayout()
        
        # 词典选择
        self.dict_combo = ComboBox(self)
        self.dict_combo.addItems([
            "Primary MDX",
            "Secondary MDX",
            "Tertiary MDX",
            "NHK 旧版",
            "NHK 新版",
            "大辞泉 (DJS)"
        ])
        self.dict_combo.setFixedWidth(150)
        query_layout.addWidget(BodyLabel("词典:", self))
        query_layout.addWidget(self.dict_combo)
        
        query_layout.addSpacing(20)
        
        # 输入框
        self.query_input = LineEdit(self)
        self.query_input.setPlaceholderText("输入日语单词...")
        self.query_input.returnPressed.connect(self.on_query)
        query_layout.addWidget(self.query_input, 1)
        
        # 查询按钮
        self.query_btn = PrimaryPushButton("查询", self)
        self.query_btn.setIcon(FIF.SEARCH)
        self.query_btn.clicked.connect(self.on_query)
        query_layout.addWidget(self.query_btn)
        
        layout.addLayout(query_layout)
        
        # HTML 显示区域
        self.web_view = QWebEngineView(self)
        self.web_view.setHtml(self._get_welcome_html())
        layout.addWidget(self.web_view, 1)
    
    def on_query(self):
        """执行查询"""
        word = self.query_input.text().strip()
        if not word:
            InfoBar.warning(
                title='警告',
                content='请输入要查询的单词',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        dict_type = self.dict_combo.currentText()
        
        try:
            # 查询词典
            html_content = self._query_dict(word, dict_type)
            
            if html_content:
                self.web_view.setHtml(self._wrap_html(html_content, word, dict_type))
            else:
                self.web_view.setHtml(self._get_not_found_html(word, dict_type))
        
        except Exception as e:
            InfoBar.error(
                title='查询失败',
                content=str(e),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            self.web_view.setHtml(self._get_error_html(str(e)))
    
    def _query_dict(self, word: str, dict_type: str) -> str:
        """查询词典"""
        try:
            from pathlib import Path
            from mdx_utils.meanings_lookup import MeaningsLookup
            
            # 从配置文件读取词典路径
            config_file = Path.home() / '.config' / 'JA-Mining' / 'gui_config.json'
            
            if not config_file.exists():
                return "<p>⚠️ 请先在主页配置词典路径</p>"
            
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 根据词典类型选择路径
            dict_path = None
            if dict_type == "Primary MDX":
                dict_path = config_data.get('primary_mdx')
            elif dict_type == "Secondary MDX":
                dict_path = config_data.get('secondary_mdx')
            elif dict_type == "Tertiary MDX":
                dict_path = config_data.get('tertiary_mdx')
            elif dict_type == "NHK 旧版":
                dict_path = config_data.get('nhk_old')
            elif dict_type == "NHK 新版":
                dict_path = config_data.get('nhk_new')
            elif dict_type == "大辞泉 (DJS)":
                dict_path = config_data.get('djs')
            
            if not dict_path or not Path(dict_path).exists():
                return f"<p>⚠️ {dict_type} 路径未配置或文件不存在</p>"
            
            # 根据选择的词典类型，只加载对应的词典
            primary_dir = None
            secondary_dir = None
            tertiary_dir = None
            
            if dict_type == "Primary MDX":
                primary_dir = Path(dict_path)
            elif dict_type == "Secondary MDX":
                secondary_dir = Path(dict_path)
            elif dict_type == "Tertiary MDX":
                tertiary_dir = Path(dict_path)
            elif dict_type in ["NHK 旧版", "NHK 新版", "大辞泉 (DJS)"]:
                # 这些特殊词典也放在 primary
                primary_dir = Path(dict_path)
            
            # 创建 MeaningsLookup 实例
            lookup = MeaningsLookup.from_dirs(
                primary_dir=primary_dir,
                secondary_dir=secondary_dir,
                tertiary_dir=tertiary_dir,
                use_jamdict=False
            )
            
            # 查询
            result = lookup.lookup(word, fallback_to_jamdict=False)
            
            if not result or result == "Not found":
                return f"<p>❌ 未在 {dict_type} 中找到 '{word}'</p>"
            
            return result
            
        except Exception as e:
            import traceback
            return f"<p>❌ 查询错误: {e}</p><pre>{traceback.format_exc()}</pre>"
    
    def _wrap_html(self, content: str, word: str, dict_type: str) -> str:
        """包装 HTML"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
                    padding: 20px;
                    background: #fafafa;
                }}
                .header {{
                    border-bottom: 2px solid #005fb8;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }}
                .word {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #005fb8;
                }}
                .dict-name {{
                    font-size: 14px;
                    color: #666;
                }}
                .content {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="word">{word}</div>
                <div class="dict-name">📖 {dict_type}</div>
            </div>
            <div class="content">
                {content}
            </div>
        </body>
        </html>
        """
    
    def _get_welcome_html(self) -> str:
        """欢迎页面"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {
                    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .welcome {
                    text-align: center;
                }
                .welcome h1 {
                    font-size: 48px;
                    margin-bottom: 20px;
                }
                .welcome p {
                    font-size: 18px;
                    opacity: 0.9;
                }
            </style>
        </head>
        <body>
            <div class="welcome">
                <h1>📖 词典查询</h1>
                <p>在上方输入日语单词开始查询</p>
            </div>
        </body>
        </html>
        """
    
    def _get_not_found_html(self, word: str, dict_type: str) -> str:
        """未找到页面"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: #fafafa;
                }}
                .not-found {{
                    text-align: center;
                }}
                .not-found h1 {{
                    font-size: 72px;
                    margin: 0;
                }}
                .not-found h2 {{
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="not-found">
                <h1>🔍</h1>
                <h2>未找到 "{word}"</h2>
                <p>在 {dict_type} 中没有找到该词条</p>
            </div>
        </body>
        </html>
        """
    
    def _get_error_html(self, error: str) -> str:
        """错误页面"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: #fafafa;
                }}
                .error {{
                    text-align: center;
                    color: #d32f2f;
                }}
                .error h1 {{
                    font-size: 72px;
                    margin: 0;
                }}
                .error pre {{
                    background: #fff;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: left;
                    color: #333;
                    max-width: 600px;
                }}
            </style>
        </head>
        <body>
            <div class="error">
                <h1>❌</h1>
                <h2>查询出错</h2>
                <pre>{error}</pre>
            </div>
        </body>
        </html>
        """
