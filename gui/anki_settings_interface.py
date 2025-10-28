"""
Anki Settings Interface - Anki 设置界面
"""

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    SubtitleLabel, BodyLabel, LineEdit, PushButton, PrimaryPushButton,
    ComboBox, InfoBar, InfoBarPosition, FluentIcon as FIF, TextEdit, ScrollArea
)
import requests

from .config_manager import ConfigManager


class AnkiTestThread(QThread):
    """Anki 连接测试线程"""
    result = Signal(bool, str)
    
    def __init__(self, url: str):
        super().__init__()
        self.url = url
    
    def run(self):
        """测试连接"""
        try:
            response = requests.post(
                self.url,
                json={"action": "version", "version": 6},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'result' in data:
                    self.result.emit(True, f"✅ 连接成功! Anki-Connect 版本: {data['result']}")
                else:
                    self.result.emit(False, "❌ 无效的响应格式")
            else:
                self.result.emit(False, f"❌ HTTP 错误: {response.status_code}")
        
        except requests.Timeout:
            self.result.emit(False, "❌ 连接超时，请确保 Anki 正在运行")
        except requests.ConnectionError:
            self.result.emit(False, "❌ 无法连接，请确保 Anki 和 Anki-Connect 插件已安装")
        except Exception as e:
            self.result.emit(False, f"❌ 错误: {e}")


class AnkiSettingsInterface(QWidget):
    """Anki 设置界面"""
    
    def __init__(self, parent=None, config_manager: ConfigManager = None):
        super().__init__(parent)
        self.setObjectName("ankiSettingsInterface")
        self.config_manager = config_manager
        self.setup_ui()
        
        # 加载配置
        if self.config_manager:
            self.load_config()
    
    def setup_ui(self):
        """设置界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建滚动区域
        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 创建内容容器
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # 标题
        title = SubtitleLabel("⚙️ Anki 设置", self)
        layout.addWidget(title)
        
        # === Anki-Connect 连接 ===
        layout.addWidget(BodyLabel("🔗 Anki-Connect", self))
        
        # URL
        url_layout = QHBoxLayout()
        url_layout.addWidget(BodyLabel("URL:", self))
        self.url_edit = LineEdit(self)
        self.url_edit.setText("http://127.0.0.1:8765")
        self.url_edit.setPlaceholderText("Anki-Connect URL")
        url_layout.addWidget(self.url_edit, 1)
        layout.addLayout(url_layout)
        
        # 测试连接按钮
        test_layout = QHBoxLayout()
        self.test_btn = PushButton("测试连接", self)
        self.test_btn.setIcon(FIF.SYNC)
        self.test_btn.clicked.connect(self.test_connection)
        test_layout.addWidget(self.test_btn)
        test_layout.addStretch()
        layout.addLayout(test_layout)
        
        # 测试结果
        self.test_result = TextEdit(self)
        self.test_result.setReadOnly(True)
        self.test_result.setPlaceholderText("点击'测试连接'按钮检查 Anki 连接状态...")
        self.test_result.setMaximumHeight(100)
        layout.addWidget(self.test_result)
        
        layout.addSpacing(20)
        
        # === 牌组设置 ===
        layout.addWidget(BodyLabel("📚 牌组配置", self))
        
        # 牌组名称
        deck_layout = QHBoxLayout()
        deck_layout.addWidget(BodyLabel("牌组:", self))
        self.deck_edit = LineEdit(self)
        self.deck_edit.setText("Japanese::Mining")
        self.deck_edit.setPlaceholderText("Anki 牌组名称")
        deck_layout.addWidget(self.deck_edit, 1)
        layout.addLayout(deck_layout)
        
        # 模型名称
        model_layout = QHBoxLayout()
        model_layout.addWidget(BodyLabel("模型:", self))
        self.model_edit = LineEdit(self)
        self.model_edit.setText("Japanese Mining")
        self.model_edit.setPlaceholderText("Anki 笔记模型名称")
        model_layout.addWidget(self.model_edit, 1)
        layout.addLayout(model_layout)
        
        layout.addSpacing(20)
        
        # === 字段映射 ===
        layout.addWidget(BodyLabel("🔄 字段映射", self))
        
        field_info = BodyLabel(
            "字段映射规则:\n"
            "• Word → 单词\n"
            "• Sentence → 句子\n"
            "• Reading → 读音\n"
            "• Definition → 释义\n"
            "• Pitch → 音调\n"
            "• Audio → 音频\n"
            "• Picture → 图片\n"
            "• Frequency → 频率",
            self
        )
        field_info.setWordWrap(True)
        layout.addWidget(field_info)
        
        layout.addSpacing(20)
        
        # === 保存按钮 ===
        save_layout = QHBoxLayout()
        self.save_btn = PrimaryPushButton("保存设置", self)
        self.save_btn.setIcon(FIF.SAVE)
        self.save_btn.clicked.connect(self.save_settings)
        save_layout.addWidget(self.save_btn)
        save_layout.addStretch()
        layout.addLayout(save_layout)
        
        layout.addStretch()
        
        # 设置滚动区域
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        # 加载设置
        self.load_settings()
    
    def test_connection(self):
        """测试 Anki 连接"""
        url = self.url_edit.text().strip()
        if not url:
            InfoBar.warning(
                title='警告',
                content='请输入 Anki-Connect URL',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        self.test_btn.setEnabled(False)
        self.test_result.clear()
        self.test_result.append("🔄 正在测试连接...\n")
        
        self.thread = AnkiTestThread(url)
        self.thread.result.connect(self.on_test_result)
        self.thread.start()
    
    def on_test_result(self, success: bool, message: str):
        """测试结果"""
        self.test_btn.setEnabled(True)
        self.test_result.append(message)
        
        if success:
            InfoBar.success(
                title='成功',
                content='Anki 连接成功',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        else:
            InfoBar.error(
                title='失败',
                content='Anki 连接失败',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def save_settings(self):
        """保存设置"""
        try:
            # 使用配置管理器保存
            if self.config_manager:
                self.save_config()
                self.config_manager.save_config()
            
            InfoBar.success(
                title='成功',
                content='设置已保存',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'保存失败: {e}',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def load_config(self):
        """加载配置到界面"""
        if not self.config_manager:
            return
        
        self.url_edit.setText(self.config_manager.get('anki_url', 'http://127.0.0.1:8765'))
        self.deck_edit.setText(self.config_manager.get('anki_deck', 'Japanese::Mining'))
        self.model_edit.setText(self.config_manager.get('anki_model', 'Japanese Mining'))
    
    def save_config(self):
        """保存界面配置"""
        if not self.config_manager:
            return
        
        self.config_manager.update({
            'anki_url': self.url_edit.text(),
            'anki_deck': self.deck_edit.text(),
            'anki_model': self.model_edit.text(),
        })
    
    def load_settings(self):
        """兼容旧版的加载设置方法（已废弃）"""
        pass
