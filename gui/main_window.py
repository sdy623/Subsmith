"""
Main Window - Fluent Design 主窗口
包含侧边导航栏和多个界面
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QColor, QCloseEvent, QIcon
from qfluentwidgets import FluentWindow, NavigationItemPosition, FluentIcon as FIF, isDarkTheme

from .config_manager import ConfigManager
from .home_interface import HomeInterface
from .dict_query_interface import DictQueryInterface
from .anki_settings_interface import AnkiSettingsInterface
from .about_interface import AboutInterface


class MiningWindow(FluentWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        # 创建配置管理器
        self.config_manager = ConfigManager()
        
        self.init_window()
        self.init_navigation()


    def init_window(self):
        """初始化窗口"""
        self.setWindowTitle("Subsmith")
        self.resize(1200, 800)
        
        # 设置微云母背景（Fluent Design 特性）
        self.setMicaEffectEnabled(False)  # 禁用云母效果，使用纯色背景
        # self.apply_theme()  # 初始化时应用主题

        # 设置窗口图标（如果有的话）
        self.setWindowIcon(QIcon("Subsmith_icon.png"))
    
    def init_navigation(self):
        """初始化导航栏"""
        # 创建各个界面，并传递配置管理器
        self.homeInterface = HomeInterface(self, self.config_manager)
        self.dictQueryInterface = DictQueryInterface(self)
        self.ankiSettingsInterface = AnkiSettingsInterface(self, self.config_manager)
        self.aboutInterface = AboutInterface(self)
        
        # 添加到导航栏
        self.addSubInterface(
            self.homeInterface,
            FIF.HOME,
            '主页',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.dictQueryInterface,
            FIF.BOOK_SHELF,
            '词典查询',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.ankiSettingsInterface,
            FIF.SETTING,
            'Anki 设置',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.aboutInterface,
            FIF.INFO,
            '关于',
            NavigationItemPosition.BOTTOM
        )
    
    def closeEvent(self, event: QCloseEvent):
        """窗口关闭事件 - 保存配置"""
        # 收集所有界面的配置
        self.homeInterface.save_config()
        self.ankiSettingsInterface.save_config()
        
        # 保存到文件
        self.config_manager.save_config()
        
        # 调用父类关闭事件
        super().closeEvent(event)
