"""
SoundMem包初始化
"""

__version__ = "0.1.0"
__author__ = "SoundMem Team"
__description__ = "智能录音记忆助手 - 实时录音转写与智能问答系统"

from soundmem.core import (
    AudioRecorder,
    ASREngine,
    TextProcessor,
    VectorStore,
    RAGEngine
)

from soundmem.utils import (
    load_config,
    Config,
    setup_logger
)

__all__ = [
    'AudioRecorder',
    'ASREngine',
    'TextProcessor',
    'VectorStore',
    'RAGEngine',
    'load_config',
    'Config',
    'setup_logger'
]

