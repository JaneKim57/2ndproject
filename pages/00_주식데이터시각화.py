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
    "Berkshire Hathaway": "BRK-A", # 또는 BRK-B (B-클래스 주식)
    "Eli Lilly and Company": "LLY", # 헬스케어 섹터 강세로 추가
    "TSMC": "TSM", # 반도체 산업 중요성
    "Johnson & Johnson": "JNJ" # 안정적인 대형 제약사
}

# --- 날짜 범위 설정 (최근 3년) ---
end_date = datetime.now()
start_date = end_date - timedelta(days=3 * 365) # 3년 전

# --- 데이터 가져오기 및 처리 함수 ---
@st.cache_data(ttl=3600) # 1시간 캐싱 (자주 호출되면 API 제한 걸릴 수 있음)
def get_stock_data(tickers, start, end):
    data = yf.download(list(tickers.values()), start=start, end=end)
    return data['Adj Close'] # 수정 종가만 반환

# --- 주가 데이터 로드 ---
with st.spinner("최근 3년간 주가 데이터를 불러오는 중..."):
    df_prices = get_stock_data(TOP_10_TICKERS, start_date, end_date)

if df_prices.empty:
    st.error("주가 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.")
else:
    # --- 시각화: 상대적 주가 변화 (정규화) ---
    st.subheader("📈 지난 3년간 주가 변화 (기준일 대비 정규화)")
    st.info("각 기업의 주가를 시작일(3년 전) 대비 100%로 정규화하여 상대적인 상승/하락률을 비교합니다.")

    # 첫 날 주가로 정규화
    normalized_prices = df_prices / df_prices.iloc[0] * 100

    fig_norm = go.Figure()
    for company_name, ticker in TOP_10_TICKERS.items():
        if ticker in normalized_prices.columns:
            fig_norm.add_trace(go.Scatter(
                x=normalized_prices.index,
                y=normalized_prices[ticker],
                mode='lines',
                name=company_name
            ))
    fig_norm.update_layout(
        title='글로벌 시총 TOP 10 기업의 상대적 주가 변화',
        xaxis_title='날짜',
        yaxis_title='주가 (시작일 대비 100%)',
        hovermode="x unified",
        legend_title="기업",
        height=600
    )
    st.plotly_chart(fig_norm, use_container_width=True)

    # --- 개별 기업 주가 선택 및 시각화 ---
    st.subheader("📊 개별 기업 주가 상세 보기")
    selected_company_name = st.selectbox(
        "주가를 확인하고 싶은 기업을 선택하세요:",
        list(TOP_10_TICKERS.keys())
    )

    selected_ticker = TOP_10_TICKERS[selected_company_name]

    if selected_ticker in df_prices.columns:
        fig_individual = go.Figure()
        fig_individual.add_trace(go.Scatter(
            x=df_prices.index,
            y=df_prices[selected_ticker],
            mode='lines',
            name=selected_company_name,
            line=dict(color='blue')
        ))
        fig_individual.update_layout(
            title=f'{selected_company_name} ({selected_ticker}) 주가 변화',
            xaxis_title='날짜',
            yaxis_title='주가 (USD)',
            hovermode="x unified",
            height=500
        )
        st.plotly_chart(fig_individual, use_container_width=True)

        # --- 데이터 테이블 보기 ---
        st.subheader(f"Raw Data: {selected_company_name} ({selected_ticker})")
        st.dataframe(df_prices[[selected_ticker]].tail(30)) # 최근 30일 데이터만 표시
    else:
        st.warning(f"선택하신 {selected_company_name} ({selected_ticker})의 주가 데이터를 찾을 수 없습니다.")

st.markdown("---")
st.markdown("데이터 출처: Yahoo Finance")
