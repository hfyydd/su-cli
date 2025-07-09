#!/usr/bin/env python3
"""测试 Agent 的桌面查询功能"""

import asyncio
from src.agent.graph import graph
from src.agent.state import State
from langchain_core.messages import HumanMessage


async def test_desktop_query():
    """测试桌面查询功能"""
    print("🧪 测试 Agent 桌面和文件操作功能\n")
    
    # 测试用例
    test_cases = [
        "桌面上有哪些文件？",
        "查看 DeepSeek应用手册.docx 文件的信息",
        "搜索桌面上是否有包含 'cli' 关键词的文件或目录",
        "使用网络搜索功能搜索 'MCP Model Context Protocol' 的最新信息"
    ]
    
    for i, query in enumerate(test_cases, 1):
        print(f"🤖 测试用例 {i}: {query}")
        
        # 创建初始状态
        initial_state = State(
            messages=[HumanMessage(content=query)]
        )
        
        try:
            # 运行 Agent
            result = await graph.ainvoke(initial_state)
            
            # 获取 Assistant 的回复
            if result.get("messages"):
                assistant_response = result["messages"][-1].content
                print(f"🤖 Assistant 回复:\n{assistant_response}\n")
                print("📊 测试结果: ✅ 成功")
            else:
                print("❌ 没有收到回复")
                print("📊 测试结果: ❌ 失败")
        
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            print("📊 测试结果: ❌ 失败")
        
        print("-" * 80)
        print()


if __name__ == "__main__":
    asyncio.run(test_desktop_query()) 