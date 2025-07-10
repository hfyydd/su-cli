import sys
import asyncio
import logging
import uuid
import os
import json
import importlib
import re
import signal
import time
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.columns import Columns
from rich.align import Align
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.markdown import Markdown
from rich.layout import Layout
from rich.box import ROUNDED
from rich_gradient import Text as GradientText

# 提示工具包将按需导入

# 国际化配置
I18N = {
    "en": {
        # Welcome and titles
        "welcome_title": "🚀 Welcome to Su-Cli command line tool!",
        "welcome_subtitle": "A powerful and simple command line assistant", 
        "quick_start_guide": "✨ Quick Start Guide ✨",
        "tips": [
            "🤖 Chat with Agent",
            "🔗 Support MCP Protocol",
            "⚡ Based on LangGraph",
            "🔄 Support interrupt recovery"
        ],
        "footer_help": "Type '/help' or '/h' for more help | Type '/exit' or '/q' to quit",
        
        # Commands and help
        "help_title": "🔧 Help",
        "help_content": """[bold cyan]Su-Cli Help Information[/bold cyan]

📋 [yellow]Available Commands:[/yellow]
  • [green]/help[/green] | [green]/h[/green] - Show this help information
  • [green]/exit[/green] | [green]/q[/green] - Exit program
  • [green]/clear[/green] - Clear screen
  • [green]/agents[/green] - Show available agents
  • [green]/use <name>[/green] - Switch to specified agent
  • [green]/history[/green] - Show conversation history
  • [green]/reset[/green] - Clear conversation history and reset thread
  • [green]/style[/green] - Show available interface styles
  • [green]/style <name>[/green] - Switch to specified style
  • [green]/lang[/green] - Show current language settings
  • [green]/set_lang <lang>[/green] - Set language (en/zh)
  • [green]show <n>[/green] - View detailed results of the nth tool call

🔧 [yellow]Tool Results Viewer:[/yellow]
  • Tool call results are automatically collapsed when displayed
  • Use 'show 1', 'show 2' etc. to view detailed results
  • Reduces interface clutter, view details on demand

🤔 [yellow]Interrupt Feature:[/yellow]
  • Agent will request your confirmation when needed
  • Type 'yes', 'y' to agree
  • Type other content to cancel operation

💡 [yellow]Tip:[/yellow] Type message directly to chat with current agent""",
        
        # Agent messages
        "agents_title": "🤖 Agents",
        "agents_current": "Current agent:",
        "no_agents": "No available agents",
        "agent_switch_success": "Switched to agent: {}",
        "agent_not_found": "Agent '{}' does not exist",
        "agent_available": "Available agents: {}",
        
        # History
        "history_title": "📝 Conversation History ({} conversations)",
        "no_history": "📝 No conversation history",
        "history_reset": "🔄 Conversation history cleared, new thread started",
        
        # Styles
        "style_title": "🎨 Interface Styles",
        "style_current": "Current style:",
        "style_available": "Available styles:",
        "style_switch_success": "Switched to {} style",
        "style_not_found": "Style '{}' does not exist",
        "style_available_list": "Available styles: {}",
        
        # Language
        "lang_title": "🌐 Language Settings",
        "lang_current": "Current language:",
        "lang_available": "Available languages:",
        "lang_switch_success": "Language switched to {}",
        "lang_not_found": "Language '{}' not supported",
        "lang_available_list": "Available languages: {}",
        
        # System messages
        "system_initializing": "Starting to initialize agent system",
        "system_ready": "Agent system is ready, currently using: {}",
        "system_init_failed": "Failed to initialize agent system: {}",
        "system_init_warning": "Agent system initialization failed, some features will be unavailable",
        
        # Agent operations
        "agent_loading": "Loading agent: {}",
        "agent_load_failed": "Unable to load agent module: {}",
        "agent_no_graph": "Agent {} has no graph object",
        "agent_thinking": "{} is thinking...",
        "agent_processing": "{} is processing your confirmation...",
        "agent_no_interrupt": "This agent does not support interrupt recovery, cannot continue",
        "agent_interrupt_tip": "Tip: You can restart the conversation",
        
        # Errors
        "error_import_core": "Failed to import core module: {}",
        "error_no_agent": "No available agent",
        "error_agent_load": "Unable to load agent: {}",
        "error_agent_call": "Failed to call agent: {}",
        "error_operation_failed": "Operation failed, please try again",
        "error_command_import": "Unable to import Command, please check langgraph version",
        
        # Confirmations
        "confirm_title": "🤔 Need Your Confirmation",
        "confirm_question": "Do you confirm to process this request? (yes/no)",
        "confirm_accepted": "✨ Confirmed, processing...",
        "confirm_cancelled": "Operation cancelled",
        
        # General
        "goodbye": "👋 Thank you for using Su-Cli, goodbye!",
        "graceful_exit": "Gracefully exiting Su-Cli...",
        "force_exit": "Force exit...",
        "user_label": "USER",
        "assistant_label": "Assistant",
        "processing": "Processing...",
        "please_confirm": "Please confirm",
        "retry": "Please try again",
        "cancelled": "Cancelled",
        "thinking": "Thinking...",
        "confirmed": "Confirmed",
        "rejected": "Rejected",
    },
    "zh": {
        # Welcome and titles
        "welcome_title": "🚀 欢迎使用 Su-Cli 命令行工具！",
        "welcome_subtitle": "一个强大而简洁的命令行助手",
        "quick_start_guide": "✨ 快速开始指南 ✨",
        "tips": [
            "🤖 与Agent 对话交流",
            "🔗 支持 MCP 协议集成", 
            "⚡ 基于 LangGraph ",
            "🔄 支持中断恢复功能"
        ],
        "footer_help": "输入 '/help' 或 '/h' 获取更多帮助信息 | 输入 '/exit' 或 '/q' 退出程序",
        
        # Commands and help
        "help_title": "🔧 帮助",
        "help_content": """[bold cyan]Su-Cli 帮助信息[/bold cyan]

📋 [yellow]可用命令：[/yellow]
  • [green]/help[/green] | [green]/h[/green] - 显示此帮助信息
  • [green]/exit[/green] | [green]/q[/green] - 退出程序
  • [green]/clear[/green] - 清屏
  • [green]/agents[/green] - 显示可用的 agents
  • [green]/use <name>[/green] - 切换到指定的 agent
  • [green]/history[/green] - 显示对话历史
  • [green]/reset[/green] - 清空对话历史并重置对话线程
  • [green]/style[/green] - 显示可用的界面风格
  • [green]/style <name>[/green] - 切换到指定风格
  • [green]/lang[/green] - 显示当前语言设置
  • [green]/set_lang <lang>[/green] - 设置语言 (en/zh)
  • [green]show <n>[/green] - 查看第n个工具调用的详细结果

🔧 [yellow]工具结果查看器：[/yellow]
  • 工具调用结果会自动折叠显示
  • 使用 'show 1', 'show 2' 等命令查看详细结果
  • 减少界面干扰，按需查看详细信息

🤔 [yellow]中断功能：[/yellow]
  • Agent 会在需要时请求您的确认
  • 输入 'yes'、'y'、'是'、'确认' 来同意
  • 输入其他内容来取消操作

💡 [yellow]提示：[/yellow] 直接输入消息与当前 agent 对话""",
        
        # Agent messages
        "agents_title": "🤖 Agents",
        "agents_current": "当前 agent:",
        "no_agents": "没有可用的 agents",
        "agent_switch_success": "已切换到 agent: {}",
        "agent_not_found": "Agent '{}' 不存在",
        "agent_available": "可用的 agents: {}",
        
        # History
        "history_title": "📝 对话历史 ({} 轮对话)",
        "no_history": "📝 暂无对话历史",
        "history_reset": "🔄 对话历史已清空，已开始新的对话线程",
        
        # Styles
        "style_title": "🎨 界面风格",
        "style_current": "当前风格:",
        "style_available": "可用风格:",
        "style_switch_success": "已切换到 {} 风格",
        "style_not_found": "风格 '{}' 不存在",
        "style_available_list": "可用风格: {}",
        
        # Language
        "lang_title": "🌐 语言设置",
        "lang_current": "当前语言:",
        "lang_available": "可用语言:",
        "lang_switch_success": "语言已切换到 {}",
        "lang_not_found": "不支持语言 '{}'",
        "lang_available_list": "可用语言: {}",
        
        # System messages
        "system_initializing": "开始初始化 agent 系统",
        "system_ready": "Agent 系统已就绪，当前使用: {}",
        "system_init_failed": "初始化 agent 系统失败: {}",
        "system_init_warning": "Agent 系统初始化失败，部分功能将不可用",
        
        # Agent operations
        "agent_loading": "开始加载 agent: {}",
        "agent_load_failed": "无法加载 agent 模块: {}",
        "agent_no_graph": "Agent {} 没有 graph 对象",
        "agent_thinking": "{} 正在思考...",
        "agent_processing": "{} 正在处理您的确认...",
        "agent_no_interrupt": "该 agent 不支持中断恢复功能，无法继续执行",
        "agent_interrupt_tip": "提示: 可以重新开始对话",
        
        # Errors
        "error_import_core": "导入 core 模块失败: {}",
        "error_no_agent": "没有可用的 agent",
        "error_agent_load": "无法加载 agent: {}",
        "error_agent_call": "调用 agent 失败: {}",
        "error_operation_failed": "操作失败，请重试",
        "error_command_import": "无法导入Command，请检查langgraph版本",
        
        # Confirmations
        "confirm_title": "🤔 需要您的确认",
        "confirm_question": "您确认要处理这个请求吗？ (yes/no)",
        "confirm_accepted": "✨ 已确认，继续处理中...",
        "confirm_cancelled": "操作已取消",
        
        # General
        "goodbye": "👋 感谢使用 Su-Cli，再见！",
        "graceful_exit": "正在优雅退出 Su-Cli...",
        "force_exit": "强制退出...",
        "user_label": "用户",
        "assistant_label": "助手",
        "processing": "正在处理...",
        "please_confirm": "请确认",
        "retry": "请重试",
        "cancelled": "已取消",
        "thinking": "正在思考...",
        "confirmed": "已确认",
        "rejected": "已拒绝",
    }
}

