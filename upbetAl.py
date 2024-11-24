import requests
import os
import time
from flask import Flask, render_template, jsonify, request, session
import matplotlib
matplotlib.use('Agg')  # GUI backend not used
import matplotlib.pyplot as plt  
import matplotlib.dates as mdates
import io
import base64
import pandas as pd
import threading
import jwt
import uuid
import hashlib
from urllib.parse import urlencode

# 환경 변수에서 액세스 키와 비밀 키 가져오기
# 가상 머니 설정
virtual_balance = 100000000  # 가상 자금: 1억 원
owned_crypto = 0  # 보유 중인 가상 암호화폐 수량
access_key = 'virtual_access_key'  # 가상 환경에서 사용할 액세스 키
secret_key = 'virtual_secret_key'  # 가상 환경에서 사용할 비밀 키
server_url = 'https://api.upbit.com'

app = Flask(__name__)
latest_analysis = ""
latest_chart_url = ""

# 업비트 API에서 캔들 데이터를 가져오는 함수
def get_upbit_minute_candle(market='KRW-BTC', minute_unit=1, count=10):
    url = f"https://api.upbit.com/v1/candles/minutes/{minute_unit}"
    querystring = {"market": market, "count": count}
    response = requests.get(url, params=querystring)
    if response.status_code == 200:
        return response.json()
    else:
        print("데이터를 가져오는 데 실패했습니다.")
        return None

# 차트를 분석하는 함수 (예시 함수, 추가 구현 필요)
def analyze_chart(candles):
    if not candles:
        return "정보 수집 중..."
    # 최근 차트가 3회 연속 양봉인지 또는 음봉인지 확인
    recent_candles = candles[-3:]
    is_up = (recent_candles[0]['trade_price'] > recent_candles[0]['opening_price'] and
             recent_candles[1]['trade_price'] > recent_candles[1]['opening_price'] and
             recent_candles[2]['trade_price'] > recent_candles[2]['opening_price'])
    is_down = (recent_candles[0]['trade_price'] < recent_candles[0]['opening_price'] and
               recent_candles[1]['trade_price'] < recent_candles[1]['opening_price'] and
               recent_candles[2]['trade_price'] < recent_candles[2]['opening_price'])
    if is_up:
        return "최근 3분 연속 양봉입니다. 매수를 고려하세요!"
    elif is_down:
        return "최근 3분 연속 음봉입니다. 매도를 고려하세요!"
    else:
        return "아직 특별한 변화가 없습니다."

# 캔들 차트를 생성하는 함수
def create_chart(candles):
    df = pd.DataFrame(candles)
    df['time'] = pd.to_datetime(df['candle_date_time_kst'])
    df = df.sort_values(by='time')
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=1))

    for idx, row in df.iterrows():
        color = 'red' if row['opening_price'] < row['trade_price'] else 'blue'
        ax.plot([row['time'], row['time']], [row['low_price'], row['high_price']], color='black')
        ax.add_patch(plt.Rectangle((row['time'], row['opening_price']), pd.Timedelta(minutes=1), row['trade_price'] - row['opening_price'], color=color, alpha=0.7))
    
    plt.xlabel('Time')
    plt.ylabel('Price (KRW)')
    plt.title('KRW-BTC 1-Minute Interval Candlestick Chart')
    plt.xticks(rotation=45)
    
    # 매수 시점 표시
    if 'buy_time' in globals() and buy_time is not None and 'buy_price' in globals() and buy_price is not None:
        ax.axhline(y=buy_price, color='red', linestyle='--', label='Buy Order')
    
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend()
    plt.tight_layout()
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return f"data:image/png;base64,{chart_url}"

