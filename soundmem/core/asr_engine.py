"""
ASR引擎模块
使用FunASR进行语音识别
"""

from typing import Optional, Dict, Any
import numpy as np
from funasr import AutoModel
from soundmem.utils.logger import log

class ASREngine:
    """ASR语音识别引擎"""
    
    def __init__(self, model_name: str = "paraformer-zh", use_vad: bool = True, use_punc: bool = True):
        """
        初始化ASR引擎
        
        Args:
            model_name: 模型名称
            use_vad: 是否使用VAD
            use_punc: 是否使用标点恢复
        """
        self.model_name = model_name
        self.use_vad = use_vad
        self.use_punc = use_punc
        self.model = None
        
        log.info(f"初始化ASR引擎: model={model_name}, vad={use_vad}, punc={use_punc}")
    
    def load_model(self):
        """加载模型"""
        try:
            log.info("正在加载ASR模型...")
            
            # 加载模型
            self.model = AutoModel(
                model=self.model_name,
                vad_model="fsmn-vad" if self.use_vad else None,
                punc_model="ct-punc" if self.use_punc else None,
                device="cpu"
            )
            
            log.info("ASR模型加载完成")
            
        except Exception as e:
            log.error(f"加载ASR模型失败: {e}")
            raise
    
    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Dict[str, Any]:
        """
        转写音频
        
        Args:
            audio_data: 音频数据
            sample_rate: 采样率
            
        Returns:
            转写结果字典
        """
        if self.model is None:
            raise RuntimeError("模型未加载，请先调用load_model()")
        
        try:
            # 确保音频数据是一维的
            if len(audio_data.shape) > 1:
                audio_data = audio_data.flatten()
            
            # 转换为int16格式
            if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
                audio_data = (audio_data * 32767).astype(np.int16)
            
            # 进行识别
            result = self.model.generate(
                input=audio_data,
                batch_size_s=300,  # 批处理大小
                hotword=""
            )
            
            # 提取文本
            if result and len(result) > 0:
                text = result[0].get("text", "")
                return {
                    "text": text,
                    "success": True,
                    "raw_result": result
                }
            else:
                return {
                    "text": "",
                    "success": False,
                    "error": "识别结果为空"
                }
                
        except Exception as e:
            log.error(f"音频转写失败: {e}")
            return {
                "text": "",
                "success": False,
                "error": str(e)
            }
    
    def transcribe_stream(self, audio_stream):
        """
        流式转写（待实现）
        
        Args:
            audio_stream: 音频流
        """
        # TODO: 实现流式识别
        pass

