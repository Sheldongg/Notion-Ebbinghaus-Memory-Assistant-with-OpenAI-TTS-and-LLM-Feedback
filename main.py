from fastapi import FastAPI, HTTPException
from starlette.responses import StreamingResponse
import requests
import io
from fastapi.middleware.cors import CORSMiddleware
from service.tts import *

from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE")
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

@app.get("/streamed_audio/")
async def streamed_audio(input_text: str, model: str = 'tts-1', voice: str = 'alloy'):
    res=originchat(input_text)
    # OpenAI API endpoint and parameters
    url = api_base+"/audio/speech"
    headers = {
        "Authorization": "Bearer "+api_key,  # Replace with your API key
    }

    data = {
        "model": model,
        "input": res,
        "voice": voice,
        "response_format": "opus",
    }

    response = requests.post(url, headers=headers, json=data, stream=True)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return StreamingResponse(io.BytesIO(response.content), media_type="audio/opus")
