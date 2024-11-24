import jwt
import uuid
import hashlib
import requests
import time
import threading
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# 발급받은 access key와 secret key
access_key = os.getenv('ACCESS_KEY')  # .env에서 접근 키 가져오기
secret_key = os.getenv('SECRET_KEY')  # .env에서 비밀 키 가져오기

# 매수 가격 및 상태 초기화
buy_price = None
volume_to_buy = 0.0  # 매수할 수량 초기화
profit_display_thread = None  # 순이익 표시 스레드
initial_price = None  # 초기 가격 변수 추가
already_bought = False  # 매수 여부를 처리할 변수 추가

def get_current_price(market='KRW-BTC'):
    url = f'https://api.upbit.com/v1/ticker?markets={market}'
    response = requests.get(url)
    return response.json()[0]['trade_price']

def display_profit():
    global buy_price, volume_to_buy
    while True:
        if buy_price is not None:
            current_price = get_current_price()
            profit = (current_price - buy_price) * volume_to_buy  # 순이익 계산
            profit_percentage = (profit / (buy_price * volume_to_buy)) * 100  # 수익률 계산
            print(f"순이익: {profit:.2f} 원, 수익률: {profit_percentage:.2f}%")
        time.sleep(3)  # 3초 간격으로 출력

def price_updater():
    global initial_price, already_bought, profit_display_thread  # 전역 변수 선언
    while True:
        time.sleep(5)
        current_price = get_current_price()
        # 가격 변화 계산
        price_change_percentage = (current_price - initial_price) / initial_price * 100
        print(f"현재 가격: {current_price}, 초기 가격 대비 변화: {price_change_percentage:.2f}%")

        # 매수 조건 체크
        if price_change_percentage >= 0.05 and not already_bought:
            response = input(f"매수 조건 충족: 현재 가격 {current_price}에서 매수하시겠습니까? (y/n): ")
            if response.lower() == 'y':
                global buy_price, volume_to_buy
                buy_price = current_price
                volume_to_buy = 10000 / buy_price  # 만원으로 매수할 수량 계산
                print(f"매수 완료: 현재 가격 {current_price}에서 매수했습니다. 수량: {volume_to_buy:.6f}")
                already_bought = True  # 매수 완료 상태로 변경
                # 순이익 표시 스레드 시작
                if profit_display_thread is None:  # 여기에서 profit_display_thread 확인
                    profit_display_thread = threading.Thread(target=display_profit, daemon=True)
                    profit_display_thread.start()

def main():
    global initial_price
    initial_price = get_current_price()  # 초기 가격 저장
    print(f"초기 가격: {initial_price}")

    # 가격 업데이트 스레드 시작
    threading.Thread(target=price_updater, daemon=True).start()

    while True:
        time.sleep(60)  # 1분 간격으로 체크

if __name__ == "__main__":
    main()
