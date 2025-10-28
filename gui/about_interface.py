"""
About Interface - 关于界面
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtGui import QPixmap

from qfluentwidgets import (
    SubtitleLabel, BodyLabel, HyperlinkLabel, FluentIcon as FIF, ScrollArea
)

class AboutInterface(QWidget):
    """关于界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("aboutInterface")
        self.setup_ui()
    
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
        layout.setSpacing(30)
        
        # Logo 区域
        logo_layout = QHBoxLayout()
        logo_layout.addStretch()
        
        logo_label = QLabel(self)
        logo_label.setPixmap(QPixmap("Subsmith_icon.png").scaled(256, 256))
        logo_layout.addWidget(logo_label)
        
        logo_layout.addStretch()
        layout.addLayout(logo_layout)
        
        # 标题
        title_layout = QHBoxLayout()
        title_layout.addStretch()
        title = SubtitleLabel("Subsmith", self)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 版本
        version_layout = QHBoxLayout()
        version_layout.addStretch()
        version = BodyLabel("Version 0.9", self)
        version.setStyleSheet("color: #666;")
        version_layout.addWidget(version)
        version_layout.addStretch()
        layout.addLayout(version_layout)
        
        layout.addSpacing(20)
        
        # 描述
        description = BodyLabel(
            "Subsmith 是一个专为日语学习者设计的视频字幕词汇挖掘工具。\n"
            "通过分析视频字幕，自动生成 Anki 卡片，\n"
            "包含单词、句子、释义、读音、音调、音频和截图。",
            self
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)
        
        layout.addSpacing(20)
        
        # === 功能特性 ===
        features_label = BodyLabel("✨ 主要特性（Subsmith）", self)
        features_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(features_label)
        
        features = [
            "🎯 智能单词匹配 - 使用 Fugashi 进行精确的词法分析",
            "📚 多词典支持 - 支持多组 MDX、NHK、DJS 等",
            "🎵 音调标注 - 自动获取音调信息",
            "🔊 音频提取 - 自动提取单词和句子音频",
            "📸 自动截图 - 捕捉对应场景画面",
            "📊 频率统计 - 支持多种频率数据格式",
            "🚀 Anki 集成 - 一键推送到 Anki",
        ]
        for feature in features:
            feature_label = BodyLabel(feature, self)
            feature_label.setStyleSheet("padding-left: 20px;")
            layout.addWidget(feature_label)
        
        layout.addSpacing(20)
        
        # === 技术栈 ===
        tech_label = BodyLabel("🔧 技术栈（Subsmith）", self)
        tech_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(tech_label)
        
        tech_items = [
            "• Python 3.10+",
            "• PySide6 + Fluent Design",
            "• Fugashi (日语形态分析)",
            "• UniDic (日语词典)",
            "• MDXScraper (MDX 词典查询)",
            "• FFmpeg (媒体处理)",
            "• pysubs2 (字幕解析)",
        ]
        
        for item in tech_items:
            tech_item_label = BodyLabel(item, self)
            tech_item_label.setStyleSheet("padding-left: 20px;")
            layout.addWidget(tech_item_label)
        
        layout.addSpacing(20)
        
        # === 链接 ===
        links_label = BodyLabel("🔗 链接", self)
        links_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(links_label)
        github_link = HyperlinkLabel(self)
        github_link.setUrl("https://github.com/sdy623/Subsmith")
        github_link.setText("Subsmith GitHub 仓库")
        #github_link.setStyleSheet("padding-left: 20px;")
        layout.addWidget(github_link)
        doc_link = HyperlinkLabel(self)
        doc_link.setUrl("https://github.com/sdy623/Subsmith/README.md")
        doc_link.setText("Subsmith 使用文档")
        #doc_link.setStyleSheet("padding-left: 20px;")
        layout.addWidget(doc_link)
        
        layout.addSpacing(20)
        
        # === 许可证 ===
        license_label = BodyLabel("📄 许可证", self)
        license_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(license_label)
        license_text = BodyLabel("GPL-3.0 License", self)
        license_text.setStyleSheet("padding-left: 20px;")
        layout.addWidget(license_text)
        
        layout.addSpacing(20)
        
        # === 致谢 ===
        thanks_label = BodyLabel("💝 致谢（Subsmith）", self)
        thanks_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(thanks_label)
        thanks_items = [
            "• FFmpeg 项目团队",
            "• Anki & AnkiConnect 开发者",
            "• Senren Anki Note Types 作者",
            "• Fugashi & MeCab 开发团队",
            "• UniDic 词典项目",
            "• PySide6-Fluent-Widgets 作者",
            "• MDXScraper 作者",
            "• Yomitan 项目团队",
            "• BCCWJ 语料库项目",
            "• FreeMdict Forum、Anki 社区",
            "• 所有贡献者和支持者",
        ]
        for item in thanks_items:
            thanks_item_label = BodyLabel(item, self)
            thanks_item_label.setStyleSheet("padding-left: 20px;")
            layout.addWidget(thanks_item_label)
        
        layout.addSpacing(20)
        
        # 版权信息
        copyright_layout = QHBoxLayout()
        copyright_layout.addStretch()
        copyright_label = BodyLabel("© 2025 Subsmith - sdy623. All rights reserved.", self)
        copyright_label.setStyleSheet("color: #999; font-size: 12px;")
        copyright_layout.addWidget(copyright_label)
        copyright_layout.addStretch()
        layout.addLayout(copyright_layout)
        
        layout.addStretch()
        
        # 设置滚动区域
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
