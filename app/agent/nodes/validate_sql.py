from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository


async def validate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "校验SQL", "status": "running"})

    try:
        sql = state["sql"]

        dw_mysql_repository: DWMySQLRepository = runtime.context["dw_mysql_repository"]

        result = await dw_mysql_repository.validate_sql(sql)

        writer({"type": "progress", "step": "校验SQL", "status": "success"})
        return result
    except Exception as e:
        logger.error(f"校验SQL失败: {e}")
        writer({"type": "progress", "step": "校验SQL", "status": "error"})
        raise e
