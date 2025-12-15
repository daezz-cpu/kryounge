import streamlit as st
import pandas as pd
import plotly.express as px
import random
import time
import google.generativeai as genai

# -----------------------------------------------------------------------------------------
# [Setup] 페이지 설정 (반드시 가장 먼저 호출되어야 함)
# -----------------------------------------------------------------------------------------

# -----------------------------------------------------------------------------------------
# [Setup] 페이지 설정
# -----------------------------------------------------------------------------------------
st.set_page_config(page_title="현명한 꼬마 시장님", layout="wide", page_icon="🏙️")

# -----------------------------------------------------------------------------------------
# [Helper Functions] 공통 함수 & 세션 초기화
# -----------------------------------------------------------------------------------------
def init_game():
    # 1. 예산 및 진행 상태
    if 'budget' not in st.session_state:
        st.session_state.budget = 0
    if 'step1_status' not in st.session_state:
        st.session_state.step1_status = False  # 1단계 완료 여부
    if 'step2_status' not in st.session_state:
        st.session_state.step2_status = False  # 2단계 완료 여부
        
    # 2. 게임 데이터
    if 'stats' not in st.session_state:
        st.session_state.stats = {'😊행복': 50, '🌳환경': 50, '🛡️안전': 50, '💰경제': 50}
    if 'turns' not in st.session_state:
        st.session_state.turns = 5
    if 'solved_problems' not in st.session_state:
        st.session_state.solved_problems = [] # 해결한 문제 ID 리스트
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    if 'game_over' not in st.session_state:
        st.session_state.game_over = False
        
    # 3. 임시 UI 상태
    if 'news_title' not in st.session_state:
        st.session_state.news_title = ""
    if 'news_category' not in st.session_state:
        st.session_state.news_category = "교통"

def reset_game():
    st.session_state.budget = 0
    st.session_state.step1_status = False
    st.session_state.step2_status = False
    st.session_state.stats = {'😊행복': 50, '🌳환경': 50, '🛡️안전': 50, '💰경제': 50}
    st.session_state.turns = 5
    st.session_state.solved_problems = []
    st.session_state.logs = []
    st.session_state.game_over = False

