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

    # USGS Earthquake Hazards Program API
    # 지난 N일간 특정 규모 이상 지진 데이터
    # GeoJSON 형식으로 요청
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={start_time.strftime('%Y-%m-%d')}&endtime={end_time.strftime('%Y-%m-%d')}&minmagnitude={min_magnitude}"

    try:
        response = requests.get(url)
        response.raise_for_status() # HTTP 오류 발생 시 예외 처리
        data = response.json()

        features = data['features']
        earthquakes = []
        for feature in features:
            props = feature['properties']
            geo = feature['geometry']
            if geo and geo['coordinates']:
                earthquakes.append({
                    'place': props['place'],
                    'magnitude': props['mag'],
                    'time': datetime.datetime.fromtimestamp(props['time']/1000), # 밀리초를 초로 변환
                    'longitude': geo['coordinates'][0],
                    'latitude': geo['coordinates'][1],
                    'depth': props['depth'],
                    'url': props['url']
                })
        return pd.DataFrame(earthquakes)
    except requests.exceptions.RequestException as e:
        st.error(f"지진 데이터를 불러오는 데 실패했습니다: {e}")
        return pd.DataFrame()

# --- 지진 규모별 색상 및 설명 ---
def get_magnitude_color(magnitude):
    if magnitude >= 8.0:
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
    else:
        return 'lightblue' # 2.5 이상

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
    map_center_lat = df_earthquakes['latitude'].mean()
    map_center_lon = df_earthquakes['longitude'].mean()
    m = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=2, control_scale=True)

    # 마커 클러스터 추가
    marker_cluster = MarkerCluster().add_to(m)

    for idx, row in df_earthquakes.iterrows():
        popup_html = f"""
        **장소:** {row['place']}<br>
        **규모:** {row['magnitude']:.1f}<br>
        **시간:** {row['time'].strftime('%Y-%m-%d %H:%M:%S')}<br>
        **깊이:** {row['depth']:.1f} km<br>
        **정보:** <a href="{row['url']}" target="_blank">자세히 보기</a>
        """
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=row['magnitude'] * 2, # 규모가 클수록 원 크기 크게
            color=get_magnitude_color(row['magnitude']),
            fill=True,
            fill_color=get_magnitude_color(row['magnitude']),
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(marker_cluster)

    # Streamlit에 Folium 지도 표시
    st_data = st_folium(m, width=1200, height=600, use_container_width=True)

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
    st.dataframe(df_earthquakes[['place', 'magnitude', 'depth', 'time']].sort_values(by='time', ascending=False).head(10), use_container_width=True)

else:
    st.warning("선택된 필터 조건에 해당하는 지진 데이터가 없습니다. 필터를 조절해 보세요.")

st.markdown("---")
st.header("📝 수업 아이디어: 지진, 에너지 전달, 파동")

st.markdown("""
### 1. 판 구조론 (Plate Tectonics) 시각화
* **활동:** 지도를 보면서 학생들이 지진이 주로 발생하는 지역(환태평양 조산대, 알프스-히말라야 조산대 등)을 찾아보게 합니다.
* **설명:** 이 지역들이 지구의 거대한 지각판(판)들이 서로 만나고, 미끄러지고, 충돌하는 경계임을 설명합니다. 지진은 이러한 판들의 움직임 때문에 발생하는 에너지 방출 현상임을 강조합니다.
    * **발산형 경계 (Divergent Plate Boundary):** 판이 서로 멀어지는 곳 (예: 대서양 중앙 해령)
    * **수렴형 경계 (Convergent Plate Boundary):** 판이 서로 가까워지는 곳 (예: 일본 해구, 히말라야 산맥)
    * **보존형 경계 (Transform Plate Boundary):** 판이 서로 스쳐 지나가는 곳 (예: 산 안드레아스 단층)

### 2. 지진과 에너지 전달 (Energy Transfer)
* **활동:** 규모별 색깔과 크기가 다른 원형 마커를 통해 지진의 '크기'를 시각적으로 보여줍니다.
* **설명:** 지진은 땅속에 축적된 에너지가 한순간에 방출되면서 발생합니다. 이 에너지는 지진파(Seismic Waves)라는 형태로 사방으로 퍼져나갑니다. 규모가 큰 지진일수록 더 많은 에너지를 방출하고, 더 강한 파동을 일으켜 더 넓은 지역에 영향을 미칩니다. (수업에서 설명한 **로그 스케일**을 다시 언급)

### 3. 지진파와 파동 (Waves) 개념
* **개념 설명:**
    * **P파 (Primary Wave):** 종파(압축파). 빠르고 고체, 액체, 기체를 모두 통과합니다. 가장 먼저 도달합니다.
    * **S파 (Secondary Wave):** 횡파(전단파). P파보다 느리고 고체만 통과합니다.
    * **표면파 (Surface Wave):** 지구 표면을 따라 이동하며 가장 큰 피해를 유발하는 파동입니다.
* **비유:**
    * 돌을 물에 던졌을 때 생기는 물결 (파동)과 비교하여 지진파가 어떻게 퍼져나가는지 설명합니다.
    * 용수철을 밀거나 당겼을 때(P파)와 흔들었을 때(S파)의 움직임을 시연하여 종파와 횡파의 차이를 이해시킵니다.
    * 지진 규모가 클수록 진동이 더 크게, 더 멀리 느껴지는 것을 통해 에너지와 파동의 관계를 설명합니다.

### 4. 깊이에 따른 영향
* **활동:** 지진 데이터 테이블에서 '깊이(Depth)' 정보를 확인하게 합니다.
* **설명:** 얕은 깊이에서 발생하는 지진(천발지진)은 에너지가 지표면으로 직접 전달되어 더 큰 피해를 유발할 수 있습니다. 깊은 곳에서 발생하는 지진(심발지진)은 에너지가 지표면에 도달하기 전에 분산되어 상대적으로 피해가 적을 수 있습니다.

### 5. 토론 및 질문
* **활동:** "왜 특정 지역에 지진이 자주 발생할까요?", "지진이 발생했을 때 에너지는 어떻게 전달되어 우리에게 느껴질까요?" 등의 질문을 통해 학생들의 이해도를 점검하고 토론을 유도합니다.
""")

st.markdown("---")
st.markdown("**데이터 출처:** [USGS Earthquake Hazards Program](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php)")
