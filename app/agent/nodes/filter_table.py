import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState, TableInfoState
from app.prompt.prompt_loader import load_prompt
from app.core.log import logger


async def filter_table(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer("过滤表信息")

    query = state["query"]
    table_infos: list[TableInfoState] = state.get("table_infos") or []

    prompt = PromptTemplate(template=load_prompt("filter_table_info"), input_variables=['query', 'table_infos'])
    output_parser = JsonOutputParser()

    chain = prompt | llm | output_parser

    result = await chain.ainvoke(
        {"query": query, "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False)})

    if not isinstance(result, dict):
        logger.warning(f"表过滤结果格式异常：{result}")
        result = {}

    filtered_table_infos: list[TableInfoState] = []
    for table_info in table_infos:
        selected_columns = result.get(table_info["name"])
        if not isinstance(selected_columns, list):
            continue
        table_info["columns"] = [column_info for column_info in table_info["columns"] if
                                 column_info["name"] in selected_columns]
        if table_info["columns"]:
            filtered_table_infos.append(table_info)

    logger.info(f"过滤后的表信息：{filtered_table_infos}")
    return {"table_infos": filtered_table_infos}
