import os

from dotenv import load_dotenv, find_dotenv
from langchain_core.tools import tool
from ragflow_sdk import RAGFlow

from api.monitor import monitor

#加载环境配置
load_dotenv(find_dotenv())

#创建ragflow客户端
ragflow_client=RAGFlow(
    api_key=os.getenv("RAGFLOW_API_KEY"),
    base_url=os.getenv("RAGFLOW_BASE_URL")
)

@tool
def get_assistant_list():
    """
    获取RAGFlow服务器所有的助手及每个助手关联的知识库,并返回组合后的字符串。如果需要知道有哪些助手可用，请使用此工具
    强调：向助手提问之前必须先调用此工具，明确助手的作用

    :return: 示例数据--> [ 助手名称： 法律助手，功能介绍：你是一个法律助手，擅长... ;关联的知识库： 中华人民共和国刑法、交通法
                         助手名称： 空调助手，功能介绍：你是一个空调安装维护助手，擅长... ;关联的知识库： 空调维修手册、...
                          ...
                        ]
    """

    # 埋点向前端推送调用信息
    monitor.report_tool(tool_name="ragflow助手列表查询工具：get_assistant_list")
    # 助手列表
    chat_list=ragflow_client.list_chats()
    print(f"助手数量：{len(chat_list)}")
    if not chat_list:
        return "没有助手可用"
    try:
        total_chat_info = ""
        for chat in chat_list:
            # print(f"助手名称：{chat.name},功能介绍：{chat.description}")
            dataset_names = []
            # 获取助手关联的知识库
            dataset_list = chat.datasets
            if dataset_list and isinstance(dataset_list, list):
                for dataset in dataset_list:
                    # print(f"知识库名：{dataset}")
                    dataset_names.append(dataset["name"])
            total_chat_info += f"助手名称：{chat.name},功能介绍：{chat.description} ;关联知识库：{"、".join(dataset_names)}\n"
        return total_chat_info
    except Exception as e:
        return  f"获取助手信息失败，异常信息：{str(e)}"



# @tool
def create_ask_close(assistant_name:str,ask: str)-> str:
    """
    向某个助手创建一个新会话，提问一次，然后删除该会话，并返回答案。当需要向特定的 RAGFlow 助手提问时，使用此工具
    强调：调用此工具前，必须先调用get_assistant_list工具，明确查询助手的名称和对应的问题
    :param assistant_name: 助手的名称
    :param ask: 提问的问题
    :return:  返回知识库的答案
    """
    # 埋点向前端推送调用信息
    monitor.report_tool(tool_name=" ragflow创建会话并提问并关闭会话工具：create_ask_close")
    try :

        assistants = ragflow_client.list_chats(name=assistant_name)
        assistant = assistants[0]
        session = assistant.create_session()
        stream=session.ask(question= ask,stream= True)

        result= ""
        for chunk in stream:
            result= chunk.content
        # 删除会话
        assistant.delete_sessions(ids=[session.id])
        return   result
    except Exception as e:
        return  f"创建会话并提问失败，异常信息：{str(e)}"


if __name__ == '__main__':
    # print(get_assistant_list())
    print(create_ask_close("空调安装助手","空调怎么加制冷剂"))