from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository


async def validate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer("校验SQL")

    sql = state["sql"]

    dw_mysql_repository: DWMySQLRepository = runtime.context["dw_mysql_repository"]

    return await dw_mysql_repository.validate_sql(sql)