# 配置常量
CONFIG = {
    "LOGGING_LEVEL": logging.WARNING,
    "PROMPT_STYLES": {
        "modern": {"en": "Modern minimalist style (with border)", "zh": "现代简约风格 (带边框)"},
        "minimal": {"en": "Minimal style", "zh": "极简风格"},
        "classic": {"en": "Classic style (bash-like)", "zh": "经典风格 (类似 bash)"},
        "colorful": {"en": "Colorful style (with icons)", "zh": "彩色风格 (带图标)"}
    },
    "DEFAULT_PROMPT_STYLE": "modern",
    "DEFAULT_LANGUAGE": "en",
    "CONFIRMATION_CHOICES": ["yes", "y", "是", "确认", "no", "n", "否", "取消"],
    "CONFIRMATION_YES": ["yes", "y", "是", "确认"],
    "EXIT_COMMANDS": ['/exit', '/quit', '/q', 'exit', 'quit'],
    "HELP_COMMANDS": ['/help', '/h', 'help'],
    "CLEAR_COMMANDS": ['/clear', 'clear'],
    "AGENTS_COMMANDS": ['/agents', 'agents'],
    "HISTORY_COMMANDS": ['/history', 'history'],
    "RESET_COMMANDS": ['/reset', 'reset'],
    "STYLE_COMMANDS": ['/style', 'style'],
    "LANG_COMMANDS": ['/lang', 'lang'],
    "SHOW_COMMANDS": ['show'],
}

# 设置日志级别和格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('su-cli.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 设置第三方库的日志级别
logging.getLogger("core").setLevel(CONFIG["LOGGING_LEVEL"])
logging.getLogger("httpx").setLevel(CONFIG["LOGGING_LEVEL"])
logging.getLogger("langgraph").setLevel(CONFIG["LOGGING_LEVEL"])

# 添加 core 模块到路径
sys.path.insert(0, str(Path(__file__).parent / "core"))

try:
    from core import scanner, scan_agents, get_available_agents, get_valid_agents
except ImportError as e:
    logger.error(f"Failed to import core module: {e}")
    sys.exit(1)

# 全局变量
console = Console()
conversation_history = []
current_agent = None
available_agents = []
prompt_style = CONFIG["DEFAULT_PROMPT_STYLE"]
current_language = CONFIG["DEFAULT_LANGUAGE"]
current_thread_id = str(uuid.uuid4())
recent_tool_messages = []  # 存储最近的工具调用消息
is_exiting = False  # 退出状态标志


