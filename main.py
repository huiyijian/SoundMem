"""
SoundMem - 智能录音记忆助手
主程序入口
"""

from soundmem.ui.gradio_app import create_app
from soundmem.utils.logger import setup_logger
from soundmem.utils.config import load_config

def main():
    """主函数"""
    # 设置日志
    logger = setup_logger()
    logger.info("启动 SoundMem 应用...")
    
    # 加载配置
    config = load_config()
    logger.info(f"配置加载完成: {config}")
    
    # 创建并启动Gradio应用
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True
    )

if __name__ == "__main__":
    main()

