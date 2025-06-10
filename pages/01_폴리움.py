import streamlit as st
import folium
from folium.plugins import MarkerCluster
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- 1. 앱 기본 설정 ---
st.set_page_config(layout="wide")
st.title("🌎 지진 발생 빈도와 판 구조론 수업")
st.markdown("""
이 수업에서는 Folium 지도를 활용하여 지진 발생 빈도를 시각적으로 탐색하고,
지진의 에너지 전달 및 파동 개념을 이해합니다.
""")

# --- 2. 데이터 로드 함수 ---
@st.cache_data(ttl=3600) # 데이터를 1시간 동안 캐싱하여 API 호출 최소화
def load_earthquake_data(start_date, end_date):
    # USGS API에서 지진 데이터 가져오기
    # 날짜 형식은 YYYY-MM-DD
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={start_date_str}&endtime={end_date_str}&minmagnitude=2"
    
    try:
        response = requests.get(url, timeout=10) # 10초 타임아웃 설정
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생
        data = response.json()
        
        features = data.get('features', [])
        
        earthquakes = []
        for feature in features:
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})
            
            if geometry and geometry.get('coordinates'):
                longitude = geometry['coordinates'][0]
                latitude = geometry['coordinates'][1]
                depth = geometry['coordinates'][2] # 깊이 정보 추가
                
                earthquakes.append({
                    'place': properties.get('place', 'Unknown'),
                    'magnitude': properties.get('mag'),
                    'time': datetime.fromtimestamp(properties.get('time', 0) / 1000), # 밀리초를 초로 변환
                    'latitude': latitude,
                    'longitude': longitude,
                    'depth': depth,
                    'felt': properties.get('felt', 0), # 진도 (사람이 느낀 정도)
                    'tsunami': properties.get('tsunami', 0) # 쓰나미 유발 여부 (0: 아니오, 1: 예)
                })
        
        df = pd.DataFrame(earthquakes)
        # 결측값 처리 (필요에 따라)
        df.dropna(subset=['latitude', 'longitude', 'magnitude'], inplace=True)
        return df
    
    except requests.exceptions.RequestException as e:
        st.error(f"지진 데이터를 불러오는 중 오류가 발생했습니다: {e}")
        return pd.DataFrame() # 빈 데이터프레임 반환

# --- 3. 사이드바 컨트롤 ---
st.sidebar.header("데이터 필터링")
today = datetime.now()
one_month_ago = today - timedelta(days=30)
start_date = st.sidebar.date_input("시작 날짜", value=one_month_ago)
end_date = st.sidebar.date_input("종료 날짜", value=today)

min_mag = st.sidebar.slider("최소 규모", min_value=0.0, max_value=8.0, value=2.0, step=0.1)

# 데이터 로드
st.subheader("📊 지진 데이터 로딩...")
earthquake_df = load_earthquake_data(start_date, end_date)