def graceful_exit(signum=None, frame=None):
    """
    优雅退出处理函数
    
    Args:
        signum: 信号编号
        frame: 当前堆栈帧
    """
    global is_exiting
    
    if is_exiting:
        # 如果已经在退出过程中，强制退出
        console.print(f"\n[red]{t('force_exit')}[/red]")
        os._exit(0)
    
    is_exiting = True
    
    try:
        # 清除当前行并移动光标
        console.print("\n")
        
        # 创建优雅的退出动画
        exit_text = GradientText(
            t('graceful_exit'),
            colors=["#f093fb", "#f5576c", "#4facfe"]
        )
        
        # 显示退出提示
        with console.status(exit_text, spinner="dots2"):
            time.sleep(1.0)  # 短暂停顿让用户看到提示
        
        # 显示告别消息
        goodbye_text = GradientText(
            t('goodbye'),
            colors=["#667eea", "#764ba2", "#f093fb"]
        )
        
        farewell_panel = Panel(
            Align.center(goodbye_text),
            style="dim blue",
            border_style="dim cyan",
            padding=(1, 2)
        )
        
        console.print(farewell_panel)
        console.print()
        
    except Exception:
        # 如果显示过程中出错，直接退出
        console.print(f"\n{t('goodbye')}")
    
    finally:
        # 确保程序退出
        os._exit(0)


def setup_signal_handlers():
    """设置信号处理器"""
    try:
        # 设置 SIGINT (Ctrl+C) 处理器
        signal.signal(signal.SIGINT, graceful_exit)
        
        # 在支持的系统上设置 SIGTERM 处理器
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, graceful_exit)
            
    except (OSError, ValueError) as e:
        # 在某些环境中可能无法设置信号处理器
        logger.debug(f"无法设置信号处理器: {e}")


def t(key: str, *args, **kwargs) -> str:
    """
    获取当前语言的翻译文本
    
    Args:
        key: 翻译键
        *args: 格式化参数
        **kwargs: 格式化参数
    
    Returns:
        str: 翻译后的文本
    """
    global current_language
    
    text = I18N.get(current_language, {}).get(key, key)
    
    # 如果当前语言没有该键，尝试使用英语
    if text == key and current_language != "en":
        text = I18N.get("en", {}).get(key, key)
    
    # 格式化文本
    if args:
        try:
            text = text.format(*args)
        except (IndexError, ValueError):
            pass
    
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    
    return text


def get_available_languages() -> List[str]:
    """获取可用语言列表"""
    return list(I18N.keys())


def set_language(lang: str) -> bool:
    """
    设置当前语言
    
    Args:
        lang: 语言代码
    
    Returns:
        bool: 是否设置成功
    """
    global current_language
    
    if lang in I18N:
        current_language = lang
        return True
    return False


def create_beautiful_prompt(agent_name: Optional[str] = None, style: str = "modern") -> str:
    """
    创建美观的命令行提示符
    
    Args:
        agent_name: 当前使用的 agent 名称，可为 None
        style: 提示符风格，支持 modern, minimal, classic, colorful
    
    Returns:
        str: 用户输入的内容，或者退出命令
    
    Raises:
        KeyboardInterrupt: 用户按下 Ctrl+C
        EOFError: 用户按下 Ctrl+D
    """
    try:
        agent_display = _format_agent_name(agent_name)
        user_input = _get_styled_input(agent_display, style)
        
        # 显示用户输入（统一的回显样式）
        if user_input:
            console.print()
            user_display = Text()
            user_display.append("   💬 ", style="bright_blue")
            user_display.append(user_input, style="white")
            console.print(user_display)
            console.print()
        
        return user_input
        
    except (KeyboardInterrupt, EOFError):
        # 如果在输入过程中按下 Ctrl+C，触发优雅退出
        graceful_exit()
        return "/exit"


def _format_agent_name(agent_name: Optional[str]) -> str:
    """格式化 agent 名称用于显示"""
    if agent_name:
        agent_display = agent_name.replace("_", " ").title()
        return agent_display
    return "CLI"


def _get_styled_input(agent_display: str, style: str) -> str:
    """根据风格获取用户输入"""
    if style == "modern":
        return _get_modern_input(agent_display)
    elif style == "minimal":
        return _get_minimal_input(agent_display)
    elif style == "classic":
        return _get_classic_input(agent_display)
    elif style == "colorful":
        return _get_colorful_input(agent_display)
    else:
        return _get_default_input(agent_display)


def _get_prompt_text(agent_display: str, style: str) -> str:
    """生成提示符文本"""
    if style == "modern":
        if agent_display != "CLI":
            return f"┌─ SuCli @ {agent_display} ─┐\n└─ ❯ "
        else:
            return "┌─ SuCli ─┐\n└─ ❯ "
    elif style == "minimal":
        if agent_display != "CLI":
            return f"su:{agent_display.lower()} ❯ "
        else:
            return "su ❯ "
    elif style == "classic":
        if agent_display != "CLI":
            return f"[SuCli@{agent_display}]$ "
        else:
            return "[SuCli]$ "
    elif style == "colorful":
        if agent_display != "CLI":
            return f"🚀 SuCli 🤖 {agent_display} ➤ "
        else:
            return "🚀 SuCli ➤ "
    else:
        return "SuCli > "


def _get_modern_input(agent_display: str) -> str:
    """现代简约风格输入"""
    # 首先显示第一行
    first_line = Text()
    first_line.append("┌─ ", style="bright_cyan")
    first_line.append("SuCli", style="bold bright_white")
    if agent_display != "CLI":
        first_line.append(" @ ", style="dim")
        first_line.append(agent_display, style="bright_magenta")
    first_line.append(" ─┐", style="bright_cyan")
    
    console.print(first_line)
    
    # 使用同步输入避免事件循环冲突
    try:
        from prompt_toolkit import prompt
        from prompt_toolkit.history import InMemoryHistory
        # 在同步上下文中使用 prompt_toolkit
        import nest_asyncio
        nest_asyncio.apply()
        return prompt("└─ ❯ ", history=InMemoryHistory()).strip()
    except (ImportError, RuntimeError):
        # Fallback 使用 rich prompt
        from rich.prompt import Prompt
        return Prompt.ask("└─ ❯ ").strip()


def _get_minimal_input(agent_display: str) -> str:
    """极简风格输入"""
    if agent_display != "CLI":
        prompt_text = f"su:{agent_display.lower()} ❯ "
    else:
        prompt_text = "su ❯ "
    
    try:
        from prompt_toolkit import prompt
        from prompt_toolkit.history import InMemoryHistory
        import nest_asyncio
        nest_asyncio.apply()
        return prompt(prompt_text, history=InMemoryHistory()).strip()
    except (ImportError, RuntimeError):
        from rich.prompt import Prompt
        return Prompt.ask(prompt_text).strip()


