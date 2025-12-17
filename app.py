import streamlit as st
import pandas as pd
import plotly.express as px
import time
import google.generativeai as genai

# -----------------------------------------------------------------------------------------
# [Setup] 페이지 설정 (반드시 가장 먼저 호출되어야 함)
# -----------------------------------------------------------------------------------------
# 목적: 웹 애플리케이션의 탭 제목, 아이콘, 레이아웃 등 기본 환경을 구성합니다.
# 결과: 브라우저 탭에 '현명한 꼬마 시장님'이라는 제목과 아이콘이 표시되며, 화면이 넓게(wide) 설정됩니다.
st.set_page_config(page_title="현명한 꼬마 시장님", layout="wide", page_icon="🏙️")

# -----------------------------------------------------------------------------------------
# [AI Helper Functions] Gemini AI 연동 및 프롬프트 관리 함수들
# -----------------------------------------------------------------------------------------

def get_ai_response(prompt):
    """
    Gemini AI에게 텍스트 생성을 요청하는 핵심 함수입니다.
    
    목적: 
    1. Streamlit Secrets에서 API 키를 가져와 보안을 유지하며 연결합니다.
    2. 여러 모델 버전(Flash 등) 중 현재 사용 가능한 모델을 자동으로 찾아 연결 실패 확률을 낮춥니다.
    
    결과: 
    AI가 생성한 텍스트 응답을 반환합니다. 만약 에러가 발생하면 에러 메시지를 반환하여 앱이 멈추지 않게 합니다.
    """
    if "GEMINI_API_KEY" not in st.secrets:
        return "🔑 API 키가 설정되지 않았어요."

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    last_error = ""
    available_models = []

    try:
        # 1. 현재 API 키로 접근 가능한 모델 목록을 조회합니다.
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 2. 응답 속도가 빠른 'Flash' 모델을 우선적으로 사용하도록 정렬합니다.
        sorted_models = sorted(available_models, key=lambda x: (
            0 if 'gemini-2.5-flash' in x else 
            1 if 'gemini-2.0-flash' in x else 
            2 if 'flash' in x else 
            3
        ))
        
        # 3. 순차적으로 모델 연결을 시도하여, 하나라도 성공하면 응답을 반환합니다.
        for model_name in sorted_models:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                last_error = f"{model_name}: {str(e)}"
                continue
                
    except Exception as e:
        return f"🤖 AI 모델 목록을 가져오는 중 오류 발생: {str(e)}"

    return f"🤖 AI 연결 실패.\n마지막 오류: {last_error}\n(사용 가능한 모델: {len(available_models)}개 발견됨)"

def analyze_persona_from_title(title):
    """
    목적: 사용자가 입력한 '뉴스 기사 제목'을 분석하여, 인터뷰하기 가장 적합한 가상 캐릭터(페르소나)를 추천합니다.
    결과: 예) '학교 앞 교통사고' 입력 시 -> '등굣길 아이' 또는 '경찰관'을 반환하여 인터뷰 대상을 자동 지정합니다.
    """
    persona_list = ['등굣길 아이', '청소부 아저씨', '경찰관', '마을 주민']
    prompt = (
        f"Analyze the news title '{title}'. "
        f"Select the most relevant persona from this list: {persona_list}. "
        f"You MUST select one from the list. "
        f"If the title is vague or you are unsure, default to '마을 주민'. "
        f"Return ONLY the persona name."
    )
    result = get_ai_response(prompt).strip().replace("'", "").replace('"', "")
    
    # AI 응답이 예상 목록에 없으면 기본값으로 '마을 주민'을 설정하여 오류를 방지합니다.
    if result not in persona_list:
        return "마을 주민"
    return result
    
