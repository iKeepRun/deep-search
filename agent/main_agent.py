# 创建主智能体
import shutil
from pathlib import Path

from deepagents import create_deep_agent
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver

from agent.llm import llm
from agent.prompts import main_agent_info
from agent.subagents.db_query_agent import db_query_agent
from agent.subagents.knowledge_base_agent import knowledge_base_agent
from agent.subagents.network_search_agent import network_search_agent
from api.context import set_thread_context, set_session_context, reset_session_context
from api.monitor import monitor

from tools.markdown_tools import generate_markdown
from tools.pdf_tools import convert_md_to_pdf
from tools.read_file_content import read_file_content



#创建主智能体
main_agent=create_deep_agent(
    model=llm ,
    system_prompt=main_agent_info['system_prompt'],
    tools=[generate_markdown,convert_md_to_pdf,read_file_content],
    # checkpointer=InMemorySaver(),
    subagents=[knowledge_base_agent,network_search_agent,db_query_agent],
)


def _process_stream_chunk(chunk):
    """
    处理 LangGraph 流式输出的增量状态 (Stream Processing)。
    目标：
    1. 解析 Agent 的每一步思考和行动。
    2. 识别关键事件（工具调用、子 Agent 委派、最终回复）。
    3. 通过 Monitor 实时上报状态给前端。
    核心逻辑：
    - 监听 `tool_calls` -> 记录日志，若是 'task' 则上报子 Agent 状态。
    - 监听 `content` -> 若无工具调用，则视为 Agent 的最终回复。
    Args:
        chunk (dict): 增量状态字典，如 {"node_name": {"messages": [AIMessage(...)]}}
    """
    # 1. [记录] 记录原始数据便于回溯
    # logger.log_main_chunk(chunk)

    # 2. [遍历] 解析每个节点的输出 (通常是 'agent' 或 'tools' 节点)
    for node_name, state in chunk.items():
        if not state or "messages" not in state: continue
        # 3. [提取] 获取最新一条消息 (Latest Message)
        messages = state["messages"]
        if isinstance(messages, list) and messages:
            last_msg = messages[-1]
            # 4. [分支] 处理 AI 消息 (AIMessage)
            if isinstance(last_msg, AIMessage):
                # Case 1: Agent 决定调用工具 (Tool Call)
                if last_msg.tool_calls:
                    for tool in last_msg.tool_calls:
                        # 特殊处理：如果是 'task' 工具，说明正在委派给子 Agent
                        if tool['name'] == 'task':
                            monitor.report_assistant(
                                tool['args'].get('subagent_type', 'Agent'),
                                {"desc": tool['args'].get('description')}
                            )
                # Case 2: Agent 生成最终回复 (Final Answer)
                elif last_msg.content:
                    monitor.report_task_result(last_msg.content)

async def run_main_agent(input_text:str, session_id:str):
    print(f"开始运行主智能体，本次的会话ID为：{session_id}")

    # 获取项目根目录
    project_root_dir = Path(__file__).parents[1].resolve()
    # 会话存储目录
    session_dir=project_root_dir / "output"/ f"session_{session_id}"
    # 没有就创建
    session_dir.mkdir(parents=True, exist_ok=True)
    # 将路径转换为字符串（替换掉 \ ，防止大模型出现幻觉）
    session_dir_str=str(session_dir).replace("\\", "/")
    # [相对化] 获取相对路径 (用于提示词展示，如 "output/session_123")
    relative_session_dir = str(session_dir.relative_to(project_root_dir)).replace("\\", "/")

    # 上传路径
    upload_dir = project_root_dir /  "upload" / f"session_{session_id}"
    # 上传文件信息
    uploaded_info = ""
    # 判断是否有上传文件
    if upload_dir.exists():
        print("有上传文件")
        # 获取上传文件列表
        upload_file_list = [f.name for f in upload_dir.iterdir() if f.is_file()]

        # 遍历上传文件列表
        if upload_file_list:
            for filename in upload_file_list:
                # 获取文件名
                # file_name = file.name
                # # 获取文件内容
                # file_content = file.read_text(encoding="utf-8")
                # # 将文件名和内容拼接到输入文本中
                # input_text += f"上传文件名：{file_name}\n上传文件内容：{file_content}\n"
                # 将上传文件复制到会话目录下
                shutil.copy2(upload_dir /filename, session_dir / filename)
                # [构造] 生成文件列表提示词
            uploaded_info = (f"\n    [已上传文件] 已加载到工作目录:\n" +
                                 "\n".join([f"    - {f}" for f in upload_file_list]) +
                                 "\n    请优先使用工具读取并参考这些文件。")

    # 设置上下文
    thread_token = set_thread_context(session_id)
    session_token = set_session_context(session_dir_str)

    # 给前端推送文件夹，方便后续查询当前会话对应文件夹下的所有文件
    monitor.report_session_dir(session_dir_str)

    # 配置运行参数
    config={
        "configurable": {
            "thread_id": session_id,          #用于memory记忆上下文
        }
    }
    # 构建提示词
    path_instruction = f"""
       【工作环境指令】
       工作目录: {relative_session_dir}
       {uploaded_info}

       规则：
       1. 新生成文件必须保存到工作目录：'{relative_session_dir}/filename'
       2. 使用相对路径，禁止使用绝对路径
       3. 若存在上传文件，请先分析内容
       """

    try:
        # astream: 异步生成器，像流水线一样逐个吐出 Agent 的思考片段
        async for chunk in main_agent.astream(
                {"messages": [{"role": "user", "content": input_text + path_instruction}]},
                config=config
        ):
            # 实时处理每一个片段 (上报前端)
            _process_stream_chunk(chunk)
        return "Done"
    except Exception as e:
        # 7. [异常处理] 兜底捕获
        print(f"Error: {e}")
        monitor._emit("error", f"Execution failed: {e}")
        return f"Error: {e}"
    finally:
        # 8. [资源清理] 必须重置 ContextVars，防止线程池复用导致的上下文污染
        # if 'session_token' in locals():
        reset_session_context(session_token, thread_token)


