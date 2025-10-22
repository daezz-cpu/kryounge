import streamlit as st

st.set_page_config(page_title="나의 첫 Streamlit 앱", page_icon=":rocket:")

st.title("안녕하세요, Streamlit!")

st.write("""
이것은 제가 만든 첫 번째 Streamlit 애플리케이션입니다.
왼쪽 사이드바에서 다양한 위젯을 사용하여 상호작용할 수 있습니다.
""")

st.header("데모 섹션")

# 텍스트 입력
user_input = st.text_input("당신의 이름은 무엇인가요?", "이름")
st.write(f"안녕하세요, {user_input}님!")

# 슬라이더
age = st.slider("당신의 나이는?", 0, 100, 25)
st.write(f"당신은 {age}세입니다.")

# 체크박스
if st.checkbox("데이터 보기"):
    st.write("일부 데이터가 여기에 표시됩니다.")
    st.dataframe({"컬럼 A": [1, 2, 3], "컬럼 B": [4, 5, 6]})

# 버튼
if st.button("인사하기"):
    st.write("만나서 반갑습니다!")

st.sidebar.header("사이드바 위젯")
st.sidebar.text_input("사이드바 입력", "기본값")
st.sidebar.selectbox("선택 상자", ["옵션 1", "옵션 2", "옵션 3"])

st.subheader("이미지 추가")
st.image("https://www.streamlit.io/images/brand/streamlit-logo-light.svg", caption="Streamlit 로고")

st.markdown("---")
st.write("© 2025 나의 첫 Streamlit 앱")
