"""
模型加载器模块
"""

from soundmem.utils.logger import log

class ModelLoader:
    """模型加载器"""
    
    @staticmethod
    def download_models():
        """下载所有需要的模型"""
        log.info("开始下载模型...")
        
        # TODO: 实现模型下载逻辑
        # 可以使用modelscope下载FunASR模型
        # 使用huggingface下载向量模型
        
        log.info("模型下载完成")


