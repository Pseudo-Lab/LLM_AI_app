from dotenv import load_dotenv
import os
from fastmcp import FastMCP 
import datetime
from pathlib import Path

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

import requests

import asyncio
import sys

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())



weather_mcp = FastMCP(
    name="weather_mcp",
    instructions="국내/해외 날씨를 조회하는 mcp server",
    port=7000
)

korea_city_list = open(Path(__file__).parent / 'assets' / 'korea_city.txt', 'r', encoding='utf-8').read().splitlines()
korea_city_list = "\n".join(korea_city_list)

china_city_list = open(Path(__file__).parent / 'assets' / 'china_city.txt', 'r', encoding='utf-8').read().splitlines()
china_city_list = "\n".join(china_city_list)

japan_city_list = open(Path(__file__).parent / 'assets' / 'japan_city.txt', 'r', encoding='utf-8').read().splitlines()
japan_city_list = "\n".join(japan_city_list)
'''
openweathermap에서 제공하는 도시 리스트
https://bulk.openweathermap.org/sample/city.list.json.gz
'''
@weather_mcp.tool()
def global_weather_tool(city: str = 'Seoul') -> str:
    f'''이 함수는 가장 먼저 호출되어야 하는 함수 입니다.

    이 함수는 날씨를 조회하기 이전 사용자 입력에서 
    입력 받은 도시가 국내(한국)인지 해외인지 확인하는 도구 입니다.
    
    만약 한국의 도시일 경우 "kor_weather_tool"을 호출하고
    해외의 도시일 경우 "global_weather_tool"을 호출하세요.

    아래는 각각 한국과 해외의 도시 리스트입니다.
    대한민국 도시 리스트: {korea_city_list}
    * 만약 "OO구" 이런 입력이 들어온다면 이는 대한민국 서울시에 존재하는 지역구를 의미합니다.
    * 최대한 대한민국 지역에 대해서는 최대한 정확한 지역구를 입력해주세요.

    해외(중국) 도시 리스트: {china_city_list}
    해외(일본) 도시 리스트: {japan_city_list}
    '''
    # print(city)
    api_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=kr"

    try:
        response = requests.get(api_url)
        print(response.status_code)
        response = response.json()

        city_temperature = response['main']['temp']
        city_feel_like = response['main']['feels_like']
        city_weather = response['weather'][0]['description']
        city_wind_speed = response['wind']['speed']
        city_name = response['name']
        
        sys_date = datetime.datetime.fromtimestamp(response['dt']).strftime('%H:%M')

        return f'''
        검색한 도시: {city_name} 
        기준 시간: {sys_date}
        온도: {city_temperature}도 (체감온도: {city_feel_like}도)
        날씨: {city_weather} 
        풍속: {city_wind_speed}m/s 
        
        1. 위 양식 그대로 반드시 사용자에게 알려주세요. 
        2. 위 정보를 바탕으로 복장을 함께 추천해주세요.
        3. 도시명을 출력할 때는 해당 국가 또한 말씀해주세요. ex) "대한민국, 광진구", "중국, 베이징", "일본, 도쿄"'''

    except Exception as e:
        return "날씨 조회 실패"





if __name__ == "__main__":
    weather_mcp.run(transport="sse")
    '''
    stdio로 실행을 원한다면
    transfport 파라미터를 삭제하거나 (default가 stdio)
    mcp.run(transport="stdio")
    으로 입력하면 됩니다.
    '''

    '''
    test code
    '''
    # from fastmcp import Client
    # import asyncio

    # client = Client(mcp)

    # async def call_tool(city: str):
    #     async with client:
    #         result = await client.call_tool("weather_tool", {"city": city})
    #         print(result)

    # asyncio.run(call_tool("Seoul"))




