#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subsmith - GUI Application
使用 PySide6-Fluent-Widgets 构建的 Fluent Design 界面
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtCore import Qt, QDir
from PySide6.QtWidgets import QApplication
from qfluentwidgets import setTheme, Theme, setThemeColor, qconfig, FluentWindow

from gui.main_window import MiningWindow


def main():
    """GUI 应用程序入口"""
    # 修复 Qt 插件路径问题
    import os
    import PySide6
    from PySide6.QtCore import QCoreApplication
    
    # 添加 PySide6 插件路径
    pyside6_dir = os.path.dirname(PySide6.__file__)
    plugins_dir = os.path.join(pyside6_dir, 'plugins')
    if os.path.exists(plugins_dir):
        QCoreApplication.addLibraryPath(plugins_dir)
    
    # 启用高 DPI 缩放（PySide6 6.5+ 已默认启用，无需手动设置）
    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    
    app = QApplication(sys.argv)
    app.setApplicationName("Subsmith")
    app.setOrganizationName("sdy623")
    
    # 必须在创建窗口之前设置主题
    setTheme(Theme.LIGHT)
    
    # 设置主题颜色（可选）
    setThemeColor('#0078d4')
    
    # 创建主窗口
    window = MiningWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
