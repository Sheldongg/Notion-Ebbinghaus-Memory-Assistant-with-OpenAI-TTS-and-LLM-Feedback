import requests
import json

def get_block_children(page_id, notion_api_token):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {notion_api_token}",
        "Notion-Version": "2021-08-16"  # 请确保使用最新的API版本
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()  # 返回包含块内容的JSON对象
    else:
        return None

def del_data(id, notion_api_token): #删除行
    headers = {
        # 设置机器人令牌，即 Notion 的机器人码
        "Authorization": "Bearer " + notion_api_token,
        # 设置 Notion 版本，目前不用改
        "Notion-Version": "2021-05-13"
    }
    url = "https://api.notion.com/v1/pages/%s" % id
    body = {
        "archived": True
    }
    del_result = requests.patch(url, headers=headers, json=body)
    print(del_result.text)

def get_page_content(page_id, notion_api_token):
    try:
        url = f"https://api.notion.com/v1/pages/{page_id}"

        headers = {
            "Authorization": f"Bearer {notion_api_token}",
            "Notion-Version": "2021-05-13"  # 此处的Notion版本可能需要更新到最新版
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 检查请求是否成功
        page_content = response.json()
        return page_content

    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

def get_page_ids_from_database(notion_database_id, notion_api_token):
    page_ids = []
    has_more = True
    start_cursor = None

    try:
        while has_more:
            url = f"https://api.notion.com/v1/databases/{notion_database_id}/query"

            headers = {
                "Authorization": f"Bearer {notion_api_token}",
                "Notion-Version": "2021-05-13"  # 此处的Notion版本可能需要更新到最新版
            }

            body = {}
            if start_cursor:
                body["start_cursor"] = start_cursor

            response = requests.post(url, json=body, headers=headers)
            response.raise_for_status()  # 检查请求是否成功
            results = response.json()

            for page in results.get('results', []):
                page_ids.append(page['id'])

            has_more = results['has_more']
            start_cursor = results.get('next_cursor')

        return page_ids

    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

def get_data(notion_database_id, notion_api_token, start_cursor=None):
    try:
        print(start_cursor, '-' * 50)
        url = "https://api.notion.com/v1/databases/%s/query" % notion_database_id

        headers = {
            # 设置机器人令牌，即 Notion 的机器人码
            "Authorization": "Bearer " + notion_api_token,
            # 设置 Notion 版本，目前不用改
            "Notion-Version": "2021-05-13"
        }
        body = {
            "sorts": [
                {
                    "property": "Name",
                    "direction": "ascending"
                }
            ],
        }
        if start_cursor != None:
            body["start_cursor"] = start_cursor
        a = requests.post(url, json=body, headers=headers,)
        a.close() #在使用requests多次访问同一个ip时，尤其是在高频率访问下，http连接太多没有关闭导致的Max retries exceeded with url 的错误
        result = json.loads(a.text)
        x = [i for i in result["results"]]
        data = []
        for i in x:
            try:
                obj = {"Line": i["properties"]["Line"]["number"], "isComplete": None, "id": i["id"]}
        #         if i["properties"].get("Community judgement") != None:
        #             obj["isComplete"] = True
        #         else:
        #             obj["isComplete"] = False
                data.append(obj)
            except:            #什么时候用到except，应该是没有判断，但是有数据。
                pass
        if result.get("has_more") == True: #查看页面是否还有剩下没加载出来的页面
            data1, result1 = get_data(notion_database_id, notion_api_token, result.get("next_cursor")) #递归
            data += data1
            result["results"] += result1["results"]
        return data, result
    except Exception as e:
        # print(result)
        print(e)