from pathlib import Path

from omegaconf import OmegaConf

from app.conf.meta_config import MetaConfig


class MetaKnowledgeService:
    def __init__(self):
        pass

    async def build(self, config_path: Path):
        # 读取配置文件
        context = OmegaConf.load(config_path)
        schema = OmegaConf.structured(MetaConfig)
        app_config: MetaConfig = OmegaConf.to_object(OmegaConf.merge(schema, context))

        # 根据配置文件同步指定的表信息和指标信息
        if app_config.tables:
            # 将表信息和字段信息保存到meta数据库中
            

        if app_config.metrics:
            # 配置文件中有指标信息 同步指标信息