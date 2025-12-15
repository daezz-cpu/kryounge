import streamlit as st
import pandas as pd
import plotly.express as px
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
def get_ai_response(prompt):
    """
    Gemini AI에게 응답을 요청합니다.
    실패 시 사용 가능한 모델 리스트를 확인하여 에러 메시지에 표시합니다.
    """
    if "GEMINI_API_KEY" not in st.secrets:
        return "🔑 API 키가 설정되지 않았어요."

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # 시도할 모델 목록 (사용 가능한 모델 우선)
    candidate_models = [
        'gemini-2.5-flash', 
        'gemini-2.0-flash', 
        'gemini-2.5-pro', 
        'gemini-1.5-flash', 
        'gemini-pro'
    ]
    
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception:
            continue
            
    # 모든 모델 실패 시 디버깅 정보 출력
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return f"🤖 AI 연결 실패. (사용 가능한 모델: {available_models})\nAPI 키 권한이나 지역 설정을 확인해주세요."
    except Exception as e:
        return f"🤖 AI 치명적 오류: 모델 목록을 가져올 수 없습니다. ({e})\nAPI 키가 올바른지 확인해주세요."

def analyze_persona_from_title(title):
    """
    기사 제목을 분석하여 적절한 페르소나를 추천합니다.
    """
    prompt = (
        f"Analyze the following news title and categorize it into one of these categories: "
        f"['Traffic', 'Environment', 'Safety', 'Economy', 'Other']. "
        f"Return ONLY the category name.\n\n"
        f"News Title: {title}"
    )
    category = get_ai_response(prompt).strip().replace("'", "").replace('"', "")
    
def evaluate_policy_with_ai(idea, problem_context):
    """
    정책 아이디어를 AI가 평가합니다 (현실성, 효율성, 창의성).
    점수(0-100), 좋은 점, 보완할 점을 반환합니다.
    """
    prompt = (
        f"Context: {problem_context}\n"
        f"Policy Idea: {idea}\n\n"
        f"Evaluate this policy idea based on Reality, Efficiency, and Creativity. "
        f"If the idea is perfect, you don't need to provide 'IMPROVE'. "
        f"Return the response in the following format ONLY:\n"
        f"SCORE: [0-100 integer]\n"
        f"GOOD: [1 sentence praising the good points in Korean]\n"
        f"IMPROVE: [1 sentence suggestion for improvement in Korean (Optional, only if needed)]"
    )
    response = get_ai_response(prompt)
    
    # 파싱 로직
    score = 50
    good = "아이디어가 접수되었습니다."
    improve = None
    
    try:
        lines = response.strip().split('\n')
        for line in lines:
            if "SCORE:" in line:
                score = int(line.replace("SCORE:", "").strip())
            if "GOOD:" in line:
                good = line.replace("GOOD:", "").strip()
            if "IMPROVE:" in line:
                val = line.replace("IMPROVE:", "").strip()
                if val and val.lower() != "none":
                    improve = val
    except:
        pass
        
    return score, good, improve

def generate_mayoral_report(stats, budget):
    """
    게임 종료 시 AI가 최종 평가 리포트를 생성합니다.
    """
    prompt = (
        f"The user has finished the city management game.\n"
        f"Final Stats: {stats}\n"
        f"Remaining Budget: {budget}\n\n"
        f"Act as a senior city planning consultant. Write a 'Mayoral Performance Report' for the user (Little Mayor).\n"
        f"Include:\n"
        f"1. A Title (e.g., 'Environmental Hero', 'Balanced Leader', etc.) based on stats.\n"
        f"2. Evaluation: Praise what they did well, and gently point out what was neglected.\n"
        f"3. Final Grade (S, A, B, C).\n"
        f"Write in Korean, friendly but professional tone."
    )
    return get_ai_response(prompt)

def check_improvement(original, feedback, new_idea):
    """
    보완된 아이디어가 피드백을 잘 반영했는지 확인합니다.
    """
    prompt = (
        f"Original Idea: {original}\n"
        f"Feedback to improve: {feedback}\n"
        f"New Idea: {new_idea}\n\n"
        f"Did the user address the feedback and improve the idea? Return ONLY 'YES' or 'NO'."
    )
    res = get_ai_response(prompt).strip().upper()
    return "YES" in res

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
        
    # 3. 임시 UI 상태 (Tab 1)
    if 'news_title' not in st.session_state:
        st.session_state.news_title = ""
    if 'news_category' not in st.session_state:
        st.session_state.news_category = "교통"
    
    # Tab 2 States
    if 'interview_summary' not in st.session_state:
        st.session_state.interview_summary = ""
    if 'policy_eval_result' not in st.session_state:
        st.session_state.policy_eval_result = {} # {score, good, improve}
    if 'bonus_claimed' not in st.session_state:
        st.session_state.bonus_claimed = False
        
    # 4. 챗봇 상태 (AI 재연동)
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_persona' not in st.session_state:
        st.session_state.current_persona = None
    st.session_state.interview_summary = ""

    # 5. Tab 3 Final Report
    if 'final_report' not in st.session_state:
        st.session_state.final_report = ""

