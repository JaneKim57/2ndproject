import streamlit as st
import numpy as np
import plotly.graph_objects as go

# 타이틀
st.title("🎯 포물선 운동 시뮬레이터")

# 사용자 입력
initial_speed = st.slider("초기 속도 (m/s)", 1, 100, 30)
angle_deg = st.slider("발사 각도 (도)", 0, 90, 45)
g = 9.81  # 중력 가속도

# 각도 라디안으로 변환
angle_rad = np.radians(angle_deg)

# 시간, 최대 도달 시간 계산
t_flight = 2 * initial_speed * np.sin(angle_rad) / g
t = np.linspace(0, t_flight, num=300)

# 운동 방정식
x = initial_speed * np.cos(angle_rad) * t
y = initial_speed * np.sin(angle_rad) * t - 0.5 * g * t**2

# Plotly 그래프
fig = go.Figure()
fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name='운동 궤적'))
fig.update_layout(
    xaxis_title='거리 (m)',
    yaxis_title='높이 (m)',
    title='포물선 운동 궤적',
    showlegend=False,
    height=500
)

# 최대 높이, 사거리, 비행 시간 계산
max_height = (initial_speed**2) * (np.sin(angle_rad)**2) / (2 * g)
range_ = (initial_speed**2) * np.sin(2 * angle_rad) / g

# 결과 출력
st.plotly_chart(fig)
st.subheader("📊 결과")
st.markdown(f"- **최대 높이**: {max_height:.2f} m")
st.markdown(f"- **도달 거리**: {range_:.2f} m")
st.markdown(f"- **비행 시간**: {t_flight:.2f} s")