def evaluate_policy_with_ai(idea, problem_context):
    """
    목적: 학생이 제출한 정책 아이디어를 AI 선생님이 되어 평가합니다.
          단순 텍스트 생성이 아니라, 프로그램에서 점수 계산에 사용할 수 있도록 정해진 형식(SCORE, GOOD 등)으로 응답을 요청합니다.
    
    결과: 
    1. 점수 (0~100점) -> 예산 지급 기준이 됨
    2. 칭찬할 점 (Good) -> 사용자에게 긍정적 피드백 제공
    3. 보완할 점 (Improve) -> 추가 미션(보너스 점수) 활성화 여부 결정
    """
    prompt = (
        f"Context: {problem_context}\n"
        f"Student's Policy Idea: {idea}\n\n"
        f"You are an AI policy evaluator for elementary school students. You MUST speak Korean ONLY.\n"
        f"Analyze the student's idea based on THREE criteria:\n"
        f"1. **WHAT** (25점): 어떤 정책인지 명확하게 설명했는가?\n"
        f"2. **HOW** (25점): 어떻게 실현/실행할 것인지 구체적인 방법이 있는가?\n"
        f"3. **WHY** (25점): 왜 이 정책이 필요한지, 어떤 문제를 해결하는지 설명했는가?\n"
        f"4. **CREATIVITY** (25점): 창의적이고 참신한 아이디어인가?\n\n"
        f"Calculate total score (0-100) based on these criteria.\n"
        f"Warning: Do NOT use any English in 'ANALYSIS', 'GOOD', or 'IMPROVE'. Write everything in polite Korean.\n\n"
        f"Return the response in the following format ONLY:\n"
        f"SCORE: [0-100 integer]\n"
        f"ANALYSIS: [Brief analysis of the idea in Korean (e.g., 정책의 목적이 뚜렷합니다)]\n"
        f"GOOD: [Praise in Korean (e.g., 구체적인 실천 방안이 돋보입니다)]\n"
        f"IMPROVE: [Advice in Korean (e.g., 실현 가능성을 조금 더 고민해보세요) - If perfect, write '없음']"
    )
    response = get_ai_response(prompt)
    
    # AI 응답 텍스트를 파싱하여 프로그램에서 사용할 변수(score, good, improve)로 변환합니다.
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
            if "ANALYSIS:" in line:
                analysis = line.replace("ANALYSIS:", "").strip()
                good = f"{analysis} {good}"  # 분석 내용을 칭찬 문구와 합쳐서 보여줍니다.
            if "IMPROVE:" in line:
                val = line.replace("IMPROVE:", "").strip()
                if val and val != "없음" and val.lower() != "none" and val != "None":
                    improve = val
    except:
        pass
        
    return score, good, improve

