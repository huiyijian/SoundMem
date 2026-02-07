import os
import sys
import time

# 将当前工作目录加入 PATH，以便找到 ffmpeg.exe
cwd = os.getcwd()
#print(f"Adding current directory to PATH: {cwd}")
os.environ["PATH"] += os.pathsep + cwd

from funasr import AutoModel

# 音频文件路径
audio_file = r"d:\ipads\asr\罗布泊介绍.m4a"

if not os.path.exists(audio_file):
    print(f"Error: File not found at {audio_file}")
    exit(1)

print("Loading models...")
start_load_time = time.time()
# 加载 Paraformer-zh 模型，以及配套的 VAD 和标点模型
# 注意：第一次运行会自动从 ModelScope 下载模型
model = AutoModel(
    model="paraformer-zh",
    vad_model="fsmn-vad",
    punc_model="ct-punc",
    # 可以指定 device="cuda" 如果有显卡
)
end_load_time = time.time()
load_duration = end_load_time - start_load_time
print(f"Model loaded in {load_duration:.2f} seconds")

print(f"Transcribing {audio_file}...")
try:
    start_transcribe_time = time.time()
    res = model.generate(input=audio_file, batch_size_s=300)
    end_transcribe_time = time.time()
    transcribe_duration = end_transcribe_time - start_transcribe_time
    print(f"Transcription finished in {transcribe_duration:.2f} seconds")
    
    #print("\nTranscription Result:")
    #print(res)
    
    # 将结果保存到文件
    output_file = "result.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        # res 通常是一个列表，包含结果字典
        if isinstance(res, list):
            for item in res:
                text = item.get('text', '')
                print(f"Text: {text}")
                f.write(text + "\n")
        else:
            print(res)
            f.write(str(res))
            
    print(f"\nResult saved to {output_file}")
    print(f"Total time: {load_duration + transcribe_duration:.2f} seconds (Load: {load_duration:.2f}s, Transcribe: {transcribe_duration:.2f}s)")


except Exception as e:
    print(f"An error occurred: {e}")
    import traceback
    traceback.print_exc()
