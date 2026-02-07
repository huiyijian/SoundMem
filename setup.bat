@echo off
echo ========================================
echo SoundMem 环境安装脚本
echo ========================================
echo.

echo [1/4] 创建conda环境...
call conda create -n soundmem python=3.10 -y

echo.
echo [2/4] 激活环境...
call conda activate soundmem

echo.
echo [3/4] 安装依赖包...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [4/4] 创建配置文件...
if not exist .env (
    copy env.example .env
    echo 已创建 .env 配置文件，请编辑填入你的API信息
) else (
    echo .env 文件已存在，跳过创建
)

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 下一步：
echo 1. 编辑 .env 文件，填入你的API Key
echo 2. 激活环境: conda activate soundmem
echo 3. 运行程序: python main.py
echo.
pause


