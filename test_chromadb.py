"""
测试ChromaDB初始化
"""
import chromadb
import traceback

print(f"ChromaDB version: {chromadb.__version__}")

# 测试1: 基本初始化
print("\nTest 1: Basic initialization")
try:
    client = chromadb.PersistentClient(path="./test_db")
    print("SUCCESS: Basic initialization")
    
    # 创建集合
    collection = client.get_or_create_collection(name="test_collection")
    print(f"SUCCESS: Collection created, count: {collection.count()}")
    
    # 清理
    client.delete_collection(name="test_collection")
    print("SUCCESS: Cleanup done")
    
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()

# 测试2: 检查Client类的签名
print("\nTest 2: Check PersistentClient parameters")
import inspect
sig = inspect.signature(chromadb.PersistentClient.__init__)
print(f"PersistentClient.__init__ signature: {sig}")

print("\nTest completed!")