def generate_mayoral_report(stats, budget):
    """
    목적: 게임 종료 시, 최종 도시 상태(Stats)와 남은 예산(Budget)을 바탕으로 AI가 종합 성적표를 작성합니다.
    결과: 사용자에게 '환경 영웅', '균형 잡힌 리더' 같은 칭호와 함께 상세한 피드백 텍스트를 제공합니다.
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
        f"Write EVERYTHING in Korean only. Use a friendly but professional tone."
    )
    return get_ai_response(prompt)

def generate_resident_reactions(problem_title, choice_label, choice_effect, choice_msg):
    """
    목적: 사용자의 정책 선택(A안/B안)에 따라, 서로 다른 입장을 가진 주민 2명의 가상 반응을 생성합니다.
    결과: 정책의 장점뿐만 아니라 단점이나 우려 사항도 주민의 목소리로 보여주어 사용자가 비판적 사고를 하도록 유도합니다.
    """
    prompt = (
        f"마을 문제: {problem_title}\n"
        f"시장님이 선택한 정책: {choice_label}\n"
        f"정책 효과: {choice_effect}\n"
        f"결과 메시지: {choice_msg}\n\n"
        f"위 정책에 대해 서로 다른 입장의 마을 주민 2명의 짧은 반응을 작성해주세요.\n"
        f"주의사항 1: '김민수' 같은 구체적인 이름을 절대 사용하지 마세요. 대신 '상인', '학부모', '경찰관', '캣맘', '주민' 등 역할이나 직업을 사용하세요.\n"
        f"주의사항 2: 반드시 **한국어만** 사용하세요. 영어 문장은 절대 포함하지 마세요.\n"
        f"형식:\n"
        f"👤 [직업/역할]: (한 문장 반응)\n"
        f"👤 [직업/역할]: (한 문장 반응)\n\n"
        f"초등학생도 이해할 수 있게 친근하고 쉽게 작성하세요.\n"
        f"반응은 정책의 장단점을 반영하여 다양하게 작성해주세요."
    )
    return get_ai_response(prompt)

def check_improvement(original, feedback, new_idea):
    """
    목적: 사용자가 AI의 피드백을 받고 아이디어를 수정했을 때, 피드백 내용을 잘 반영했는지 AI가 판단합니다.
    결과: 반영 여부에 따라 'YES' 또는 'NO'를 반환하여 보너스 점수 지급 로직의 판단 기준으로 사용합니다.
    """
    prompt = (
        f"Original Idea: {original}\n"
        f"Feedback to improve: {feedback}\n"
        f"New Idea: {new_idea}\n\n"
        f"Determine if the student has made an effort to improve the idea based on the feedback.\n"
        f"Criteria for 'YES':\n"
        f"1. Does the new idea include at least one KEYWORD from the feedback?\n"
        f"2. Is there ANY sign of effort to address the feedback?\n"
        f"If either of these is true, return 'YES'. Be very generous and encouraging.\n"
        f"Only return 'NO' if the new idea is completely irrelevant or improved nothing.\n"
        f"Return ONLY 'YES' or 'NO'."
    )
    res = get_ai_response(prompt).strip().upper()
    return "YES" in res

# -----------------------------------------------------------------------------------------
# [Helper Functions] 세션 상태 초기화 (Session State Management)
# -----------------------------------------------------------------------------------------
def init_game():
    """
    목적: Streamlit은 버튼 클릭 등 상호작용 시마다 코드가 재실행되는 특성이 있습니다. 
         따라서 예산, 점수, 진행 단계 등의 데이터가 날아가지 않도록 st.session_state에 저장하여 상태를 유지해야 합니다.
    결과: 앱이 새로고침 되어도 사용자의 게임 진행 상황(예산, 해결한 문제 등)이 그대로 유지됩니다.
    """
    # 1. 예산 및 단계 진행 상태 (Step 1, Step 2 완료 여부)
    if 'budget' not in st.session_state:
        st.session_state.budget = 0
    if 'step1_status' not in st.session_state:
        st.session_state.step1_status = False 
    if 'step2_status' not in st.session_state:
        st.session_state.step2_status = False 
        
    # 2. 게임 데이터 (도시 지표, 남은 턴 수, 해결한 문제 등)
    if 'stats' not in st.session_state:
        st.session_state.stats = {'😊행복': 50, '🌳환경': 50, '🛡️안전': 50, '💰경제': 50}
    if 'turns' not in st.session_state:
        st.session_state.turns = 5
    if 'solved_problems' not in st.session_state:
        st.session_state.solved_problems = [] 
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    if 'game_over' not in st.session_state:
        st.session_state.game_over = False
        
    # 3. UI 상태 (뉴스 제목, 선택된 카테고리 등)
    if 'news_title' not in st.session_state:
        st.session_state.news_title = ""
    if 'news_category' not in st.session_state:
        st.session_state.news_category = "교통"
    
    # 정책 연구소 관련 상태 (인터뷰 요약, 평가 결과, 보너스 수령 여부)
    if 'interview_summary' not in st.session_state:
        st.session_state.interview_summary = ""
    if 'policy_eval_result' not in st.session_state:
        st.session_state.policy_eval_result = {} 
    if 'bonus_claimed' not in st.session_state:
        st.session_state.bonus_claimed = False
        
    # 4. 챗봇 상태 (대화 내역 저장)
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_persona' not in st.session_state:
        st.session_state.current_persona = None
    st.session_state.interview_summary = ""

    # 5. 최종 리포트 및 주민 반응 저장
    if 'final_report' not in st.session_state:
        st.session_state.final_report = ""
    
    if 'resident_reaction' not in st.session_state:
        st.session_state.resident_reaction = None
    if 'last_choice_msg' not in st.session_state:
        st.session_state.last_choice_msg = None

def reset_game():
    """
    목적: 사용자가 '다시 하기'를 원할 때, 모든 진행 상황 변수를 초기값으로 되돌려 게임을 처음부터 시작하게 합니다.
    """
    st.session_state.budget = 0
    st.session_state.step1_status = False
    st.session_state.step2_status = False
    st.session_state.stats = {'😊행복': 50, '🌳환경': 50, '🛡️안전': 50, '💰경제': 50}
    st.session_state.turns = 5
    st.session_state.solved_problems = []
    st.session_state.logs = []
    st.session_state.game_over = False
    
    st.session_state.chat_history = []
    st.session_state.current_persona = None
    st.session_state.interview_summary = ""
    st.session_state.policy_eval_result = {}
    st.session_state.bonus_claimed = False
    st.session_state.final_report = ""
    st.session_state.resident_reaction = None
    st.session_state.last_choice_msg = None

# [Game Data] 게임에서 사용될 문제 시나리오 데이터 정의
# 목적: 각 문제의 제목, 설명, 선택지(A/B)에 따른 비용과 도시 지표 변화량을 딕셔너리 형태로 미리 정의해둡니다.
problems = [
    {
        "id": 1, "title": "스쿨존 주차난", "image": "assets/school_zone.jpg",
        "desc": "학교 앞 스쿨존에 불법 주차된 차들이 너무 많아요. 아이들이 위험해요!",
        "A": {"label": "불법주차 단속 카메라 설치 (20코인)", "cost": 20, "effect": {"🛡️안전": 25, "💰경제": -5, "😊행복": -5}, "msg": "불법 주차는 줄었지만, 잠시 댈 곳도 없다고 상인들이 화났어요!"},
        "B": {"label": "공영 주차장 건설 (45코인)", "cost": 45, "effect": {"💰경제": 15, "😊행복": 10}, "msg": "주차는 편해졌지만 예산이 많이 들었어요."}
    },
    # ... (중략) ...
    {
        "id": 7, "title": "버스 배차 불편", "image": "assets/bus_stop.jpg",
        "desc": "버스가 너무 안 와서 학교 가기가 힘들어요.",
        "A": {"label": "버스 증차 (40코인)", "cost": 40, "effect": {"😊행복": 25, "💰경제": 5}, "msg": "편해졌지만 유지비가 엄청나요!"},
        "B": {"label": "행복 택시 쿠폰 (10코인)", "cost": 10, "effect": {"😊행복": 10}, "msg": "급한 불은 껐지만 근본 해결책은 아니에요."}
    }
]

# -----------------------------------------------------------------------------------------
# [App Start] 메인 애플리케이션 시작
# -----------------------------------------------------------------------------------------
# 앱이 시작되면 가장 먼저 세션 상태를 초기화합니다.
init_game()

# [Sidebar] 왼쪽 사이드바 구성
# 목적: 사용자가 현재 예산, 진행 단계, 도시의 상태(4가지 지표)를 언제든지 확인할 수 있게 고정된 영역을 만듭니다.
with st.sidebar:
    st.title(f"💰 현재 예산: {st.session_state.budget} 코인")
    st.divider()
    
    st.subheader("✅ 진행 상황")
    chk1 = "✅" if st.session_state.step1_status else "⬜"
    chk2 = "✅" if st.session_state.step2_status else "⬜"
    chk3 = "✅" if st.session_state.solved_problems else "⬜"
    
    st.write(f"{chk1} 1단계: 뉴스룸")
    st.write(f"{chk2} 2단계: 정책 연구소")
    st.write(f"{chk3} 3단계: 꼬마 시장님")
    
    st.divider()
    st.subheader("📊 우리 마을 상태")
    
    # 목적: Plotly 라이브러리를 사용하여 도시 상태를 Radar Chart(방사형 차트)로 시각화합니다.
    # 결과: 사용자가 숫자만 보는 것보다 '행복', '환경' 등 어떤 분야가 부족한지 도형의 찌그러짐을 통해 직관적으로 파악할 수 있습니다.
    df_stats = pd.DataFrame(dict(
        r=list(st.session_state.stats.values()),
        theta=list(st.session_state.stats.keys())
    ))
    fig = px.line_polar(df_stats, r='r', theta='theta', line_close=True, range_r=[0, 100])
    fig.update_traces(fill='toself')
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("현재 마을 지표:")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("😊행복", st.session_state.stats.get("😊행복", 50))
        st.metric("💰경제", st.session_state.stats.get("💰경제", 50))
    with c2:
        st.metric("🌳환경", st.session_state.stats.get("🌳환경", 50))
        st.metric("🛡️안전", st.session_state.stats.get("🛡️안전", 50))


st.title("🏙️ 우리 지역 문제를 찾아 현명하게 해결해보자!")
# 메인 화면을 3개의 탭으로 나누어 단계별 학습 활동을 구성합니다.
tab1, tab2, tab3 = st.tabs(["📰 1단계: 뉴스룸", "💡 2단계: 정책 연구소", "🏛️ 3단계: 꼬마 시장님"])


# -----------------------------------------------------------------------------------------
# [Tab 1] 1단계: 뉴스룸 (문제 탐색 및 인터뷰)
# -----------------------------------------------------------------------------------------
with tab1:
    st.header("📰 우리 동네에 무슨 일이?!")
    
    # [Step 1-1] 리얼 월드 탐색 (뉴스 검색 및 등록)
    st.subheader("Step 1. 리얼 월드 탐색")
    # ... (생략) ...
    
    with col_input:
        # 사용자가 찾은 기사 제목과 분야를 입력받습니다.
        title_in = st.text_input("기사 제목을 입력하세요", value=st.session_state.news_title)
        cat_in = st.selectbox("어떤 분야인가요?", ["교통", "환경", "안전", "기타"])
        
        if st.button("📝 기사 등록"):
            if len(title_in) > 1:
                st.session_state.news_title = title_in
                st.session_state.news_category = cat_in
                
                # 목적: 사용자가 입력한 제목을 바탕으로 AI가 적절한 인터뷰 대상(페르소나)을 자동으로 추천해줍니다.
                # 결과: 사용자가 고민하지 않아도 문맥에 맞는 캐릭터(예: 스쿨존 문제 -> 아이)가 자동 선택되어 몰입감을 높입니다.
                with st.spinner("AI가 기사 내용을 분석하여 인터뷰 대상을 찾고 있습니다..."):
                      recommended_persona = analyze_persona_from_title(title_in)
                      st.session_state.current_persona = recommended_persona
                      st.session_state.chat_history = [] 
                      st.toast(f"AI 추천: 이 뉴스는 '{recommended_persona}'와 대화하는 것이 좋겠어요!", icon="🤖")

                st.success("기사가 등록되었습니다! 아래 주민 인터뷰를 진행하세요.")
            # ... (생략) ...
                
    st.divider()
    
    # [Step 1-2] 가상 주민 인터뷰 (AI 챗봇)
    st.subheader("Step 2. 가상 주민 인터뷰")
    
    if st.session_state.news_title:
        # ... (생략) ...
        
        # 채팅 UI 표시
        if current_p:
            # ... (생략) ...
            
            # 사용자 입력 처리
            if prompt := st.chat_input("질문을 입력하세요..."):
                # ... (생략) ...
                
                # AI 응답 생성
                with st.chat_message("assistant"):
                    with st.spinner(f"{current_p}님이 생각 중입니다..."):
                        # ... (생략) ...
                        
                        # AI에게 역할(페르소나)을 부여하고 상황에 맞는 답변을 요구합니다.
                        # 대화의 맥락(history_text)을 함께 전송하여 이전 대화를 기억하게 만듭니다.
                        system_prompt = (
                            f"당신은 '{current_p}'입니다. 우리 동네에 살고 있으며, 현재 '{news_context}' 문제로 인해 겪고 있는 어려움이나 생각을 말해주세요.\n"
                            # ... (프롬프트 내용 생략) ...
                        )
                        
                        ai_reply = get_ai_response(system_prompt)
                        st.markdown(ai_reply)
                        
                st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})
        # ... (생략) ...

# -----------------------------------------------------------------------------------------
# [Tab 2] 2단계: 정책 연구소 (아이디어 제안 및 AI 심사)
# -----------------------------------------------------------------------------------------
with tab2:
    st.header("💡 정책 아이디어 연구소")
    # ... (생략) ...
    
    # [AI 심사 요청]
    if st.button("🤖 AI 심사 받기"):
        if not st.session_state.step2_status:
            
            with st.spinner("AI 심사위원이 정책을 분석 중입니다..."):
                problem_ctx = f"Problem: {st.session_state.news_title}, Category: {st.session_state.news_category}, Interview: {st.session_state.interview_summary}"
                # 목적: 학생의 아이디어를 AI에게 전송하여 점수와 피드백을 받아옵니다.
                score, good, improve = evaluate_policy_with_ai(idea_in, problem_ctx)
                
                # 결과 저장 및 등급 산정
                st.session_state.policy_eval_result = {"score": score, "good": good, "improve": improve}
                
                # 점수에 따른 예산 지급 로직 (높은 점수일수록 더 많은 예산을 획득)
                if score >= 80:
                    score_acc = 100
                    # ...
                elif score >= 50:
                    score_acc = 70
                    # ...
                else:
                    score_acc = 40
                    # ...

            st.session_state.budget += score_acc
            st.session_state.step2_status = True
            st.balloons() # 목적: 성취감을 주기 위한 시각적 효과 (풍선 애니메이션)
            # ... (생략) ...

    # [심사 결과 표시 및 보완 미션]
    if st.session_state.step2_status and st.session_state.policy_eval_result:
        # ... (생략) ...
        
        # 보완할 점이 있다면 추가 미션(보너스 코인 기회)을 제공합니다.
        if res['improve']:
            st.warning(f"🔧 보완할 점: {res['improve']}")
            
            if not st.session_state.bonus_claimed:
                # ... (생략) ...
                
                if st.button("✨ 보완 제출"):
                    if len(refined_idea) > 5:
                        with st.spinner("AI가 보완 여부를 확인 중입니다..."):
                            # 목적: 단순히 글자만 쓴 게 아니라, 실제로 AI의 피드백을 반영했는지 검사하여 '의미 있는 학습'을 유도합니다.
                            is_improved = check_improvement(idea_in, res['improve'], refined_idea)
                            
                            if is_improved:
                                st.session_state.budget += 30
                                st.session_state.bonus_claimed = True
                                # ... (생략) ...
                            else:
                                st.error("피드백 내용이 충분히 반영되지 않은 것 같아요. 다시 한번 고민해보세요!")
                    else:
                        st.warning("내용을 조금 더 적어주세요.")

# -----------------------------------------------------------------------------------------
# [Tab 3] 3단계: 꼬마 시장님 (예산 운용 시뮬레이션 게임)
# -----------------------------------------------------------------------------------------
with tab3:
    st.header("🏛️ 꼬마 시장님 시뮬레이션")
    
    # [접근 제어] 1, 2단계를 완료하지 않았다면 게임을 진행할 수 없습니다.
    if not st.session_state.step1_status or not st.session_state.step2_status:
        st.warning("⚠️ 1단계와 2단계를 먼저 완료해야 게임에 도전할 수 있어요!")
        st.stop()  # 목적: 조건을 충족하지 못한 경우 코드를 여기서 중단시켜 아래 게임 화면이 보이지 않게 막습니다.
    
    # ... (생략) ...
    
    # [문제 제시] 현재 턴에 해당하는 문제를 가져와 화면에 표시합니다.
    current_idx = 5 - st.session_state.turns
    if current_idx < len(problems):
        prob = problems[current_idx]
        
        st.subheader(f"문제 {current_idx + 1}: {prob['title']}")
        
        col1, col2 = st.columns(2)
        # A안 선택 로직
        with col1:
            # ... (생략) ...
            if st.button("선택 A 실행", key=f"btn_a_{current_idx}"):
                # 목적: 현재 보유한 예산이 정책 비용보다 많은지 확인합니다.
                if st.session_state.budget >= prob['A']['cost']:
                    # 예산 차감 및 도시 지표 업데이트 (수치가 0~100 사이를 벗어나지 않도록 min/max 처리)
                    st.session_state.budget -= prob['A']['cost']
                    for k, v in prob['A']['effect'].items():
                        st.session_state.stats[k] = min(100, max(0, st.session_state.stats[k] + v))
                    
                    st.session_state.logs.append(f"A 선택: {prob['A']['msg']}")
                    st.session_state.solved_problems.append(prob['id'])
                    
                    # 선택 결과에 따른 AI 주민 반응 생성
                    with st.spinner("주민들의 반응을 확인하는 중..."):
                        reaction = generate_resident_reactions(...)
                        st.session_state.resident_reaction = reaction
                    
                    st.session_state.turns -= 1
                    # 턴 종료 여부 확인
                    if st.session_state.turns == 0:
                        st.session_state.game_over = True
                    st.rerun()
                else:
                    st.error("예산이 부족해요!")
