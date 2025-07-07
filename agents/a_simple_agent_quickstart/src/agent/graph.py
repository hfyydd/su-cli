from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from src.agent.state import State
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from src.agent.utils import create_agent
from src.agent.prompts import system_prompt 
from src.agent.tools import get_current_time

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
    """聊天机器人节点，包含用户确认中断"""
    try:
        # 获取用户的最新消息
        user_message = state['messages'][-1].content if state['messages'] else ""
        
        # 触发中断，请求用户确认
        # interrupt() 函数会返回通过 Command(resume=value) 提供的值
        user_confirmation = interrupt({
            "message": f"用户消息: {user_message}",
            "question": "您确认要处理这个请求吗？(yes/no)",
            "type": "confirmation"
        })
        
        # 检查用户确认
        if str(user_confirmation).lower() not in ['yes', 'y', '是', '确认']:
            # 导入必要的消息类型
            from langchain_core.messages import AIMessage
            return {
                "messages": [AIMessage(content="好的，我已取消处理这个请求。")]
            }
        
        # 创建agent，添加系统提示
        agent = create_agent("chatbot", llm, [get_current_time], system_prompt)
        
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
        # 检查是否是中断异常，如果是则重新抛出，不显示错误
        if "Interrupt" in str(type(e)) or "interrupt" in str(e).lower():
            raise e
        # 只对其他异常显示错误信息
        print(f"❌ chatbot节点执行失败: {e}")
        raise e

# 构建LangGraph图
builder = StateGraph(State)

# 添加节点
builder.add_node("chatbot", chatbot_node)

# 添加边
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)

# 创建checkpointer（生产环境中应使用持久化存储）
checkpointer = MemorySaver()

# 编译图，添加checkpointer以支持中断功能
graph = builder.compile(checkpointer=checkpointer)




