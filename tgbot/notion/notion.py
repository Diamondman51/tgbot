import asyncio
import json
import os
import pprint
import aiohttp
import dotenv
# import requests


dotenv.load_dotenv()

DB_TOKEN = os.getenv('DB_TOKEN')

DB_ID = os.getenv('DB_ID')


async def get_headers(DB_TOKEN):
    headers = {
    'Authorization': "Bearer " + DB_TOKEN,
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
    }
    return headers


async def get_page(DB_ID, DB_TOKEN, num_pages: int=None) -> list:
    url = f"https://api.notion.com/v1/databases/{DB_ID}/query"
    headers = await get_headers(DB_TOKEN)
    print(headers)
    get_all = num_pages is None
    page_size = 100 if get_all else num_pages

    payload = {'page_size': page_size}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            data: dict = await response.json()
    
    results: list = data.get("results")

    while data.get("has_more") and get_all:
        payload = {"page_size": page_size, 'start_cursor': data.get("next_cursor")}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
        results.extend(data.get("results"))

    pprint.pprint(data.get('results'))

    # with open('notion.txt', 'w') as f:
    #     json.dump(data, f, ensure_ascii=False, indent=4)

    pages = data.get("results")
    
    for page in pages:
        props = page["properties"]
        url = props["URL"]["title"][0]["text"]["content"]
        title = props["Title"]["rich_text"][0]["text"]["content"]
        published = props["Priority"]["select"]["name"]
        text = props["Category"]['rich_text'][0]['plain_text']
        print(url, title, published, text)

    return results


async def create_page(data: dict, DB_ID, DB_TOKEN) -> dict:
    headers = await get_headers(DB_TOKEN)
    create_url = "https://api.notion.com/v1/pages"
    payload = {"parent": {"database_id": DB_ID}, "properties": data}
    async with aiohttp.ClientSession() as session:
        async with session.post(create_url, headers=headers, json=payload) as response:
            # print(await response.json())
            return await response.json()


URL = "I am"
Title = "The"
Category = "Guru"
Priority = "One"


async def create_page_data(URL, Title, Category, Priority) -> dict:
    data: dict = {
        'URL': {"title": [{'text': {'content': URL}}]},
        'Title': {'rich_text': [{'text': {"content": Title}}]},
        'Priority': {'select': {'name': Priority}},
        'Category': {'rich_text': [{'text': {'content': Category}}]}
    }

    return data


if __name__ == "__main__":
    async def main():
        # await get_page(DB_ID, DB_TOKEN)
        res: dict = await create_page(await create_page_data(URL, Title, Priority, Category), DB_ID, DB_TOKEN)
        print()
        pprint.pprint(res)

    asyncio.run(main())