def reset_game():
    st.session_state.budget = 0
    st.session_state.step1_status = False
    st.session_state.step2_status = False
    st.session_state.stats = {'😊행복': 50, '🌳환경': 50, '🛡️안전': 50, '💰경제': 50}
    st.session_state.turns = 5
    st.session_state.solved_problems = []
    st.session_state.logs = []
    st.session_state.game_over = False
    # Chat reset
    st.session_state.chat_history = []
    st.session_state.current_persona = None
    st.session_state.interview_summary = ""
    st.session_state.policy_eval_result = {}
    st.session_state.bonus_claimed = False
    st.session_state.final_report = ""

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
    
    # Activity Description
    st.info("💡 활동 안내: 검색 포털에 우리 지역의 이름이나, 지역에서 생긴 다양한 문제들을 검색해보세요!")
    
    col_link, col_input = st.columns([1, 2])
    with col_link:
        st.write("")
        # Naver Main Link
        st.link_button("🔍 네이버에서 검색하기", "https://www.naver.com")
        
    with col_input:
        title_in = st.text_input("기사 제목을 입력하세요", value=st.session_state.news_title)
        # Selectbox is kept for manual override, but AI will suggest/set persona
        cat_in = st.selectbox("어떤 분야인가요?", ["교통", "환경", "안전", "기타"], index=["교통", "환경", "안전", "기타"].index(st.session_state.news_category))
        
        if st.button("📝 기사 등록"):
            if len(title_in) > 1:
                st.session_state.news_title = title_in
                st.session_state.news_category = cat_in
                
                # AI Auto-Analysis for Persona
                with st.spinner("AI가 기사 내용을 분석하여 인터뷰 대상을 찾고 있습니다..."):
                     recommended_persona = analyze_persona_from_title(title_in)
                     st.session_state.current_persona = recommended_persona
                     st.session_state.chat_history = [] # Reset chat
                     st.toast(f"AI 추천: 이 뉴스는 '{recommended_persona}'와 대화하는 것이 좋겠어요!", icon="🤖")

                st.success("기사가 등록되었습니다! 아래 주민 인터뷰를 진행하세요.")
            else:
                st.warning("제목을 입력해주세요.")
                
    st.divider()
    
    # Step 1-2. Chatbot with AI & Persona Switching
    st.subheader("Step 2. 가상 주민 인터뷰")
    
    if st.session_state.news_title:
        st.write("누구와 인터뷰할까요? 인물을 선택하면 새로운 대화가 시작됩니다.")
        
        # Persona Selection Buttons
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        
        def set_persona(p_name):
            st.session_state.current_persona = p_name
            st.session_state.chat_history = [] 
        
        with col_p1:
            if st.button("🎒 등굣길 아이", use_container_width=True): set_persona("등굣길 아이")
        with col_p2:
            if st.button("🧹 청소부 아저씨", use_container_width=True): set_persona("청소부 아저씨")
        with col_p3:
            if st.button("👮 경찰관", use_container_width=True): set_persona("경찰관")
        with col_p4:
            if st.button("🙋 마을 주민", use_container_width=True): set_persona("마을 주민")
            
        current_p = st.session_state.current_persona
        
        if current_p:
            st.markdown(f"### 💬 지금 **'{current_p}'**님과 인터뷰 중입니다.")
            
            # Display Chat History
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            
            # Chat Input
            if prompt := st.chat_input("질문을 입력하세요..."):
                # 1. User Message
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # 2. AI Message logic
                with st.chat_message("assistant"):
                    with st.spinner(f"{current_p}님이 생각 중입니다..."):
                        news_context = f"뉴스 제목: {st.session_state.news_title}, 분야: {st.session_state.news_category}"
                        system_prompt = (
                            f"당신은 '{current_p}'입니다. 우리 동네에 살고 있으며, 현재 '{news_context}' 문제로 인해 겪고 있는 어려움이나 생각을 말해주세요. "
                            f"사용자는 '꼬마 시장'입니다. 초등학생에게 말하듯이 친근하고, '{current_p}'의 말투(참고: 아이는 존댓말/반말 섞기, 경찰은 듬직하게, 청소부는 구수하게)를 써주세요. "
                            f" 답변은 3문장 이내로 짧게 해주세요."
                            f"\n사용자 메시지: {prompt}"
                        )
                        
                        ai_reply = get_ai_response(system_prompt)
                        st.markdown(ai_reply)
                        
                st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})
        else:
             st.info("👆 위 버튼을 눌러 인터뷰하고 싶은 주민을 선택해주세요!")

        st.divider()
        # Increased Reward: 50 Coins
        if st.button("✅ 취재 완료 (코인 받기)"):
            # Check question count
            user_msg_count = len([m for m in st.session_state.chat_history if m['role'] == 'user'])
            
            if not st.session_state.step1_status:
                if user_msg_count >= 3:
                    st.session_state.budget += 50
                    st.session_state.step1_status = True
                    st.balloons()
                    st.success("취재비 50코인을 받았습니다! (정책 연구소로 이동하세요)")
                    time.sleep(1) # 풍선 보여줄 시간
                    st.rerun() # [UX Fix] Update Sidebar Immediately
                else:
                    st.warning(f"인터뷰가 부족해요! 주민에게 최소 3가지 이상 질문을 해주세요. (현재: {user_msg_count}/3)")
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
    
    # 1. Show Context (Step 1 Info)
    if st.session_state.news_title:
        st.success(f"📌 해결해야 할 문제: **{st.session_state.news_title}** [{st.session_state.news_category}]")
        
        # Generate Summary if needed
        if not st.session_state.interview_summary and st.session_state.chat_history:
            with st.spinner("AI가 지난 인터뷰 내용을 요약하고 있습니다..."):
                # Assuming summarize_interview function exists, if not, it needs to be added.
                # For now, let's mock it or assume it's defined elsewhere.
                # If it's not defined, this will cause an error.
                # For the purpose of this edit, I'll assume it exists or is a placeholder.
                st.session_state.interview_summary = "인터뷰 요약 (임시): 주민들이 해당 문제에 대해 다양한 의견을 가지고 있습니다." # Placeholder
        
        if st.session_state.interview_summary:
            st.info(f"💬 주민 인터뷰 요약: {st.session_state.interview_summary}")
    else:
        st.warning("1단계 뉴스룸을 먼저 완료하면, 더 정확한 정책 심사를 받을 수 있어요!")
    
    # Guidance
    st.caption("💡 힌트: **What?** (어떤 정책?), **How?** (어떻게 실현?), **Why?** (왜 필요?) 내용을 포함하면 더 높은 점수를 받아요!")
    idea_in = st.text_area("나만의 아이디어를 적어주세요.", height=150)
    
    if st.button("🤖 AI 심사 받기"):
        if not st.session_state.step2_status:
            
            # AI Evaluation
            with st.spinner("AI 심사위원이 정책을 분석 중입니다..."):
                problem_ctx = f"Problem: {st.session_state.news_title}, Category: {st.session_state.news_category}, Interview: {st.session_state.interview_summary}"
                score, good, improve = evaluate_policy_with_ai(idea_in, problem_ctx)
                
                # Save Result
                st.session_state.policy_eval_result = {"score": score, "good": good, "improve": improve}
                
                # Tier Logic
                if score >= 80:
                    score_acc = 100
                    tier = "A"
                    badge = "🌟 [최우수 정책]"
                elif score >= 50:
                    score_acc = 70
                    tier = "B"
                    badge = "👍 [우수 정책]"
                else:
                    score_acc = 40
                    tier = "C"
                    badge = "🤔 [노력 정책]"

            st.session_state.budget += score_acc
            st.session_state.step2_status = True
            
            st.balloons()
            time.sleep(1)
            st.rerun() # [UX Fix] Update Sidebar
        else:
            st.warning("이미 정책 지원금을 받았습니다.")

    # Show Result & Revision Loop
    if st.session_state.step2_status and st.session_state.policy_eval_result:
        res = st.session_state.policy_eval_result
        st.divider()
        st.subheader(f"📊 심사 결과: {res['score']}점")
        
        st.success(f"✅ 잘한 점: {res['good']}")
        
        if res['improve']:
            st.warning(f"🔧 보완할 점: {res['improve']}")
            
            if not st.session_state.bonus_claimed:
                st.markdown("---")
                st.write("### 🧩 아이디어 보완하기 (+30코인)")
                st.write("심사위원의 피드백을 반영하여 아이디어를 더 멋지게 다듬어보세요!")
                
                refined_idea = st.text_area("보완된 아이디어를 입력하세요:", placeholder="피드백 내용을 반영해서 적어보세요.")
                
                if st.button("✨ 보완 제출"):
                    if len(refined_idea) > 5:
                        with st.spinner("AI가 보완 여부를 확인 중입니다..."):
                            is_improved = check_improvement(idea_in, res['improve'], refined_idea)
                            
                            if is_improved:
                                st.session_state.budget += 30
                                st.session_state.bonus_claimed = True
                                st.balloons()
                                st.success("멋지게 보완하셨군요! 추가 예산 30코인을 받았습니다.")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("피드백 내용이 충분히 반영되지 않은 것 같아요. 다시 한번 고민해보세요!")
                    else:
                        st.warning("내용을 조금 더 적어주세요.")
            else:
                st.info("🎉 보완 미션 완료! 추가 보너스를 이미 받았습니다.")
        else:
            st.info("완벽한 정책입니다! 더 이상 보완할 점이 없네요. 👏")

