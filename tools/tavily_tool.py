import os

from dotenv.variables import Literal
from langchain_core.tools import tool
from tavily import TavilyClient

from api.monitor import monitor

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))




@tool
def internal_search(query:str,
                    topic:Literal["news","finance","general"]="general",
                    max_results:int=5,
                    include_raw_content:bool= False):
    """
    根据用户问题进行网络信息搜索
    :param query:   用户的查询信息
    :param topic:   查询的类型
    :param max_results:  返回的数据条数
    :param include_raw_content:  是否返回精简内容  False:精简  True:详细
    :return:
    """


    monitor.report_tool(tool_name="网络搜索工具",
                        args={"query":query,"topic":topic,"max_results":max_results,"include_raw_content":include_raw_content})
    results = client.search(query=query,
                            topic=topic,
                            max_results=max_results,
                            include_raw_content= include_raw_content,
                            )
    return results

