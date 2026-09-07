import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState, MetricInfoState
from app.prompt.prompt_loader import load_prompt
from app.core.log import logger


async def filter_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "过滤指标信息", "status": "running"})

    try:
        query = state["query"]
        metric_infos: list[MetricInfoState] = state.get("metric_infos") or []

        prompt = PromptTemplate(template=load_prompt("filter_metric_info"), input_variables=['query', 'metric_infos'])
        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser

        result = await chain.ainvoke(
            {"query": query, "metric_infos": yaml.dump(metric_infos, allow_unicode=True, sort_keys=False)})

        if not isinstance(result, list):
            logger.warning(f"指标过滤结果格式异常：{result}")
            result = []

        filtered_metric_infos = [metric_info for metric_info in metric_infos if metric_info["name"] in result]

        logger.info(f"过滤后的指标信息：{filtered_metric_infos}")

        writer({"type": "progress", "step": "过滤指标信息", "status": "success"})
        return {"metric_infos": filtered_metric_infos}
    except Exception as e:
        logger.error(f"过滤指标信息失败: {e}")
        writer({"type": "progress", "step": "过滤指标信息", "status": "error"})
        raise e
