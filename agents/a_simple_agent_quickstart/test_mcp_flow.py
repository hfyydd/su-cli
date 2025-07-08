"""
测试 MCP 工具节点功能的脚本
"""

import asyncio
from uuid import uuid4
from langchain_core.messages import HumanMessage
from src.agent.graph import build_graph_with_memory
from langgraph.types import Command

async def test_mcp_flow():
    """测试包含 MCP 工具节点的完整流程"""
    
    # 构建带内存的图
    graph = build_graph_with_memory()
    
    # 创建配置
    config = {
        "configurable": {
            "thread_id": str(uuid4())
        }
    }
    
    # 初始状态
    initial_state = {
        "messages": [HumanMessage(content="请帮我查询天气信息")]
    }
    
    print("🚀 开始测试 MCP 工具流程...")
    print(f"📝 用户消息: {initial_state['messages'][0].content}")
    print("-" * 50)
    
    try:
        # 运行图直到第一个中断
        events = []
        async for event in graph.astream(initial_state, config):
            events.append(event)
            print(f"📊 事件: {event}")
            
            # 检查是否有中断
            if "__interrupt__" in event:
                print("\n⏸️  检测到中断，等待用户确认...")
                interrupt_info = event["__interrupt__"]
                print(f"🔔 中断信息: {interrupt_info}")
                
                # 模拟用户接受确认
                print("✅ 模拟用户接受 MCP 操作...")
                
                # 继续执行，提供用户确认
                resume_config = {
                    **config,
                    "configurable": {
                        **config["configurable"],
                    }
                }
                
                # 使用 Command(resume="[ACCEPTED]") 来恢复执行
                try:
                    async for event in graph.astream(
                        Command(resume="[ACCEPTED]"), 
                        resume_config
                    ):
                        events.append(event)
                        print(f"📊 恢复后事件: {event}")
                except Exception as e:
                    print(f"❌ 恢复执行时出错: {e}")
                
                break
        
        print("\n" + "=" * 50)
        print("📋 完整执行日志:")
        for i, event in enumerate(events, 1):
            print(f"{i}. {event}")
            
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

async def test_reject_mcp_flow():
    """测试拒绝 MCP 操作的流程"""
    
    # 构建带内存的图
    graph = build_graph_with_memory()
    
    # 创建配置
    config = {
        "configurable": {
            "thread_id": str(uuid4())
        }
    }
    
    # 初始状态
    initial_state = {
        "messages": [HumanMessage(content="请帮我搜索一些信息")]
    }
    
    print("\n🚀 开始测试拒绝 MCP 操作流程...")
    print(f"📝 用户消息: {initial_state['messages'][0].content}")
    print("-" * 50)
    
    try:
        # 运行图直到第一个中断
        events = []
        async for event in graph.astream(initial_state, config):
            events.append(event)
            print(f"📊 事件: {event}")
            
            # 检查是否有中断
            if "__interrupt__" in event:
                print("\n⏸️  检测到中断，等待用户确认...")
                interrupt_info = event["__interrupt__"]
                print(f"🔔 中断信息: {interrupt_info}")
                
                # 模拟用户拒绝确认
                print("❌ 模拟用户拒绝 MCP 操作...")
                
                # 继续执行，提供用户拒绝
                resume_config = {
                    **config,
                    "configurable": {
                        **config["configurable"],
                    }
                }
                
                # 使用 Command(resume="[REJECTED]") 来恢复执行
                try:
                    async for event in graph.astream(
                        Command(resume="[REJECTED]"), 
                        resume_config
                    ):
                        events.append(event)
                        print(f"📊 恢复后事件: {event}")
                except Exception as e:
                    print(f"❌ 恢复执行时出错: {e}")
                
                break
        
        print("\n" + "=" * 50)
        print("📋 完整执行日志:")
        for i, event in enumerate(events, 1):
            print(f"{i}. {event}")
            
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_mcp_flow())
    asyncio.run(test_reject_mcp_flow()) 