if not earthquake_df.empty:
    # 규모 필터링 적용
    filtered_df = earthquake_df[earthquake_df['magnitude'] >= min_mag]

    st.success(f"총 {len(filtered_df)} 건의 지진 데이터가 로드되었습니다.")
    st.dataframe(filtered_df[['time', 'place', 'magnitude', 'latitude', 'longitude', 'depth']].head())

    # --- 4. Folium 지도 생성 ---
    st.subheader("🗺️ 지진 발생 지도")
    st.markdown("지진 마커를 클릭하면 상세 정보를 볼 수 있습니다. 마커가 겹쳐 있는 곳은 확대하면 개별 지진을 볼 수 있습니다.")

    # 지도의 초기 중심점 (세계 평균)
    map_center = [filtered_df['latitude'].mean() if not filtered_df.empty else 0, 
                  filtered_df['longitude'].mean() if not filtered_df.empty else 0]
    
    # 지진 데이터가 없는 경우를 대비한 기본 중심점
    if filtered_df.empty:
        map_center = [30, 0] # 대략 지구의 중앙

    m = folium.Map(location=map_center, zoom_start=2, tiles="OpenStreetMap") # 'CartoDB positron', 'Stamen Terrain' 등 다른 타일 사용 가능

    marker_cluster = MarkerCluster().add_to(m)

    # 지진 규모에 따른 색상 및 크기 부여 (에너지 전달 시각화)
    # 규모가 클수록 더 큰 에너지 방출
    def get_marker_color(magnitude):
        if magnitude >= 7.0:
            return 'red'
        elif magnitude >= 6.0:
            return 'orange'
        elif magnitude >= 5.0:
            return 'darkred'
        elif magnitude >= 4.0:
            return 'purple'
        else:
            return 'blue'

    for idx, row in filtered_df.iterrows():
        # 팝업 내용 생성
        popup_html = f"""
        <b>장소:</b> {row['place']}<br>
        <b>규모:</b> {row['magnitude']}<br>
        <b>시간:</b> {row['time'].strftime('%Y-%m-%d %H:%M:%S')}<br>
        <b>위도:</b> {row['latitude']:.2f}°<br>
        <b>경도:</b> {row['longitude']:.2f}°<br>
        <b>깊이:</b> {row['depth']:.2f} km<br>
        <b>느낀 정도:</b> {row['felt']}명<br>
        <b>쓰나미:</b> {'예' if row['tsunami'] == 1 else '아니오'}
        """
        
        # 원의 크기를 지진 규모에 비례하게 설정하여 에너지 크기 시각화
        radius = row['magnitude'] * 2.5 # 스케일 조절 가능

        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=radius,
            color=get_marker_color(row['magnitude']),
            fill=True,
            fill_color=get_marker_color(row['magnitude']),
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(marker_cluster)

    # Streamlit에 Folium 지도 표시
    st_data = st.components.v1.html(folium.Figure().add_child(m).render(), height=500)

    # --- 5. 판 구조론, 에너지 전달, 파동 개념 설명 ---
    st.header("🔬 학습 개념")

    st.subheader("1. 판 구조론과 지진 발생")
    st.markdown("""
    지구의 표면은 여러 개의 거대한 '판'으로 나뉘어 있습니다. 이 판들은 맨틀 대류에 의해 끊임없이 움직이고 있으며,
    판들이 서로 부딪히거나 멀어지거나 스쳐 지나가는 경계에서 대부분의 지진이 발생합니다.
    특히, **수렴형 경계 (Convergent Boundary)** 에서는 판들이 충돌하여 산맥을 형성하거나 한 판이 다른 판 밑으로 들어가는 **섭입대 (Subduction Zone)** 가 형성되며,
    이곳에서 규모가 큰 지진이 자주 발생합니다.

    * **발산형 경계 (Divergent Boundary):** 판들이 멀어지는 곳 (해령)
    * **수렴형 경계 (Convergent Boundary):** 판들이 충돌하는 곳 (섭입대, 산맥)
    * **보존형 경계 (Transform Boundary):** 판들이 스쳐 지나가는 곳 (변환 단층)

    지진 지도를 통해 지진 발생 빈도가 높은 지역이 지구의 판 경계와 일치하는 것을 확인할 수 있습니다.
    """)

    st.subheader("2. 지진의 에너지 전달 (규모와 파동의 관계)")
    st.markdown("""
    지진은 땅이 갑자기 흔들리면서 발생하는 현상으로, 지하의 단층면에서 축적된 에너지가 **지진파**의 형태로 사방으로 방출되는 것입니다.
    지진의 **규모(Magnitude)**는 지진이 방출한 총 에너지의 크기를 나타냅니다. 규모가 1 증가할 때마다 지진의 에너지는 약 32배 증가합니다.
    지도에서 마커의 **크기**와 **색상**은 지진의 규모를 시각적으로 나타냅니다.

    * **작은 규모 지진:** 비교적 적은 에너지를 방출하며, 주변 지역에만 영향을 미칩니다.
    * **큰 규모 지진:** 엄청난 에너지를 방출하며, 광범위한 지역에 큰 피해를 줄 수 있습니다.

    지진파는 에너지를 전달하는 파동의 일종입니다. 물결이 퍼져나가듯이 지진파도 땅속을 통해 사방으로 퍼져나갑니다.
    이 파동은 크게 **실체파(P파, S파)**와 **표면파(Love파, Rayleigh파)**로 나눌 수 있습니다.

    * **P파 (Primary Wave):** 종파로, 고체, 액체, 기체를 모두 통과하며 가장 빠르게 전파됩니다. 지진 발생 시 가장 먼저 도달하여 땅의 상하 운동을 유발합니다.
    * **S파 (Secondary Wave):** 횡파로, 고체만 통과하며 P파보다 느리게 전파됩니다. 땅의 좌우 또는 전후 운동을 유발합니다.
    * **표면파:** 지표면을 따라 전파되며, 실체파보다 속도는 느리지만 지진의 실제 피해를 일으키는 주된 파동입니다.

    지진의 에너지는 파동을 통해 멀리까지 전달될 수 있으며, 지진파의 속도와 진폭은 주변 지질 환경에 따라 달라질 수 있습니다.
    규모가 큰 지진은 더 강한 진폭의 파동을 발생시켜 더 넓은 지역에 영향을 미칩니다.

    """)
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Tectonic_plates_boundaries.png/800px-Tectonic_plates_boundaries.png", 
             caption="세계 판 경계 (출처: 위키미디어 커먼즈)", use_column_width=True)
    st.markdown("[세계 판 경계 지도 출처: Wikipedia](https://commons.wikimedia.org/wiki/File:Tectonic_plates_boundaries.png)")

    st.info("참고: 위에 표시된 지진 데이터는 USGS에서 제공하는 정보이며, 실시간으로 업데이트될 수 있습니다.")

else:
    st.warning("선택된 기간에 해당하는 지진 데이터가 없습니다. 날짜 범위를 조정해 보세요.")

st.sidebar.markdown("---")
st.sidebar.markdown("© 2025 지진 학습 앱")
