"""
Gradio用户界面
"""

import gradio as gr
import threading
import queue
import time
from datetime import datetime
from typing import Optional
import numpy as np

from soundmem.core import AudioRecorder, ASREngine, TextProcessor, VectorStore, RAGEngine
from soundmem.utils import load_config, ensure_directories, log

class SoundMemApp:
    """SoundMem应用主类"""
    
    def __init__(self):
        """初始化应用"""
        # 确保目录存在
        ensure_directories()
        
        # 加载配置
        self.config = load_config()
        
        # 初始化组件
        self.recorder = AudioRecorder(
            sample_rate=self.config.sample_rate,
            channels=self.config.channels,
            chunk_duration=self.config.chunk_duration
        )
        
        self.asr_engine = ASREngine()
        self.text_processor = TextProcessor()
        self.vector_store = VectorStore(
            db_path=self.config.vector_db_path,
            collection_name=self.config.collection_name
        )
        
        self.rag_engine: Optional[RAGEngine] = None
        
        # 状态变量
        self.is_recording = False
        self.transcription_text = ""
        self.processing_thread: Optional[threading.Thread] = None
        self.stop_processing = False
        
        log.info("SoundMem应用初始化完成")
    
    def initialize_models(self, progress=gr.Progress()):
        """初始化模型"""
        try:
            progress(0, desc="正在加载ASR模型...")
            self.asr_engine.load_model()
            
            progress(0.5, desc="正在加载向量模型...")
            self.vector_store.load_model()
            self.vector_store.initialize()
            
            progress(1.0, desc="模型加载完成！")
            
            return "✅ 模型加载成功！可以开始使用了。"
        except Exception as e:
            log.error(f"模型加载失败: {e}")
            return f"❌ 模型加载失败: {str(e)}"
    
    def start_recording(self):
        """开始录音"""
        if self.is_recording:
            return "⚠️ 录音已在进行中", self.transcription_text
        
        try:
            # 启动录音
            self.recorder.start_recording()
            self.is_recording = True
            self.stop_processing = False
            self.transcription_text = ""
            
            # 启动处理线程
            self.processing_thread = threading.Thread(target=self._process_audio_loop)
            self.processing_thread.start()
            
            log.info("录音开始")
            return "🎙️ 录音中...", ""
            
        except Exception as e:
            log.error(f"启动录音失败: {e}")
            return f"❌ 启动录音失败: {str(e)}", ""
    
    def stop_recording(self):
        """停止录音"""
        if not self.is_recording:
            return "⚠️ 录音未在进行中", self.transcription_text
        
        try:
            # 停止录音
            self.is_recording = False
            self.stop_processing = True
            self.recorder.stop_recording()
            
            # 等待处理线程结束
            if self.processing_thread:
                self.processing_thread.join(timeout=5)
            
            log.info("录音停止")
            return "⏹️ 录音已停止", self.transcription_text
            
        except Exception as e:
            log.error(f"停止录音失败: {e}")
            return f"❌ 停止录音失败: {str(e)}", self.transcription_text
    
    def _process_audio_loop(self):
        """音频处理循环（在独立线程中运行）
        
        双层检测机制：
        1. 简单能量检测：决定何时发送给ASR（粗过滤）
        2. FunASR的VAD：精确分段和标点恢复（精处理）
        """
        audio_buffer = []
        buffer_duration = 0
        silence_duration = 0
        
        # 可调参数
        min_duration = 2.0       # 最小2秒再发送给ASR
        silence_threshold = 1.0  # 静音1秒触发
        energy_threshold = 0.01  # 语音能量阈值（可根据环境调整）
        
        # 如果想完全依赖FunASR的VAD，可以设置：
        # energy_threshold = 0.0  # 禁用能量检测
        # silence_threshold = 0.0  # 禁用静音检测
        # 这样就只按 min_duration 定时发送
        
        while not self.stop_processing:
            # 获取音频块
            audio_chunk = self.recorder.get_audio_chunk(timeout=0.5)
            
            if audio_chunk is None:
                continue
            
            # 添加到缓冲区
            audio_buffer.append(audio_chunk)
            chunk_duration = len(audio_chunk) / self.config.sample_rate
            buffer_duration += chunk_duration
            
            # 简单的能量检测（第一层过滤）
            if energy_threshold > 0:
                energy = np.sqrt(np.mean(audio_chunk ** 2))
                is_speech = energy > energy_threshold
                
                if not is_speech:
                    silence_duration += chunk_duration
                else:
                    silence_duration = 0
            else:
                # 禁用能量检测时，认为一直有语音
                silence_duration = 0
            
            # 决定是否发送给ASR处理
            # 策略：达到最小时长 且 检测到静音（或禁用了静音检测）
            should_process = (buffer_duration >= min_duration and 
                            (silence_threshold == 0 or silence_duration >= silence_threshold))
            
            # 当满足条件时，发送给ASR（FunASR会自动用VAD分段和添加标点）
            if should_process and audio_buffer:
                log.info(f"发送 {buffer_duration:.2f}s 音频给ASR处理（静音: {silence_duration:.2f}s）")
                
                # 合并音频
                audio_data = np.concatenate(audio_buffer, axis=0)
                
                # ASR转写 - FunASR会自动使用VAD分段和标点恢复
                result = self.asr_engine.transcribe(audio_data, self.config.sample_rate)
                
                if result['success'] and result['text']:
                    text = result['text']
                    timestamp = datetime.now().isoformat()
                    
                    # 更新转写文本
                    self.transcription_text += f"[{timestamp}] {text}\n\n"
                    
                    # 如果有分段信息，也可以显示
                    if 'segments' in result and result['segments']:
                        log.info(f"FunASR返回了 {len(result['segments'])} 个分段")
                    
                    # 文本分块
                    chunks = self.text_processor.chunk_text(text, timestamp)
                    
                    # 添加到向量库
                    if chunks:
                        texts = [chunk['text'] for chunk in chunks]
                        metadatas = [{'timestamp': chunk['timestamp']} for chunk in chunks]
                        self.vector_store.add_texts(texts, metadatas)
                        
                        log.info(f"已添加 {len(chunks)} 个文本块到向量库")
                
                # 清空缓冲区
                audio_buffer = []
                buffer_duration = 0
                silence_duration = 0
    
    def chat(self, message, history, api_key, base_url, model_name):
        """聊天功能"""
        if not message:
            return history, ""
        
        # 初始化RAG引擎（如果需要）
        if self.rag_engine is None or api_key:
            try:
                self.rag_engine = RAGEngine(
                    vector_store=self.vector_store,
                    api_key=api_key or self.config.openai_api_key,
                    base_url=base_url or self.config.openai_base_url,
                    model_name=model_name or self.config.model_name
                )
            except Exception as e:
                history.append((message, f"❌ 初始化失败: {str(e)}"))
                return history, ""
        
        # 查询
        result = self.rag_engine.query(
            message,
            top_k=self.config.top_k,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        if result['success']:
            answer = result['answer']
        else:
            answer = result['answer']
        
        history.append((message, answer))
        
        return history, ""
    
    def get_stats(self):
        """获取统计信息"""
        doc_count = self.vector_store.get_count()
        status = "🎙️ 录音中..." if self.is_recording else "⏹️ 未录音"
        
        return f"{status} | 已存储文本片段: {doc_count}"
    
    def clear_database(self):
        """清空数据库"""
        try:
            self.vector_store.clear()
            self.transcription_text = ""
            return "✅ 向量库已清空", ""
        except Exception as e:
            return f"❌ 清空失败: {str(e)}", self.transcription_text

def create_app():
    """创建Gradio应用"""
    app = SoundMemApp()
    
    with gr.Blocks(title="SoundMem - 智能录音记忆助手", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🎙️ SoundMem - 智能录音记忆助手
        
        实时录音转写 + 智能问答，让你的录音内容可以被检索和对话
        """)
        
        # 初始化按钮
        with gr.Row():
            init_btn = gr.Button("🚀 初始化模型（首次使用请点击）", variant="primary", size="lg")
        
        init_status = gr.Textbox(label="初始化状态", interactive=False)
        init_btn.click(app.initialize_models, outputs=init_status)
        
        with gr.Row():
            # 左侧：录音控制
            with gr.Column(scale=1):
                gr.Markdown("### 📝 录音控制")
                
                with gr.Row():
                    start_btn = gr.Button("🎙️ 开始录音", variant="primary")
                    stop_btn = gr.Button("⏹️ 停止录音", variant="stop")
                
                status_text = gr.Textbox(label="录音状态", interactive=False)
                
                transcription = gr.Textbox(
                    label="实时转写文本",
                    lines=15,
                    interactive=False,
                    placeholder="转写的文本将在这里显示..."
                )
                
                with gr.Row():
                    stats_text = gr.Textbox(label="统计信息", interactive=False)
                    refresh_btn = gr.Button("🔄 刷新")
                
                clear_btn = gr.Button("🗑️ 清空向量库", variant="stop")
            
            # 右侧：对话区
            with gr.Column(scale=1):
                gr.Markdown("### 💬 智能问答")
                
                # API配置（可折叠）
                with gr.Accordion("⚙️ API配置", open=False):
                    api_key_input = gr.Textbox(
                        label="API Key",
                        type="password",
                        placeholder="留空则使用.env中的配置"
                    )
                    base_url_input = gr.Textbox(
                        label="Base URL",
                        placeholder="留空则使用.env中的配置"
                    )
                    model_input = gr.Textbox(
                        label="模型名称",
                        placeholder="留空则使用.env中的配置"
                    )
                
                chatbot = gr.Chatbot(
                    label="对话历史",
                    height=400
                )
                
                with gr.Row():
                    msg_input = gr.Textbox(
                        label="输入问题",
                        placeholder="问我关于录音内容的问题...",
                        scale=4
                    )
                    send_btn = gr.Button("发送", variant="primary", scale=1)
        
        # 事件绑定
        start_btn.click(
            app.start_recording,
            outputs=[status_text, transcription]
        )
        
        stop_btn.click(
            app.stop_recording,
            outputs=[status_text, transcription]
        )
        
        refresh_btn.click(
            app.get_stats,
            outputs=stats_text
        )
        
        clear_btn.click(
            app.clear_database,
            outputs=[status_text, transcription]
        )
        
        send_btn.click(
            app.chat,
            inputs=[msg_input, chatbot, api_key_input, base_url_input, model_input],
            outputs=[chatbot, msg_input]
        )
        
        msg_input.submit(
            app.chat,
            inputs=[msg_input, chatbot, api_key_input, base_url_input, model_input],
            outputs=[chatbot, msg_input]
        )
        
        # 定时刷新转写文本和统计信息
        demo.load(app.get_stats, outputs=stats_text, every=2)
    
    return demo

