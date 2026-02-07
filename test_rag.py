"""
测试完整的RAG引擎初始化
"""
import sys
sys.path.insert(0, 'd:/ipads/0207')

from soundmem.core.vector_store import VectorStore
from soundmem.core.rag_engine import RAGEngine
import traceback

print("Test RAG Engine initialization")

# 测试1: 初始化向量库
print("\nTest 1: Initialize VectorStore")
try:
    vector_store = VectorStore(
        db_path="./test_vectordb",
        collection_name="test_collection"
    )
    print("SUCCESS: VectorStore created")
    
    # 不加载模型，只测试初始化
    vector_store.initialize()
    print("SUCCESS: VectorStore initialized")
    
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# 测试2: 初始化RAG引擎
print("\nTest 2: Initialize RAGEngine")
try:
    rag_engine = RAGEngine(
        vector_store=vector_store,
        api_key="test_key",
        base_url="https://api.openai.com/v1",
        model_name="gpt-3.5-turbo"
    )
    print("SUCCESS: RAGEngine initialized")
    
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()

print("\nTest completed!")

