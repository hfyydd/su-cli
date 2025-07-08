#!/usr/bin/env python3
"""
a_simple_agent 快速测试

快速验证核心功能是否正常工作
"""

import asyncio
from uuid import uuid4
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from src.agent.graph import build_graph_with_memory


async def quick_test():
    """快速测试 - 验证核心功能"""
    print("🚀 a_simple_agent 快速测试")
    print("-" * 40)
    
    graph = build_graph_with_memory()
    config = {"configurable": {"thread_id": str(uuid4())}}
    
    # 测试基本流程
    initial_state = {"messages": [HumanMessage(content="测试消息")]}
    
    print("✓ 执行到中断...")
    events = []
    async for event in graph.astream(initial_state, config):
        events.append(event)
        if "__interrupt__" in event:
            break
    
    assert any("chatbot" in event for event in events), "chatbot节点应执行"
    assert "__interrupt__" in events[-1], "应触发MCP中断"
    
    print("✓ 测试用户确认...")
    resume_events = []
    async for event in graph.astream(Command(resume="[ACCEPTED]"), config):
        resume_events.append(event)
    
    assert any("tool" in event for event in resume_events), "tool节点应执行"
    
    print("✓ 验证响应消息...")
    tool_event = next(event for event in resume_events if "tool" in event)
    response = tool_event["tool"]["messages"][0].content
    assert "✅ MCP 工具已成功处理请求" in response, "应返回成功消息"
    
    print("🎉 快速测试通过!")
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(quick_test())
        print("😊 所有核心功能正常工作")
        exit(0)
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        exit(1) 