import streamlit as st
import requests
from tempfile import NamedTemporaryFile

st.set_page_config(page_title='Audio Streaming Test', layout='wide')

st.title("SIfuture Audio Streaming ")
#st.write("硅基未来yu")

input_text = st.text_input("Enter text for audio generation:", "银鞍照白马 飒沓如流星你知道是什么意思吗")
submit_button = st.button("Submit")

if submit_button and input_text:
    # 向 FastAPI 发送请求
    response = requests.get(
        f'http://127.0.0.1:8000/streamed_audio/',
        params={"input_text": input_text},
        stream=True
    )

    if response.status_code == 200:
        # 创建临时文件保存音频
        with NamedTemporaryFile(delete=False, suffix='.opus') as tmp:
            tmp.write(response.content)
            tmp.flush()  # 确保所有数据都写入磁盘
            # 使用 Streamlit 的 audio 组件播放音频文件
            st.audio(tmp.name)
    else:
        st.error(f"Failed to get audio (status code: {response.status_code})")