# 매수/매도 주문을 처리하는 함수
def place_order(side, market, volume, price=None):
    global virtual_balance, owned_crypto
    if side == 'bid':  # 매수 주문 시
        try:
            price = float(price)
            volume = float(volume)
            cost = price * volume
        except (ValueError, TypeError):
            return {'status': 'failed', 'message': '잘못된 가격 또는 수량 입력'}
        
        if virtual_balance >= cost:
            virtual_balance -= cost
            owned_crypto += volume
            print("가상 매수 주문이 성공적으로 요청되었습니다.")
            return {'status': 'success', 'message': '매수 주문 완료'}
        else:
            print("주문 실패: 가상 매수 자금이 부족합니다.")
            return {'status': 'failed', 'message': '자금 부족'}
    elif side == 'ask':  # 매도 주문 시
        try:
            price = float(price)
            volume = float(volume)
            proceeds = price * volume
        except (ValueError, TypeError):
            return {'status': 'failed', 'message': '잘못된 가격 또는 수량 입력'}
        
        if owned_crypto >= volume and proceeds > 0:
            owned_crypto -= volume
            virtual_balance += proceeds
            print("가상 매도 주문이 성공적으로 요청되었습니다.")
            return {'status': 'success', 'message': '매도 주문 완료'}
        else:
            print("매도 실패: 잘못된 수익 계산입니다.")
            return {'status': 'failed', 'message': '잘못된 수익 계산 또는 보유 자산 부족'}
    else:
        print("잘못된 주문 요청입니다.")
        return {'status': 'failed', 'message': '잘못된 요청'}

# 매수/매도 요청을 위한 Flask 라우팅
@app.route('/buy', methods=['POST'])
def buy():
    global buy_time, buy_price, virtual_balance, latest_chart_url, latest_analysis
    # 전액 매수
    candles = get_upbit_minute_candle(market='KRW-BTC', minute_unit=1, count=1)
    if not candles:
        return jsonify({"message": "매수 주문 실패: 가격 데이터를 가져오지 못했습니다.", "virtual_balance": virtual_balance})
    latest_price = candles[0]['trade_price']
    amount = virtual_balance / latest_price

    res = place_order('bid', 'KRW-BTC', amount, latest_price)
    if res['status'] == 'success':
        buy_time = pd.Timestamp.now()
        buy_price = latest_price
        # 매수 버튼 누른 시점을 차트에 기록
        candles = get_upbit_minute_candle(market='KRW-BTC', minute_unit=1, count=10)
        latest_chart_url = create_chart(candles) if candles else None
        return jsonify({"message": "매수 주문이 완료되었습니다.", "virtual_balance": virtual_balance, "status": "success"})
    else:
        return jsonify({"message": res['message'], "virtual_balance": virtual_balance})

@app.route('/sell', methods=['POST'])
def sell():
    global sell_time, buy_time, virtual_balance, latest_chart_url, latest_analysis
    # 전액 매도
    candles = get_upbit_minute_candle(market='KRW-BTC', minute_unit=1, count=1)
    if not candles:
        return jsonify({"message": "매도 주문 실패: 가격 데이터를 가져오지 못했습니다.", "virtual_balance": virtual_balance})
    latest_price = candles[0]['trade_price']
    amount = owned_crypto  # 보유한 전체 암호화폐 수량을 매도

    res = place_order('ask', 'KRW-BTC', amount, latest_price)
    if res['status'] == 'success':
        sell_time = pd.Timestamp.now()
        buy_time = None
        # 매도 버튼 누른 시점을 차트에 기록
        candles = get_upbit_minute_candle(market='KRW-BTC', minute_unit=1, count=10)
        latest_chart_url = create_chart(candles) if candles else None
        return jsonify({"message": "매도 주문이 완료되었습니다.", "virtual_balance": virtual_balance})
    else:
        return jsonify({"message": res['message'], "virtual_balance": virtual_balance})

@app.route('/')
def index():
    market = 'KRW-BTC'  # 원하는 거래 쌍 설정 (예: KRW-BTC)
    candles = get_upbit_minute_candle(market=market, minute_unit=1, count=10)
    analysis_result = analyze_chart(candles)
    chart_url = create_chart(candles) if candles else None
    return render_template('index.html', analysis_result=analysis_result, chart_url=chart_url, virtual_balance=virtual_balance)

@app.route('/live_analysis')
def live_analysis():
    return jsonify({'analysis': latest_analysis, 'chart_url': latest_chart_url, 'virtual_balance': virtual_balance})

def update_analysis():
    global latest_analysis, latest_chart_url
    market = 'KRW-BTC'
    while True:
        candles = get_upbit_minute_candle(market=market, minute_unit=1, count=10)
        latest_analysis = analyze_chart(candles)
        latest_chart_url = create_chart(candles) if candles else None
        time.sleep(1)  # 1초마다 갱신

if __name__ == "__main__":
    threading.Thread(target=update_analysis, daemon=True).start()
    app.run(debug=True)