def _get_classic_input(agent_display: str) -> str:
    """经典风格输入"""
    if agent_display != "CLI":
        prompt_text = f"[SuCli@{agent_display}]$ "
    else:
        prompt_text = "[SuCli]$ "
    
    try:
        from prompt_toolkit import prompt
        from prompt_toolkit.history import InMemoryHistory
        return prompt(prompt_text, history=InMemoryHistory()).strip()
    except ImportError:
        from rich.prompt import Prompt
        return Prompt.ask(prompt_text).strip()


def _get_colorful_input(agent_display: str) -> str:
    """彩色风格输入"""
    if agent_display != "CLI":
        prompt_text = f"🚀 SuCli 🤖 {agent_display} ➤ "
    else:
        prompt_text = "🚀 SuCli ➤ "
    
    try:
        from prompt_toolkit import prompt
        from prompt_toolkit.history import InMemoryHistory
        return prompt(prompt_text, history=InMemoryHistory()).strip()
    except ImportError:
        from rich.prompt import Prompt
        return Prompt.ask(prompt_text).strip()


def _get_default_input(agent_display: str) -> str:
    """默认输入方式"""
    try:
        from prompt_toolkit import prompt
        from prompt_toolkit.history import InMemoryHistory
        return prompt("SuCli > ", history=InMemoryHistory()).strip()
    except ImportError:
        from rich.prompt import Prompt
        return Prompt.ask("SuCli > ").strip()


def initialize_agent_system() -> bool:
    """初始化 agent 系统"""
    global available_agents, current_agent
    
    try:
        agents = scan_agents()
        # 只获取有效的 agents
        valid_agents = get_valid_agents()
        available_agents = list(valid_agents.keys())
        
        if not available_agents:
            console.print(f"❌ [red]{t('no_agents')}[/red]")
            return False
        
        # 默认选择 'default' agent，如果不存在则选择第一个 agent
        if "default" in available_agents:
            current_agent = "default"
        else:
            current_agent = available_agents[0]
        console.print(f"✅ [green]{t('system_ready', current_agent)}[/green]")
        
        return True
        
    except Exception as e:
        logger.error(t("system_init_failed", e), exc_info=True)
        console.print(f"❌ [red]{t('system_init_failed', e)}[/red]")
        return False


def create_message_state(user_input: str, message_history: List[Dict] = None) -> Dict[str, Any]:
    """
    创建符合 Langgraph State 格式的消息状态
    """
    try:
        from langchain_core.messages import HumanMessage, AIMessage
        
        messages = []
        
        # 添加历史消息
        if message_history:
            for msg in message_history:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # 添加当前用户输入
        messages.append(HumanMessage(content=user_input))
        
        return {
            "messages": messages,
            "confirmed": None,
            "user_input": None
        }
        
    except ImportError:
        # 简单格式兼容
        messages = message_history or []
        messages.append({"role": "user", "content": user_input})
        return {
            "messages": messages,
            "confirmed": None,
            "user_input": None
        }


def load_agent_graph(agent_name: str) -> Tuple[Optional[Any], Optional[Any]]:
    """
    加载指定 agent 的 graph 对象
    
    Returns:
        tuple: (graph, graph_with_memory) - 普通graph和带内存的graph
    """
    try:
        # 加载 agent 模块
        module = scanner.load_agent_module(agent_name)
        if not module:
            return None, None
        
        # 获取 graph 对象
        if not hasattr(module, 'graph'):
            return None, None
        
        graph = module.graph
        graph_with_memory = None
        
        # 尝试获取带内存的 graph
        try:
            agent_info = scanner.get_agent_info(agent_name)
            if agent_info:
                graph_with_memory = _build_graph_with_memory(agent_info)
        except Exception:
            pass
        
        return graph, graph_with_memory
        
    except Exception as e:
        logger.error(f"Failed to load agent graph: {e}", exc_info=True)
        return None, None


