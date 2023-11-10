import argparse
import io
import os
import speech_recognition as sr

from service.tts import voice_to_text as whisper
from datetime import datetime, timedelta
from queue import Queue
from tempfile import NamedTemporaryFile
from time import sleep
from sys import platform
import platform

def voice():
    # 命令行参数解析器的初始化
    parser = argparse.ArgumentParser()
    # 添加一个可选参数 --model，用于选择使用的模型大小，默认为 "medium"
    parser.add_argument("--model", default="medium", help="Model to use",
                        choices=["tiny", "base", "small", "medium", "large"])
    # 添加一个布尔参数 --non_english，当指定时表示不使用英语模型
    parser.add_argument("--non_english", action='store_true',
                        help="Don't use the english model.")
    # 添加一个整数参数 --energy_threshold，用于设置麦克风检测声音的能量阈值，默认为1000
    parser.add_argument("--energy_threshold", default=1000,
                        help="Energy level for mic to detect.", type=int)
    # 添加一个浮点参数 --record_timeout，指定录音的实时性（秒），默认为2秒
    parser.add_argument("--record_timeout", default=2,
                        help="How real time the recording is in seconds.", type=float)
    # 添加一个浮点参数 --phrase_timeout，指定录音间空白长度，以决定何时视为新的转录行，默认为3秒
    parser.add_argument("--phrase_timeout", default=3,
                        help="How much empty space between recordings before we "
                             "consider it a new line in the transcription.", type=float)
    # 如果是Linux系统，添加一个字符串参数 --default_microphone，用于选择默认麦克风设备
    if 'linux' in platform.system().lower():
        parser.add_argument("--default_microphone", default='pulse',
                            help="Default microphone name for SpeechRecognition. "
                                 "Run this with 'list' to view available Microphones.", type=str)
    # 解析命令行参数
    args = parser.parse_args()

    # 以下变量用于语音转录逻辑
    phrase_time = None  # 上次从队列中检索录音的时间
    last_sample = bytes()  # 当前原始音频字节
    data_queue = Queue()  # 线程安全队列，用于从线程化的录音回调中传递数据

    # 使用SpeechRecognition的Recognizer类来录制音频
    recorder = sr.Recognizer()
    recorder.energy_threshold = args.energy_threshold  # 设置能量阈值
    recorder.dynamic_energy_threshold = False  # 禁用动态能量阈值调整

    # 针对Linux用户的特殊处理，以避免使用错误的麦克风设备导致应用挂起或崩溃
    if 'linux' in platform.system().lower():
        mic_name = args.default_microphone
        if mic_name == 'list':
            # 如果指定为 'list'，则打印可用的麦克风设备并退出程序
            print("Available microphone devices are: ")
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                print(f"Microphone with name \"{name}\" found")
            return
        else:
            # 根据指定的麦克风名称查找并设置相应的设备
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                if mic_name in name:
                    source = sr.Microphone(sample_rate=16000, device_index=index)
                    break
    else:
        # 对于非Linux系统，默认使用16000采样率的麦克风
        source = sr.Microphone(sample_rate=16000)

    # 设置录音超时和短语超时参数
    record_timeout = args.record_timeout
    phrase_timeout = args.phrase_timeout

    temp_file = NamedTemporaryFile(suffix='.wav',dir='./temp').name  # 创建一个临时文件
    print(temp_file)
    transcription = ['']  # 初始化转录文本列表

    # 调整麦克风以适应环境噪音
    with source:
        recorder.adjust_for_ambient_noise(source)

    # 录音回调函数，用于接收录音完成时的音频数据
    def record_callback(_, audio: sr.AudioData) -> None:
        data = audio.get_raw_data()  # 获取原始音频数据
        data_queue.put(data)  # 将数据放入线程安全队列

    # 创建一个后台线程，该线程将传递原始音频字节
    recorder.listen_in_background(source, record_callback, phrase_time_limit=record_timeout)

    # 主循环，不断检查队列并进行转录
    while True:
        try:
            now = datetime.utcnow()
            # 如果队列中有数据，处理这些数据
            if not data_queue.empty():
                phrase_complete = False
                # 如果自上次录音以来已经过了足够长的时间默认5s，则认为短语结束
                if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout):
                    print("问题回答完成.\n")
                    return transcription[0]
                    last_sample = bytes()  # 重置音频缓冲区
                    phrase_complete = True
                phrase_time = now  # 更新接收新音频数据的时间

                # 连接当前音频数据与队列中的最新音频数据
                while not data_queue.empty():
                    data = data_queue.get()
                    last_sample += data

                # 将原始数据转换为wav格式的音频数据
                audio_data = sr.AudioData(last_sample, source.SAMPLE_RATE, source.SAMPLE_WIDTH)
                wav_data = io.BytesIO(audio_data.get_wav_data())

                # 将wav数据写入临时文件
                with open(temp_file, 'wb') as f:  # 请注意 'wb' 而不是 'w+b'
                    f.write(wav_data.getvalue())  # 使用 getvalue() 而不是 read()，因为 getvalue() 会返回整个缓冲区的内容

                # 使用Whisper模型进行转录
                text= whisper(temp_file)
                #text = result['text'].strip()  # 获取转录文本

                # 如果检测到录音之间的暂停，将新文本添加到转录列表中
                if phrase_complete:
                    transcription.append(text)
                else:
                    transcription[-1] = text  # 更新最后一项转录文本

                # 清除控制台并重新打印更新的转录
                os.system('cls' if os.name=='nt' else 'clear')
                for line in transcription:
                    print(line)
                # 刷新标准输出
                print('', end='', flush=True)

                # 在无限循环中适当休眠，以减少对处理器的负担
                sleep(0.25)
                data_complete=datetime.utcnow()
            try:
                if datetime.utcnow() - data_complete > timedelta(seconds=phrase_timeout):
                    break
            except NameError:
                pass

        except KeyboardInterrupt:
            # 如果用户中断程序，则退出循环
            break

    # 打印最终的转录结果
    print("\n\nTranscription:")
    for line in transcription:
        print(line)

# # 当脚本作为主程序运行时，调用 main 函数
# if __name__ == "__main__":
#     voice()