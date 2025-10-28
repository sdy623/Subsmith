"""
Home Interface - 主界面（参数配置）
"""

from pathlib import Path
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from qfluentwidgets import (
    SubtitleLabel, BodyLabel, LineEdit, PushButton, ToolButton,
    PrimaryPushButton, ProgressBar, TextEdit, CheckBox,
    InfoBar, InfoBarPosition, FluentIcon as FIF, ScrollArea
)

from .config_manager import ConfigManager


class DragDropLineEdit(LineEdit):
    """支持拖拽的输入框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """拖拽释放事件"""
        urls = event.mimeData().urls()
        if urls:
            # 获取第一个文件路径
            file_path = urls[0].toLocalFile()
            self.setText(file_path)
            event.acceptProposedAction()
        else:
            event.ignore()



class ProcessingThread(QThread):
    """后台处理线程"""
    progress = Signal(int)
    log = Signal(str)
    finished_signal = Signal(bool, str)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
    
    def run(self):
        """执行处理"""
        try:
            from core.processor import MiningProcessor
            
            self.log.emit("🚀 初始化处理器...")
            processor = MiningProcessor(self.config)
            processor.logger.quiet = False  # GUI 模式显示日志到窗口
            
            # 重定向日志输出
            import sys
            from io import StringIO
            old_stdout = sys.stdout
            sys.stdout = LogCapture(self.log)
            
            try:
                if not processor.initialize():
                    self.finished_signal.emit(False, "初始化失败")
                    return
                
                self.log.emit("📊 开始处理...")
                cards = processor.process()
                
                self.progress.emit(80)
                
                # 导出 CSV
                if self.config.csv:
                    self.log.emit("📝 导出 CSV...")
                    from core.csv_exporter import CSVExporter
                    exporter = CSVExporter(self.config)
                    exporter.export(cards)
                
                self.progress.emit(90)
                
                # 推送到 Anki
                if self.config.anki:
                    self.log.emit("🚀 推送到 Anki...")
                    from core.anki_pusher import AnkiPusher
                    pusher = AnkiPusher(self.config)
                    success, fail = pusher.push(cards)
                    self.log.emit(f"✅ 成功: {success} 张, 失败: {fail} 张")
                
                self.progress.emit(100)
                self.finished_signal.emit(True, f"完成! 共 {len(cards)} 张卡片")
            
            finally:
                sys.stdout = old_stdout
            
        except Exception as e:
            self.log.emit(f"❌ 错误: {e}")
            self.finished_signal.emit(False, str(e))


class LogCapture:
    """捕获 print 输出并发送到 GUI"""
    def __init__(self, signal):
        self.signal = signal
    
    def write(self, text):
        if text.strip():
            self.signal.emit(text.rstrip())
    
    def flush(self):
        pass


class HomeInterface(QWidget):
    """主界面"""
    
    def __init__(self, parent=None, config_manager: ConfigManager = None):
        super().__init__(parent)
        self.setObjectName("homeInterface")
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
        title = SubtitleLabel("Subsmith", self)
        layout.addWidget(title)
        
        # === 第一组：素材区域 ===
        layout.addWidget(BodyLabel("📹 素材文件", self))
        
        # 视频文件
        video_layout = self._create_file_row("视频文件:", "video")
        layout.addLayout(video_layout)
        
        # 字幕文件
        subs_layout = self._create_file_row("字幕文件:", "subs")
        layout.addLayout(subs_layout)
        
        # 单词列表
        words_layout = self._create_file_row("单词列表:", "words")
        layout.addLayout(words_layout)
        
        # 输出目录
        outdir_layout = self._create_file_row("输出目录:", "outdir", is_dir=True)
        layout.addLayout(outdir_layout)
        
        layout.addSpacing(20)
        
        # === 第二组：词典目录 ===
        layout.addWidget(BodyLabel("📚 词典目录", self))
        
        # Primary MDX
        primary_layout = self._create_file_row("Primary 词典:", "primary_mdx", is_dir=False)
        layout.addLayout(primary_layout)
        
        # Secondary MDX
        secondary_layout = self._create_file_row("Secondary 词典:", "secondary_mdx", is_dir=False)
        layout.addLayout(secondary_layout)
        
        # Tertiary MDX
        tertiary_layout = self._create_file_row("Tertiary 词典:", "tertiary_mdx", is_dir=False)
        layout.addLayout(tertiary_layout)
        
        # NHK Old
        nhk_old_layout = self._create_file_row("NHK 旧版:", "nhk_old", is_dir=False)
        layout.addLayout(nhk_old_layout)
        
        # NHK New
        nhk_new_layout = self._create_file_row("NHK 新版:", "nhk_new", is_dir=False)
        layout.addLayout(nhk_new_layout)
        
        # DJS
        djs_layout = self._create_file_row("大辞泉 (DJS):", "djs", is_dir=False)
        layout.addLayout(djs_layout)
        
        # 频率数据
        freq_layout = self._create_file_row("频率数据:", "freq")
        layout.addLayout(freq_layout)
        
        layout.addSpacing(20)
        
        # === 第三组：开关选项 ===
        layout.addWidget(BodyLabel("⚙️ 导出选项", self))
        
        options_layout = QHBoxLayout()
        self.csv_check = CheckBox("导出 CSV", self)
        self.csv_check.setChecked(True)
        self.anki_check = CheckBox("推送到 Anki", self)
        options_layout.addWidget(self.csv_check)
        options_layout.addWidget(self.anki_check)
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        # 标签设置
        tags_layout = QHBoxLayout()
        tags_layout.addWidget(BodyLabel("标签:", self))
        self.tags_edit = LineEdit(self)
        self.tags_edit.setPlaceholderText("多个标签用空格分隔，例如: mining anime")
        tags_layout.addWidget(self.tags_edit, 1)
        layout.addLayout(tags_layout)
        
        layout.addSpacing(10)
        
        # 进度条
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 按钮行：开始、停止、清空日志
        button_layout = QHBoxLayout()
        
        self.start_button = PrimaryPushButton("开始处理", self)
        self.start_button.setIcon(FIF.PLAY)
        self.start_button.clicked.connect(self.start_processing)
        self.start_button.setFixedWidth(150)  # 固定宽度
        button_layout.addWidget(self.start_button)
        
        self.stop_button = PushButton("停止处理", self)
        self.stop_button.setIcon(FIF.CLOSE)
        self.stop_button.clicked.connect(self.stop_processing)
        self.stop_button.setEnabled(False)
        self.stop_button.setFixedWidth(150)
        button_layout.addWidget(self.stop_button)
        
        self.clear_log_button = PushButton("清空日志", self)
        self.clear_log_button.setIcon(FIF.DELETE)
        self.clear_log_button.clicked.connect(self.clear_log)
        self.clear_log_button.setFixedWidth(150)
        button_layout.addWidget(self.clear_log_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 日志输出
        layout.addWidget(BodyLabel("📋 处理日志", self))
        self.log_text = TextEdit(self)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text, 1)
        
        # 设置滚动区域
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
    
    def _create_file_row(self, label_text: str, attr_name: str, is_dir: bool = False):
        """创建文件选择行"""
        layout = QHBoxLayout()
        
        # 标签
        label = BodyLabel(label_text, self)
        label.setFixedWidth(120)
        layout.addWidget(label)
        
        # 输入框（支持拖拽）
        line_edit = DragDropLineEdit(self)
        line_edit.setPlaceholderText("点击浏览或拖拽文件..." if not is_dir else "点击浏览或拖拽目录...")
        setattr(self, f"{attr_name}_edit", line_edit)
        layout.addWidget(line_edit, 1)
        
        # 浏览按钮
        browse_btn = ToolButton(FIF.FOLDER, self)
        browse_btn.clicked.connect(lambda: self._browse_file(attr_name, is_dir))
        layout.addWidget(browse_btn)
        
        return layout
    
    def _browse_file(self, attr_name: str, is_dir: bool):
        """浏览文件或目录"""
        line_edit = getattr(self, f"{attr_name}_edit")
        
        if is_dir:
            path = QFileDialog.getExistingDirectory(
                self, "选择目录",
                str(Path.home())
            )
        else:
            # 根据类型选择文件过滤器
            if 'video' in attr_name:
                filter_str = "视频文件 (*.mp4 *.mkv *.avi);;所有文件 (*.*)"
            elif 'subs' in attr_name:
                filter_str = "字幕文件 (*.srt *.ass *.vtt);;所有文件 (*.*)"
            elif 'words' in attr_name:
                filter_str = "文本文件 (*.txt);;所有文件 (*.*)"
            elif 'freq' in attr_name:
                filter_str = "数据文件 (*.json *.zip *.csv *.tsv);;所有文件 (*.*)"
            else:
                filter_str = "所有文件 (*.*)"
            
            path, _ = QFileDialog.getOpenFileName(
                self, "选择文件",
                str(Path.home()),
                filter_str
            )
        
        if path:
            line_edit.setText(path)
    
    def start_processing(self):
        """开始处理"""
        # 验证必需字段
        required_fields = ['video', 'subs', 'words', 'outdir']
        for field in required_fields:
            edit = getattr(self, f"{field}_edit")
            if not edit.text():
                InfoBar.warning(
                    title='警告',
                    content=f'请选择{field}',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
        
        # 创建配置
        from core.config import Config
        
        csv_path = Path(self.outdir_edit.text()) / "cards.csv"
        
        # 从配置管理器获取 Anki 设置
        anki_deck = self.config_manager.get('anki_deck', 'Japanese::Mining') if self.config_manager else 'Japanese::Mining'
        anki_model = self.config_manager.get('anki_model', 'Japanese Mining') if self.config_manager else 'Japanese Mining'
        anki_url = self.config_manager.get('anki_url', 'http://127.0.0.1:8765') if self.config_manager else 'http://127.0.0.1:8765'
        
        # 处理标签（从字符串转为列表）
        tags_text = self.tags_edit.text().strip()
        anki_tags = tags_text.split() if tags_text else []
        
        config = Config(
            video=Path(self.video_edit.text()),
            subs=Path(self.subs_edit.text()),
            words=Path(self.words_edit.text()),
            outdir=Path(self.outdir_edit.text()),
            csv=csv_path if self.csv_check.isChecked() else None,
            primary_mdx=Path(self.primary_mdx_edit.text()) if self.primary_mdx_edit.text() else None,
            secondary_mdx=Path(self.secondary_mdx_edit.text()) if self.secondary_mdx_edit.text() else None,
            tertiary_mdx=Path(self.tertiary_mdx_edit.text()) if self.tertiary_mdx_edit.text() else None,
            nhk_old=Path(self.nhk_old_edit.text()) if self.nhk_old_edit.text() else None,
            nhk_new=Path(self.nhk_new_edit.text()) if self.nhk_new_edit.text() else None,
            djs=Path(self.djs_edit.text()) if self.djs_edit.text() else None,
            freq=Path(self.freq_edit.text()) if self.freq_edit.text() else None,
            anki=self.anki_check.isChecked(),
            anki_deck=anki_deck,
            anki_model=anki_model,
            anki_tags=anki_tags,
            ankiconnect_url=anki_url,
        )
        
        # 启动处理线程
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.log_text.append("🚀 准备开始处理...\n")
        
        self.thread = ProcessingThread(config)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.log.connect(self.log_text.append)
        self.thread.finished_signal.connect(self.on_finished)
        self.thread.start()
    
    def stop_processing(self):
        """停止处理"""
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.terminate()
            self.thread.wait()
            self.log_text.append("\n⛔ 处理已停止\n")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            
            InfoBar.warning(
                title='已停止',
                content='处理已被用户停止',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        InfoBar.success(
            title='已清空',
            content='日志已清空',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1000,
            parent=self
        )
    
    def on_finished(self, success: bool, message: str):
        """处理完成"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        if success:
            InfoBar.success(
                title='完成',
                content=message,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            InfoBar.error(
                title='错误',
                content=message,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    
    def load_config(self):
        """加载配置到界面"""
        if not self.config_manager:
            return
        
        # 文件路径
        self.video_edit.setText(self.config_manager.get('video_file', ''))
        self.subs_edit.setText(self.config_manager.get('subtitle_file', ''))
        self.words_edit.setText(self.config_manager.get('words_file', ''))
        self.outdir_edit.setText(self.config_manager.get('output_dir', ''))
        self.primary_mdx_edit.setText(self.config_manager.get('primary_mdx', ''))
        self.secondary_mdx_edit.setText(self.config_manager.get('secondary_mdx', ''))
        self.tertiary_mdx_edit.setText(self.config_manager.get('tertiary_mdx', ''))
        self.nhk_old_edit.setText(self.config_manager.get('nhk_old', ''))
        self.nhk_new_edit.setText(self.config_manager.get('nhk_new', ''))
        self.djs_edit.setText(self.config_manager.get('djs', ''))
        self.freq_edit.setText(self.config_manager.get('freq', ''))
        
        # 选项
        self.csv_check.setChecked(self.config_manager.get('push_to_anki', False) == False)
        self.anki_check.setChecked(self.config_manager.get('push_to_anki', False))
        
        # 标签
        self.tags_edit.setText(self.config_manager.get('anki_tags', ''))
    
    def save_config(self):
        """保存界面配置"""
        if not self.config_manager:
            return
        
        self.config_manager.update({
            'video_file': self.video_edit.text(),
            'subtitle_file': self.subs_edit.text(),
            'words_file': self.words_edit.text(),
            'output_dir': self.outdir_edit.text(),
            'primary_mdx': self.primary_mdx_edit.text(),
            'secondary_mdx': self.secondary_mdx_edit.text(),
            'tertiary_mdx': self.tertiary_mdx_edit.text(),
            'nhk_old': self.nhk_old_edit.text(),
            'nhk_new': self.nhk_new_edit.text(),
            'djs': self.djs_edit.text(),
            'freq': self.freq_edit.text(),
            'push_to_anki': self.anki_check.isChecked(),
            'anki_tags': self.tags_edit.text(),
        })
