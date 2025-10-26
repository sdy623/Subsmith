"""
Yomitan Format MDX Query Module
提供符合 Yomitan 浏览器插件格式的 MDX 词典查询功能
"""

import re
import sys
from pathlib import Path
from typing import Optional, List, Tuple

from bs4 import BeautifulSoup
from mdxscraper import Dictionary
from mdxscraper.core.renderer import merge_css, embed_images


def query_word_yomitan_format(
    mdx_file: Path, 
    word: str, 
    dict_name: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """查询单个词典并返回 Yomitan 格式的 HTML 和 CSS
    
    Args:
        mdx_file: MDX 词典文件路径
        word: 要查询的单词
        dict_name: 词典名称（用于 data-dictionary 属性）,为 None 时使用文件名
        
    Returns:
        (html_content, css_content) 元组,未找到时返回 (None, None)
        
    Example:
        >>> html, css = query_word_yomitan_format(
        ...     Path("dict.mdx"), 
        ...     "単語", 
        ...     "大辞泉"
        ... )
        >>> if html:
        ...     print(f"Found definition with {len(css)} chars of CSS")
    """
    if not isinstance(mdx_file, Path):
        mdx_file = Path(mdx_file)
    
    # 如果未指定词典名称，使用文件名（不含扩展名）
    if dict_name is None:
        dict_name = mdx_file.stem
    
    try:
        # 打开词典
        with Dictionary(mdx_file) as dict_obj:
            # 查询单词
            html_content = dict_obj.lookup_html(word)
            
            if not html_content:
                return None, None
            
            # 提取词典 CSS
            dict_css = ""
            try:
                if '<link' in html_content.lower():
                    temp_html = f"<html><head>{html_content}</head><body></body></html>"
                    temp_soup = BeautifulSoup(temp_html, 'lxml')
                    merged_soup = merge_css(temp_soup, mdx_file.parent, dict_obj.impl, None)
                    
                    if merged_soup.head and merged_soup.head.style:
                        dict_css = merged_soup.head.style.string or ""
            except Exception:
                pass  # CSS 提取失败不影响主要功能
            
            # 嵌入图片（转为 base64）
            try:
                temp_soup = BeautifulSoup(f"<html><body>{html_content}</body></html>", 'lxml')
                embedded_soup = embed_images(temp_soup, dict_obj.impl)
                html_content = str(embedded_soup.body)
                html_content = html_content.replace('<body>', '').replace('</body>', '')
            except Exception:
                pass  # 图片嵌入失败不影响主要功能
            
            return html_content, dict_css
    
    except Exception as e:
        # 词典打开或查询失败
        return None, None


def add_css_namespace(css_content: str, dict_name: str) -> str:
    """为 CSS 规则添加词典命名空间,防止多词典样式冲突
    
    Args:
        css_content: 原始 CSS 内容
        dict_name: 词典名称（用于命名空间）
        
    Returns:
        添加了命名空间的 CSS 字符串
        
    Example:
        >>> css = ".word { font-weight: bold; }"
        >>> namespaced = add_css_namespace(css, "大辞泉")
        >>> print(namespaced)
        .yomitan-glossary [data-dictionary="大辞泉"] .word { font-weight: bold; }
    """
    if not css_content:
        return ""
    
    # 命名空间前缀
    namespace = f'.yomitan-glossary [data-dictionary="{dict_name}"]'
    
    # 处理 CSS 规则
    # 1. 分割成单独的规则（按 {} 括号）
    rules = []
    current_rule = ""
    brace_count = 0
    
    for char in css_content:
        current_rule += char
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and current_rule.strip():
                rules.append(current_rule.strip())
                current_rule = ""
    
    # 2. 为每个规则添加命名空间
    namespaced_rules = []
    for rule in rules:
        if not rule or '{' not in rule:
            continue
        
        # 分离选择器和属性
        match = re.match(r'(.+?)\s*\{(.+)\}', rule, re.DOTALL)
        if not match:
            continue
        
        selectors_str, properties = match.groups()
        
        # 分割多个选择器（用逗号分隔）
        selectors = [s.strip() for s in selectors_str.split(',')]
        
        # 为每个选择器添加命名空间
        namespaced_selectors = []
        for selector in selectors:
            if selector:
                # 在选择器前添加命名空间
                namespaced_selector = f"{namespace} {selector}"
                namespaced_selectors.append(namespaced_selector)
        
        # 重组规则
        if namespaced_selectors:
            namespaced_rule = ', '.join(namespaced_selectors) + ' {' + properties + '}'
            namespaced_rules.append(namespaced_rule)
    
    return '\n'.join(namespaced_rules)


def query_multiple_dicts_yomitan(
    mdx_files: List[Tuple[Path, str]], 
    word: str, 
    output_file: Optional[Path] = None
) -> Optional[str]:
    """查询多个词典并组合为 Yomitan 格式
    
    生成符合 Yomitan 浏览器插件标准的多词典 HTML 格式,
    可直接用于 AnkiConnect 的 definition/glossary 字段。
    
    Args:
        mdx_files: [(mdx_path, dict_name), ...] 列表,指定词典文件和显示名称
        word: 要查询的单词
        output_file: 可选的输出文件路径（用于预览）
        
    Returns:
        完整的 Yomitan 格式 HTML 字符串,所有词典均未找到时返回 None
        
    格式说明:
        返回的 HTML 结构为:
        <div class="yomitan-glossary">
          <ol>
            <li data-dictionary="词典1"><i>(词典1)</i> <span>{{HTML}}</span></li>
            <style>{{命名空间化的CSS}}</style>
            <li data-dictionary="词典2"><i>(词典2)</i> <span>{{HTML}}</span></li>
            <style>{{命名空间化的CSS}}</style>
          </ol>
        </div>
        
    Example:
        >>> mdx_dicts = [
        ...     (Path("daijisen.mdx"), "大辞泉 第二版"),
        ...     (Path("meikyou.mdx"), "明鏡日汉双解辞典"),
        ... ]
        >>> html = query_multiple_dicts_yomitan(mdx_dicts, "政権")
        >>> if html:
        ...     # 可直接用于 AnkiConnect addNote 的 definition 字段
        ...     note_fields["definition"] = html
    """
    entries = []  # 存储每个词典的条目
    
    for mdx_file, dict_name in mdx_files:
        html_content, dict_css = query_word_yomitan_format(mdx_file, word, dict_name)
        
        if html_content:
            # 构建单个词典条目（Yomitan 格式）
            entry = f'<li data-dictionary="{dict_name}"><i>({dict_name})</i> <span>{html_content}</span></li>'
            
            # 如果有 CSS,添加 style 标签
            if dict_css:
                # 为 CSS 添加词典命名空间（正确处理每个选择器）
                namespaced_css = add_css_namespace(dict_css, dict_name)
                entry += f'<style>{namespaced_css}</style>'
            
            entries.append(entry)
    
    if not entries:
        return None
    
    # 组合所有条目
    yomitan_html = f'<div style="text-align: left;" class="yomitan-glossary"><ol>{"".join(entries)}</ol></div>'
    
    # 保存到文件（如果指定）- 用于预览调试
    if output_file:
        preview_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{word} - Yomitan Preview</title>
</head>
<body style="background-color: #f5f5f5; padding: 20px;">
{yomitan_html}
</body>
</html>"""
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(preview_html, encoding='utf-8')
    
    return yomitan_html
