import sys
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
import uuid
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

# 设置日志级别，减少不必要的信息输出
logging.getLogger("core").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# 添加 core 模块到路径
sys.path.insert(0, str(Path(__file__).parent / "core"))
from core import scanner, scan_agents, get_available_agents

# 全局变量
console = Console()
conversation_history = []
current_agent = None
available_agents = []
prompt_style = "modern"  # 当前提示符风格
current_thread_id = str(uuid.uuid4())  # 当前对话的线程ID


def create_beautiful_prompt(agent_name: str = None, style: str = "modern") -> str:
    """
    创建美观的命令行提示符
    支持多种风格: modern, minimal, classic, colorful
    """
    if agent_name:
        agent_display = agent_name.replace("a_simple_agent_quickstart", "简单助手")
        agent_display = agent_display.replace("_", " ").title()
    else:
        agent_display = "CLI"
    
    try:
        if style == "modern":
            # 风格1: 现代简约风格
            first_line = Text()
            first_line.append("┌─ ", style="bright_cyan")
            first_line.append("SuCli", style="bold bright_white")
            if agent_name:
                first_line.append(" @ ", style="dim")
                first_line.append(agent_display, style="bright_magenta")
            first_line.append(" ─┐", style="bright_cyan")
            
            second_line = Text()
            second_line.append("└─ ", style="bright_cyan")
            second_line.append("❯ ", style="bold bright_green")
            
            console.print(first_line)
            user_input = Prompt.ask(second_line, default="").strip()
            
        elif style == "minimal":
            # 风格2: 极简风格
            prompt_text = Text()
            prompt_text.append("su", style="bold bright_blue")
            if agent_name:
                prompt_text.append(f":{agent_display.lower()}", style="bright_yellow")
            prompt_text.append(" ❯ ", style="bold bright_green")
            
            user_input = Prompt.ask(prompt_text, default="").strip()
            
        elif style == "classic":
            # 风格3: 经典风格
            prompt_text = Text()
            prompt_text.append("[", style="bright_white")
            prompt_text.append("SuCli", style="bold bright_cyan")
            if agent_name:
                prompt_text.append("@", style="dim")
                prompt_text.append(agent_display, style="bright_magenta")
            prompt_text.append("]", style="bright_white")
            prompt_text.append("$ ", style="bold bright_green")
            
            user_input = Prompt.ask(prompt_text, default="").strip()
            
        elif style == "colorful":
            # 风格4: 彩色风格
            prompt_text = Text()
            prompt_text.append("🚀 ", style="")
            prompt_text.append("Su", style="bold red")
            prompt_text.append("Cli", style="bold blue")
            if agent_name:
                prompt_text.append(" 🤖 ", style="")
                prompt_text.append(agent_display, style="bold bright_magenta")
            prompt_text.append(" ➤ ", style="bold bright_yellow")
            
            user_input = Prompt.ask(prompt_text, default="").strip()
        
        else:
            # 默认简单风格
            user_input = Prompt.ask("[bold green]SuCli >[/] ", default="").strip()
        
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


def initialize_agent_system():
    """初始化 agent 系统"""
    global available_agents, current_agent
    
    try:
        agents = scan_agents()
        available_agents = get_available_agents()
        
        if not available_agents:
            console.print("❌ [red]没有发现可用的 agents[/red]")
            return False
        
        # 默认选择第一个 agent
        current_agent = available_agents[0]
        console.print(f"✅ [green]Agent 系统已就绪，当前使用: {current_agent}[/green]")
        
        return True
        
    except Exception as e:
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


