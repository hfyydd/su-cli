#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Su-Cli 自动补全系统

提供命令、Agent 名称、文件路径等的智能补全功能
"""

from typing import List, Dict, Optional, Tuple, Set
import re
from pathlib import Path

try:
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.document import Document
    from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.keys import Keys
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False
    # 提供兼容性类
    class Completion:
        def __init__(self, text: str, start_position: int = 0, display: str = None, style: str = ""):
            self.text = text
            self.start_position = start_position
            self.display = display or text
            self.style = style
    
    class Document:
        def __init__(self, text: str = "", cursor_position: int = 0):
            self.text = text
            self.cursor_position = cursor_position
    
    class Completer:
        def get_completions(self, document: Document, complete_event=None):
            return []
    
    class Suggestion:
        def __init__(self, text: str):
            self.text = text
    
    class AutoSuggest:
        def get_suggestion(self, buffer, document):
            return None
    
    class KeyBindings:
        def add(self, *args, **kwargs):
            return lambda f: f
    
    class Keys:
        Tab = 'tab'


class SuCliAutoSuggest(AutoSuggest):
    """
    Su-Cli 自动建议类，实现内联灰色文本补全
    """
    
    def __init__(self):
        """初始化自动建议器"""
        # 基础命令列表
        self.base_commands = {
            # 帮助和退出命令
            '/help': '显示帮助信息',
            '/h': '显示帮助信息（简写）',
            '/exit': '退出程序',
            '/quit': '退出程序',
            '/q': '退出程序（简写）',
            
            # 系统命令
            '/clear': '清屏',
            '/agents': '显示可用的 Agent',
            '/use': '切换到指定的 Agent',
            
            # 历史和重置
            '/history': '显示对话历史',
            '/reset': '清空对话历史并重置线程',
            
            # 界面风格命令
            '/style': '显示或设置界面风格',
            
            # 语言设置命令
            '/lang': '显示当前语言设置',
            '/set_lang': '设置语言',
            
            # 工具命令
            'show': '显示工具调用结果',
        }
        
        # 风格选项
        self.style_options = ['modern', 'minimal', 'classic', 'colorful']
        
        # 语言选项
        self.language_options = ['en', 'zh']
        
        # 可用的 Agents（将在运行时更新）
        self.available_agents = []
        
        # 最近的工具消息数量
        self.recent_tool_count = 0
    
    def update_agents(self, agents: List[str]):
        """更新可用的 Agent 列表"""
        self.available_agents = agents.copy()
    
    def update_tool_count(self, count: int):
        """更新最近工具消息数量"""
        self.recent_tool_count = count
    
    def get_suggestion(self, buffer, document):
        """
        获取自动建议
        
        Args:
            buffer: 缓冲区对象
            document: 文档对象
            
        Returns:
            Suggestion: 建议对象，如果没有建议则返回 None
        """
        text = document.text
        cursor_position = document.cursor_position
        
        # 只在光标在行尾时提供建议
        if cursor_position != len(text):
            return None
        
        # 分析上下文
        context = self._analyze_context(text, cursor_position)
        
        # 获取当前输入的词
        words = text.split()
        if not words:
            current_word = ""
        else:
            # 检查是否以空格结尾
            if text.endswith(' '):
                current_word = ""
            else:
                current_word = words[-1]
        
        # 根据上下文获取最佳建议
        suggestion_text = self._get_best_suggestion(context, current_word, text)
        
        if suggestion_text:
            return Suggestion(suggestion_text)
        
        return None
    
    def _get_best_suggestion(self, context: Dict[str, str], current_word: str, full_text: str) -> Optional[str]:
        """获取最佳建议文本"""
        context_type = context['type']
        
        if context_type == 'command':
            return self._get_best_command_suggestion(current_word)
        elif context_type == 'agent_name':
            return self._get_best_agent_suggestion(current_word)
        elif context_type == 'style_name':
            return self._get_best_style_suggestion(current_word)
        elif context_type == 'language':
            return self._get_best_language_suggestion(current_word)
        elif context_type == 'number':
            return self._get_best_number_suggestion(current_word)
        
        return None
    
    def _get_best_command_suggestion(self, current_word: str) -> Optional[str]:
        """获取最佳命令建议"""
        current_lower = current_word.lower()
        
        # 定义命令优先级（越小优先级越高）
        command_priority = {
            '/help': 1, '/h': 1,
            '/exit': 2, '/quit': 2, '/q': 2,
            '/clear': 3,
            '/agents': 4,
            '/use': 5,
            '/history': 6,
            '/reset': 7,
            '/style': 8,
            '/lang': 9,
            '/set_lang': 10,
            'show': 11,
        }
        
        # 收集所有匹配的命令
        matches = []
        for cmd in self.base_commands.keys():
            if cmd.lower().startswith(current_lower):
                priority = command_priority.get(cmd, 999)
                matches.append((priority, cmd))
        
        # 按优先级排序，取第一个
        if matches:
            matches.sort(key=lambda x: x[0])
            best_cmd = matches[0][1]
            return best_cmd[len(current_word):]
        
        return None
    
    def _get_best_agent_suggestion(self, current_word: str) -> Optional[str]:
        """获取最佳 Agent 建议"""
        current_lower = current_word.lower()
        
        # 定义 Agent 优先级
        agent_priority = {
            'default': 1,
            'deer-flow': 2,
        }
        
        # 收集所有匹配的 Agent
        matches = []
        for agent in self.available_agents:
            if agent.lower().startswith(current_lower):
                priority = agent_priority.get(agent, 999)
                matches.append((priority, agent))
        
        # 按优先级排序，取第一个
        if matches:
            matches.sort(key=lambda x: x[0])
            best_agent = matches[0][1]
            return best_agent[len(current_word):]
        
        return None
    
    def _get_best_style_suggestion(self, current_word: str) -> Optional[str]:
        """获取最佳风格建议"""
        current_lower = current_word.lower()
        
        # 定义风格优先级（按使用频率）
        style_priority = {
            'modern': 1,
            'minimal': 2,
            'classic': 3,
            'colorful': 4,
        }
        
        # 收集所有匹配的风格
        matches = []
        for style in self.style_options:
            if style.lower().startswith(current_lower):
                priority = style_priority.get(style, 999)
                matches.append((priority, style))
        
        # 按优先级排序，取第一个
        if matches:
            matches.sort(key=lambda x: x[0])
            best_style = matches[0][1]
            return best_style[len(current_word):]
        
        return None
    
    def _get_best_language_suggestion(self, current_word: str) -> Optional[str]:
        """获取最佳语言建议"""
        current_lower = current_word.lower()
        
        # 定义语言优先级（中文优先）
        language_priority = {
            'zh': 1,
            'en': 2,
        }
        
        # 收集所有匹配的语言
        matches = []
        for lang in self.language_options:
            if lang.lower().startswith(current_lower):
                priority = language_priority.get(lang, 999)
                matches.append((priority, lang))
        
        # 按优先级排序，取第一个
        if matches:
            matches.sort(key=lambda x: x[0])
            best_lang = matches[0][1]
            return best_lang[len(current_word):]
        
        return None
    
    def _get_best_number_suggestion(self, current_word: str) -> Optional[str]:
        """获取最佳数字建议"""
        # 如果当前词为空，建议 "1"
        if current_word == "":
            return "1"
        
        # 如果当前词是数字开头，寻找匹配的数字
        if current_word.isdigit():
            for i in range(1, min(self.recent_tool_count + 1, 11)):
                if str(i).startswith(current_word):
                    return str(i)[len(current_word):]
        
        return None
    
    def _analyze_context(self, text: str, cursor_position: int) -> Dict[str, str]:
        """
        分析当前输入的上下文，确定补全类型
        
        Returns:
            Dict: 包含上下文信息的字典
        """
        # 获取光标前的文本（不去除空格，保持原始格式）
        before_cursor = text[:cursor_position]
        
        # 分析具体命令的参数
        words = before_cursor.split()
        if not words:
            return {'type': 'command'}
        
        first_word = words[0].lower()
        
        # 检查是否在命令后面有空格（表示要输入参数）
        has_trailing_space = before_cursor.endswith(' ')
        
        # /use 命令后补全 Agent 名称
        if first_word == '/use' and (len(words) > 1 or has_trailing_space):
            return {'type': 'agent_name'}
        
        # /style 命令后补全风格名称
        if first_word == '/style' and (len(words) > 1 or has_trailing_space):
            return {'type': 'style_name'}
        
        # /set_lang 命令后补全语言
        if first_word == '/set_lang' and (len(words) > 1 or has_trailing_space):
            return {'type': 'language'}
        
        # show 命令后补全数字
        if first_word == 'show' and (len(words) > 1 or has_trailing_space):
            return {'type': 'number'}
        
        # 如果是以 / 开头，或者是空输入，或者是单个命令词（没有空格），进行命令补全
        if before_cursor.strip().startswith('/') or before_cursor.strip() == '' or (len(words) == 1 and not has_trailing_space):
            return {'type': 'command'}
        
        # 其他情况不进行补全
        return {'type': 'none'}


class SuCliCompleter(Completer):
    """Su-Cli 的自动补全器"""
    
    def __init__(self):
        """初始化补全器"""
        # 基本命令列表
        self.base_commands = {
            # 系统命令
            '/help': '显示帮助信息',
            '/h': '显示帮助信息（简写）',
            '/exit': '退出程序',
            '/quit': '退出程序',
            '/q': '退出程序（简写）',
            '/clear': '清屏',
            
            # Agent 管理命令
            '/agents': '显示可用的 Agent',
            '/use': '切换到指定的 Agent',
            
            # 历史管理命令
            '/history': '显示对话历史',
            '/reset': '清空对话历史并重置线程',
            
            # 界面风格命令
            '/style': '显示或设置界面风格',
            
            # 语言设置命令
            '/lang': '显示当前语言设置',
            '/set_lang': '设置语言',
            
            # 工具命令
            'show': '显示工具调用结果',
        }
        
        # 风格选项
        self.style_options = ['modern', 'minimal', 'classic', 'colorful']
        
        # 语言选项
        self.language_options = ['en', 'zh']
        
        # 可用的 Agents（将在运行时更新）
        self.available_agents: List[str] = []
        
        # 最近的工具消息数量（用于 show 命令补全）
        self.recent_tool_count = 0
    
    def update_agents(self, agents: List[str]):
        """更新可用的 Agent 列表"""
        self.available_agents = agents.copy()
    
    def update_tool_count(self, count: int):
        """更新最近工具消息数量"""
        self.recent_tool_count = count
    
    def get_completions(self, document: Document, complete_event=None):
        """
        获取补全建议
        
        Args:
            document: 当前文档状态
            complete_event: 补全事件（可选）
            
        Yields:
            Completion: 补全建议对象
        """
        text = document.text
        cursor_position = document.cursor_position
        
        # 获取当前词的开始和结束位置
        word_start, word_end = self._get_current_word_bounds(text, cursor_position)
        current_word = text[word_start:cursor_position]
        
        # 分析当前输入的上下文
        context = self._analyze_context(text, cursor_position)
        
        # 根据上下文生成补全建议
        completions = []
        
        if context['type'] == 'command':
            completions = self._get_command_completions(current_word, word_start, cursor_position)
        elif context['type'] == 'agent_name':
            completions = self._get_agent_completions(current_word, word_start, cursor_position)
        elif context['type'] == 'style_name':
            completions = self._get_style_completions(current_word, word_start, cursor_position)
        elif context['type'] == 'language':
            completions = self._get_language_completions(current_word, word_start, cursor_position)
        elif context['type'] == 'number':
            completions = self._get_number_completions(current_word, word_start, cursor_position)
        
        return completions
    
    def _get_current_word_bounds(self, text: str, cursor_position: int) -> Tuple[int, int]:
        """
        获取当前词的边界位置
        
        Returns:
            Tuple[int, int]: (开始位置, 结束位置)
        """
        # 向前查找词的开始
        start = cursor_position
        while start > 0 and text[start - 1] not in ' \t\n':
            start -= 1
        
        # 向后查找词的结束
        end = cursor_position
        while end < len(text) and text[end] not in ' \t\n':
            end += 1
        
        return start, end
    
    def _analyze_context(self, text: str, cursor_position: int) -> Dict[str, str]:
        """
        分析当前输入的上下文，确定补全类型
        
        Returns:
            Dict: 包含上下文信息的字典
        """
        # 获取光标前的文本（不去除空格，保持原始格式）
        before_cursor = text[:cursor_position]
        
        # 分析具体命令的参数
        words = before_cursor.split()
        if not words:
            return {'type': 'command'}
        
        first_word = words[0].lower()
        
        # 检查是否在命令后面有空格（表示要输入参数）
        has_trailing_space = before_cursor.endswith(' ')
        
        # /use 命令后补全 Agent 名称
        if first_word == '/use' and (len(words) > 1 or has_trailing_space):
            return {'type': 'agent_name'}
        
        # /style 命令后补全风格名称
        if first_word == '/style' and (len(words) > 1 or has_trailing_space):
            return {'type': 'style_name'}
        
        # /set_lang 命令后补全语言
        if first_word == '/set_lang' and (len(words) > 1 or has_trailing_space):
            return {'type': 'language'}
        
        # show 命令后补全数字
        if first_word == 'show' and (len(words) > 1 or has_trailing_space):
            return {'type': 'number'}
        
        # 如果是以 / 开头，或者是空输入，或者是单个命令词（没有空格），进行命令补全
        if before_cursor.strip().startswith('/') or before_cursor.strip() == '' or (len(words) == 1 and not has_trailing_space):
            return {'type': 'command'}
        
        # 其他情况不进行补全
        return {'type': 'none'}
    
    def _get_command_completions(self, current_word: str, word_start: int, cursor_position: int) -> List[Completion]:
        """获取命令补全建议"""
        completions = []
        
        # 过滤匹配的命令
        current_lower = current_word.lower()
        
        for cmd, description in self.base_commands.items():
            if cmd.lower().startswith(current_lower):
                # 计算需要补全的部分
                completion_text = cmd[len(current_word):]
                
                # 创建补全对象
                completion = Completion(
                    text=completion_text,
                    start_position=0,
                    display=f"{cmd} - {description}",
                    style="class:completion.command"
                )
                completions.append(completion)
        
        return completions
    
    def _get_agent_completions(self, current_word: str, word_start: int, cursor_position: int) -> List[Completion]:
        """获取 Agent 名称补全建议"""
        completions = []
        current_lower = current_word.lower()
        
        for agent in self.available_agents:
            if agent.lower().startswith(current_lower):
                completion_text = agent[len(current_word):]
                completion = Completion(
                    text=completion_text,
                    start_position=0,
                    display=f"{agent} - Agent",
                    style="class:completion.agent"
                )
                completions.append(completion)
        
        return completions
    
    def _get_style_completions(self, current_word: str, word_start: int, cursor_position: int) -> List[Completion]:
        """获取风格名称补全建议"""
        completions = []
        current_lower = current_word.lower()
        
        for style in self.style_options:
            if style.lower().startswith(current_lower):
                completion_text = style[len(current_word):]
                completion = Completion(
                    text=completion_text,
                    start_position=0,
                    display=f"{style} - 界面风格",
                    style="class:completion.style"
                )
                completions.append(completion)
        
        return completions
    
    def _get_language_completions(self, current_word: str, word_start: int, cursor_position: int) -> List[Completion]:
        """获取语言补全建议"""
        completions = []
        current_lower = current_word.lower()
        
        language_names = {
            'en': 'English',
            'zh': '中文'
        }
        
        for lang, name in language_names.items():
            # 只有当前词为空或者语言代码以当前词开头时才显示
            if current_word == '' or lang.lower().startswith(current_lower):
                completion_text = lang[len(current_word):]
                completion = Completion(
                    text=completion_text,
                    start_position=0,
                    display=f"{lang} - {name}",
                    style="class:completion.language"
                )
                completions.append(completion)
        
        return completions
    
    def _get_number_completions(self, current_word: str, word_start: int, cursor_position: int) -> List[Completion]:
        """获取数字补全建议（用于 show 命令）"""
        completions = []
        
        # 只有当前词是数字开头或为空时才提供数字补全
        if current_word == '' or current_word.isdigit():
            for i in range(1, min(self.recent_tool_count + 1, 11)):  # 最多显示10个选项
                if str(i).startswith(current_word):
                    completion_text = str(i)[len(current_word):]
                    completion = Completion(
                        text=completion_text,
                        start_position=0,
                        display=f"{i} - 查看第{i}个工具调用结果",
                        style="class:completion.number"
                    )
                    completions.append(completion)
        
        return completions


# 全局实例
_completer_instance: Optional[SuCliCompleter] = None
_auto_suggest_instance: Optional[SuCliAutoSuggest] = None


def get_completer() -> SuCliCompleter:
    """获取全局补全器实例（保留旧版本兼容性）"""
    global _completer_instance
    if _completer_instance is None:
        _completer_instance = SuCliCompleter()
    return _completer_instance


def get_auto_suggest() -> SuCliAutoSuggest:
    """获取全局自动建议器实例"""
    global _auto_suggest_instance
    if _auto_suggest_instance is None:
        _auto_suggest_instance = SuCliAutoSuggest()
    return _auto_suggest_instance


def update_completer_agents(agents: List[str]):
    """更新自动建议器的 Agent 列表"""
    auto_suggest = get_auto_suggest()
    auto_suggest.update_agents(agents)


def update_completer_tool_count(count: int):
    """更新自动建议器的工具消息数量"""
    auto_suggest = get_auto_suggest()
    auto_suggest.update_tool_count(count)


# 内联补全样式定义
COMPLETION_STYLES = {
    # 内联补全的灰色文本样式
    'autosuggestion': '#666666',              # 灰色建议文本
    'autosuggestion.cursor': '#888888',       # 光标在建议文本上时的样式
}


def create_key_bindings():
    """创建 key bindings 来处理 Tab 键接受建议"""
    if not PROMPT_TOOLKIT_AVAILABLE:
        return None
    
    bindings = KeyBindings()
    
    @bindings.add(Keys.Tab)
    def _(event):
        """Tab 键接受自动建议"""
        buffer = event.app.current_buffer
        suggestion = buffer.suggestion
        
        if suggestion:
            # 接受建议文本
            buffer.insert_text(suggestion.text)
        else:
            # 如果没有建议，插入制表符（默认行为）
            buffer.insert_text('    ')  # 4个空格作为制表符
    
    @bindings.add(Keys.ControlRight)  # Ctrl + 右方向键也可以接受建议
    def _(event):
        """Ctrl + 右方向键接受自动建议"""
        buffer = event.app.current_buffer
        suggestion = buffer.suggestion
        
        if suggestion:
            buffer.insert_text(suggestion.text)
    
    return bindings 


def get_prompt_config():
    """
    获取完整的 prompt 配置，包括自动建议和按键绑定
    
    Returns:
        dict: 包含 auto_suggest 和 key_bindings 的配置字典
    """
    if not PROMPT_TOOLKIT_AVAILABLE:
        return {
            'auto_suggest': None,
            'key_bindings': None
        }
    
    return {
        'auto_suggest': get_auto_suggest(),
        'key_bindings': create_key_bindings()
    }