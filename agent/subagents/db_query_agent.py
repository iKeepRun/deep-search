import os

from agent.prompts import sub_agents_info
from tools.db_tools import list_sql_tables, get_table_data, execute_sql_query

# 数据库查询智能体
db_query_agent={
    "name": sub_agents_info["db"]["name"],
    "description": sub_agents_info["db"]["description"],
    "system_message": sub_agents_info["db"]["system_prompt"],
    "tools": [list_sql_tables, get_table_data, execute_sql_query]
}