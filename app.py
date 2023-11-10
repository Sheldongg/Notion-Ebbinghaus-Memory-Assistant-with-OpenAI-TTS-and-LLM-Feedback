from service.knowledge_serveice import *
from datetime import datetime
from service.tts import *
import pytz
from voice import voice

load_dotenv()

notion_database_id = os.getenv("notion_database_id")
notion_api_token = os.getenv("notion_api_token")

today={}


def get_review_data(notion_database_id,notion_api_token):
    i = 0
    answer = ''
    question = ''
    _, result = get_data(notion_database_id, notion_api_token)

    for data in result['results']:
        Next_time=data['properties']['Next']['formula']['date']['start']
        dt_obj = datetime.fromisoformat(Next_time)
        now_utc = datetime.now(pytz.utc)
        if dt_obj < now_utc:
            i+=1
            for ids in data['properties']['答案']['rich_text']:
                answer+=ids['text']['content']
            for ids in data['properties']['Name']['title']:
                question+=ids['text']['content']
            today[str(i)]=[question,answer]
            answer = ''
            question = ''
    return today
today = get_review_data(notion_database_id,notion_api_token)
if __name__ == '__main__':
    for real_data in today:
        question=today[real_data][0]
        print(question)
        tts(question)
        answer=today[real_data][1]
        user_answer=voice()

        print("正在判断对错")
        response=chatllm(question,answer,user_answer)

        print(response)
        tts(response)


