"""
ASR引擎模块
使用FunASR进行语音识别
"""

from typing import Optional, Dict, Any, List
import numpy as np
from funasr import AutoModel
from soundmem.utils.logger import log
import tempfile
import os
import soundfile as sf

class ASREngine:
    """ASR语音识别引擎"""
    
    def __init__(self, model_name: str = "paraformer-zh", use_vad: bool = True, use_punc: bool = True):
        """
        初始化ASR引擎
        
        Args:
            model_name: 模型名称
            use_vad: 是否使用VAD（语音活动检测）
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
            
            # 加载模型 - FunASR会自动处理VAD分段和标点恢复
            self.model = AutoModel(
                model=self.model_name,
                vad_model="fsmn-vad" if self.use_vad else None,
                punc_model="ct-punc" if self.use_punc else None,
                device="cpu"
            )
            
            log.info("ASR模型加载完成（包含VAD和标点恢复）")
            
        except Exception as e:
            log.error(f"加载ASR模型失败: {e}")
            raise
    
    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Dict[str, Any]:
        """
        转写音频 - 使用FunASR的VAD自动分段
        
        Args:
            audio_data: 音频数据
            sample_rate: 采样率
            
        Returns:
            转写结果字典，包含多个分段结果
        """
        if self.model is None:
            raise RuntimeError("模型未加载，请先调用load_model()")
        
        try:
            # 确保音频数据是一维的
            if len(audio_data.shape) > 1:
                audio_data = audio_data.flatten()
            
            # 确保音频数据是float32格式（FunASR要求）
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32767.0
            elif audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # 保存为临时WAV文件（FunASR对文件输入处理更好）
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                sf.write(tmp_path, audio_data, sample_rate)
            
            try:
                # 进行识别 - FunASR会自动使用VAD分段
                result = self.model.generate(
                    input=tmp_path,
                    batch_size_s=300,  # 批处理大小
                    hotword=""
                )
                
                # 提取文本 - FunASR的VAD会返回多个分段
                if result and len(result) > 0:
                    # 合并所有分段的文本
                    all_texts = []
                    segments = []
                    
                    for item in result:
                        text = item.get("text", "")
                        if text:
                            all_texts.append(text)
                            segments.append({
                                "text": text,
                                "start": item.get("start", 0),
                                "end": item.get("end", 0)
                            })
                    
                    combined_text = " ".join(all_texts)
                    
                    return {
                        "text": combined_text,
                        "segments": segments,  # 保留分段信息
                        "success": True,
                        "raw_result": result
                    }
                else:
                    return {
                        "text": "",
                        "segments": [],
                        "success": False,
                        "error": "识别结果为空"
                    }
            finally:
                # 删除临时文件
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                
        except Exception as e:
            log.error(f"音频转写失败: {e}")
            return {
                "text": "",
                "segments": [],
                "success": False,
                "error": str(e)
            }
    
    def transcribe_realtime(self, audio_data: np.ndarray, sample_rate: int = 16000, 
                           cache: Optional[Dict] = None) -> Dict[str, Any]:
        """
        实时流式转写（使用FunASR的流式模式）
        
        Args:
            audio_data: 音频数据
            sample_rate: 采样率
            cache: 缓存字典，用于保持上下文
            
        Returns:
            转写结果字典
        """
        if self.model is None:
            raise RuntimeError("模型未加载，请先调用load_model()")
        
        try:
            # 确保音频数据格式正确
            if len(audio_data.shape) > 1:
                audio_data = audio_data.flatten()
            
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32767.0
            elif audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # 使用流式识别
            if cache is None:
                cache = {}
            
            result = self.model.generate(
                input=audio_data,
                cache=cache,  # 保持上下文
                is_final=False,  # 非最终结果
                batch_size_s=300
            )
            
            if result and len(result) > 0:
                text = result[0].get("text", "")
                return {
                    "text": text,
                    "success": True,
                    "is_final": False,
                    "cache": cache
                }
            else:
                return {
                    "text": "",
                    "success": False,
                    "is_final": False,
                    "cache": cache
                }
                
        except Exception as e:
            log.error(f"实时转写失败: {e}")
            return {
                "text": "",
                "success": False,
                "error": str(e),
                "cache": cache
            }

