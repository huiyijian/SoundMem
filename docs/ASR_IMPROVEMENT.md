# ASR识别效果改进方案

## 📊 问题分析

### 原有问题

从用户反馈的识别结果来看，存在以下问题：

```
[2026-02-07T19:13:03] 那我再让我们看一篇政治学院，我知道有些凯众朋友们来说的这不是命红灵的
[2026-02-07T19:13:05] 般情况下，你很难看到经济学上聊经济，经济，大洲已经有大量。
[2026-02-07T19:13:10] 的非法移民当地的民众呢也认为财富不均等以及医保的问题已经导致他们。
```

**核心问题**：
1. ❌ 句子被频繁切断，语义不连贯
2. ❌ 每2-5秒产生一个新分段，上下文丢失
3. ❌ 识别准确率不高（如"凯众"应为"某些"）

### 根本原因

#### 1. 批处理模式的局限性

**原有流程**：
```
音频采集 → 累积5秒 → 清空缓冲区 → ASR识别 → 保存
         ↑_______________|（上下文丢失）
```

- 每5秒清空缓冲区，导致FunASR无法利用前后文信息
- 短音频片段让VAD难以准确判断语音边界
- 每次识别都是独立的，没有连续性

#### 2. 未使用流式识别能力

代码中已经实现了 `transcribe_realtime()` 方法，但实际使用的是 `transcribe()` 批处理方法。

## ✅ 改进方案

### 方案1：启用流式识别模式（已实施）⭐

#### 核心改进

**新流程**：
```
音频采集 → 累积2秒 → 流式识别（保持上下文）→ 累积文本
                    ↑_____cache______|
                                     ↓
                            每30秒或句子结束时保存
```

#### 关键变化

1. **使用流式识别API**
   ```python
   # 旧代码：批处理模式
   result = self.asr_engine.transcribe(audio_data, sample_rate)
   
   # 新代码：流式模式
   result = self.asr_engine.transcribe_realtime(
       audio_data, 
       sample_rate,
       cache=asr_cache  # 保持上下文
   )
   ```

2. **保持ASR上下文**
   - 使用 `asr_cache` 在多次识别间传递上下文
   - FunASR可以利用前面的识别结果优化当前识别

3. **文本累积策略**
   - 每2秒识别一次（更实时）
   - 文本持续累积，不立即切断
   - 检测到句子结束（。！？）或30秒后才保存到向量库

4. **智能保存时机**
   ```python
   should_save = (
       (current_time - last_save_time >= 30) or  # 30秒超时
       (text.rstrip()[-1] in '。！？.!?')        # 句子结束
   )
   ```

#### 预期效果

**改进前**：
```
[19:13:03] 那我再让我们看一篇政治学院
[19:13:05] 我知道有些凯众朋友们来说的
```

**改进后**：
```
[19:13:00] 那我再让我们看一篇政治学院，我知道有些观众朋友们来说的这不是命红灵的写着经济学院吗？一般情况下，你很难看到经济学上聊经济。
```

### 方案2：音频质量优化（可选）

如果识别效果仍不理想，可以考虑：

#### 2.1 增加音频预处理

在 `audio_recorder.py` 中添加：

```python
def preprocess_audio(audio_data):
    """音频预处理"""
    # 1. 音量归一化
    audio_data = audio_data / np.max(np.abs(audio_data))
    
    # 2. 降噪（可选，需要安装noisereduce）
    # import noisereduce as nr
    # audio_data = nr.reduce_noise(y=audio_data, sr=sample_rate)
    
    return audio_data
```

#### 2.2 调整采样参数

在 `.env` 或配置中：

```env
# 提高音频质量（但会增加计算量）
SAMPLE_RATE=16000  # 保持16kHz（FunASR推荐）
CHANNELS=1         # 单声道

# 调整识别间隔
CHUNK_INTERVAL=2.0      # 识别间隔（秒）
MAX_BUFFER_DURATION=30.0  # 最大缓冲时长（秒）
```

### 方案3：模型优化（高级）

#### 3.1 使用更大的ASR模型

```python
# 在 asr_engine.py 中
self.model = AutoModel(
    model="paraformer-zh-streaming",  # 流式专用模型
    # 或使用更大的模型
    # model="paraformer-large-zh",
    vad_model="fsmn-vad",
    punc_model="ct-punc",
    device="cpu"
)
```

#### 3.2 添加热词支持

对于特定领域的词汇（如"政治学院"、"经济学"），可以添加热词：

```python
result = self.model.generate(
    input=audio_data,
    cache=cache,
    hotword="政治学院 经济学 民众 移民"  # 提高这些词的识别准确率
)
```

## 🔧 配置参数说明

### 当前参数（已优化）

| 参数 | 值 | 说明 |
|------|-----|------|
| `chunk_interval` | 2.0秒 | 识别间隔，更频繁=更实时 |
| `max_buffer_duration` | 30.0秒 | 最大缓冲时长，避免内存溢出 |
| `sample_rate` | 16000Hz | FunASR推荐采样率 |
| `blocksize` | 100ms | 音频采集块大小 |

### 可调整参数

如果需要进一步优化，可以调整：

```python
# 在 gradio_app.py 的 _process_audio_loop 方法中

# 更实时但可能更碎片化
chunk_interval = 1.0  # 每1秒识别

# 更完整但延迟更高
chunk_interval = 3.0  # 每3秒识别

# 更频繁保存
max_buffer_duration = 15.0  # 15秒保存一次

# 更长的上下文
max_buffer_duration = 60.0  # 60秒保存一次
```

## 📈 性能对比

### 改进前（批处理模式）

- ✅ 实现简单
- ❌ 上下文丢失
- ❌ 句子被切断
- ❌ 识别准确率低
- ⚡ 延迟：5秒

### 改进后（流式模式）

- ✅ 保持上下文连续性
- ✅ 句子完整性好
- ✅ 识别准确率提升
- ✅ 更实时的反馈
- ⚡ 延迟：2秒

## 🚀 使用建议

### 1. 麦克风设置

确保麦克风设置正确（参考 README.md）：
- 录制外部声音：使用麦克风
- 录制电脑声音：启用立体声混音

### 2. 环境要求

- 安静的环境（减少背景噪音）
- 清晰的发音
- 适中的音量（不要太小或太大）

### 3. 测试建议

1. 先用简单的句子测试
2. 观察实时转写文本的连贯性
3. 检查向量库中保存的文本质量
4. 根据效果调整参数

### 4. 故障排查

如果识别效果仍不理想：

1. **检查日志**：查看 `logs/` 目录下的日志文件
2. **音频质量**：确认麦克风音量适中
3. **模型加载**：确认VAD和标点模型都已加载
4. **参数调整**：尝试调整 `chunk_interval` 参数

## 📝 后续优化方向

1. **添加音频预处理**：降噪、音量归一化
2. **支持热词配置**：提高特定领域词汇的识别率
3. **多模型对比**：测试不同ASR模型的效果
4. **实时显示优化**：显示识别置信度、分段信息
5. **导出功能**：支持导出完整的转写文本

## 🔗 相关资源

- [FunASR官方文档](https://github.com/alibaba-damo-academy/FunASR)
- [流式识别最佳实践](https://github.com/alibaba-damo-academy/FunASR/blob/main/docs/streaming_asr.md)
- [VAD参数调优](https://github.com/alibaba-damo-academy/FunASR/blob/main/docs/vad.md)

---

**更新时间**: 2026-02-07  
**版本**: v1.1 - 流式识别模式

