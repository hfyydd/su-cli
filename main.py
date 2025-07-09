import sys
import asyncio
import logging
import uuid
import os
import json
import importlib
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.columns import Columns
from rich.align import Align
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.markdown import Markdown
from rich.layout import Layout
from rich.box import ROUNDED
from rich_gradient import Text as GradientText

# 配置常量
CONFIG = {
    "LOGGING_LEVEL": logging.WARNING,
    "PROMPT_STYLES": {
        "modern": "现代简约风格 (带边框)",
        "minimal": "极简风格",
        "classic": "经典风格 (类似 bash)",
        "colorful": "彩色风格 (带图标)"
    },
    "DEFAULT_PROMPT_STYLE": "modern",
    "CONFIRMATION_CHOICES": ["yes", "y", "是", "确认", "no", "n", "否", "取消"],
    "CONFIRMATION_YES": ["yes", "y", "是", "确认"],
    "EXIT_COMMANDS": ['/exit', '/quit', '/q', 'exit', 'quit'],
    "HELP_COMMANDS": ['/help', '/h', 'help'],
    "CLEAR_COMMANDS": ['/clear', 'clear'],
    "AGENTS_COMMANDS": ['/agents', 'agents'],
    "HISTORY_COMMANDS": ['/history', 'history'],
    "RESET_COMMANDS": ['/reset', 'reset'],
    "STYLE_COMMANDS": ['/style', 'style'],
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
    logger.error(f"导入 core 模块失败: {e}")
    sys.exit(1)

# 全局变量
console = Console()
conversation_history = []
current_agent = None
available_agents = []
prompt_style = CONFIG["DEFAULT_PROMPT_STYLE"]
current_thread_id = str(uuid.uuid4())


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
        console.print("\n👋 再见！")
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
        return Prompt.ask("[bold green]SuCli >[/] ").strip()


def _get_modern_input(agent_display: str) -> str:
    """现代简约风格输入"""
    first_line = Text()
    first_line.append("┌─ ", style="bright_cyan")
    first_line.append("SuCli", style="bold bright_white")
    if agent_display != "CLI":
        first_line.append(" @ ", style="dim")
        first_line.append(agent_display, style="bright_magenta")
    first_line.append(" ─┐", style="bright_cyan")
    
    second_line = Text()
    second_line.append("└─ ", style="bright_cyan")
    second_line.append("❯ ", style="bold bright_green")
    
    console.print(first_line)
    return Prompt.ask(second_line).strip()


def _get_minimal_input(agent_display: str) -> str:
    """极简风格输入"""
    prompt_text = Text()
    prompt_text.append("su", style="bold bright_blue")
    if agent_display != "CLI":
        prompt_text.append(f":{agent_display.lower()}", style="bright_yellow")
    prompt_text.append(" ❯ ", style="bold bright_green")
    
    return Prompt.ask(prompt_text).strip()


def _get_classic_input(agent_display: str) -> str:
    """经典风格输入"""
    prompt_text = Text()
    prompt_text.append("[", style="bright_white")
    prompt_text.append("SuCli", style="bold bright_cyan")
    if agent_display != "CLI":
        prompt_text.append("@", style="dim")
        prompt_text.append(agent_display, style="bright_magenta")
    prompt_text.append("]", style="bright_white")
    prompt_text.append("$ ", style="bold bright_green")
    
    return Prompt.ask(prompt_text).strip()


def _get_colorful_input(agent_display: str) -> str:
    """彩色风格输入"""
    prompt_text = Text()
    prompt_text.append("🚀 ", style="")
    prompt_text.append("Su", style="bold red")
    prompt_text.append("Cli", style="bold blue")
    if agent_display != "CLI":
        prompt_text.append(" 🤖 ", style="")
        prompt_text.append(agent_display, style="bold bright_magenta")
    prompt_text.append(" ➤ ", style="bold bright_yellow")
    
    return Prompt.ask(prompt_text).strip()


def initialize_agent_system() -> bool:
    """初始化 agent 系统"""
    global available_agents, current_agent
    
    try:
        logger.info("开始初始化 agent 系统")
        agents = scan_agents()
        # 只获取有效的 agents
        valid_agents = get_valid_agents()
        available_agents = list(valid_agents.keys())
        
        if not available_agents:
            logger.warning("没有发现可用的 agents")
            console.print("❌ [red]没有发现可用的 agents[/red]")
            return False
        
        # 默认选择 'default' agent，如果不存在则选择第一个 agent
        if "default" in available_agents:
            current_agent = "default"
        else:
            current_agent = available_agents[0]
        logger.info(f"Agent 系统初始化成功，当前使用: {current_agent}")
        console.print(f"✅ [green]Agent 系统已就绪，当前使用: {current_agent}[/green]")
        
        return True
        
    except Exception as e:
        logger.error(f"初始化 agent 系统失败: {e}", exc_info=True)
        console.print(f"❌ [red]初始化 agent 系统失败: {e}[/red]")
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
        logger.debug(f"开始加载 agent: {agent_name}")
        
        # 加载 agent 模块
        module = scanner.load_agent_module(agent_name)
        if not module:
            logger.error(f"无法加载 agent 模块: {agent_name}")
            return None, None
        
        # 获取 graph 对象
        if not hasattr(module, 'graph'):
            logger.error(f"Agent {agent_name} 没有 graph 对象")
            return None, None
        
        graph = module.graph
        graph_with_memory = None
        
        # 尝试获取带内存的 graph
        try:
            agent_info = scanner.get_agent_info(agent_name)
            if agent_info:
                graph_with_memory = _build_graph_with_memory(agent_info)
                if graph_with_memory:
                    logger.debug(f"成功创建带内存的 graph: {agent_name}")
                else:
                    logger.debug(f"无法创建带内存的 graph: {agent_name}")
        except Exception as e:
            logger.debug(f"创建带内存的 graph 失败: {e}")
        
        return graph, graph_with_memory
        
    except Exception as e:
        logger.error(f"加载 agent graph 失败: {e}", exc_info=True)
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
    处理流式响应的数据块
    
    Returns:
        tuple: (full_response, current_interrupt)
    """
    full_response = ""
    current_interrupt = None
    
    try:
        async for chunk in graph.astream(state, config=config):
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
                        if hasattr(message, 'content'):
                            full_response += message.content
                        elif isinstance(message, dict) and 'content' in message:
                            full_response += message['content']
    except Exception as e:
        logger.error(f"处理流式响应时发生错误: {e}", exc_info=True)
        raise
    
    return full_response, current_interrupt


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
        panel_content = f"[yellow]📋 {interrupt_data}[/yellow]\n\n[cyan]❓ 请确认[/cyan]"
    elif isinstance(interrupt_data, dict):
        message = interrupt_data.get('message', '')
        question = interrupt_data.get('question', '请确认')
        panel_content = f"[yellow]📋 {message}[/yellow]\n\n[cyan]❓ {question}[/cyan]"
    else:
        panel_content = f"[yellow]📋 {str(interrupt_data)}[/yellow]\n\n[cyan]❓ 请确认[/cyan]"
    
    console.print(Panel(
        panel_content,
        title="🤔 需要您的确认",
        border_style="yellow",
        padding=(1, 2)
    ))
    console.print()
    
    # 获取用户输入
    try:
        user_confirmation = Prompt.ask(
            "[bold green]您确认要处理这个请求吗？ (yes/no)[/bold green]",
            choices=CONFIG["CONFIRMATION_CHOICES"],
            default="yes",
            show_choices=False
        ).strip().lower()
        
        # 标准化用户输入
        if user_confirmation in CONFIG["CONFIRMATION_YES"]:
            console.print(f"✨ 已确认，继续处理中...")
            console.print()
            return "[ACCEPTED]"
        else:
            return "[REJECTED]"
            
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]操作已取消[/yellow]")
        return None


async def resume_after_interrupt(graph_with_memory, user_confirmation: str, config: Dict) -> str:
    """
    中断后恢复执行
    
    Returns:
        str: 恢复后的完整响应
    """
    if graph_with_memory is None:
        console.print("[yellow]⚠️ 该 agent 不支持中断恢复功能，无法继续执行[/yellow]")
        console.print("[cyan]💡 提示: 可以重新开始对话[/cyan]")
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
        console.print("❌ [red]无法导入Command，请检查langgraph版本[/red]")
        return ""
    except Exception as resume_error:
        console.print(f"❌ [red]操作失败，请重试[/red]")
        return ""


def display_agent_response(response: str, agent_name: str):
    """
    显示agent响应
    """
    if not response:
        return
    
    # 创建更简洁的对话显示
    agent_display = agent_name.replace("a_simple_agent_quickstart", "助手")
    agent_display = agent_display.replace("_", " ").title()
    
    response_text = Text()
    response_text.append("🤖 ", style="bright_cyan")
    response_text.append(f"{agent_display}: ", style="bold bright_cyan")
    response_text.append(response, style="white")
    
    console.print()
    console.print(response_text)
    console.print()


async def stream_agent_response(user_input: str) -> Optional[str]:
    """
    流式调用 agent 并处理响应，支持中断功能
    """
    global current_agent, conversation_history, current_thread_id
    
    if not current_agent:
        console.print("❌ [red]没有可用的 agent[/red]")
        return None
    
    # 加载 agent 的 graph 对象
    graph, graph_with_memory = load_agent_graph(current_agent)
    if not graph:
        console.print(f"❌ [red]无法加载 agent: {current_agent}[/red]")
        return None
    
    # 构造输入状态和配置
    state = create_message_state(user_input, conversation_history)
    config = {"configurable": {"thread_id": current_thread_id}}
    
    # 选择合适的 graph：如果有支持 checkpointer 的版本，优先使用它
    target_graph = graph_with_memory if graph_with_memory is not None else graph
    
    # 用于存储完整响应
    full_response = ""
    current_interrupt = None
    
    with console.status(f"[cyan]{current_agent}[/cyan] 正在思考...", spinner="dots"):
        try:
            # 处理流式响应
            full_response, current_interrupt = await process_stream_chunks(
                target_graph, state, config
            )
        except Exception as invoke_error:
            logger.error(f"调用 agent 失败: {invoke_error}", exc_info=True)
            console.print(f"❌ [red]调用 agent 失败: {invoke_error}[/red]")
            return None
    
    # 处理中断情况
    if current_interrupt:
        interrupt_data = current_interrupt.value
        user_confirmation = handle_user_interrupt(interrupt_data)
        
        if user_confirmation is None:
            return None
        
        # 恢复执行
        with console.status(f"[cyan]{current_agent}[/cyan] 正在处理您的确认...", spinner="dots"):
            resume_response = await resume_after_interrupt(
                graph_with_memory, user_confirmation, config
            )
            if resume_response:
                full_response = resume_response
    
    # 显示响应并更新历史
    if full_response:
        display_agent_response(full_response, current_agent)
        
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
        "\n🚀 欢迎使用 Su-Cli 命令行工具！",
        colors=["#6a85b6", "#baa6dc", "#a8c8ec"]  # 柔和蓝紫色过渡
    )
    
    # 创建柔和渐变副标题
    subtitle = GradientText(
        "一个强大而简洁的命令行助手",
        colors=["#889abb", "#9baed6", "#adc3ee"]  # 更柔和的蓝色过渡
    )
    
    # 创建使用提示 - 使用渐变效果
    tips = [
        "🤖 与Agent 对话交流",
        "🔗 支持 MCP 协议集成", 
        "⚡ 基于 LangGraph ",
        "🔄 支持中断恢复功能"
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
        border_color = ["green", "yellow", "blue", "magenta"][i]
        tip_panels.append(Panel(gradient_tip, style=border_color, width=25))
    
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
        "✨ 快速开始指南 ✨",
        colors=["#a8c8ec", "#baa6dc", "#d1a3e8"]  # 柔和蓝紫色过渡
    )
    console.print(Align.center(guide_title))
    console.print()
    console.print(Columns(tip_panels, equal=True, expand=True))
    console.print()
    
    # 底部信息
    footer = Panel(
        Align.center(Text("输入 '/help' 或 '/h' 获取更多帮助信息 | 输入 '/exit' 或 '/q' 退出程序", style="dim white")),
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
        console.print("👋 [bold green]感谢使用 Su-Cli，再见！[/bold green]")
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
    else:
        # 处理普通对话
        if not current_agent:
            console.print("❌ [red]没有可用的 agent，请先初始化系统[/red]")
            return True
        
        # 调用 agent 进行对话
        await stream_agent_response(command)
    
    return True


def _show_help():
    """显示帮助信息"""
    console.print(Panel.fit(
        "[bold cyan]Su-Cli 帮助信息[/bold cyan]\n\n"
        "📋 [yellow]可用命令：[/yellow]\n"
        "  • [green]/help[/green] | [green]/h[/green] - 显示此帮助信息\n"
        "  • [green]/exit[/green] | [green]/q[/green] - 退出程序\n"
        "  • [green]/clear[/green] - 清屏\n"
        "  • [green]/agents[/green] - 显示可用的 agents\n"
        "  • [green]/use <name>[/green] - 切换到指定的 agent\n"
        "  • [green]/history[/green] - 显示对话历史\n"
        "  • [green]/reset[/green] - 清空对话历史并重置对话线程\n\n"
        "🤔 [yellow]中断功能：[/yellow]\n"
        "  • Agent 会在需要时请求您的确认\n"
        "  • 输入 'yes'、'y'、'是'、'确认' 来同意\n"
        "  • 输入其他内容来取消操作\n\n"
        "💡 [yellow]提示：[/yellow] 直接输入消息与当前 agent 对话",
        title="🔧 帮助",
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
            f"[bold cyan]可用的 Agents[/bold cyan]\n\n{agent_list}\n\n"
            f"[yellow]当前 agent:[/yellow] [green]{current_agent}[/green]",
            title="🤖 Agents",
            border_style="cyan"
        ))
    else:
        console.print("❌ [red]没有可用的 agents[/red]")


def _switch_agent(agent_name: str):
    """切换到指定的 agent"""
    global current_agent
    
    if agent_name in available_agents:
        current_agent = agent_name
        console.print(f"✅ [green]已切换到 agent: {current_agent}[/green]")
    else:
        console.print(f"❌ [red]Agent '{agent_name}' 不存在[/red]")
        console.print(f"💡 [yellow]可用的 agents: {', '.join(available_agents)}[/yellow]")


def _show_history():
    """显示对话历史"""
    if conversation_history:
        history_text = ""
        for msg in conversation_history:
            role_emoji = "👤" if msg["role"] == "user" else "🤖"
            role_color = "blue" if msg["role"] == "user" else "green"
            content = msg['content'][:100] + ('...' if len(msg['content']) > 100 else '')
            history_text += f"{role_emoji} [{role_color}]{msg['role'].upper()}[/{role_color}]: {content}\n\n"
        
        console.print(Panel.fit(
            history_text.strip(),
            title=f"📝 对话历史 ({len(conversation_history)//2} 轮对话)",
            border_style="yellow"
        ))
    else:
        console.print("📝 [yellow]暂无对话历史[/yellow]")


def _reset_conversation():
    """重置对话历史和线程ID"""
    global conversation_history, current_thread_id
    
    conversation_history.clear()
    current_thread_id = str(uuid.uuid4())
    console.print("🔄 [green]对话历史已清空，已开始新的对话线程[/green]")


def _show_styles():
    """显示可用的风格"""
    style_text = f"[yellow]当前风格:[/yellow] [green]{prompt_style}[/green] - {CONFIG['PROMPT_STYLES'].get(prompt_style, '未知')}\n\n"
    style_text += "[yellow]可用风格:[/yellow]\n"
    
    for style_name, description in CONFIG['PROMPT_STYLES'].items():
        indicator = "🎯 " if style_name == prompt_style else "   "
        style_text += f"{indicator}[cyan]{style_name}[/cyan] - {description}\n"
    
    console.print(Panel.fit(
        style_text.strip(),
        title="🎨 界面风格",
        border_style="magenta"
    ))


def _switch_style(style_name: str):
    """切换界面风格"""
    global prompt_style
    
    if style_name in CONFIG['PROMPT_STYLES']:
        prompt_style = style_name
        console.print(f"✅ [green]已切换到 {style_name} 风格[/green]")
    else:
        console.print(f"❌ [red]风格 '{style_name}' 不存在[/red]")
        console.print(f"💡 [yellow]可用风格: {', '.join(CONFIG['PROMPT_STYLES'].keys())}[/yellow]")

async def main():
    """主函数"""
    
    # 显示欢迎界面
    create_welcome_screen()
    
    # 初始化 agent 系统
    if not initialize_agent_system():
        console.print("⚠️ [yellow]Agent 系统初始化失败，部分功能将不可用[/yellow]")
    
    console.print()
    
    # 主循环 - 处理用户输入
    while True:
        try:
            # 使用美观的命令行提示符
            user_input = create_beautiful_prompt(current_agent, prompt_style)
            
            # 处理退出命令
            if user_input in ["/exit", "/q"]:
                console.print("👋 [bold green]感谢使用 Su-Cli，再见！[/bold green]")
                break
            
            # 处理命令
            should_continue = await handle_command(user_input)
            if not should_continue:
                break
                
        except KeyboardInterrupt:
            console.print("\n👋 [bold green]感谢使用 Su-Cli，再见！[/bold green]")
            break
        except EOFError:
            console.print("\n👋 [bold green]感谢使用 Su-Cli，再见！[/bold green]")
            break

def run_main():
    """运行主函数的包装器"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n👋 [bold green]感谢使用 Su-Cli，再见！[/bold green]")

if __name__ == "__main__":
    run_main()
