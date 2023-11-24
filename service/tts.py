from openai import OpenAI
from dotenv import load_dotenv
import os, tempfile
import simpleaudio as sa
from pydub import AudioSegment
from io import BytesIO
import requests
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE")
client = OpenAI(
    api_key=api_key,
    base_url=api_base
)


def chatllm(question,answer,user_answer,model="gpt-4-turbo"):
    response_out = client.chat.completions.create(
      model=model,
      messages=[
        {"role": "system", "content": "你是一个人情练达，能说会到的秘书，你将根据问题以及正确答案，来判断我的回答和给定的答案是否相同，以及有哪些内容需要补充。回答的语气要幽默风趣，调皮可爱用中文回复。"},
        {"role": "user", "content": f"""问题：{question}
        标准答案:{answer}
        用户答案:{user_answer}
        """},
      ]
    )
    return response_out.choices[0].message.content

def originchat(question, model = "gpt-4-1106-preview"):
    response_out = client.chat.completions.create(
      model=model,
      messages=[
        {"role": "system", "content": "你是一个人情练达，能说会到的秘书，现在要根据我的问题进行回答。回答的语气要幽默风趣，调皮可爱用中文回复。"},
        {"role": "user", "content": f"""请回答问题：{question}"""},
      ],
      stream=True
    )


    return response_out


ji=originchat("喜欢的人不给自己回应怎么办")
print(ji)
def tts(ttscontent):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=ttscontent,
    )

    # 将响应流转换为音频对象
    audio_stream = BytesIO(response.content)
    audio = AudioSegment.from_file(audio_stream, format="mp3")

    # 播放音频
    play_obj = sa.play_buffer(
        audio.raw_data,
        num_channels=audio.channels,
        bytes_per_sample=audio.sample_width,
        sample_rate=audio.frame_rate
    )

    # 等待播放结束
    play_obj.wait_done()
def voice_to_text(filepath):
    audio_file = open(filepath, "rb")
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="text"
    )
    return transcript

def select_voice():
    voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]  # 可用的声音列表
    print("Please select a voice for the TTS response:")
    for i, voice in enumerate(voices):
        print(f"{i+1}. {voice}")

    choice = 0
    while choice not in range(1, len(voices)+1):
        try:
            choice = int(input("Enter your choice (1-6): "))
        except ValueError:
            pass

    return voices[choice - 1]
