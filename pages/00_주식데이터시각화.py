import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 페이지 설정 ---
st.set_page_config(layout="wide", page_title="글로벌 시총 TOP 10 주가 변화")
st.title("💰 글로벌 시총 TOP 10 기업 주가 변화 (최근 3년)")

st.markdown("""
    이 앱은 글로벌 시가총액 상위 10개 기업의 지난 3년간 주가 변화를 보여줍니다.
    데이터는 `yfinance`를 통해 실시간으로 가져옵니다.
""")

# --- 글로벌 시총 TOP 10 기업 티커 (2025년 6월 현재 기준 예상) ---
# 실제 시총 순위는 변동되므로, 최신 정보를 반영하여 필요시 업데이트하세요.
# 편의상 대표적인 초대형 기술 기업 위주로 선정했습니다.
# 이 리스트는 변동될 수 있습니다. (예: NVIDIA, Broadcom 등)
TOP_10_TICKERS = {
    "Microsoft": "MSFT",
    "Apple": "AAPL",
    "NVIDIA": "NVDA", # 최근 급성장으로 추가
    "Amazon": "AMZN",
    "Alphabet (Google)": "GOOGL", # GOOG (Class C) 또는 GOOGL (Class A) 선택
    "Meta Platforms": "META",
    "Berkshire Hathaway": "BRK-A", # 또는 BRK-B (B-클래스 주식) - A클래스 주식은 거래량이 적고 가격이 매우 높아 B클래스(BRK-B)를 권장합니다.
    "Eli Lilly and Company": "LLY", # 헬스케어 섹터 강세로 추가
    "TSMC": "TSM", # 반도체 산업 중요성
    "Johnson & Johnson": "JNJ" # 안정적인 대형 제약사
}

# Berkshire Hathaway A클래스는 가격이 너무 높아 그래프 시각화가 어려울 수 있어 B클래스(BRK-B)로 변경 권장
# BRK-A는 주당 가격이 매우 높아서 다른 주식들과 함께 정규화 그래프에 그리기 부적합할 수 있습니다.
# 만약 BRK-A를 사용하고자 한다면 다른 기업들과 분리하여 시각화하는 것을 고려하거나,
# 다른 대형주 (예: Tesla (TSLA), Saudi Aramco (2222.SR - 사우디아람코는 yfinance에서 직접 조회 어려울 수 있음)) 로 변경하는 것을 추천합니다.
# 여기서는 시각화의 용이성을 위해 BRK-B로 가정하고 진행하겠습니다.
# 만약 BRK-A를 꼭 포함하고 싶다면, 해당 기업만 별도로 처리하는 로직이 필요할 수 있습니다.
# 현재 예시에서는 BRK-A를 포함하되, 주가가 매우 높아서 다른 기업 그래프에 비해 왜곡될 수 있다는 점을 인지해야 합니다.
# 안정적인 시각화를 위해 TOP_10_TICKERS에서 BRK-A 대신 BRK-B를 포함하는 것이 좋습니다.
TOP_10_TICKERS_CLEANED = {
    "Microsoft": "MSFT",
    "Apple": "AAPL",
    "NVIDIA": "NVDA",
    "Amazon": "AMZN",
    "Alphabet (Google)": "GOOGL",
    "Meta Platforms": "META",
    "Berkshire Hathaway (B)": "BRK-B", # BRK-A 대신 BRK-B 사용 권장
    "Eli Lilly and Company": "LLY",
    "TSMC": "TSM",
    "Johnson & Johnson": "JNJ"
}


# --- 날짜 범위 설정 (최근 3년) ---
end_date = datetime.now()
start_date = end_date - timedelta(days=3 * 365) # 3년 전

# --- 데이터 가져오기 및 처리 함수 ---
@st.cache_data(ttl=3600) # 1시간 캐싱 (자주 호출되면 API 제한 걸릴 수 있음)
def get_stock_data(tickers_dict, start, end):
    # yfinance는 여러 티커를 요청할 때 MultiIndex 컬럼을 반환합니다.
    # 이를 처리하기 위해 각 티커의 'Adj Close'만 추출하여 하나의 DataFrame으로 만듭니다.
    ticker_list = list(tickers_dict.values())
    full_data = yf.download(ticker_list, start=start, end=end)

    # 'Adj Close' 컬럼만 추출하여 새 DataFrame 생성
    adj_close_data = pd.DataFrame()
    for ticker in ticker_list:
        if ('Adj Close', ticker) in full_data.columns:
            adj_close_data[ticker] = full_data['Adj Close'][ticker]
        else: # 단일 티커 요청 시에는 MultiIndex가 아닐 수 있음
             if 'Adj Close' in full_data.columns:
                 # 이 경우는 단일 티커를 처리하는 것이 아니므로, 위 if 문으로 충분합니다.
                 # 혹시 모를 경우를 대비한 방어 코드 (여기서는 해당되지 않을 가능성 높음)
                 pass
             st.warning(f"티커 {ticker}의 'Adj Close' 데이터를 찾을 수 없습니다.")
    
    # 컬럼 이름을 회사 이름으로 변경 (시각화 편의성)
    # 딕셔너리를 사용하여 티커 -> 회사 이름 매핑
    reverse_ticker_map = {v: k for k, v in tickers_dict.items()}
    adj_close_data.rename(columns=reverse_ticker_map, inplace=True)
    
    return adj_close_data

# --- 주가 데이터 로드 ---
with st.spinner("최근 3년간 주가 데이터를 불러오는 중..."):
    df_prices = get_stock_data(TOP_10_TICKERS_CLEANED, start_date, end_date) # 수정된 티커 딕셔너리 사용

if df_prices.empty or df_prices.isnull().all().all(): # 데이터가 비었거나 전부 NaN인 경우
    st.error("주가 데이터를 불러오지 못했습니다. Yahoo Finance API 또는 인터넷 연결 상태를 확인해주세요. (일부 티커에 문제 있을 수 있음)")
else:
    # --- 시각화: 상대적 주가 변화 (정규화) ---
    st.subheader("📈 지난 3년간 주가 변화 (기준일 대비 정규화)")
    st.info("각 기업의 주가를 시작일(3년 전) 대비 100%로 정규화하여 상대적인 상승/하락률을 비교합니다.")

    # 첫 날 주가로 정규화 (NaN 값 제거 후 첫 유효한 값으로 정규화)
    # NaN 값은 정규화에 방해가 되므로 dropna(how='all')로 최소한 모든 컬럼이 NaN인 행 제거
    # 첫