async def stream_agent_response(user_input: str) -> Optional[str]:
    """
    流式调用 agent 并处理响应，支持中断功能
    """
    global current_agent, conversation_history, current_thread_id
    
    if not current_agent:
        console.print("❌ [red]没有可用的 agent[/red]")
        return None
    
    # 加载 agent 模块
    module = scanner.load_agent_module(current_agent)
    if not module:
        console.print(f"❌ [red]无法加载 agent: {current_agent}[/red]")
        return None
    
    # 获取 graph 对象
    if not hasattr(module, 'graph'):
        console.print(f"❌ [red]Agent {current_agent} 没有 graph 对象[/red]")
        return None
    
    graph = module.graph
    
    # 构造输入状态
    state = create_message_state(user_input, conversation_history)
    
    # 配置线程ID
    config = {"configurable": {"thread_id": current_thread_id}}
    
    # 用于存储完整响应
    full_response = ""
    current_interrupt = None
    
    with console.status(f"[cyan]{current_agent}[/cyan] 正在思考...", spinner="dots"):
        try:
            # 使用stream方法调用 agent，支持中断
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
                            
        except Exception as invoke_error:
            console.print(f"❌ [red]调用 agent 失败: {invoke_error}[/red]")
            return None
    
    # 如果有中断，在 status 上下文外处理用户确认
    if current_interrupt:
        interrupt_data = current_interrupt.value
        
        # 显示中断信息
        console.print()
        console.print(Panel(
            f"[yellow]📋 {interrupt_data.get('message', '')}[/yellow]\n\n"
            f"[cyan]❓ {interrupt_data.get('question', '请确认')}[/cyan]",
            title="🤔 需要您的确认",
            border_style="yellow",
            padding=(1, 2)
        ))
        console.print()
        
        # 获取用户输入 - 现在在 status 上下文外
        try:
            user_confirmation = Prompt.ask(
                "[bold green]您确认要处理这个请求吗？ (yes/no)[/bold green]",
                choices=["yes", "y", "是", "确认", "no", "n", "否", "取消"],
                default="yes",
                show_choices=False
            ).strip().lower()
            
            # 标准化用户输入
            if user_confirmation in ["yes", "y", "是", "确认"]:
                user_confirmation = "yes"
            else:
                user_confirmation = "no"
                
            console.print(f"[dim]您的选择: {user_confirmation}[/dim]")
            console.print()
            
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]操作已取消[/yellow]")
            return None
        
        # 导入Command并继续执行
        try:
            from langgraph.types import Command
            
            # 使用新的 status 显示继续执行
            with console.status(f"[cyan]{current_agent}[/cyan] 正在处理您的确认...", spinner="dots"):
                # 重置响应，开始收集恢复后的内容
                resume_response = ""
                async for chunk in graph.astream(
                    Command(resume=user_confirmation), 
                    config=config
                ):
                    # 调试输出
                    # console.print(f"[dim]收到 chunk: {chunk}[/dim]")
                    
                    # 处理恢复后的消息块
                    for node_name, node_output in chunk.items():
                        # 跳过特殊键如 __interrupt__
                        if node_name.startswith('__'):
                            continue
                        if isinstance(node_output, dict) and 'messages' in node_output:
                            for message in node_output['messages']:
                                if hasattr(message, 'content'):
                                    resume_response += message.content
                                elif isinstance(message, dict) and 'content' in message:
                                    resume_response += message['content']
                
                # 将恢复后的响应设置为最终响应
                full_response = resume_response
                
                # 调试输出
                if not full_response.strip():
                    console.print("[yellow]⚠️ 警告: Agent 没有返回内容[/yellow]")
            
        except ImportError:
            console.print("❌ [red]无法导入Command，请检查langgraph版本[/red]")
            return None
        except Exception as resume_error:
            console.print(f"❌ [red]恢复执行失败: {resume_error}[/red]")
            import traceback
            console.print(f"[dim]错误详情: {traceback.format_exc()}[/dim]")
            return None
    
    # 显示完整响应
    if full_response:
        console.print(Panel(
            Markdown(full_response),
            title=f"🤖 {current_agent}",
            border_style="cyan",
            padding=(1, 2)
        ))
        
        # 添加到对话历史
        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": full_response})
    
    return full_response

