import os

# import mysql
from dotenv import load_dotenv, find_dotenv
from langchain_core.tools import tool

from mysql.connector import connect, Error

from api.monitor import monitor

load_dotenv(find_dotenv(), override=True)

# 加载数据库配置信息
def get_db_config():
    config = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
        "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
        "collation": os.getenv("MYSQL_COLLATION", "utf8mb4_unicode_ci"),
        "autocommit": True,
        "sql_mode": os.getenv("MYSQL_SQL_MODE", "TRADITIONAL")
    }
    # 移出空的值
    config = {k: v for k, v in config.items() if v}
    # 没有必须配项则报错
    require_key=[ "user", "password", "database"]
    if any(k not in config for k in require_key):
        raise ValueError("缺少必要配置项")
    return config


@tool
def list_sql_tables()->str:
   """
    查询数据库所有的表
    核心用途：
        AI Agent 需要查看数据库中有哪些表时调用，为后续执行 SQL 查询提供基础信息。
    返回值：
        str: 成功时返回 "可用数据表：表1, 表2, ..."；
             配置缺失时返回错误提示；
             执行异常时返回具体错误信息。
    异常处理：
        捕获数据库连接/执行 SQL 时的所有 Error 异常，返回可读的错误信息，避免 Agent 崩溃。
   :return:
   """
   # 埋点监控：记录工具调用行为（便于分析工具使用频率）
   monitor.report_tool("数据库表获取工具")
   # 获取数据库配置信息
   config=get_db_config()
   try:
   # 创建mysql连接
       with connect(**config) as conn:
           with conn.cursor() as cursor:
               cursor.execute("SHOW TABLES")
               tables = cursor.fetchall()
               if not tables:
                   return "没有找到任何表"
               else:
                   return "可用数据表：" + ", ".join(table[0] for table in tables)

   except Error as e:
       return f"查询数据库表失败: {str(e)}"


@tool
def get_table_data(table_name:str)->str:
    """
    查询表数据,最多返回一百条数据
    :param table_name: 需要查询的表名
    :return: 返回csv格式的表数据
           id , name , ege \n
           1  , xxx  , 18  \n
           2  , zzz  , 16  \n
    """
    # 埋点监控：记录工具调用行为（便于分析工具使用频率）
    monitor.report_tool(f"数据库表数据获取工具，查询的表是：{table_name}")
    config=get_db_config()
    try:
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
                # 获取表的列名
                description=cursor.description
                if  description is None:
                    return f"表 {table_name} 没有数据"
                # 获取列名
                column_names=[desc[0] for desc in description]
                rows=cursor.fetchall()
                str_rows=[",".join( map(str, row)) for row in rows]

                return ",".join(column_names) + "\n" + "\n".join(str_rows)
    except Error as e:
        return f"查询表数据失败: {str(e)}"

@tool
def execute_sql_query(sql:str)->str:
    """
    执行自定义sql查询，必须先根据list_sql_tables 明确表名，再根据get_table_data明确表的列名和数据结构
    :param sql: 自定义的sql语句
    :return:
    """
    config = get_db_config()
    try:
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                # 获取表的列名
                description = cursor.description
                if not description:
                    return f"执行{sql}没有查询到数据"
                # 获取列名
                column_names = [desc[0] for desc in description]
                rows = cursor.fetchall()
                str_rows = [",".join(map(str, row)) for row in rows]

                return ",".join(column_names) + "\n" + "\n".join(str_rows)
    except Error as e:
        return f"查询表数据失败: {str(e)}"
if __name__ == '__main__':
    print(excute_sql_query("select * from drugs join sales_records on drugs.drug_id = sales_records.drug_id"))
