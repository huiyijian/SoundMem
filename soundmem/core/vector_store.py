"""
向量数据库模块
使用ChromaDB存储和检索文本向量
"""

from typing import List, Dict, Any, Optional
import chromadb
from sentence_transformers import SentenceTransformer
from soundmem.utils.logger import log

class VectorStore:
    """向量数据库"""
    
    def __init__(self, db_path: str = "./data/vectordb", collection_name: str = "soundmem_recordings"):
        """
        初始化向量数据库
        
        Args:
            db_path: 数据库路径
            collection_name: 集合名称
        """
        self.db_path = db_path
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.embedding_model = None
        
        log.info(f"向量数据库初始化: path={db_path}, collection={collection_name}")
    
    def load_model(self, model_name: str = "BAAI/bge-small-zh-v1.5"):
        """
        加载向量模型
        
        Args:
            model_name: 模型名称
        """
        try:
            log.info(f"正在加载向量模型: {model_name}")
            self.embedding_model = SentenceTransformer(model_name)
            log.info("向量模型加载完成")
        except Exception as e:
            log.error(f"加载向量模型失败: {e}")
            raise
    
    def initialize(self):
        """初始化数据库连接"""
        try:
            # 创建ChromaDB客户端
            self.client = chromadb.PersistentClient(
                path=self.db_path
            )
            
            # 获取或创建集合
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "SoundMem录音文本向量库"}
            )
            
            log.info(f"向量数据库初始化完成，当前文档数: {self.collection.count()}")
            
        except Exception as e:
            log.error(f"初始化向量数据库失败: {e}")
            raise
    
    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """
        添加文本到向量库
        
        Args:
            texts: 文本列表
            metadatas: 元数据列表
            
        Returns:
            文档ID列表
        """
        if not texts:
            return []
        
        if self.collection is None:
            raise RuntimeError("数据库未初始化，请先调用initialize()")
        
        if self.embedding_model is None:
            raise RuntimeError("向量模型未加载，请先调用load_model()")
        
        try:
            # 生成向量
            embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
            
            # 生成ID
            import uuid
            ids = [str(uuid.uuid4()) for _ in texts]
            
            # 添加到数据库
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=texts,
                metadatas=metadatas or [{} for _ in texts],
                ids=ids
            )
            
            log.info(f"成功添加 {len(texts)} 条文本到向量库")
            
            return ids
            
        except Exception as e:
            log.error(f"添加文本到向量库失败: {e}")
            raise
    
    def search(self, query: str, top_k: int = 5, filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        搜索相似文本
        
        Args:
            query: 查询文本
            top_k: 返回前K个结果
            filter_dict: 过滤条件
            
        Returns:
            搜索结果列表
        """
        if self.collection is None:
            raise RuntimeError("数据库未初始化，请先调用initialize()")
        
        if self.embedding_model is None:
            raise RuntimeError("向量模型未加载，请先调用load_model()")
        
        try:
            # 生成查询向量
            query_embedding = self.embedding_model.encode([query], show_progress_bar=False)[0]
            
            # 搜索
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                where=filter_dict
            )
            
            # 格式化结果
            formatted_results = []
            if results['documents'] and len(results['documents']) > 0:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0,
                        'id': results['ids'][0][i]
                    })
            
            log.info(f"搜索完成，返回 {len(formatted_results)} 条结果")
            
            return formatted_results
            
        except Exception as e:
            log.error(f"搜索失败: {e}")
            return []
    
    def delete_collection(self):
        """删除集合"""
        if self.client and self.collection_name:
            try:
                self.client.delete_collection(name=self.collection_name)
                log.info(f"集合 {self.collection_name} 已删除")
            except Exception as e:
                log.error(f"删除集合失败: {e}")
    
    def get_count(self) -> int:
        """获取文档数量"""
        if self.collection:
            return self.collection.count()
        return 0
    
    def clear(self):
        """清空集合"""
        if self.collection:
            try:
                # 删除并重新创建集合
                self.delete_collection()
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"description": "SoundMem录音文本向量库"}
                )
                log.info("向量库已清空")
            except Exception as e:
                log.error(f"清空向量库失败: {e}")

