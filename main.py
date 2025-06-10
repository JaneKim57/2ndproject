import streamlit as st
import folium
from streamlit_folium import st_folium

# 페이지 기본 설정
st.set_page_config(page_title="캘리포니아 여행 가이드", layout="wide")

st.title("🌴 캘리포니아 여행 가이드")

# 상단 GIF 추가 (즐겁게 달리는 강아지 GIF)
st.image("http://googleusercontent.com/image_collection/image_retrieval/2792857878627952875", use_container_width=True, caption="귀여운 강아지와 함께 즐거운 여행을 시작해 볼까요?")

st.markdown("""
캘리포니아는 아름다운 자연과 도시 문화가 공존하는 미국 최고의 여행지입니다.
아래에서 명소, 지도, 호텔/식당 정보, 그리고 검색 필터를 확인해 보세요.
""")

# 관광지 데이터 정의 (모든 이미지 링크를 한 줄로, 닫는 따옴표 확인)
places = [
    {
        "name": "금문교 (Golden Gate Bridge)",
        "location": (37.8199, -122.4783),
        "description": "샌프란시스코의 상징적인 붉은 현수교. 멋진 전망과 사진 명소로 유명합니다.",
        "image": "http://googleusercontent.com/image_collection/image_retrieval/12811980171929845623",
        "city": "샌프란시스코",
        "hotels": ["Hotel Nikko", "Fairmont SF"],
        "food": ["Boudin Bakery", "Tartine Bakery"]
    },
    {
        "name": "요세미티 국립공원 (Yosemite National Park)",
        "location": (37.8651, -119.5383),
        "description": "절경의 폭포, 바위, 숲이 있는 미국 최고의 국립공원 중 하나입니다.",
        "image": "http://googleusercontent.com/image_collection/image_retrieval/7701363284168280550",
        "city": "요세미티",
        "hotels": ["The Ahwahnee", "Yosemite Valley Lodge"],
        "food": ["Degnan's Kitchen", "The Mountain Room"]
    },
    {
        "name": "디즈니랜드 (Disneyland)",
        "location": (33.8121, -117.9190),
        "description": "세계 최초 디즈니 테마파크로 가족 여행에 최적입니다.",
        "image": "http://googleusercontent.com/image_collection/image_retrieval/6728884052599063633",
        "city": "애너하임",
        "hotels": ["Disneyland Hotel", "Best Western Plus Park Place"],
        "food": ["Blue Bayou", "Plaza Inn"]
    },
    {
        "name": "산타모니카 피어 (Santa Monica Pier)",
        "location": (34.0094, -118.4973),
        "description": "놀이공원, 레스토랑, 바다가 어우러진 활기찬 부두입니다.",
        "image": "http://googleusercontent.com/image_collection/image_retrieval/3926574581861087751",
        "city": "로스앤젤레스",
        "hotels": ["Shutters on the Beach", "Loews Santa Monica"],
        "food": ["The Lobster", "Blue Plate Taco"]
    },
    {
        "name": "할리우드 사인 (Hollywood Sign)",
        "location": (34.1341, -118.3215),
        "description": "로스앤젤레스 언덕 위에 위치한 세계적인 상징물입니다.",
        "image": "http://googleusercontent.com/image_collection/image_retrieval/14861853874461514626",
        "city": "로스앤젤레스",
        "hotels": ["Hollywood Roosevelt", "Dream Hollywood"],
        "food": ["Musso & Frank Grill", "In-N-Out Burger"]
    },
    {
        "name": "빅서 (Big Sur)",
        "location": (36.3615, -121.8563),
        "description": "장대한 해안 절벽과 드라이브 코스로 유명한 절경 지역입니다.",
        "image": "http://googleusercontent.com/image_collection/image_retrieval/8827568600891187301",
        "city": "빅서",
        "hotels": ["Post Ranch Inn", "Ventana Big Sur"],
        "food": ["Nepenthe", "Big Sur Bakery"]
    },
    {
        "name": "타호 호수 (Lake Tahoe)",
        "location": (39.0968, -120.0324),
        "description": "여름엔 수상스포츠, 겨울엔 스키로 유명한 다용도 휴양지입니다.",
        "image": "http://googleusercontent.com/image_collection/image_retrieval/4590479594125388461",
        "city": "타호",
        "hotels": ["The Ritz-Carlton", "Edgewood Tahoe"],
        "food": ["Base Camp Pizza", "The Boathouse on the Pier"]
    },
    {
        "name": "샌디에이고 동물원 (San Diego Zoo)",
        "location": (32.7353, -117.1490),
        "description": "세계적인 규모와 다양한 동물종을 자랑하는 샌디에이고 동물원입니다.",
        "image": "http://googleusercontent.com/image_collection/image_retrieval/8309596567328073649",
        "city": "샌디에이고",
        "hotels": ["Hotel del Coronado", "Pendry San Diego"],
        "food": ["The Prado", "Hodad's"]
    },
    {
        "name": "데스 밸리 국립공원 (Death Valley National Park)",
        "location": (36.5054, -117.0794),
        "description": "미국에서 가장 건조하고 뜨거운 국립공원입니다. 지형이 매우 독특합니다.",
        "image": "http://googleusercontent.com/image_collection/image_retrieval/3347876852439818039",
        "city": "데스 밸리",
        "hotels": ["The Oasis at Death Valley", "Panamint Springs Resort"],
        "food": ["Timbisha Tacos", "Badwater Saloon"]
    },
    {
        "name": "나파 밸리 (Napa Valley)",
        "location": (38.5025, -122.2654),
        "description": "세계적으로 유명한 와인 산지로 고급 와이너리 투어가 가능합니다.",
        "image": "http://googleusercontent.com/image_collection/image_retrieval/2679799718701777949",
        "city": "나파",
        "hotels": ["Auberge du Soleil", "Carneros Resort"],
        "food": ["Bouchon Bistro", "The French Laundry"]
    }
]

# 지역 필터
cities = sorted(list(set([place["city"] for place in places])))
selected_city = st.selectbox("🔎 도시 필터", ["전체 보기"] + cities)

# 지도 초기화
m = folium.Map(location=[36.7783, -119.4179], zoom_start=6)

# 마커 추가
for place in places:
    if selected_city != "전체 보기" and place["city"] != selected_city:
        continue
    folium.Marker(
        location=place["location"],
        popup=place["name"],
        tooltip=place["name"]
    ).add_to(m)

# 지도 표시
st.subheader("🗺️ 관광지 지도")
st_data = st_folium(m, width=700, height=500)

# 장소 상세 출력
st.subheader("📍 관광지 상세 안내")
for place in places:
    if selected_city != "전체 보기" and place["city"] != selected_city:
        continue
    st.markdown(f"### {place['name']}")
    st.image(place["image"], use_container_width=True)
    st.markdown(place["description"])
    st.markdown(f"**🏨 추천 숙소:** {', '.join(place['hotels'])}")
    st.markdown(f"**🍽️ 추천 음식점:** {', '.join(place['food'])}")
    st.markdown("---")