# 문제 데이터 (ID, 제목, 설명, 선택지)
problems = [
    {
        "id": 1, "title": "스쿨존 주차난", 
        "desc": "학교 앞 스쿨존에 불법 주차된 차들이 너무 많아요. 아이들이 위험해요!",
        "A": {"label": "튼튼한 펜스 설치 (15코인)", "cost": 15, "effect": {"🛡️안전": 20, "💰경제": -5}, "msg": "안전해졌지만 상인들은 불만이에요."},
        "B": {"label": "공영 주차장 건설 (45코인)", "cost": 45, "effect": {"💰경제": 15, "😊행복": 10}, "msg": "주차는 편해졌지만 예산이 많이 들었어요."}
    },
    {
        "id": 2, "title": "쓰레기 악취", 
        "desc": "골목길에 쓰레기가 쌓여서 냄새가 심해요!",
        "A": {"label": "예쁜 쓰레기통 설치 (5코인)", "cost": 5, "effect": {"🌳환경": 10, "😊행복": -5}, "msg": "깨끗해졌지만 집 앞 설치를 반대하네요."},
        "B": {"label": "CCTV 감시 카메라 (25코인)", "cost": 25, "effect": {"🛡️안전": 10, "🌳환경": 10}, "msg": "쓰레기는 줄었지만 감시받는 기분이래요."}
    },
    {
        "id": 3, "title": "낡은 놀이터", 
        "desc": "놀이터 기구가 낡아서 아이들이 놀 곳이 없어요.",
        "A": {"label": "워터파크 개조 (35코인)", "cost": 35, "effect": {"😊행복": 30, "🌳환경": -10}, "msg": "아이들은 신났지만 소음 신고가 들어왔어요."},
        "B": {"label": "어린이 도서관 (15코인)", "cost": 15, "effect": {"😊행복": 10, "💰경제": 5}, "msg": "조용해서 좋지만 뛰어놀고 싶은 아이들은 심심해요."}
    },
    {
        "id": 4, "title": "길고양이 갈등", 
        "desc": "배고픈 고양이 울음소리 때문에 이웃 간 다툼이 있어요.",
        "A": {"label": "고양이 급식소 (5코인)", "cost": 5, "effect": {"😊행복": 10, "🌳환경": -5}, "msg": "싸움은 줄었지만 고양이가 더 모였어요."},
        "B": {"label": "중성화 수술 지원 (25코인)", "cost": 25, "effect": {"🌳환경": 15}, "msg": "장기적으로 개체 수가 조절될 거예요."}
    },
    {
        "id": 5, "title": "어두운 밤길", 
        "desc": "가로등이 없어서 밤에 다니기가 너무 무서워요.",
        "A": {"label": "강력 LED 설치 (15코인)", "cost": 15, "effect": {"🛡️안전": 20, "🌳환경": -5}, "msg": "밝아졌지만 빛 공해로 잠을 설친대요."},
        "B": {"label": "자율 방범대 운영 (35코인)", "cost": 35, "effect": {"🛡️안전": 15, "💰경제": 10}, "msg": "일자리는 늘었지만 인건비가 계속 나가요."}
    },
    {
        "id": 6, "title": "공장 매연", 
        "desc": "공장에서 나오는 연기 때문에 공기가 탁해요.",
        "A": {"label": "친환경 필터 지원 (30코인)", "cost": 30, "effect": {"🌳환경": 25, "😊행복": 10}, "msg": "공기는 맑아졌지만 예산 출혈이 커요."},
        "B": {"label": "공장 가동 제한 (0코인)", "cost": 0, "effect": {"💰경제": -20, "🌳환경": 15}, "msg": "공기는 좋아졌지만 공장 수익이 줄었어요."}
    },
    {
        "id": 7, "title": "버스 배차 불편", 
        "desc": "버스가 너무 안 와서 학교 가기가 힘들어요.",
        "A": {"label": "버스 증차 (40코인)", "cost": 40, "effect": {"😊행복": 25, "💰경제": 5}, "msg": "편해졌지만 유지비가 엄청나요!"},
        "B": {"label": "행복 택시 쿠폰 (10코인)", "cost": 10, "effect": {"😊행복": 10}, "msg": "급한 불은 껐지만 근본 해결책은 아니에요."}
    }
]

# -----------------------------------------------------------------------------------------
# [App Start]
# -----------------------------------------------------------------------------------------
init_game()

# [Sidebar]
with st.sidebar:
    st.title(f"💰 현재 예산: {st.session_state.budget} 코인")
    st.divider()
    
    st.subheader("✅ 진행 상황")
    chk1 = "✅" if st.session_state.step1_status else "⬜"
    chk2 = "✅" if st.session_state.step2_status else "⬜"
    chk3 = "✅" if st.session_state.solved_problems else "⬜" # 게임 시작하면 체크
    
    st.write(f"{chk1} 1단계: 뉴스룸")
    st.write(f"{chk2} 2단계: 정책 연구소")
    st.write(f"{chk3} 3단계: 꼬마 시장님")
    
    st.divider()
    st.subheader("📊 우리 마을 상태")
    
    # Radar Chart
    df_stats = pd.DataFrame(dict(
        r=list(st.session_state.stats.values()),
        theta=list(st.session_state.stats.keys())
    ))
    fig = px.line_polar(df_stats, r='r', theta='theta', line_close=True, range_r=[0, 100])
    fig.update_traces(fill='toself')
    st.plotly_chart(fig, use_container_width=True)


st.title("🏙️ 우리 지역 문제를 찾아 현명하게 해결해보자!")
tab1, tab2, tab3 = st.tabs(["📰 1단계: 뉴스룸", "💡 2단계: 정책 연구소", "🏛️ 3단계: 꼬마 시장님"])


