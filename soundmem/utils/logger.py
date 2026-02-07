"""
日志工具模块
"""

import sys
from pathlib import Path
from loguru import logger
from soundmem.utils.config import load_config

def setup_logger():
    """设置日志"""
    config = load_config()
    
    # 移除默认处理器
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=config.log_level,
        colorize=True
    )
    
    # 添加文件输出
    log_path = Path(config.log_path)
    log_path.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_path / "soundmem_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=config.log_level,
        rotation="00:00",  # 每天轮转
        retention="7 days",  # 保留7天
        compression="zip",  # 压缩旧日志
        encoding="utf-8"
    )
    
    return logger

# 导出全局logger实例
log = setup_logger()

