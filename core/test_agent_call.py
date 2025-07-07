#!/usr/bin/env python3
"""
Agent 调用功能测试
测试基础的 agent 调用、消息构造和响应处理功能
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging

# 添加 core 模块到路径
sys.path.insert(0, str(Path(__file__).parent))
from core import scanner, scan_agents, get_available_agents

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_message_state(user_input: str, message_history: List[Dict] = None) -> Dict[str, Any]:
    """
    创建符合 Langgraph State 格式的消息状态
    
    Args:
        user_input: 用户输入
        message_history: 历史消息列表
        
    Returns:
        Dict: 格式化的状态字典
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
        
        return {"messages": messages}
        
    except ImportError:
        logger.warning("未安装 langchain_core，使用简单格式")
        # 简单格式兼容
        messages = message_history or []
        messages.append({"role": "user", "content": user_input})
        return {"messages": messages}


async def invoke_agent_test(agent_name: str, user_input: str, message_history: List[Dict] = None) -> Optional[Dict[str, Any]]:
    """
    测试异步调用指定的 agent
    
    Args:
        agent_name: agent 名称
        user_input: 用户输入
        message_history: 历史消息列表
        
    Returns:
        Dict: agent 响应结果
    """
    # 加载 agent 模块
    module = scanner.load_agent_module(agent_name)
    if not module:
        logger.error(f"无法加载 agent: {agent_name}")
        return None
        
    try:
        # 获取 graph 对象
        if hasattr(module, 'graph'):
            graph = module.graph
        else:
            logger.error(f"Agent {agent_name} 没有 graph 对象")
            return None
        
        # 构造输入状态
        state = create_message_state(user_input, message_history)
        
        logger.info(f"🚀 调用 agent: {agent_name}")
        logger.info(f"📝 用户输入: {user_input}")
        
        # 异步调用
        result = await graph.ainvoke(state)
        
        logger.info(f"✅ Agent {agent_name} 调用成功")
        return result
        
    except Exception as e:
        logger.error(f"调用 agent {agent_name} 失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_response_content(result: Dict[str, Any]) -> str:
    """
    从 agent 响应结果中提取内容
    
    Args:
        result: agent 调用结果
        
    Returns:
        str: 提取的响应内容
    """
    try:
        if isinstance(result, dict):
            # 处理标准的 Langgraph 响应格式
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
                elif isinstance(last_message, dict):
                    return last_message.get('content', str(last_message))
                    
            # 如果没有 messages，尝试其他字段
            for key in ['content', 'response', 'output', 'text']:
                if key in result:
                    return str(result[key])
                    
            # 如果都没有，返回整个结果的字符串表示
            return str(result)
        else:
            return str(result)
            
    except Exception as e:
        logger.warning(f"提取响应内容失败: {e}")
        return str(result)


async def test_basic_agent_call():
    """测试基础的 agent 调用功能"""
    print("🔧 测试基础的 Agent 调用功能")
    print("=" * 50)
    
    # 1. 扫描 agents
    print("1. 扫描可用的 agents...")
    agents = scan_agents()
    available_agents = get_available_agents()
    
    if not available_agents:
        print("❌ 没有发现可用的 agents")
        return
    
    print(f"✅ 发现 {len(available_agents)} 个 agents: {available_agents}")
    
    # 2. 选择第一个可用的 agent 进行测试
    test_agent = available_agents[0]
    print(f"\n2. 测试 agent: {test_agent}")
    
    # 3. 测试简单调用
    print(f"\n3. 测试简单调用...")
    user_input = "你好，请介绍一下你自己"
    
    try:
        result = await invoke_agent_test(test_agent, user_input)
        
        if result:
            response_content = extract_response_content(result)
            print(f"📤 用户输入: {user_input}")
            print(f"📥 Agent回复: {response_content[:200]}...")  # 只显示前200个字符
            print(f"✅ 调用成功！")
        else:
            print(f"❌ 调用失败")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_basic_agent_call()) 