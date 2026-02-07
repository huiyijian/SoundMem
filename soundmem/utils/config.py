"""
配置管理模块
"""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# 加载环境变量
load_dotenv()

class Config(BaseModel):
    """配置类"""
    
    model_config = {"protected_namespaces": ()}  # 允许使用model_开头的字段名
    
    # API配置
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    openai_base_url: str = Field(default="https://api.openai.com/v1", description="API Base URL")
    model_name: str = Field(default="gpt-3.5-turbo", description="模型名称")
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: int = Field(default=2000, description="最大token数")
    
    # 向量数据库配置
    vector_db_path: str = Field(default="./data/vectordb", description="向量数据库路径")
    collection_name: str = Field(default="soundmem_recordings", description="集合名称")
    
    # 录音配置
    sample_rate: int = Field(default=16000, description="采样率")
    channels: int = Field(default=1, description="声道数")
    chunk_duration: int = Field(default=5, description="音频块时长(秒)")
    
    # RAG配置
    top_k: int = Field(default=5, description="检索Top-K")
    similarity_threshold: float = Field(default=0.5, description="相似度阈值")
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_path: str = Field(default="./logs", description="日志路径")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def load_config() -> Config:
    """加载配置"""
    return Config(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        model_name=os.getenv("MODEL_NAME", "gpt-3.5-turbo"),
        temperature=float(os.getenv("TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("MAX_TOKENS", "2000")),
        vector_db_path=os.getenv("VECTOR_DB_PATH", "./data/vectordb"),
        collection_name=os.getenv("COLLECTION_NAME", "soundmem_recordings"),
        sample_rate=int(os.getenv("SAMPLE_RATE", "16000")),
        channels=int(os.getenv("CHANNELS", "1")),
        chunk_duration=int(os.getenv("CHUNK_DURATION", "5")),
        top_k=int(os.getenv("TOP_K", "5")),
        similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", "0.5")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_path=os.getenv("LOG_PATH", "./logs")
    )

def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent.parent

def ensure_directories():
    """确保必要的目录存在"""
    root = get_project_root()
    directories = [
        root / "data" / "audio",
        root / "data" / "vectordb",
        root / "logs",
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

