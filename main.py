from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.columns import Columns
from rich.align import Align
from rich.prompt import Prompt

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
        "❓ 具体描述获得最佳结果",
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

def handle_command(command: str) -> bool:
    """处理用户输入的命令
    
    Args:
        command: 用户输入的命令
        
    Returns:
        bool: True 继续程序，False 退出程序
    """
    console = Console()
    
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
            "  • [green]/clear[/green] - 清屏\n\n"
            "💡 [yellow]提示：[/yellow] 您可以输入任何文本，Su-Cli 将处理您的请求",
            title="🔧 帮助",
            border_style="cyan"
        ))
    elif command.lower() in ['/clear', 'clear']:
        console.clear()
        create_welcome_screen()
    else:
        console.print(f"💬 [bold white]您输入了：[/bold white][cyan]{command}[/cyan]")
        console.print("⚡ [yellow]正在处理您的请求...[/yellow]")
        # 这里可以添加更多的命令处理逻辑
        console.print("✅ [green]命令已接收！目前这是一个演示版本。[/green]\n")
    
    return True

def main():
    """主函数"""
    console = Console()
    
    # 显示欢迎界面
    create_welcome_screen()
    
    # 主循环 - 处理用户输入
    while True:
        try:
            # 创建输入提示
            user_input = Prompt.ask(
                "[bold green]Su-Cli[/bold green] [dim]>[/dim]",
                default=""
            )
            
            # 处理命令
            should_continue = handle_command(user_input)
            if not should_continue:
                break
                
        except KeyboardInterrupt:
            console.print("\n👋 [bold green]感谢使用 Su-Cli，再见！[/bold green]")
            break
        except EOFError:
            console.print("\n👋 [bold green]感谢使用 Su-Cli，再见！[/bold green]")
            break

if __name__ == "__main__":
    main()
