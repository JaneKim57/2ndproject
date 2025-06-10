import streamlit as st
import folium
from streamlit_folium import st_folium

# 페이지 기본 설정
st.set_page_config(page_title="캘리포니아 관광 가이드", layout="wide")

st.title("🌴 캘리포니아 주요 관광지 가이드")
st.markdown("""
캘리포니아는 아름다운 해변, 세계적인 관광지, 다양한 문화로 가득한 미국 서부의 보석입니다.  
아래는 캘리포니아에서 꼭 가봐야 할 명소들을 소개합니다. 지도를 통해 각 위치를 직접 확인할 수 있어요!
""")

# 관광지 정보
places = [
    {
        "name": "Golden Gate Bridge",
        "location": (37.8199, -122.4783),
        "description": "샌프란시스코의 상징적인 붉은 현수교. 멋진 전망과 사진 명소로 유명합니다.",
        "image": "https://upload.wikimedia.org/wikipedia/commons/0/0c/GoldenGateBridge-001.jpg"
    },
    {
        "name": "Yosemite National Park",
        "location": (37.8651, -119.5383),
        "description": "절경의 폭포, 바위, 숲이 있는 미국 최고의 국립공원 중 하나입니다.",
        "image": "https://upload.wikimedia.org/wikipedia/commons/6/60/Yosemite_Valley_from_Wawona_Tunnel_view%2C_California%2C_USA_-_Diliff.jpg"
    },
    {
        "name": "Disneyland",
        "location": (33.8121, -117.9190),
        "description": "애너하임에 위치한 세계 최초의 디즈니 테마파크로 가족 여행에 최적입니다.",
        "image": "https://upload.wikimedia.org/wikipedia/commons/3/3d/Disneyland_Sleeping_Beauty_Castle.jpg"
    },
    {
        "name": "Santa Monica Pier",
        "location": (34.0094, -118.4973),
        "description": "놀이공원, 레스토랑, 바다가 어우러진 활기찬 부두입니다.",
        "image": "https://upload.wikimedia.org/wikipedia/commons/1/1f/Santa_Monica_Pier_-_from_beach.jpg"
    }
]

# 지도 초기화
m = folium.Map(location=[36.7783, -119.4179], zoom_start=6)

# 마커 추가
for place in places:
    folium.Marker(
        location=place["location"],
        popup=place["name"],
        tooltip=place["name"]
    ).add_to(m)

# 지도 표시
st.subheader("🗺️ 관광지 지도 보기")
st_data = st_folium(m, width=700, height=500)

# 각 장소 정보 출력
st.subheader("📍 상세 관광지 안내")
for place in places:
    with st.container():
        st.markdown(f"### {place['name']}")
        st.image(place["image"], width=600)
        st.markdown(place["description"])
        st.markdown("---")
