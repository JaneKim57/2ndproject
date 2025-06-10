import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import requests
import datetime

st.set_page_config(layout="wide", page_title="지진과 판 구조론 탐험")

# --- 데이터 가져오기 함수 ---
@st.cache_data(ttl=3600) # 1시간마다 데이터 갱신
def load_earthquake_data(days=30, min_magnitude=2.5):
    """
    USGS API에서 최근 지진 데이터를 가져옵니다.
    """
    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(days=days)

    url = (
        f"https://earthquake.usgs.gov/fdsnws/event/1/query?"
        f"format=geojson&starttime={start_time.strftime('%Y-%m-%d')}&endtime={end_time.strftime('%Y-%m-%d')}"
        f"&minmagnitude={min_magnitude}"
    )

    try:
        response = requests.get(url)
        response.raise_for_status() # HTTP 오류 발생 시 예외 처리 (4xx, 5xx 에러)
        data = response.json()

        features = data.get('features', []) # 'features' 키가 없을 경우 빈 리스트 반환
        earthquakes = []
        for feature in features:
            props = feature.get('properties', {}) # 'properties' 키가 없을 경우 빈 딕셔너리 반환
            geo = feature.get('geometry', {})     # 'geometry' 키가 없을 경우 빈 딕셔너리 반환

            # 필요한 모든 데이터가 있는지 확인
            if geo and geo.get('coordinates') and props.get('mag') is not None:
                coords = geo['coordinates']
                earthquakes.append({
                    'place': props.get('place', '장소 정보 없음'),
                    'magnitude': props['mag'],
                    'time': datetime.datetime.fromtimestamp(props.get('time', 0)/1000), # 'time' 키가 없을 경우 0으로 처리
                    'longitude': coords[0],
                    'latitude': coords[1],
                    'depth': props.get('depth', None), # 'depth' 키가 없을 경우 None으로 처리
                    'url': props.get('url', '#')
                })
        return pd.DataFrame(earthquakes)
    except requests.exceptions.RequestException as e:
        st.error(f"지진 데이터를 불러오는 데 실패했습니다: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"데이터 처리 중 예상치 못한 오류가 발생했습니다: {e}")
        return pd.DataFrame()

# --- 지진 규모별 색상 및 설명 ---
def get_magnitude_color(magnitude):
    if magnitude is None: # None 값 처리 추가
        return 'gray'
    elif magnitude >= 8.0:
        return 'darkred'
    elif magnitude >= 7.0:
        return 'red'
    elif magnitude >= 6.0:
        return 'orange'
    elif magnitude >= 5.0:
        return 'darkorange'
    elif magnitude >= 4.0:
        return 'lightred'
    elif magnitude >= 3.0:
        return 'beige'
    else: # 2.5 이상
        return 'lightblue'

def get_magnitude_info(magnitude):
    if magnitude is None:
        return "정보 없음"
    elif magnitude < 2.0:
        return "미진 (Micro): 거의 느껴지지 않음"
    elif magnitude < 3.0:
        return "약진 (Minor): 일부가 느낌"
    elif magnitude < 4.0:
        return "경진 (Minor-Light): 많은 사람이 느낌, 피해 없음"
    elif magnitude < 5.0:
        return "강진 (Light): 대부분 느낌, 미미한 피해 가능"
    elif magnitude < 6.0:
        return "중진 (Moderate): 부실 건물 피해 가능"
    elif magnitude < 7.0:
        return "대진 (Strong): 잘 지어진 건물도 중간 피해, 부실 건물은 심각"
    elif magnitude < 8.0:
        return "거대 지진 (Major): 넓은 지역에 심각한 피해, 인명 피해"
    else: # magnitude >= 8.0
        return "초거대 지진 (Great): 광범위한 파괴 및 인명 피해"

# --- 스트림릿 UI 시작 ---
st.sidebar.title("설정")
st.sidebar.header("데이터 필터링")

num_days = st.sidebar.slider(
    "지난 몇 일간의 지진 데이터?",
    min_value=1, max_value=365, value=30, step=1
)
min_mag = st.sidebar.slider(
    "최소 지진 규모 필터 (M)",
    min_value=1.0, max_value=8.0, value=2.5, step=0.1
)

st.title("🌍 지진과 판 구조론 탐험")
st.markdown("이 앱은 USGS(미국 지질조사국)의 실시간 지진 데이터를 기반으로 지진 발생 빈도와 판 구조론의 관계를 시각적으로 보여줍니다.")
st.markdown("---")

st.info(f"**💡 Tip:** 왼쪽 사이드바에서 데이터 필터를 조절하여 지진 정보를 변경할 수 있습니다.")

# 지진 데이터 로드
df_earthquakes = load_earthquake_data(num_days, min_mag)

if not df_earthquakes.empty:
    st.header(f"최근 {num_days}일 간 규모 {min_mag} 이상 지진 분포")

    # 지도 생성 (평균 위도, 경도)
    # 데이터프레임이 비어 있지 않으므로 .mean() 사용 가능
    map_center_lat = df_earthquakes['latitude'].mean()
    map_center_lon = df_earthquakes['longitude'].mean()
    m = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=2, control_scale=True)

    # 마커 클러스터 추가
    marker_cluster = MarkerCluster().add_to(m)

    for idx, row in df_earthquakes.iterrows():
        # 'depth'가 None일 경우 '정보 없음'으로 표시
        depth_info = f"{row['depth']:.1f} km" if row['depth'] is not None else "정보 없음"
        popup_html = f"""
        <b>장소:</b> {row['place']}<br>
        <b>규모:</b> {row['magnitude']:.1f}<br>
        <b>시간:</b> {row['time'].strftime('%Y-%m-%d %H:%M:%S')}<br>
        <b>깊이:</b> {depth_info}<br>
        <b>정보:</b> <a href="{row['url']}" target="_blank">자세히 보기</a>
        """
        # magnitude가 None일 경우 대비 (radius 계산 및 color 결정)
        marker_radius = row['magnitude'] * 2 if row['magnitude'] is not None else 5
        marker_color = get_magnitude_color(row['magnitude'])

        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=marker_radius,
            color=marker_color,
            fill=True,
            fill_color=marker_color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(marker_cluster)

    # Streamlit에 Folium 지도 표시
    # use_container_width=True는 st_folium에서 지원되지 않으므로, width와 height를 직접 설정합니다.
    from streamlit_folium import st_folium
    st_data = st_folium(m, width=1200, height=600) # Removed use_container_width=True

    st.markdown("---")
    st.header("지진 규모 설명")
    st.markdown("""
    지진의 규모(Magnitude)는 지진의 에너지 방출량을 나타내는 척도입니다. 이 척도는 **로그 스케일**을 사용하는데,
    이는 한 단위가 증가할 때마다 지진 에너지 방출량이 약 32배 증가한다는 것을 의미합니다.
    (예: 규모 6의 지진은 규모 5의 지진보다 에너지를 약 32배 더 많이 방출합니다.)
    """)

    # 규모별 정보 테이블
    mag_descriptions = {
        "규모": [
            "~2.0", "2.0~2.9", "3.0~3.9", "4.0~4.9",
            "5.0~5.9", "6.0~6.9", "7.0~7.9", "8.0 이상"
        ],
        "분류": [
            "미진 (Micro)", "약진 (Minor)", "경진 (Minor-Light)", "강진 (Light)",
            "중진 (Moderate)", "대진 (Strong)", "거대 지진 (Major)", "초거대 지진 (Great)"
        ],
        "느껴지는 정도 및 영향": [
            "거의 느껴지지 않음",
            "일부 사람만 느낌",
            "많은 사람이 느낌, 피해 없음",
            "대부분이 느낌, 미미한 피해 가능",
            "부실 건물에 피해 가능",
            "잘 지어진 건물도 중간 피해, 부실 건물은 심각",
            "넓은 지역에 심각한 피해, 인명 피해",
            "광범위한 파괴 및 인명 피해"
        ]
    }
    st.table(pd.DataFrame(mag_descriptions).set_index('규모'))

    st.markdown("---")
    st.header("지진 발생 빈도 통계")
    st.write(f"총 {len(df_earthquakes)} 건의 지진이 발생했습니다.")
    # 'depth' 컬럼이 None 값을 포함할 수 있으므로, .head() 이후에 .fillna() 적용
    st.dataframe(
        df_earthquakes[['place', 'magnitude', 'depth', 'time']]
        .sort_values(by='time', ascending=False)
        .head(10)
        .fillna({'depth': '정보 없음'}), # None 값을 '정보 없음'으로 표시
        use_container_width=True
    )

else:
    st.warning("선택된 필터 조건에 해당하는 지진 데이터가 없습니다. 필터를 조절해 보세요.")

