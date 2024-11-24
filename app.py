import requests
import json
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정
API_KEY = os.getenv('OPENAI_API_KEY')  # .env에서 OpenAI API 키 가져오기

# API 요청 URL
url = "https://api.openai.com/v1/chat/completions"

# 요청 헤더 설정
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# 요청 데이터 설정
data = {
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
}

# POST 요청 보내기
response = requests.post(url, headers=headers, data=json.dumps(data))

# 응답 확인
if response.status_code == 200:
    response_data = response.json()
    print("응답 데이터:")
    print(json.dumps(response_data, indent=2))  # JSON 포맷으로 출력
else:
    print(f"요청 실패: {response.status_code}")
    print(response.text)
