"""
RAG检索引擎模块
"""

from typing import List, Dict, Any
from openai import OpenAI
from soundmem.core.vector_store import VectorStore
from soundmem.utils.logger import log

class RAGEngine:
    """RAG检索引擎"""
    
    def __init__(self, vector_store: VectorStore, api_key: str, base_url: str, model_name: str):
        """
        初始化RAG引擎
        
        Args:
            vector_store: 向量数据库
            api_key: API密钥
            base_url: API基础URL
            model_name: 模型名称
        """
        self.vector_store = vector_store
        self.model_name = model_name
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # 系统提示词
        self.system_prompt = """你是一个智能录音助手，专门帮助用户回答关于录音内容的问题。

你的任务是：
1. 基于提供的录音转写文本片段回答用户的问题
2. 如果录音内容中有相关信息，请准确引用并回答
3. 如果录音内容中没有相关信息，请明确告知用户
4. 回答时可以引用时间戳，帮助用户定位信息来源
5. 保持回答简洁、准确、有帮助

注意：
- 只基于提供的录音内容回答，不要编造信息
- 如果不确定，请说"根据录音内容，我无法确定..."
"""
        
        log.info(f"RAG引擎初始化完成: model={model_name}")
    
    def build_context(self, query: str, top_k: int = 5) -> tuple[str, List[Dict[str, Any]]]:
        """
        构建上下文
        
        Args:
            query: 用户查询
            top_k: 检索数量
            
        Returns:
            (上下文文本, 检索结果列表)
        """
        # 从向量库检索相关文本
        results = self.vector_store.search(query, top_k=top_k)
        
        if not results:
            return "暂无相关录音内容。", []
        
        # 构建上下文
        context_parts = []
        for i, result in enumerate(results, 1):
            text = result['text']
            metadata = result['metadata']
            timestamp = metadata.get('timestamp', '未知时间')
            
            context_parts.append(f"[片段{i}] (时间: {timestamp})\n{text}")
        
        context = "\n\n".join(context_parts)
        
        return context, results
    
    def query(self, question: str, top_k: int = 5, temperature: float = 0.7, max_tokens: int = 2000) -> Dict[str, Any]:
        """
        查询问答
        
        Args:
            question: 用户问题
            top_k: 检索数量
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            回答结果字典
        """
        try:
            # 构建上下文
            context, retrieved_docs = self.build_context(question, top_k)
            
            # 构建用户消息
            user_message = f"""录音内容：
{context}

用户问题：{question}

请基于上述录音内容回答用户的问题。"""
            
            # 调用LLM
            # 构建API调用参数
            api_params = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # 通义千问API需要禁用enable_thinking（非流式调用）
            if "qwen" in self.model_name.lower() or "dashscope" in str(self.client.base_url).lower():
                api_params["extra_body"] = {"enable_thinking": False}
            
            response = self.client.chat.completions.create(**api_params)
            
            answer = response.choices[0].message.content
            
            log.info(f"RAG查询完成: question='{question[:50]}...', retrieved={len(retrieved_docs)}")
            
            return {
                "answer": answer,
                "context": context,
                "retrieved_docs": retrieved_docs,
                "success": True
            }
            
        except Exception as e:
            log.error(f"RAG查询失败: {e}")
            return {
                "answer": f"抱歉，查询过程中出现错误: {str(e)}",
                "context": "",
                "retrieved_docs": [],
                "success": False,
                "error": str(e)
            }
    
    def stream_query(self, question: str, top_k: int = 5, temperature: float = 0.7, max_tokens: int = 2000):
        """
        流式查询问答
        
        Args:
            question: 用户问题
            top_k: 检索数量
            temperature: 温度参数
            max_tokens: 最大token数
            
        Yields:
            回答文本片段
        """
        try:
            # 构建上下文
            context, retrieved_docs = self.build_context(question, top_k)
            
            # 构建用户消息
            user_message = f"""录音内容：
{context}

用户问题：{question}

请基于上述录音内容回答用户的问题。"""
            
            # 调用LLM流式接口
            # 构建API调用参数
            api_params = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True
            }
            
            # 通义千问API的流式调用可以启用enable_thinking
            if "qwen" in self.model_name.lower() or "dashscope" in str(self.client.base_url).lower():
                api_params["extra_body"] = {"enable_thinking": True}
            
            stream = self.client.chat.completions.create(**api_params)
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            
        except Exception as e:
            log.error(f"流式RAG查询失败: {e}")
            yield f"抱歉，查询过程中出现错误: {str(e)}"

