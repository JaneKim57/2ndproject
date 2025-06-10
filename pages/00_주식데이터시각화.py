import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 페이지 설정 ---
st.set_page_config(layout="wide", page_title="글로벌 시총 TOP 10 주가 변화")
st.title("💰 글로벌 시총 TOP 10 기업 주가 변화 (최근 3년) - 종가 기준")

st.markdown("""
    이 앱은 글로벌 시가총액 상위 10개 기업의 지난 3년간 주가 변화를 보여줍니다.
    **'수정 종가(Adj Close)' 대신 '종가(Close)' 데이터를 사용합니다.**
    따라서 주식 분할이나 배당 등의 이벤트가 발생했을 경우 실제 가치 변동과 그래프가 다르게 보일 수 있습니다.
    데이터는 `yfinance`를 통해 실시간으로 가져옵니다.
""")

# --- 글로벌 시총 TOP 10 기업 티커 (2025년 6월 현재 기준 예상) ---
# 실제 시총 순위는 변동되므로, 최신 정보를 반영하여 필요시 업데이트하세요.
# 안정적인 시각화를 위해 Berkshire Hathaway는 B클래스(BRK-B)를 사용합니다.
TOP_10_TICKERS = {
    "Microsoft": "MSFT",
    "Apple": "AAPL",
    "NVIDIA": "NVDA",
    "Amazon": "AMZN",
    "Alphabet (Google)": "GOOGL",
    "Meta Platforms": "META",
    "Berkshire Hathaway (B)": "BRK-B", # BRK-A는 가격이 너무 높아 시각화가 어려움
    "Eli Lilly and Company": "LLY",
    "TSMC": "TSM",
    "Johnson & Johnson": "JNJ"
}

# --- 날짜 범위 설정 (최근 3년) ---
end_date = datetime.now()
start_date = end_date - timedelta(days=3 * 365) # 3년 전

# --- 데이터 가져오기 및 처리 함수 ---
@st.cache_data(ttl=3600) # 1시간 캐싱 (자주 호출되면 API 제한 걸릴 수 있음)
def get_stock_data_close(tickers_dict, start, end):
    ticker_list = list(tickers_dict.values())
    full_data = yf.download(ticker_list, start=start, end=end)

    # 'Close' 컬럼만 추출하여 새 DataFrame 생성
    close_data = pd.DataFrame()
    for ticker in ticker_list:
        if ('Close', ticker) in full_data.columns:
            close_data[ticker] = full_data['Close'][ticker]
        elif 'Close' in full_data.columns and len(ticker_list) == 1: # 단일 티커 요청 시
            close_data[ticker] = full_data['Close']
        else:
            st.warning(f"티커 {ticker}의 'Close' 데이터를 찾을 수 없습니다. 이 기업은 제외됩니다.")
            close_data[ticker] = None # 데이터를 찾을 수 없을 때 해당 컬럼을 NaN으로 채움

    # 컬럼 이름을 회사 이름으로 변경 (시각화 편의성)
    reverse_ticker_map = {v: k for k, v in tickers_dict.items()}
    close_data.rename(columns=reverse_ticker_map, inplace=True)

    return close_data

# --- 주가 데이터 로드 ---
with st.spinner("최근 3년간 주가 데이터를 불러오는 중..."):
    df_prices = get_stock_data_close(TOP_10_TICKERS, start_date, end_date)

if df_prices.empty or df_prices.isnull().all().all(): # 데이터가 비었거나 전부 NaN인 경우
    st.error("주가 데이터를 불러오지 못했습니다. Yahoo Finance API 또는 인터넷 연결 상태를 확인해주세요. (일부 티커에 문제 있을 수 있음)")
else:
    # --- 시각화: 상대적 주가 변화 (정규화) ---
    st.subheader("📈 지난 3년간 주가 변화 (기준일 대비 정규화)")
    st.info("각 기업의 주가를 시작일(3년 전) 대비 100%로 정규화하여 상대적인 상승/하락률을 비교합니다.")

    # 각 컬럼의 첫 유효한 값으로 나누어 정규화 (NaN 처리 강화)
    normalized_df = pd.DataFrame()
    for col in df_prices.columns:
        first_valid_value = df_prices[col].dropna().iloc[0] if not df_prices[col].dropna().empty else None
        if first_valid_value is not None and first_valid_value != 0:
            normalized_df[col] = (df_prices[col] / first_valid_value) * 100
        else:
            st.warning(f"{col}의 초기 주가 데이터가 없거나 0이어서 정규화할 수 없습니다. 이 기업은 그래프에서 제외됩니다.")
            normalized_df[col] = None # 제외된 컬럼은 NaN으로 채움

    fig_norm = go.Figure()
    for company_name in normalized_df.columns:
        if normalized_df[company_name].notna().any(): # NaN이 아닌 유효한 데이터가 있는 경우만 그림
            fig_norm.add_trace(go.Scatter(
                x=normalized_df.index,
                y=normalized_df[company_name],
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
        list(df_prices.columns)
    )

    if selected_company_name in df_prices.columns:
        fig_individual = go.Figure()
        fig_individual.add_trace(go.Scatter(
            x=df_prices.index,
            y=df_prices[selected_company_name],
            mode='lines',
            name=selected_company_name,
            line=dict(color='blue')
        ))
        fig_individual.update_layout(
            title=f'{selected_company_name} 주가 변화',
            xaxis_title='날짜',
            yaxis_title='주가 (USD)',
            hovermode="x unified",
            height=500
        )
        st.plotly_chart(fig_individual, use_container_width=True)

        # --- 데이터 테이블 보기 ---
        st.subheader(f"Raw Data: {selected_company_name}")
        st.dataframe(df_prices[[selected_company_name]].tail(30)) # 최근 30일 데이터만 표시
    else:
        st.warning(f"선택하신 {selected_company_name}의 주가 데이터를 찾을 수 없습니다. 데이터 로드에 문제가 발생했을 수 있습니다.")

st.markdown("---")
st.markdown("데이터 출처: Yahoo Finance (종가 기준)")
