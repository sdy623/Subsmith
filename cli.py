#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JP Media Mining CLI Tool - 命令行工具入口

重构版本 - 高内聚低耦合的模块化设计
"""

import argparse
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.config import Config
from core.processor import MiningProcessor


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    ap = argparse.ArgumentParser(
        description='JP Media Mining → Anki Cards (模块化版本)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # 必需参数
    ap.add_argument('--video', required=True, type=Path, help='视频文件路径')
    ap.add_argument('--subs', required=True, type=Path, help='字幕文件路径 (.srt/.ass/.vtt)')
    ap.add_argument('--words', required=True, type=Path, help='目标单词列表文件')
    ap.add_argument('--outdir', required=True, type=Path, help='输出目录')
    ap.add_argument('--csv', required=True, type=Path, help='CSV 输出路径')
    
    # MDX 词典 (释义)
    ap.add_argument('--primary-mdx', type=Path, help='主要释义词典目录')
    ap.add_argument('--secondary-mdx', type=Path, help='次要释义词典目录')
    ap.add_argument('--tertiary-mdx', type=Path, help='第三级释义词典目录')
    ap.add_argument('--use-jamdict', action='store_true', help='启用 JMDict fallback')
    
    # MDX 词典 (音频和音调)
    ap.add_argument('--nhk-old', type=Path, help='NHK 旧版词典目录')
    ap.add_argument('--nhk-new', type=Path, help='NHK 新版词典目录')
    ap.add_argument('--djs', type=Path, help='大辞泉词典目录')
    
    # 频率数据
    ap.add_argument('--freq', type=Path, help='频率数据文件 (JSON/ZIP/CSV/TSV)')
    
    # 媒体处理选项
    ap.add_argument('--pad', type=float, default=0.0, help='音频裁剪前后填充时间(秒)')
    ap.add_argument('--vf', type=str, help='FFmpeg 视频滤镜')
    
    # 输出选项
    ap.add_argument('--quiet', action='store_true', help='安静模式')
    
    # Anki 推送选项
    ap.add_argument('--anki', action='store_true', help='推送到 Anki')
    ap.add_argument('--anki-deck', type=str, default='Japanese::Anime', help='Anki 牌组名称')
    ap.add_argument('--anki-model', type=str, default='Senren', help='Anki 笔记类型')
    ap.add_argument('--anki-tags', type=str, nargs='+', default=['anime', 'mining'], help='Anki 卡片标签')
    ap.add_argument('--anki-allow-duplicates', action='store_true', help='允许重复卡片')
    ap.add_argument('--ankiconnect-url', type=str, default='http://localhost:8765', help='AnkiConnect API 地址')
    
    return ap


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 创建配置
    config = Config.from_args(args)
    
    # 创建处理器
    processor = MiningProcessor(config)
    
    # 初始化
    if not processor.initialize():
        return 1
    
    # 执行处理
    try:
        cards = processor.process()
        
        # 导出 CSV
        if config.csv:
            print(f"\n📊 导出 CSV...")
            from core.csv_exporter import CSVExporter
            exporter = CSVExporter(config)
            exporter.export(cards)
        
        # 推送到 Anki
        if config.anki:
            print(f"\n🚀 推送到 Anki...")
            from core.anki_pusher import AnkiPusher
            pusher = AnkiPusher(config)
            success, fail = pusher.push(cards)
            print(f"   ✅ 成功: {success} 张")
            if fail > 0:
                print(f"   ❌ 失败: {fail} 张")
        
        print("\n" + "=" * 60)
        print("✅ 全部完成!")
        print("=" * 60)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        return 130
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
