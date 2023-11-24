# 导入必要的库
import os
import pyaudio  # 用于音频输入和输出
import wave  # 用于处理WAV音频文件
from openai import OpenAI  # OpenAI的API客户端
import pygame  # 用于播放音频文件
import speech_recognition as sr  # 用于语音识别
from dotenv import load_dotenv  # 用于加载环境变量
from service.knowledge_serveice import *
from service.tts import *
from service.fast_tts import *

# 加载环境变量，通常用于存储敏感信息如API密钥
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE")

notion_database_id = os.getenv("notion_database_id")
notion_api_token = os.getenv("notion_api_token")

client = OpenAI(
    api_key=api_key,
    base_url=api_base
)


# 定义主函数main
def main():
    recognizer = sr.Recognizer()  # 初始化语音识别器
    #recognizer.pause_threshold = 3
    recognizer.dynamic_energy_threshold=False
    data = get_review_data(notion_database_id, notion_api_token)

    for real_data in data:
        question=today[real_data][0]
        print(question)
        tts(question)
        answer=today[real_data][1]

    # 使用麦克风作为输入源
        with sr.Microphone() as source:
            print('Adjusting for ambient noise. Please wait.')
            recognizer.adjust_for_ambient_noise(source)  # 调整麦克风设置以适应环境噪音

            print('Please start speaking.')
            audio = recognizer.listen(source)  # 监听并记录用户的语音

        print('Finished recording')

        # 将语音记录保存为WAV文件
        wav_file_path = 'speech_files/userSpeech.wav'
        with open(wav_file_path, "wb") as file:
            file.write(audio.get_wav_data())

        print('Finished recording and saved to', wav_file_path)

        # 使用OpenAI处理语音转换为文本
        with open(wav_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                prompt='关于'+question+'的问题'+'答案是:'+answer,
                model="whisper-1",
                file=audio_file
            )
        print("User: " + transcript.text)

        os.remove(wav_file_path)  # 删除临时WAV文件
        chatmultthread_voice(question, answer, transcript.text)


if __name__ == '__main__':
    main()