# -----------------------------------------------------------------------------------------
# [Tab 1] 뉴스룸
# -----------------------------------------------------------------------------------------
with tab1:
    st.header("📰 우리 동네에 무슨 일이?!")
    
    # Step 1-1. Search
    st.subheader("Step 1. 리얼 월드 탐색")
    st.info("🕵️‍♂️ 먼저 우리 지역의 뉴스를 찾아보고 오세요!")
    
    col_link, col_input = st.columns([1, 2])
    with col_link:
        st.write("")
        st.link_button("🔍 네이버에서 검색하기", "https://search.naver.com/search.naver?query=우리동네+문제점")
        
    with col_input:
        title_in = st.text_input("기사 제목을 입력하세요", value=st.session_state.news_title)
        cat_in = st.selectbox("어떤 분야인가요?", ["교통", "환경", "안전", "기타"], index=["교통", "환경", "안전", "기타"].index(st.session_state.news_category))
        
        if st.button("📝 기사 등록"):
            if len(title_in) > 1:
                st.session_state.news_title = title_in
                st.session_state.news_category = cat_in
                st.success("기사가 등록되었습니다! 아래 인터뷰를 진행하세요.")
            else:
                st.warning("제목을 입력해주세요.")
                
    st.divider()
    
    # Step 1-2. Chatbot
    st.subheader("Step 2. 가상 주민 인터뷰")
    if st.session_state.news_title:
        # 캐릭터 설정
        personas = {
            "교통": {"name": "🎒 등굣길 아이", "msg": "시장님! 차들이 너무 쌩쌩 달려서 무서워요."},
            "환경": {"name": "🧹 청소부 아저씨", "msg": "쓰레기가 너무 많아서 치워도 끝이 없어요."},
            "안전": {"name": "👮 경찰관", "msg": "어두운 골목길에서 사고가 자주 납니다."}
        }
        persona = personas.get(st.session_state.news_category, {"name": "🙋 민원인", "msg": "우리 동네 문제를 해결해주세요!"})
        
        st.chat_message("assistant", avatar="👤").write(f"**{persona['name']}**: {persona['msg']}")
        
        user_input = st.text_input("주민에게 건넬 위로의 말을 적어주세요.", key="chat_tab1")
        if user_input:
            reply = "시장님... 제발 저희 이야기를 들어주세요."
            if any(k in user_input for k in ["안녕", "반가", "하이"]):
                reply = "네 안녕하세요 시장님! 바쁘신데 와주셔서 감사합니다."
            elif any(k in user_input for k in ["왜", "이유", "원인", "뭐"]):
                reply = f"그게요, '{st.session_state.news_title}' 문제 때문에 다들 난리도 아니에요."
            elif any(k in user_input for k in ["해결", "약속", "도와", "고쳐"]):
                reply = "정말인가요? 시장님만 믿겠습니다! 꼭 해결해주셔야 해요!"
            
            st.chat_message("user").write(user_input)
            st.chat_message("assistant", avatar="👤").write(reply)
            
        if st.button("✅ 취재 완료 (코인 받기)"):
            if not st.session_state.step1_status:
                st.session_state.budget += 40
                st.session_state.step1_status = True
                st.balloons()
                st.success("취재비 40코인을 받았습니다! (정책 연구소로 이동하세요)")
            else:
                st.info("이미 예산을 수령했습니다.")
    else:
        st.caption("위에서 기사를 먼저 등록해주세요.")

# -----------------------------------------------------------------------------------------
# [Tab 2] 정책 연구소
# -----------------------------------------------------------------------------------------
with tab2:
    st.header("💡 정책 아이디어 연구소")
    st.write("해결책을 제안하고 예산을 확보하세요!")
    
    idea_in = st.text_area("나만의 아이디어를 적어주세요. (구체적일수록 예산이 많아요!)", height=100)
    
    if st.button("🤖 AI 심사 받기"):
        if not st.session_state.step2_status:
            score_acc = 20
            tier = "C"
            
            # Keywords
            tier_a = ['캠페인', '홍보', '포스터', '교육', '약속', '규칙', '지킴이']
            tier_b = ['설치', '건설', '만들', 'CCTV', '주차장', '가로등', '구매']
            
            if any(k in idea_in for k in tier_a):
                score_acc = 60
                tier = "A"
                msg = "🌟 [최우수 정책] 사람들의 생각을 바꾸는 멋진 아이디어예요!"
            elif any(k in idea_in for k in tier_b):
                score_acc = 40
                tier = "B"
                msg = "👍 [우수 정책] 필요한 시설을 만드는 좋은 방법이네요."
            else:
                msg = "🤔 [노력 정책] 조금 더 구체적인 해결책을 고민해볼까요?"

            st.session_state.budget += score_acc
            st.session_state.step2_status = True
            
            st.info(f"심사 결과: {msg}")
            st.metric("확보한 예산", f"+{score_acc} 코인")
            st.balloons()
        else:
            st.warning("이미 정책 지원금을 받았습니다. 3단계로 이동하세요!")

