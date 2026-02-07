# SoundMem - 智能录音记忆助手

<div align="center">

**实时录音 · 语音转文字 · 智能问答**

一个基于本地ASR和RAG技术的录音记忆系统，让你的录音内容可以被智能检索和问答。

</div>

## ✨ 特性

- 🎙️ **实时录音转写**: 使用FunASR进行高质量的中英文语音识别
- 🧠 **智能记忆**: 基于向量数据库的语义检索，快速定位录音内容
- 💬 **自然对话**: 支持OpenAI格式API，与录音内容进行智能问答
- 🚀 **本地部署**: 无需GPU，CPU即可流畅运行
- 🔒 **隐私保护**: 所有数据本地存储，保护隐私安全
- ⚡ **实时响应**: 边录音边问答，支持实时查询

## 🏗️ 技术架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  录音采集    │ --> │  ASR转写    │ --> │  文本分段    │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ↓
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  LLM回答    │ <-- │  RAG检索    │ <-- │  向量化存储  │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 核心技术栈

- **ASR引擎**: FunASR (paraformer-zh + VAD + 标点恢复)
- **向量数据库**: ChromaDB
- **向量模型**: bge-small-zh-v1.5
- **前端框架**: Gradio
- **LLM接口**: OpenAI API (兼容多家厂商)

## 📦 安装

### 1. 创建Conda环境

```bash
conda create -n soundmem python=3.10
conda activate soundmem
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置API

复制配置模板并填入你的API信息：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-3.5-turbo
```

## 🚀 快速开始

### ⚠️ 重要：麦克风设置

**在使用前，请务必正确设置麦克风！**

#### 录制外部声音（麦克风）
- 确保麦克风已连接并设置为系统默认录音设备
- Windows: 设置 → 系统 → 声音 → 输入 → 选择麦克风设备

#### 录制电脑内部声音（系统音频）
Windows系统需要启用"立体声混音"：

1. 右键点击任务栏音量图标 → 声音设置
2. 点击"更多声音设置"
3. 切换到"录制"选项卡
4. 右键空白处 → 勾选"显示已禁用的设备"
5. 找到"立体声混音"或"Stereo Mix"
6. 右键 → 启用
7. 右键 → 设置为默认设备

**注意**：如果找不到立体声混音选项，可能需要更新声卡驱动程序。

### 启动应用

```bash
python main.py
```

应用将在浏览器中自动打开，默认地址: `http://localhost:7860`

### 使用流程

1. **配置API**: 在顶部配置区填入你的API信息
2. **初始化模型**: 首次使用点击"初始化模型"按钮
3. **检查麦克风**: 确认已按上述说明设置好麦克风
4. **开始录音**: 点击"开始录音"按钮，系统开始实时转写
5. **查看转写**: 左侧实时显示转写文本
6. **智能问答**: 在右侧对话框提问，系统基于录音内容回答
7. **停止录音**: 点击"停止录音"结束本次会话

## 📁 项目结构

```
soundmem/
├── soundmem/              # 核心代码
│   ├── core/             # 核心模块
│   │   ├── audio_recorder.py    # 录音模块
│   │   ├── asr_engine.py        # ASR引擎
│   │   ├── text_processor.py    # 文本处理
│   │   ├── vector_store.py      # 向量数据库
│   │   └── rag_engine.py        # RAG检索
│   ├── models/           # 模型管理
│   │   └── model_loader.py      # 模型加载器
│   ├── utils/            # 工具函数
│   │   ├── config.py            # 配置管理
│   │   └── logger.py            # 日志工具
│   └── ui/               # 用户界面
│       └── gradio_app.py        # Gradio界面
├── data/                 # 数据目录
│   ├── audio/           # 录音文件
│   └── vectordb/        # 向量数据库
├── logs/                # 日志文件
├── main.py              # 主程序入口
├── requirements.txt     # 依赖列表
├── .env.example         # 配置模板
└── README.md           # 项目说明
```

## ⚙️ 配置说明

### API配置

支持所有OpenAI格式的API，包括：

- OpenAI
- DeepSeek
- Kimi (月之暗面)
- 通义千问
- 智谱AI
- 其他兼容OpenAI格式的API

### 模型配置

首次运行会自动下载以下模型：

- ASR模型: paraformer-zh (~200MB)
- VAD模型: fsmn-vad (~50MB)
- 标点模型: ct-punc (~50MB)
- 向量模型: bge-small-zh-v1.5 (~100MB)

模型会缓存在本地，后续启动无需重复下载。

## 🔧 高级功能

### 多会话管理

支持创建多个独立的录音会话，每个会话有独立的向量库。

### 时间定位

回答中会标注信息来源的时间点，方便回溯原始录音。

### 导出功能

支持导出转写文本和对话记录。

## 📊 性能指标

- **CPU占用**: < 50%
- **内存占用**: < 2GB
- **转写延迟**: < 1秒
- **检索速度**: < 100ms
- **支持平台**: Windows / macOS / Linux

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [FunASR](https://github.com/alibaba-damo-academy/FunASR) - 优秀的ASR工具
- [ChromaDB](https://www.trychroma.com/) - 轻量级向量数据库
- [Gradio](https://gradio.app/) - 快速构建Web界面

---

<div align="center">
Made with ❤️ by SoundMem Team
</div>


