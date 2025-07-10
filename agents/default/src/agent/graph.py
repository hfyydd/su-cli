
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.agent.state import State
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from src.agent.utils import create_agent
from src.agent.prompts import system_prompt 
from src.agent.tools import get_all_tools_async

load_dotenv()

# 创建ChatOpenAI实例
model_name = os.getenv("DEEPSEEK_MODEL") or os.getenv("MODEL_NAME")
llm = ChatOpenAI(
    model=model_name,
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    temperature=0
)

async def chatbot_node(state: State):
    """聊天机器人节点"""
    try:
        from src.agent.mcp_utils import MCPToolManager
        
        # 本地工具
        from src.agent.tools import get_current_time
        local_tools = [get_current_time]
        
        # 使用 MCP 管理器获取 MCP 工具
        mcp_manager = MCPToolManager()
        client_config = mcp_manager._convert_config_for_client()
        
        if client_config:
            # 使用 MultiServerMCPClient 直接调用 get_tools()
            from langchain_mcp_adapters.client import MultiServerMCPClient
            
            client = MultiServerMCPClient(client_config)
            mcp_tools = await client.get_tools()
            tools = local_tools + mcp_tools
            
            # 调试信息：显示可用的工具
            tool_names = [tool.name for tool in tools]
            print(f"🔧 {len(tool_names)} tools available")
            
            # 创建agent，添加系统提示和所有工具
            agent = create_agent("chatbot", llm, tools, system_prompt)
            
            # 执行 agent 并返回结果
            response = await agent.ainvoke(state)
            
            if isinstance(response, dict) and 'messages' in response:
                new_messages = response['messages'][len(state['messages']):]
                return {"messages": new_messages}
            else:
                return response
        else:
            # 没有 MCP 配置，只使用本地工具
            tools = local_tools
            
            # 调试信息：显示可用的工具
            tool_names = [tool.name for tool in tools]
            print(f"🔧 {len(tool_names)} tools available (local only)")
            
            # 创建agent，添加系统提示和所有工具
            agent = create_agent("chatbot", llm, tools, system_prompt)
        
            # create_react_agent需要传入整个状态，而不是消息列表
            response = await agent.ainvoke(state)
            
            # create_react_agent返回字典格式 {'messages': [...]}
            # 需要提取新消息（agent的回复），而不是替换整个消息列表
            if isinstance(response, dict) and 'messages' in response:
                # 获取新消息（通常是最后一条，即agent的回复）
                new_messages = response['messages'][len(state['messages']):]
                return {"messages": new_messages}
            else:
                # 如果格式不符合预期，直接返回
                return response
        
    except Exception as e:
        # 记录错误但不显示技术细节
        print(f"❌ Agent 执行出错: {str(e)}")
        # 返回错误消息作为 agent 的回复
        from langchain_core.messages import AIMessage
        error_msg = AIMessage(content=f"抱歉，我遇到了一个技术问题。错误信息：{str(e)}")
        return {"messages": [error_msg]}


def _build_base_graph():
    """构建基础图结构"""
    builder = StateGraph(State)
    
    # 添加节点
    builder.add_node("chatbot", chatbot_node)
    
    # 添加边
    builder.add_edge(START, "chatbot")
    builder.add_edge("chatbot", END)
    
    return builder


def build_graph():
    """构建不带内存的图"""
    builder = _build_base_graph()
    return builder.compile()


def build_graph_with_memory():
    """构建带内存的图"""
    # 使用持久内存保存对话历史
    memory = MemorySaver()
    
    builder = _build_base_graph()
    return builder.compile(checkpointer=memory)


# 默认图（不带内存）
graph = build_graph()