def create_welcome_screen():
    """创建 Su-Cli 欢迎界面"""
    console = Console()
    
    # 创建渐变色的 ASCII 艺术字标题
    ascii_art = """
███████╗██╗   ██╗      ██████╗██╗     ██╗
██╔════╝██║   ██║     ██╔════╝██║     ██║
███████╗██║   ██║     ██║     ██║     ██║
╚════██║██║   ██║     ██║     ██║     ██║
███████║╚██████╔╝     ╚██████╗███████╗██║
╚══════╝ ╚═════╝       ╚═════╝╚══════╝╚═╝
    """
    
    # 创建渐变色标题
    title = Text(ascii_art)
    title.stylize("bold magenta", 0, len(ascii_art) // 3)
    title.stylize("bold blue", len(ascii_art) // 3, len(ascii_art) * 2 // 3)
    title.stylize("bold cyan", len(ascii_art) * 2 // 3, len(ascii_art))
    
    # 创建欢迎信息
    welcome_text = Text("\n🚀 欢迎使用 Su-Cli 命令行工具！", style="bold white")
    subtitle = Text("一个强大而简洁的命令行助手", style="italic bright_blue")
    
    # 创建使用提示
    tips = [
        "💡 输入命令来开始使用",
        "📝 编辑文件或运行指令", 
        "❓具体描述获得最佳结果",
        "🔧 自定义您的工作流程"
    ]
    
    tip_panels = []
    for i, tip in enumerate(tips):
        color = ["green", "yellow", "blue", "magenta"][i]
        tip_panels.append(Panel(tip, style=color, width=25))
    
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
    
    # 显示提示面板
    console.print(Align.center(Text("✨ 快速开始指南 ✨", style="bold yellow")))
    console.print()
    console.print(Columns(tip_panels, equal=True, expand=True))
    console.print()
    
    # 底部信息
    footer = Panel(
        Align.center(Text("输入 '/help' 获取更多帮助信息 | 输入 '/exit' 退出程序", style="dim white")),
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
        
    if command.lower() in ['/exit', '/quit', 'exit', 'quit']:
        console.print("👋 [bold green]感谢使用 Su-Cli，再见！[/bold green]")
        return False
    elif command.lower() in ['/help', 'help']:
        console.print(Panel.fit(
            "[bold cyan]Su-Cli 帮助信息[/bold cyan]\n\n"
            "📋 [yellow]可用命令：[/yellow]\n"
            "  • [green]/help[/green] - 显示此帮助信息\n"
            "  • [green]/exit[/green] - 退出程序\n"
            "  • [green]/clear[/green] - 清屏\n"
            "  • [green]/agents[/green] - 显示可用的 agents\n"
            "  • [green]/agent <name>[/green] - 切换到指定的 agent\n"
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
    elif command.lower() in ['/clear', 'clear']:
        console.clear()
        create_welcome_screen()
    elif command.lower() in ['/agents', 'agents']:
        if available_agents:
            agent_list = "\n".join([f"  • {'🤖 ' if agent == current_agent else '  '}{agent}" for agent in available_agents])
            console.print(Panel.fit(
                f"[bold cyan]可用的 Agents[/bold cyan]\n\n{agent_list}\n\n"
                f"[yellow]当前 agent:[/yellow] [green]{current_agent}[/green]",
                title="🤖 Agents",
                border_style="cyan"
            ))
        else:
            console.print("❌ [red]没有可用的 agents[/red]")
    elif command.lower().startswith('/agent '):
        agent_name = command[7:].strip()
        if agent_name in available_agents:
            current_agent = agent_name
            console.print(f"✅ [green]已切换到 agent: {current_agent}[/green]")
        else:
            console.print(f"❌ [red]Agent '{agent_name}' 不存在[/red]")
            console.print(f"💡 [yellow]可用的 agents: {', '.join(available_agents)}[/yellow]")
    elif command.lower() in ['/history', 'history']:
        if conversation_history:
            history_text = ""
            for i, msg in enumerate(conversation_history):
                role_emoji = "👤" if msg["role"] == "user" else "🤖"
                role_color = "blue" if msg["role"] == "user" else "green"
                history_text += f"{role_emoji} [{role_color}]{msg['role'].upper()}[/{role_color}]: {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}\n\n"
            
            console.print(Panel.fit(
                history_text.strip(),
                title=f"📝 对话历史 ({len(conversation_history)//2} 轮对话)",
                border_style="yellow"
            ))
        else:
            console.print("📝 [yellow]暂无对话历史[/yellow]")
    elif command.lower() in ['/reset', 'reset']:
        conversation_history.clear()
        global current_thread_id
        current_thread_id = str(uuid.uuid4())  # 重置线程ID
        console.print("🔄 [green]对话历史已清空，已开始新的对话线程[/green]")
    elif command.lower() in ['/style', 'style']:
        # 显示当前风格和可用风格
        styles = {
            "modern": "现代简约风格 (带边框)",
            "minimal": "极简风格",
            "classic": "经典风格 (类似 bash)",
            "colorful": "彩色风格 (带图标)"
        }
        
        style_text = f"[yellow]当前风格:[/yellow] [green]{prompt_style}[/green] - {styles.get(prompt_style, '未知')}\n\n"
        style_text += "[yellow]可用风格:[/yellow]\n"
        for style_name, description in styles.items():
            indicator = "🎯 " if style_name == prompt_style else "   "
            style_text += f"{indicator}[cyan]{style_name}[/cyan] - {description}\n"
        
        console.print(Panel.fit(
            style_text.strip(),
            title="🎨 界面风格",
            border_style="magenta"
        ))
    elif command.lower().startswith('/style '):
        style_name = command[7:].strip().lower()
        valid_styles = ["modern", "minimal", "classic", "colorful"]
        
        if style_name in valid_styles:
            prompt_style = style_name
            console.print(f"✅ [green]已切换到 {style_name} 风格[/green]")
        else:
            console.print(f"❌ [red]风格 '{style_name}' 不存在[/red]")
            console.print(f"💡 [yellow]可用风格: {', '.join(valid_styles)}[/yellow]")
    else:
        # 处理普通对话
        if not current_agent:
            console.print("❌ [red]没有可用的 agent，请先初始化系统[/red]")
            return True
        
        # 调用 agent 进行对话
        await stream_agent_response(command)
    
    return True

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
            if user_input == "/exit":
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