# -----------------------------------------------------------------------------------------
# [Tab 3] 꼬마 시장님
# -----------------------------------------------------------------------------------------
with tab3:
    st.header("🏛️ 꼬마 시장님 시뮬레이션")
    
    # Intro
    st.info("""
    **📖 활동 안내**
    1, 2단계에서 모은 예산을 활용하여 발생한 5가지 마을 문제를 해결해보세요!
    각 선택은 '행복', '환경', '안전', '경제' 수치에 영향을 줍니다.
    
    **🎯 배울 수 있어요!**
    *   **자원 관리**: 한정된 예산을 가장 필요한 곳에 쓰는 법을 배웁니다.
    *   **가치 판단**: 편리함과 환경 보호 사이에서 어떤 가치가 더 중요한지 고민해봅니다.
    *   **책임감**: 나의 결정이 우리 마을에 어떤 결과를 가져오는지 책임감을 느껴보세요.
    """)
    st.divider()
    
    if st.session_state.game_over:
        st.error("게임이 종료되었습니다! 최종 결과를 확인하세요.")
        st.metric("최종 남은 예산", f"{st.session_state.budget} 코인")
        
        # Final Report
        if not st.session_state.final_report:
            with st.spinner("AI가 시장님의 활동을 평가하여 리포트를 작성 중입니다..."):
                st.session_state.final_report = generate_mayoral_report(st.session_state.stats, st.session_state.budget)
        
        st.markdown("### 🏆 최종 시장님 성적표")
        st.success(st.session_state.final_report)
        
        if st.button("🔄 게임 다시 시작하기"):
            reset_game()
            st.rerun()
    else:
        st.write(f"남은 턴: {st.session_state.turns}")
        
        # 문제 뽑기 (순서대로)
        current_idx = 5 - st.session_state.turns
        if current_idx < len(problems):
            prob = problems[current_idx]
            
            st.subheader(f"문제 {current_idx + 1}: {prob['title']}")
            st.write(prob['desc'])
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"선택 A: {prob['A']['label']}")
                st.caption(f"효과: {prob['A']['effect']}")
                if st.button("선택 A 실행", key=f"btn_a_{current_idx}"):
                    if st.session_state.budget >= prob['A']['cost']:
                        st.session_state.budget -= prob['A']['cost']
                        for k, v in prob['A']['effect'].items():
                            st.session_state.stats[k] = min(100, max(0, st.session_state.stats[k] + v))
                        
                        st.session_state.logs.append(f"A 선택: {prob['msg']}")
                        st.session_state.solved_problems.append(prob['id'])
                        st.session_state.turns -= 1
                        st.success(prob['msg'])
                        if st.session_state.turns == 0:
                            st.session_state.game_over = True
                        st.rerun()
                    else:
                        st.error("예산이 부족해요!")
                        
            with col2:
                st.info(f"선택 B: {prob['B']['label']}")
                st.caption(f"효과: {prob['B']['effect']}")
                if st.button("선택 B 실행", key=f"btn_b_{current_idx}"):
                    if st.session_state.budget >= prob['B']['cost']:
                        st.session_state.budget -= prob['B']['cost']
                        for k, v in prob['B']['effect'].items():
                            st.session_state.stats[k] = min(100, max(0, st.session_state.stats[k] + v))
                        
                        st.session_state.logs.append(f"B 선택: {prob['msg']}")
                        st.session_state.solved_problems.append(prob['id'])
                        st.session_state.turns -= 1
                        st.success(prob['msg'])
                        if st.session_state.turns == 0:
                            st.session_state.game_over = True
                        st.rerun()
                    else:
                        st.error("예산이 부족해요!")
        else:
            st.session_state.game_over = True
            st.rerun()
