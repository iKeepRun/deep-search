from agent.prompts import sub_agents_info
from tools.ragflow_tools import get_assistant_list, create_ask_close
from tools.tavily_tool import internal_search

# 网络搜索子智能体
# 创建子智能体的两种方式： 1.字典 2.compiledSubAgent(langchain.langgraph)

knowledge_base_agent ={
    "name":  sub_agents_info["ragflow"]["name"]  ,
    "description": sub_agents_info["ragflow"]["description"],
    "system_prompt": sub_agents_info["ragflow"]["system_prompt"],
    "tools": [get_assistant_list,create_ask_close],
}