# -----------------------------------------------------------------------------------------
# [Tab 3] 꼬마 시장님
# -----------------------------------------------------------------------------------------
with tab3:
    st.header("🏛️ 꼬마 시장님 시뮬레이션")
    
    # 1. 입장 조건 체크
    if not (st.session_state.step1_status and st.session_state.step2_status):
        st.error("🚨 뉴스룸과 정책 연구소 단계를 먼저 완료하고 오세요!")
        st.stop()
        
    # 2. 엔딩 조건 체크 (턴 종료 or 모든 문제 해결)
    available_problems = [p for p in problems if p['id'] not in st.session_state.solved_problems]
    
    if st.session_state.turns <= 0 or not available_problems:
        st.balloons()
        st.success("🎓 시장님의 임기가 끝났습니다! 수고하셨습니다.")
        
        # 성적표
        final_score = sum(st.session_state.stats.values())
        if final_score >= 300:
            grade = "🏆 전설의 시장님! (완벽해요)"
        elif final_score >= 200:
            grade = "🎖️ 훌륭한 시장님! (잘했어요)"
        else:
            grade = "🌱 노력하는 시장님! (조금 더 힘내요)"
            
        st.subheader(f"당신의 등급: {grade}")
        st.write("정답은 없습니다. 이웃을 생각하며 고민하는 과정이 바로 민주주의입니다.")
        
        if st.button("🔄 게임 다시 하기"):
            reset_game()
            st.rerun()
            
    else:
        st.metric("남은 기회", f"{st.session_state.turns}번")
        
        # 3. 문제 선택 (Selectbox에 해결 안 된 것만 표시)
        p_titles = [p['title'] for p in available_problems]
        choice = st.selectbox("해결할 문제를 선택하세요:", p_titles)
        
        # 선택된 문제 데이터 찾기
        selected_p = next((p for p in available_problems if p['title'] == choice), None)
        
        if selected_p:
            st.subheader(f"Q. {selected_p['title']}")
            st.write(selected_p['desc'])
            
            c1, c2 = st.columns(2)
            
            # Action Button Logic
            def run_choice(opt):
                cost = selected_p[opt]['cost']
                effects = selected_p[opt]['effect']
                
                if st.session_state.budget >= cost:
                    # Execute
                    st.session_state.budget -= cost
                    st.session_state.turns -= 1
                    st.session_state.solved_problems.append(selected_p['id'])
                    
                    # Update Stats
                    for k, v in effects.items():
                        st.session_state.stats[k] = max(0, min(100, st.session_state.stats[k] + v))
                    
                    # Log
                    st.session_state.logs.append(f"{selected_p['title']} ({opt}안) 해결!")
                    
                    st.toast(selected_p[opt]['msg'], icon="🎉")
                    time.sleep(1) # 토스트 메시지 볼 시간 줌
                    st.rerun() # 화면 갱신 (선택한 문제 목록에서 제거)
                else:
                    st.error("예산이 부족합니다! 다른 방법을 찾거나 뉴스룸에서 예산을 더 구해오세요.")

            with c1:
                st.info(selected_p["A"]["label"])
                if st.button("🅰️ 선택 (A안)", key=f"btn_a_{selected_p['id']}"):
                    run_choice("A")
            
            with c2:
                st.warning(selected_p["B"]["label"])
                if st.button("🅱️ 선택 (B안)", key=f"btn_b_{selected_p['id']}"):
                    run_choice("B")
