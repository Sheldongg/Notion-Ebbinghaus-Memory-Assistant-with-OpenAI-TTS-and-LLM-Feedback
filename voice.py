import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE")

# Initialize OpenAI client
client = OpenAI(api_key=api_key, base_url=api_base)

# FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Function to generate audio stream
def generate_audio_stream(input_text, model='tts-1', voice='alloy'):
    url = "https://ai.api.moblin.net/api/openai/v1/audio/speech"
    headers = {"Authorization": 'Bearer ' + api_key}
    data = {"model": model, "input": input_text, "voice": voice, "response_format": "opus"}
    print("文字正处理"+str(input_text))

    try:

        response = requests.post(url, headers=headers, json=data, stream=True)
        if response.status_code == 200:
            return response.iter_content(chunk_size=4096)
        else:
            return "Error in audio generation"
    except requests.RequestException as e:
        return "Error in audio generation"

# Function to process input text and generate responses
def print_w_stream(message):
    try:
        completion = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {"role": "system", "content": "You are a friendly AI assistant."},
                {"role": "user", "content": message},
            ],
            stream=True,
            temperature=0,
            max_tokens=500,
        )
        sentence = ''
        sentences = []
        sentence_end_chars = {'?', '! ', '\n', '？', '。', '！'}

        for chunk in completion:
            content = chunk.choices[0].delta.content
            if content is not None:
                for char in content:
                    sentence += char
                    if char in sentence_end_chars:
                        sentence = sentence.strip()
                        if sentence and sentence not in sentences:
                            yield sentence
                            print(f"Queued sentence: {sentence}")  # Logging queued sentence
                        sentence = ''
    except Exception as e:
        yield f"Error in generating text: {str(e)}"




@app.post("/generate-audio")
async def api_generate_audio(input_text: str):
    async def audio_stream_generator():
        for sentence in print_w_stream(input_text):
            audio_stream = generate_audio_stream(sentence)
            for chunk in audio_stream:
                yield chunk

    return StreamingResponse(audio_stream_generator(), media_type="audio/opus")
# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
