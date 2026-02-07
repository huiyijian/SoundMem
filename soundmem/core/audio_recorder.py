"""
录音模块
实现实时音频采集功能
"""

import queue
import threading
import time
from typing import Optional, Callable
import numpy as np
import sounddevice as sd
from soundmem.utils.logger import log

class AudioRecorder:
    """音频录音器"""
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1, chunk_duration: int = 5):
        """
        初始化录音器
        
        Args:
            sample_rate: 采样率
            channels: 声道数
            chunk_duration: 音频块时长(秒)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_duration = chunk_duration
        self.chunk_size = sample_rate * chunk_duration
        
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.stream: Optional[sd.InputStream] = None
        self.record_thread: Optional[threading.Thread] = None
        
        log.info(f"音频录音器初始化: 采样率={sample_rate}Hz, 声道={channels}, 块时长={chunk_duration}s")
    
    def _audio_callback(self, indata, frames, time_info, status):
        """音频回调函数"""
        if status:
            log.warning(f"音频流状态: {status}")
        
        # 将音频数据放入队列
        audio_data = indata.copy()
        self.audio_queue.put(audio_data)
    
    def start_recording(self):
        """开始录音"""
        if self.is_recording:
            log.warning("录音已在进行中")
            return
        
        self.is_recording = True
        
        try:
            # 创建音频流
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32,
                callback=self._audio_callback,
                blocksize=int(self.sample_rate * 0.1)  # 100ms块
            )
            self.stream.start()
            log.info("录音开始")
            
        except Exception as e:
            log.error(f"启动录音失败: {e}")
            self.is_recording = False
            raise
    
    def stop_recording(self):
        """停止录音"""
        if not self.is_recording:
            log.warning("录音未在进行中")
            return
        
        self.is_recording = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        log.info("录音停止")
    
    def get_audio_chunk(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """
        获取音频块
        
        Args:
            timeout: 超时时间(秒)
            
        Returns:
            音频数据数组，如果超时返回None
        """
        try:
            audio_data = self.audio_queue.get(timeout=timeout)
            return audio_data
        except queue.Empty:
            return None
    
    def get_audio_stream(self) -> queue.Queue:
        """获取音频流队列"""
        return self.audio_queue
    
    def clear_queue(self):
        """清空音频队列"""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
    
    @staticmethod
    def list_devices():
        """列出可用的音频设备"""
        devices = sd.query_devices()
        log.info("可用音频设备:")
        for i, device in enumerate(devices):
            log.info(f"  [{i}] {device['name']} (输入通道: {device['max_input_channels']})")
        return devices
    
    def __del__(self):
        """析构函数"""
        if self.is_recording:
            self.stop_recording()

