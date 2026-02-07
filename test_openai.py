"""
测试OpenAI客户端初始化
"""
from openai import OpenAI
import traceback
import inspect

print("Test OpenAI client initialization")

# 测试1: 检查OpenAI.__init__的签名
print("\nTest 1: Check OpenAI.__init__ signature")
sig = inspect.signature(OpenAI.__init__)
print(f"OpenAI.__init__ signature: {sig}")

# 测试2: 基本初始化
print("\nTest 2: Basic initialization")
try:
    client = OpenAI(
        api_key="test_key",
        base_url="https://api.openai.com/v1"
    )
    print("SUCCESS: OpenAI client initialized")
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()

print("\nTest completed!")