def _build_graph_with_memory(agent_info: Dict) -> Optional[Any]:
    """
    构建带内存的 graph 对象
    """
    agent_path = scanner.project_root / agent_info["path"]
    src_path = agent_path / "src"
    
    if not src_path.exists():
        return None
    
    import sys
    import os
    import importlib
    import json
    
    original_path = sys.path.copy()
    original_cwd = os.getcwd()
    
    try:
        # 添加 src 路径到 sys.path
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        # 切换到 agent 目录
        os.chdir(agent_path)
        
        # 读取 langgraph.json 配置
        langgraph_json_path = agent_path / "langgraph.json"
        if not langgraph_json_path.exists():
            return None
        
        with open(langgraph_json_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 获取第一个graph的模块路径
        graphs = config.get('graphs', {})
        if not graphs:
            return None
        
        # 取第一个graph配置
        first_graph_path = list(graphs.values())[0]
        
        # 解析路径格式：./src/agent/graph.py:graph -> src.agent.graph
        if ':' not in first_graph_path:
            return None
        
        module_path = first_graph_path.split(':')[0]
        # 去掉 ./ 前缀，转换为Python模块路径
        module_path = module_path.lstrip('./').replace('/', '.').replace('.py', '')
        
        # 清除可能的缓存模块
        modules_to_clear = [module_path, f"{module_path}.builder"]
        for mod in modules_to_clear:
            if mod in sys.modules:
                del sys.modules[mod]
        
        # 尝试导入模块并查找 build_graph_with_memory 函数
        graph_module = importlib.import_module(module_path)
        if hasattr(graph_module, 'build_graph_with_memory'):
            return graph_module.build_graph_with_memory()
        
        return None
        
    except Exception:
        return None
    finally:
        # 恢复原始路径和工作目录
        sys.path = original_path
        os.chdir(original_cwd)


async def process_stream_chunks(graph, state, config):
    """
    处理流式响应的数据块，区分不同role的消息
    
    Returns:
        tuple: (full_response, current_interrupt, tool_messages)
    """
    full_response = ""
    current_interrupt = None
    tool_messages = []
    
    try:
        async for chunk in graph.astream(state, config=config):
            # 检查是否正在退出
            if is_exiting:
                break
                
            # 检查是否有中断
            if '__interrupt__' in chunk:
                current_interrupt = chunk['__interrupt__'][0]
                break
            
            # 处理正常的消息块  
            for node_name, node_output in chunk.items():
                # 跳过特殊键如 __interrupt__
                if node_name.startswith('__'):
                    continue
                if isinstance(node_output, dict) and 'messages' in node_output:
                    for message in node_output['messages']:
                        # 获取消息的role
                        message_role = None
                        message_content = None
                        
                        if hasattr(message, 'type'):
                            # LangChain消息对象
                            message_role = message.type
                            message_content = getattr(message, 'content', '')
                        elif hasattr(message, '__class__'):
                            # 根据类名判断role
                            class_name = message.__class__.__name__.lower()
                            if 'human' in class_name or 'user' in class_name:
                                message_role = 'user'
                            elif 'ai' in class_name or 'assistant' in class_name:
                                message_role = 'assistant'
                            elif 'tool' in class_name:
                                message_role = 'tool'
                            elif 'function' in class_name:
                                message_role = 'function'
                            else:
                                message_role = 'unknown'
                            message_content = getattr(message, 'content', '')
                        elif isinstance(message, dict):
                            # 字典格式消息
                            message_role = message.get('role', 'unknown')
                            message_content = message.get('content', '')
                        
                        if message_content:
                            # 只有 user 和 assistant 的消息加入主响应
                            if message_role in ['user', 'assistant', 'ai', 'human']:
                                full_response += message_content
                            # tool 和 function 消息单独收集
                            elif message_role in ['tool', 'function']:
                                tool_messages.append({
                                    'role': message_role,
                                    'content': message_content,
                                    'node': node_name
                                })
    except Exception as e:
        logger.error(f"处理流式响应时发生错误: {e}", exc_info=True)
        raise
    
    return full_response, current_interrupt, tool_messages


def handle_user_interrupt(interrupt_data) -> Optional[str]:
    """
    处理用户中断确认
    
    Returns:
        Optional[str]: 用户确认结果，None表示取消
    """
    # 显示中断信息
    console.print()
    
    # 处理不同类型的中断数据
    if isinstance(interrupt_data, str):
        panel_content = f"[yellow]📋 {interrupt_data}[/yellow]\n\n[cyan]❓ {t('please_confirm')}[/cyan]"
    elif isinstance(interrupt_data, dict):
        message = interrupt_data.get('message', '')
        question = interrupt_data.get('question', t('please_confirm'))
        panel_content = f"[yellow]📋 {message}[/yellow]\n\n[cyan]❓ {question}[/cyan]"
    else:
        panel_content = f"[yellow]📋 {str(interrupt_data)}[/yellow]\n\n[cyan]❓ {t('please_confirm')}[/cyan]"
    
    console.print(Panel(
        panel_content,
        title=t("confirm_title"),
        border_style="yellow",
        padding=(1, 2)
    ))
    console.print()
    
    # 获取用户输入 - 使用 prompt_toolkit 支持中文输入
    try:
        try:
            from prompt_toolkit.shortcuts import confirm
            result = confirm(f"{t('confirm_question')}", default=True)
            if result:
                console.print(f"✨ {t('confirm_accepted')}")
                console.print()
                return "[ACCEPTED]"
            else:
                return "[REJECTED]"
        except ImportError:
            # Fallback 手动输入
            try:
                from prompt_toolkit import prompt
                from prompt_toolkit.history import InMemoryHistory
                user_confirmation = prompt(
                    f"{t('confirm_question')} ",
                    history=InMemoryHistory()
                ).strip().lower()
            except ImportError:
                # 最终 fallback 使用 rich prompt
                from rich.prompt import Prompt
                user_confirmation = Prompt.ask(
                    f"{t('confirm_question')}",
                    choices=CONFIG["CONFIRMATION_CHOICES"],
                    default="yes",
                    show_choices=False
                ).strip().lower()
            
            # 标准化用户输入
            if user_confirmation in CONFIG["CONFIRMATION_YES"]:
                console.print(f"✨ {t('confirm_accepted')}")
                console.print()
                return "[ACCEPTED]"
            else:
                return "[REJECTED]"
            
    except (KeyboardInterrupt, EOFError):
        # 在确认过程中按下 Ctrl+C，触发优雅退出
        graceful_exit()
        return None


async def resume_after_interrupt(graph_with_memory, user_confirmation: str, config: Dict) -> str:
    """
    中断后恢复执行
    
    Returns:
        str: 恢复后的完整响应
    """
    if graph_with_memory is None:
        console.print(f"[yellow]{t('agent_no_interrupt')}[/yellow]")
        console.print(f"[cyan]{t('agent_interrupt_tip')}[/cyan]")
        return ""
    
    try:
        from langgraph.types import Command
        
        resume_response = ""
        async for chunk in graph_with_memory.astream(
            Command(resume=user_confirmation), 
            config=config
        ):
            # 处理恢复后的消息块
            for node_name, node_output in chunk.items():
                # 跳过特殊键如 __interrupt__
                if node_name.startswith('__'):
                    continue
                
                # 处理不同类型的输出
                if isinstance(node_output, dict):
                    # 检查是否有 messages 字段
                    if 'messages' in node_output:
                        for message in node_output['messages']:
                            if hasattr(message, 'content'):
                                resume_response += message.content
                            elif isinstance(message, dict) and 'content' in message:
                                resume_response += message['content']
                    
                    # 检查是否有 final_report 字段（deer-flow特有）
                    elif 'final_report' in node_output:
                        resume_response += node_output['final_report']
                    
                    # 检查其他可能的内容字段
                    elif 'content' in node_output:
                        resume_response += node_output['content']
                    elif 'text' in node_output:
                        resume_response += node_output['text']
                
                elif isinstance(node_output, str):
                    resume_response += node_output
                
                elif hasattr(node_output, 'content'):
                    resume_response += node_output.content
        
        return resume_response
        
    except ImportError:
        console.print(f"❌ [red]{t('error_command_import')}[/red]")
        return ""
    except Exception as resume_error:
        console.print(f"❌ [red]{t('retry')}[/red]")
        return ""


def detect_markdown(text: str) -> bool:
    """
    检测文本是否包含markdown格式
    
    Args:
        text: 要检测的文本
        
    Returns:
        bool: 是否包含markdown格式
    """
    # 常见的markdown模式
    markdown_patterns = [
        r'#{1,6}\s+.+',           # 标题 (# ## ### 等)
        r'\*\*.*?\*\*',           # 粗体 **text**
        r'\*.*?\*',               # 斜体 *text*
        r'`.*?`',                 # 行内代码 `code`
        r'```[\s\S]*?```',        # 代码块 ```code```
        r'^\s*[-\*\+]\s+',        # 无序列表 - * +
        r'^\s*\d+\.\s+',          # 有序列表 1. 2. 3.
        r'^\s*>\s+',              # 引用 >
        r'\[.*?\]\(.*?\)',        # 链接 [text](url)
        r'!\[.*?\]\(.*?\)',       # 图片 ![alt](url)
        r'\|.*?\|',               # 表格 |col1|col2|
        r'^-{3,}$',               # 分隔线 ---
        r'={3,}$',                # 分隔线 ===
    ]
    
    # 检查是否匹配任何markdown模式
    for pattern in markdown_patterns:
        if re.search(pattern, text, re.MULTILINE):
            return True
    
    return False


def display_agent_response(response: str, agent_name: str):
    """
    显示agent响应，支持markdown格式识别和渲染
    """
    if not response:
        return
    
    # 创建agent显示名称
    agent_display = agent_name.replace("a_simple_agent_quickstart", t("assistant_label"))
    agent_display = agent_display.replace("_", " ").title()
    
    console.print()
    
    # 显示agent标识
    agent_header = Text()
    agent_header.append("🤖 ", style="bright_cyan")
    agent_header.append(f"{agent_display}", style="bold bright_cyan")
    console.print(agent_header)
    
    # 检测是否为markdown格式
    if detect_markdown(response):
        # 渲染markdown内容
        try:
            # 创建markdown对象，设置代码主题
            markdown_content = Markdown(response, code_theme="monokai")
            
            # 在面板中显示markdown内容
            markdown_panel = Panel(
                markdown_content,
                border_style="dim cyan",
                padding=(1, 2),
                title="📝 Response",
                title_align="left"
            )
            console.print(markdown_panel)
        except Exception as e:
            # 如果markdown渲染失败，回退到普通文本
            console.print(f"[dim yellow]Warning: Markdown rendering failed, displaying as plain text[/dim yellow]")
            _display_plain_text(response)
    else:
        # 显示普通文本
        _display_plain_text(response)
    
    console.print()


def display_tool_messages_summary(tool_messages: List[Dict[str, Any]]):
    """
    显示工具消息的摘要信息
    
    Args:
        tool_messages: 工具消息列表
    """
    if not tool_messages:
        return
    
    console.print()
    
    # 按node分组工具消息
    tool_groups = {}
    for i, msg in enumerate(tool_messages):
        node = msg.get('node', 'unknown')
        if node not in tool_groups:
            tool_groups[node] = []
        tool_groups[node].append((i + 1, msg))
    
    # 显示摘要
    total_count = len(tool_messages)
    if total_count == 1:
        msg = tool_messages[0]
        content_preview = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
        console.print(f"🔧 检测到 1 个工具调用结果")
        console.print(f"  📦 {msg.get('node', 'unknown')} ({len(msg['content'])} 字符) - 输入 'show 1' 查看详细结果")
    else:
        console.print(f"🔧 检测到 {total_count} 个工具调用结果")
        for node, messages in tool_groups.items():
            for idx, (msg_num, msg) in enumerate(messages):
                console.print(f"  📦 {node} ({len(msg['content'])} 字符) - 输入 'show {msg_num}' 查看详细结果")
    
    console.print()


def show_tool_message(index: int):
    """
    显示指定索引的工具消息详细内容
    
    Args:
        index: 消息索引（从1开始）
    """
    global recent_tool_messages
    
    if not recent_tool_messages:
        console.print("❌ [red]没有可查看的工具调用结果[/red]")
        return
    
    if index < 1 or index > len(recent_tool_messages):
        console.print(f"❌ [red]无效的索引：{index}。请输入 1-{len(recent_tool_messages)} 之间的数字[/red]")
        return
    
    msg = recent_tool_messages[index - 1]
    
    console.print()
    console.print(f"🔧 [bold cyan]工具调用结果 #{index}[/bold cyan]")
    console.print(f"📦 [yellow]节点：[/yellow] {msg.get('node', 'unknown')}")
    console.print(f"🏷️  [yellow]类型：[/yellow] {msg.get('role', 'unknown')}")
    console.print()
    
    content = msg['content']
    
    # 尝试格式化JSON内容
    try:
        import json
        if content.strip().startswith('{') or content.strip().startswith('['):
            parsed = json.loads(content)
            formatted_content = json.dumps(parsed, indent=2, ensure_ascii=False)
            content = formatted_content
    except:
        pass
    
    # 显示内容
    content_panel = Panel(
        Text(content, style="white"),
        border_style="dim green",
        padding=(1, 2),
        title=f"📄 内容 ({len(content)} 字符)",
        title_align="left"
    )
    console.print(content_panel)
    console.print()


def _display_plain_text(text: str):
    """
    显示普通文本响应
    
    Args:
        text: 要显示的文本
    """
    # 为长文本添加面板包装
    if len(text) > 200 or '\n' in text:
        text_panel = Panel(
            Text(text, style="white"),
            border_style="dim blue",
            padding=(1, 2),
            title="💬 Response",
            title_align="left"
        )
        console.print(text_panel)
    else:
        # 短文本直接显示
        console.print(f"  {text}", style="white")


async def stream_agent_response(user_input: str) -> Optional[str]:
    """
    流式调用 agent 并处理响应，支持中断功能
    """
    global current_agent, conversation_history, current_thread_id
    
    if not current_agent:
        console.print(f"❌ [red]{t('error_no_agent')}[/red]")
        return None
    
    # 加载 agent 的 graph 对象
    graph, graph_with_memory = load_agent_graph(current_agent)
    if not graph:
        console.print(f"❌ [red]{t('error_agent_load', current_agent)}[/red]")
        return None
    
    # 构造输入状态和配置
    state = create_message_state(user_input, conversation_history)
    config = {"configurable": {"thread_id": current_thread_id}}
    
    # 选择合适的 graph：如果有支持 checkpointer 的版本，优先使用它
    target_graph = graph_with_memory if graph_with_memory is not None else graph
    
    # 用于存储完整响应
    full_response = ""
    current_interrupt = None
    
    with console.status(f"[cyan]{current_agent}[/cyan] {t('agent_thinking', current_agent)}", spinner="dots"):
        try:
            # 处理流式响应
            full_response, current_interrupt, tool_messages = await process_stream_chunks(
                target_graph, state, config
            )
        except Exception as invoke_error:
            logger.error(t("error_agent_call", invoke_error), exc_info=True)
            console.print(f"❌ [red]{t('error_agent_call', invoke_error)}[/red]")
            return None
    
    # 处理中断情况
    if current_interrupt:
        interrupt_data = current_interrupt.value
        user_confirmation = handle_user_interrupt(interrupt_data)
        
        if user_confirmation is None:
            return None
        
        # 恢复执行
        with console.status(f"[cyan]{current_agent}[/cyan] {t('agent_processing', current_agent)}", spinner="dots"):
            resume_response = await resume_after_interrupt(
                graph_with_memory, user_confirmation, config
            )
            if resume_response:
                full_response = resume_response
    
    # 显示响应并更新历史
    if full_response:
        display_agent_response(full_response, current_agent)
        
        # 处理工具消息
        global recent_tool_messages
        recent_tool_messages = tool_messages
        if tool_messages:
            display_tool_messages_summary(tool_messages)
        
        # 添加到对话历史
        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": full_response})
    
    return full_response

def create_welcome_screen():
    """创建 Su-Cli 欢迎界面"""
    console = Console()
    
    # 创建带3D阴影效果的 ASCII 艺术字标题
    ascii_art = """
███████╗██╗   ██╗      ██████╗██╗     ██╗
██╔════╝██║   ██║     ██╔════╝██║     ██║
███████╗██║   ██║     ██║     ██║     ██║
╚════██║██║   ██║     ██║     ██║     ██║
███████║╚██████╔╝     ╚██████╗███████╗██║
╚══════╝ ╚═════╝       ╚═════╝╚══════╝╚═╝
 ▓▓▓▓▓▓▓ ▓▓▓▓▓▓        ▓▓▓▓▓▓ ▓▓▓▓▓▓▓ ▓▓
  ▒▒▒▒▒▒ ▒▒▒▒▒          ▒▒▒▒▒ ▒▒▒▒▒▒▒ ▒▒
   ░░░░░ ░░░░░            ░░░░░ ░░░░░░ ░░
    """
    
    # 使用 rich-gradient 创建美丽的渐变标题
    title = GradientText(
        ascii_art.strip(),
        colors=[
            "#667eea",  # 柔和蓝色
            "#764ba2",  # 深紫色
            "#f093fb",  # 粉紫色
            "#f5576c",  # 柔和红色
            "#4facfe",  # 天蓝色
        ],
        rainbow=False  # 使用自定义柔和颜色
    )
    
    # 创建柔和渐变欢迎信息
    welcome_text = GradientText(
        f"\n{t('welcome_title')}",
        colors=["#6a85b6", "#baa6dc", "#a8c8ec"]  # 柔和蓝紫色过渡
    )
    
    # 创建柔和渐变副标题
    subtitle = GradientText(
        f"{t('welcome_subtitle')}",
        colors=["#889abb", "#9baed6", "#adc3ee"]  # 更柔和的蓝色过渡
    )
    
    # 创建使用提示 - 使用渐变效果和统一尺寸
    tips = [
        t("tips")[0],
        t("tips")[1], 
        t("tips")[2],
        t("tips")[3]
    ]
    
    # 为每个提示创建柔和渐变文本
    gradient_colors = [
        ["#7eb3e3", "#a3c4e8"],  # 柔和天蓝色过渡
        ["#c8a8e8", "#d1b3ec"],  # 柔和紫色过渡
        ["#9bb5e3", "#b3c9e8"],  # 柔和蓝紫色过渡
        ["#e8b3d1", "#ecbfd8"]   # 柔和粉紫色过渡
    ]
    
    tip_panels = []
    for i, tip in enumerate(tips):
        gradient_tip = GradientText(tip, colors=gradient_colors[i])
        
        # 直接使用居中的渐变文本，不添加边框
        tip_panels.append(Align.center(gradient_tip))
    
    # 组合所有元素
    header = Align.center(title)
    welcome = Align.center(welcome_text)
    sub = Align.center(subtitle)
    
    # 显示界面
    console.print()
    console.print(header)
    console.print(welcome)
    console.print(sub)
    console.print()
    
    # 显示提示面板 - 使用柔和渐变效果
    guide_title = GradientText(
        f"{t('quick_start_guide')}",
        colors=["#a8c8ec", "#baa6dc", "#d1a3e8"]  # 柔和蓝紫色过渡
    )
    console.print(Align.center(guide_title))
    console.print()
    console.print(Columns(tip_panels, equal=True, expand=True, padding=(0, 1)))
    console.print()
    
    # 底部信息
    footer = Panel(
        Align.center(Text(f"{t('footer_help')}", style="dim white")),
        style="dim blue",
        border_style="dim"
    )
    console.print(footer)
    console.print()

async def handle_command(command: str) -> bool:
    """处理用户输入的命令
    
    Args:
        command: 用户输入的命令
        
    Returns:
        bool: True 继续程序，False 退出程序
    """
    global current_agent, conversation_history, available_agents, prompt_style
    
    if not command.strip():
        return True
        
    if command.lower() in CONFIG["EXIT_COMMANDS"]:
        console.print(f"\n{t('goodbye')}")
        return False
    elif command.lower() in CONFIG["HELP_COMMANDS"]:
        _show_help()
    elif command.lower() in CONFIG["CLEAR_COMMANDS"]:
        console.clear()
        create_welcome_screen()
    elif command.lower() in CONFIG["AGENTS_COMMANDS"]:
        _show_agents()
    elif command.lower().startswith('/use '):
        _switch_agent(command[5:].strip())
    elif command.lower() in CONFIG["HISTORY_COMMANDS"]:
        _show_history()
    elif command.lower() in CONFIG["RESET_COMMANDS"]:
        _reset_conversation()
    elif command.lower() in CONFIG["STYLE_COMMANDS"]:
        _show_styles()
    elif command.lower().startswith('/style '):
        _switch_style(command[7:].strip().lower())
    elif command.lower().startswith('/set_lang '):
        _set_language(command[10:].strip().lower())
    elif command.lower() in CONFIG["LANG_COMMANDS"]:
        _show_language()
    elif command.lower().startswith('show '):
        # 处理show命令
        try:
            index = int(command[5:].strip())
            show_tool_message(index)
        except ValueError:
            console.print("❌ [red]请输入有效的数字，例如：show 1[/red]")
    else:
        # 处理普通对话
        if not current_agent:
            console.print(f"❌ [red]{t('error_no_agent')}[/red]")
            return True
        
        # 调用 agent 进行对话
        await stream_agent_response(command)
    
    return True


def _show_help():
    """显示帮助信息"""
    console.print(Panel.fit(
        f"[bold cyan]{t('help_title')}[/bold cyan]\n\n"
        f"{t('help_content')}",
        title=t("help_title"),
        border_style="cyan"
    ))


def _show_agents():
    """显示可用的 agents"""
    if available_agents:
        agent_list = "\n".join([
            f"  • {'🤖 ' if agent == current_agent else '  '}{agent}" 
            for agent in available_agents
        ])
        console.print(Panel.fit(
            f"[bold cyan]{t('agents_title')}[/bold cyan]\n\n{agent_list}\n\n"
            f"[yellow]{t('agents_current')}[/yellow] [green]{current_agent}[/green]",
            title=t("agents_title"),
            border_style="cyan"
        ))
    else:
        console.print(f"❌ [red]{t('no_agents')}[/red]")


def _switch_agent(agent_name: str):
    """切换到指定的 agent"""
    global current_agent
    
    if agent_name in available_agents:
        current_agent = agent_name
        console.print(f"✅ [green]{t('agent_switch_success', current_agent)}[/green]")
    else:
        console.print(f"❌ [red]{t('agent_not_found', agent_name)}[/red]")
        console.print(f"💡 [yellow]{t('agent_available', ', '.join(available_agents))}[/yellow]")


def _show_history():
    """显示对话历史"""
    if conversation_history:
        history_text = ""
        for msg in conversation_history:
            role_emoji = "👤" if msg["role"] == "user" else "🤖"
            role_color = "blue" if msg["role"] == "user" else "green"
            role_label = t("user_label") if msg["role"] == "user" else t("assistant_label")
            content = msg['content'][:100] + ('...' if len(msg['content']) > 100 else '')
            history_text += f"{role_emoji} [{role_color}]{role_label.upper()}[/{role_color}]: {content}\n\n"
        
        console.print(Panel.fit(
            history_text.strip(),
            title=t("history_title", len(conversation_history)//2),
            border_style="yellow"
        ))
    else:
        console.print(f"📝 [yellow]{t('no_history')}[/yellow]")


def _reset_conversation():
    """重置对话历史和线程ID"""
    global conversation_history, current_thread_id
    
    conversation_history.clear()
    current_thread_id = str(uuid.uuid4())
    console.print(f"🔄 [green]{t('history_reset')}[/green]")


def _show_styles():
    """显示可用的风格"""
    current_style_desc = CONFIG['PROMPT_STYLES'].get(prompt_style, {}).get(current_language, "Unknown")
    style_text = f"[yellow]{t('style_current')}[/yellow] [green]{prompt_style}[/green] - {current_style_desc}\n\n"
    style_text += f"[yellow]{t('style_available')}[/yellow]\n"
    
    for style_name, descriptions in CONFIG['PROMPT_STYLES'].items():
        indicator = "🎯 " if style_name == prompt_style else "   "
        description = descriptions.get(current_language, style_name)
        style_text += f"{indicator}[cyan]{style_name}[/cyan] - {description}\n"
    
    console.print(Panel.fit(
        style_text.strip(),
        title=t("style_title"),
        border_style="magenta"
    ))


def _switch_style(style_name: str):
    """切换界面风格"""
    global prompt_style
    
    if style_name in CONFIG['PROMPT_STYLES']:
        prompt_style = style_name
        console.print(f"✅ [green]{t('style_switch_success', style_name)}[/green]")
    else:
        console.print(f"❌ [red]{t('style_not_found', style_name)}[/red]")
        console.print(f"💡 [yellow]{t('style_available_list', ', '.join(CONFIG['PROMPT_STYLES'].keys()))}[/yellow]")


def _show_language():
    """显示语言设置"""
    lang_descriptions = {"en": "English", "zh": "中文"}
    lang_text = f"[yellow]{t('lang_current')}[/yellow] [green]{current_language}[/green] - {lang_descriptions.get(current_language, current_language)}\n\n"
    lang_text += f"[yellow]{t('lang_available')}[/yellow]\n"
    
    for lang_code in get_available_languages():
        indicator = "🌐 " if lang_code == current_language else "   "
        lang_name = lang_descriptions.get(lang_code, lang_code)
        lang_text += f"{indicator}[cyan]{lang_code}[/cyan] - {lang_name}\n"
    
    console.print(Panel.fit(
        lang_text.strip(),
        title=t("lang_title"),
        border_style="green"
    ))


def _set_language(lang: str):
    """设置当前语言"""
    if set_language(lang):
        console.print(f"✅ [green]{t('lang_switch_success', lang)}[/green]")
    else:
        console.print(f"❌ [red]{t('lang_not_found', lang)}[/red]")
        console.print(f"💡 [yellow]{t('lang_available_list', ', '.join(get_available_languages()))}[/yellow]")


async def main():
    """主函数"""
    
    # 设置信号处理器
    setup_signal_handlers()
    
    # 显示欢迎界面
    create_welcome_screen()
    
    # 初始化 agent 系统
    if not initialize_agent_system():
        console.print(f"⚠️ [yellow]{t('system_init_warning')}[/yellow]")
    
    console.print()
    
    # 主循环 - 处理用户输入
    while True and not is_exiting:
        try:
            # 使用美观的命令行提示符
            user_input = create_beautiful_prompt(current_agent, prompt_style)
            
            # 检查是否正在退出
            if is_exiting:
                break
            
            # 处理退出命令
            if user_input in ["/exit", "/q"]:
                graceful_exit()
                break
            
            # 处理命令
            should_continue = await handle_command(user_input)
            if not should_continue:
                break
                
        except EOFError:
            # EOF (Ctrl+D) 也触发优雅退出
            graceful_exit()
            break
        except Exception as e:
            # 处理其他意外错误
            if not is_exiting:
                logger.error(f"主循环发生错误: {e}", exc_info=True)
                console.print(f"❌ [red]发生错误: {e}[/red]")
                console.print("[yellow]程序继续运行，如需退出请按 Ctrl+C[/yellow]")

def run_main():
    """运行主函数的包装器"""
    try:
        asyncio.run(main())
    except Exception as e:
        # 处理意外错误
        if not is_exiting:
            logger.error(f"程序异常退出: {e}", exc_info=True)
            console.print(f"❌ [red]程序异常退出: {e}[/red]")
        graceful_exit()

if __name__ == "__main__":
    run_main()
