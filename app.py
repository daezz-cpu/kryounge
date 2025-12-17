import streamlit as st
import pandas as pd
import plotly.express as px
import time
import google.generativeai as genai

# -----------------------------------------------------------------------------------------
# [Setup] 페이지 설정 (반드시 가장 먼저 호출되어야 함)
# -----------------------------------------------------------------------------------------
# 목적: 웹 브라우저 탭의 제목, 아이콘, 그리고 전체 레이아웃(넓은 화면 모드)을 초기화합니다.
# 결과: 사용자가 접속했을 때 브라우저 탭에 '현명한 꼬마 시장님'이라는 제목과 아이콘이 보입니다.
st.set_page_config(page_title="현명한 꼬마 시장님", layout="wide", page_icon="🏙️")

# -----------------------------------------------------------------------------------------
# [AI Helper Functions] Gemini AI 연동 및 프롬프트 관리 함수들
# -----------------------------------------------------------------------------------------

def get_ai_response(prompt):
    """Gemini AI 응답 생성 함수"""
    # 목적: API 키가 보안 설정(secrets)에 저장되어 있는지 확인하여 오류를 방지합니다.
    if "GEMINI_API_KEY" not in st.secrets:
        return "🔑 API 키가 설정되지 않았어요."

    # 목적: Google Gemini AI를 사용하기 위한 인증 절차를 수행합니다.
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    last_error = ""
    available_models = []

    try:
        # 목적: 현재 사용 가능한 AI 모델 목록을 가져와서, 성능이 빠르고 좋은 모델 순서로 정렬합니다.
        # 결과: 특정 모델이 응답하지 않더라도 다른 모델로 자동 대체하여 안정적인 서비스를 제공합니다.
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        sorted_models = sorted(available_models, key=lambda x: (
            0 if 'gemini-2.5-flash' in x else 
            1 if 'gemini-2.0-flash' in x else 
            2 if 'flash' in x else 
            3
        ))
        
        # 목적: 정렬된 순서대로 모델에 요청을 보내고, 성공하면 즉시 응답 텍스트를 반환합니다.
        for model_name in sorted_models:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                last_error = f"{model_name}: {str(e)}"
                continue
                
    except Exception as e:
        return f"🤖 AI 모델 목록 오류: {str(e)}"

    return f"🤖 AI 연결 실패.\n마지막 오류: {last_error}\n(사용 가능 모델: {len(available_models)}개)"

def analyze_persona_from_title(title):
    """뉴스 제목 분석 후 페르소나 추천"""
    # 목적: 사용자가 입력한 사회 문제(뉴스 제목)에 가장 적합한 인터뷰 대상(페르소나)을 정의합니다.
    persona_list = ['등굣길 아이', '청소부 아저씨', '경찰관', '마을 주민']
    
    # 목적: AI에게 뉴스 제목을 분석시키고, 위 리스트 중 가장 관련 있는 인물을 하나만 뽑도록 지시합니다.
    prompt = (
        f"Analyze the news title '{title}'. "
        f"Select the most relevant persona from this list: {persona_list}. "
        f"You MUST select one from the list. "
        f"If the title is vague or you are unsure, default to '마을 주민'. "
        f"Return ONLY the persona name."
    )
    # 결과: AI 응답에서 불필요한 따옴표 등을 제거하여 깔끔한 '역할 이름'만 반환합니다.
    result = get_ai_response(prompt).strip().replace("'", "").replace('"', "")
    
    # 목적: 혹시라도 AI가 엉뚱한 값을 줄 경우를 대비해 기본값('마을 주민')을 설정합니다.
    if result not in persona_list:
        return "마을 주민"
    return result
    
def evaluate_policy_with_ai(idea, problem_context):
    """아이디어 평가 및 점수 산출"""
    # 목적: 학생이 낸 아이디어를 4가지 교육적 기준(명확성, 구체성, 타당성, 창의성)으로 AI가 채점하게 합니다.
    # 결과: 점수(숫자)와 구체적인 피드백(칭찬, 보완점)을 구조화된 텍스트로 받아옵니다.
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
        f"ANALYSIS: [Brief analysis of the idea in Korean]\n"
        f"GOOD: [Praise in Korean]\n"
        f"IMPROVE: [Advice in Korean - If perfect, write '없음']"
    )
    response = get_ai_response(prompt)
    
    score = 50
    good = "아이디어가 접수되었습니다."
    improve = None
    
    # 목적: AI의 줄글 응답을 파싱(분해)하여 점수, 장점, 개선점으로 나누어 변수에 저장합니다.
    try:
        lines = response.strip().split('\n')
        for line in lines:
            if "SCORE:" in line:
                score = int(line.replace("SCORE:", "").strip())
            if "GOOD:" in line:
                good = line.replace("GOOD:", "").strip()
            if "ANALYSIS:" in line:
                analysis = line.replace("ANALYSIS:", "").strip()
                good = f"{analysis} {good}"
            if "IMPROVE:" in line:
                val = line.replace("IMPROVE:", "").strip()
                if val and val != "없음" and val.lower() != "none" and val != "None":
                    improve = val
    except:
        pass
        
    return score, good, improve

def generate_mayoral_report(stats, budget):
    """최종 리포트 생성"""
    # 목적: 게임 종료 후, 플레이어의 활동 결과(지표, 남은 예산)를 바탕으로 격려와 평가가 담긴 성적표를 작성합니다.
    prompt = (
        f"The user has finished the city management game.\n"
        f"Final Stats: {stats}\n"
        f"Remaining Budget: {budget}\n\n"
        f"Act as a senior city planning consultant. Write a 'Mayoral Performance Report' for the user.\n"
        f"Include:\n"
        f"1. A Title (e.g., 'Environmental Hero', 'Balanced Leader') based on stats.\n"
        f"2. Evaluation: Praise what they did well, and gently point out what was neglected.\n"
        f"3. Final Grade (S, A, B, C).\n"
        f"Write EVERYTHING in Korean only. Use a friendly but professional tone."
    )
    return get_ai_response(prompt)

def generate_resident_reactions(problem_title, choice_label, choice_effect, choice_msg):
    """정책 선택에 대한 주민 반응 생성"""
    # 목적: 플레이어의 선택이 실제 주민들의 삶에 어떤 영향을 주는지, 찬성/반대 등 다양한 입장의 대사로 보여줍니다.
    # 결과: "상인: 장사가 안돼요!" 처럼 생생한 캐릭터 대사가 생성됩니다.
    prompt = (
        f"마을 문제: {problem_title}\n"
        f"시장님이 선택한 정책: {choice_label}\n"
        f"정책 효과: {choice_effect}\n"
        f"결과 메시지: {choice_msg}\n\n"
        f"위 정책에 대해 서로 다른 입장의 마을 주민 2명의 짧은 반응을 작성해주세요.\n"
        f"주의사항 1: '김민수' 같은 이름 대신 '상인', '학부모', '경찰관' 등 역할을 사용하세요.\n"
        f"주의사항 2: 반드시 **한국어만** 사용하세요.\n"
        f"형식:\n"
        f"👤 [직업/역할]: (한 문장 반응)\n"
        f"👤 [직업/역할]: (한 문장 반응)\n\n"
        f"초등학생도 이해할 수 있게 친근하고 쉽게 작성하세요."
    )
    return get_ai_response(prompt)

def check_improvement(original, feedback, new_idea):
    """피드백 반영 여부 확인"""
    # 목적: 학생이 AI의 피드백을 무시하지 않고, 수정된 아이디어에 반영했는지 AI가 판단합니다.
    # 결과: 피드백 반영이 확인되면 'YES', 아니면 'NO'를 반환하여 보너스 점수 지급 여부를 결정합니다.
    prompt = (
        f"Original Idea: {original}\n"
        f"Feedback to improve: {feedback}\n"
        f"New Idea: {new_idea}\n\n"
        f"Determine if the student has made an effort to improve the idea based on the feedback.\n"
        f"Criteria for 'YES':\n"
        f"1. Does the new idea include at least one KEYWORD from the feedback?\n"
        f"2. Is there ANY sign of effort to address the feedback?\n"
        f"If either of these is true, return 'YES'.\n"
        f"Return ONLY 'YES' or 'NO'."
    )
    res = get_ai_response(prompt).strip().upper()
    return "YES" in res

# -----------------------------------------------------------------------------------------
# [Helper Functions] 세션 상태 초기화
# -----------------------------------------------------------------------------------------
def init_game():
    """
    Streamlit은 버튼 클릭 등 이벤트가 발생할 때마다 코드가 재실행됩니다.
    이 함수는 데이터가 초기화되지 않고 유지되도록 'session_state'에 변수들을 저장합니다.
    """
    # 게임의 핵심 자원 (예산, 단계별 완료 여부)
    if 'budget' not in st.session_state: st.session_state.budget = 0
    if 'step1_status' not in st.session_state: st.session_state.step1_status = False 
    if 'step2_status' not in st.session_state: st.session_state.step2_status = False 
    
    # 마을 상태 통계 및 게임 진행 상황
    if 'stats' not in st.session_state:
        st.session_state.stats = {'😊행복': 50, '🌳환경': 50, '🛡️안전': 50, '💰경제': 50}
    if 'turns' not in st.session_state: st.session_state.turns = 5
    if 'solved_problems' not in st.session_state: st.session_state.solved_problems = [] 
    if 'logs' not in st.session_state: st.session_state.logs = []
    if 'game_over' not in st.session_state: st.session_state.game_over = False
        
    # 뉴스룸(1단계) 관련 데이터
    if 'news_title' not in st.session_state: st.session_state.news_title = ""
    if 'news_category' not in st.session_state: st.session_state.news_category = "교통"
    
    # 정책 연구소(2단계) 관련 데이터
    if 'interview_summary' not in st.session_state: st.session_state.interview_summary = ""
    if 'policy_eval_result' not in st.session_state: st.session_state.policy_eval_result = {} 
    if 'bonus_claimed' not in st.session_state: st.session_state.bonus_claimed = False
        
    # 채팅 인터페이스 데이터
    if 'chat_history' not in st.session_state: st.session_state.chat_history = []
    if 'current_persona' not in st.session_state: st.session_state.current_persona = None
    
    # 최종 결과 및 피드백 데이터
    if 'final_report' not in st.session_state: st.session_state.final_report = ""
    if 'resident_reaction' not in st.session_state: st.session_state.resident_reaction = None
    if 'last_choice_msg' not in st.session_state: st.session_state.last_choice_msg = None

def reset_game():
    """
    사용자가 '게임 다시하기'를 눌렀을 때 호출되는 함수입니다.
    모든 상태 변수를 초기값으로 되돌려 새로운 게임을 시작할 수 있게 만듭니다.
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

# [Game Data] 게임 데이터
# 시뮬레이션 단계에서 사용될 7가지 문제 상황과 선택지(A/B)에 따른 비용 및 효과 데이터입니다.
problems = [
    {
        "id": 1, "title": "스쿨존 주차난", "image": "assets/school_zone.jpg",
        "desc": "학교 앞 스쿨존에 불법 주차된 차들이 너무 많아요. 아이들이 위험해요!",
        "A": {"label": "불법주차 단속 카메라 설치 (20코인)", "cost": 20, "effect": {"🛡️안전": 25, "💰경제": -5, "😊행복": -5}, "msg": "불법 주차는 줄었지만, 잠시 댈 곳도 없다고 상인들이 화났어요!"},
        "B": {"label": "공영 주차장 건설 (45코인)", "cost": 45, "effect": {"💰경제": 15, "😊행복": 10}, "msg": "주차는 편해졌지만 예산이 많이 들었어요."}
    },
    {
        "id": 2, "title": "쓰레기 악취", "image": "assets/trash_pile.jpg",
        "desc": "골목길에 쓰레기가 쌓여서 냄새가 심해요!",
        "A": {"label": "분리수거장 설치 (10코인)", "cost": 10, "effect": {"🌳환경": 15, "😊행복": 5}, "msg": "깨끗해졌지만 주민들이 관리를 귀찮아해요."},
        "B": {"label": "스마트 CCTV 설치 (30코인)", "cost": 30, "effect": {"🛡️안전": 10, "🌳환경": 20}, "msg": "쓰레기 무단 투기가 싹 사라졌어요!"}
    },
    {
        "id": 3, "title": "낡은 놀이터", "image": "assets/old_playground.jpg",
        "desc": "놀이터 기구가 낡아서 아이들이 놀 곳이 없어요.",
        "A": {"label": "놀이기구 페인트칠 (10코인)", "cost": 10, "effect": {"😊행복": 10, "💰경제": 5}, "msg": "깔끔해졌지만, 새로운 놀이기구가 없어서 아쉬워해요."},
        "B": {"label": "최신 테마 놀이터 조성 (50코인)", "cost": 50, "effect": {"😊행복": 30, "🌳환경": 10}, "msg": "아이들이 너무 좋아해요! 다른 동네에서도 놀러 와요."}
    },
    {
        "id": 4, "title": "길고양이 갈등", "image": "assets/stray_cats.jpg",
        "desc": "배고픈 고양이 울음소리 때문에 이웃 간 다툼이 있어요.",
        "A": {"label": "고양이 급식소 (5코인)", "cost": 5, "effect": {"😊행복": 10, "🌳환경": -5}, "msg": "싸움은 줄었지만 고양이가 더 모였어요."},
        "B": {"label": "마을 고양이 보호소 설치 (40코인)", "cost": 40, "effect": {"🌳환경": 20, "😊행복": 10}, "msg": "고양이들이 안전하게 보호받고, 주민 갈등도 사라졌어요!"}
    },
    {
        "id": 5, "title": "어두운 밤길", "image": "assets/dark_street.jpg",
        "desc": "가로등이 없어서 밤에 다니기가 너무 무서워요.",
        "A": {"label": "강력 LED 설치 (15코인)", "cost": 15, "effect": {"🛡️안전": 20, "🌳환경": -5}, "msg": "밝아졌지만 빛 공해로 잠을 설친대요."},
        "B": {"label": "자율 방범대 운영 (35코인)", "cost": 35, "effect": {"🛡️안전": 15, "💰경제": 10}, "msg": "일자리는 늘었지만 인건비가 계속 나가요."}
    },
    {
        "id": 6, "title": "공장 매연", "image": "assets/factory_smoke.jpg",
        "desc": "공장에서 나오는 연기 때문에 공기가 탁해요.",
        "A": {"label": "친환경 필터 지원 (30코인)", "cost": 30, "effect": {"🌳환경": 25, "😊행복": 10}, "msg": "공기는 맑아졌지만 예산 출혈이 커요."},
        "B": {"label": "공장 가동 제한 (0코인)", "cost": 0, "effect": {"💰경제": -20, "🌳환경": 15}, "msg": "공기는 좋아졌지만 공장 수익이 줄었어요."}
    },
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
# 목적: 앱 실행 시 세션 변수들이 없으면 에러가 나므로, 초기화 함수를 가장 먼저 호출합니다.
init_game()

# [Sidebar] 왼쪽 사이드바 구성
# 목적: 사용자가 어느 탭(페이지)에 있더라도 '현재 예산'과 '마을 상태'를 항상 확인할 수 있게 합니다.
with st.sidebar:
    st.title(f"💰 현재 예산: {st.session_state.budget} 코인")
    st.divider()
    
    st.subheader("✅ 진행 상황")
    # 목적: 3단계 학습 과정 중 어디까지 완료했는지 시각적으로(체크박스) 보여줍니다.
    chk1 = "✅" if st.session_state.step1_status else "⬜"
    chk2 = "✅" if st.session_state.step2_status else "⬜"
    chk3 = "✅" if st.session_state.solved_problems else "⬜"
    
    st.write(f"{chk1} 1단계: 뉴스룸")
    st.write(f"{chk2} 2단계: 정책 연구소")
    st.write(f"{chk3} 3단계: 꼬마 시장님")
    
    st.divider()
    st.subheader("📊 우리 마을 상태")
    
    # 목적: 행복, 환경, 안전, 경제 4가지 지표의 균형을 시각적으로 보여주기 위해 방사형 차트(Radar Chart)를 그립니다.
    df_stats = pd.DataFrame(dict(
        r=list(st.session_state.stats.values()),
        theta=list(st.session_state.stats.keys())
    ))
    fig = px.line_polar(df_stats, r='r', theta='theta', line_close=True, range_r=[0, 100])
    fig.update_traces(fill='toself')
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100]), # 그래프 축을 0~100점으로 고정
            angularaxis=dict(tickfont=dict(size=12, color="black"), visible=True)
        ),
        margin=dict(t=30, b=30, l=40, r=40) 
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 그래프 아래에 정확한 수치를 텍스트로도 보여줍니다.
    c1, c2 = st.columns(2)
    with c1:
        st.metric("😊행복", st.session_state.stats.get("😊행복", 50))
        st.metric("💰경제", st.session_state.stats.get("💰경제", 50))
    with c2:
        st.metric("🌳환경", st.session_state.stats.get("🌳환경", 50))
        st.metric("🛡️안전", st.session_state.stats.get("🛡️안전", 50))


st.title("🏙️ 우리 지역 문제를 찾아 현명하게 해결해보자!")
# 목적: 3단계 학습 과정을 탭으로 분리하여 순차적으로 진행하도록 유도합니다.
tab1, tab2, tab3 = st.tabs(["📰 1단계: 뉴스룸", "💡 2단계: 정책 연구소", "🏛️ 3단계: 꼬마 시장님"])


# -----------------------------------------------------------------------------------------
# [Tab 1] 1단계: 뉴스룸
# -----------------------------------------------------------------------------------------
# 목적: 실제 뉴스를 탐색하고 가상의 주민과 대화하며 문제를 발견하는 단계입니다.
with tab1:
    st.header("📰 우리 동네에 무슨 일이?!")
    st.subheader("Step 1. 리얼 월드 탐색")
    st.info("💡 활동 안내: 검색 포털에 우리 지역의 이름이나, 지역에서 생긴 다양한 문제들을 검색해보세요!")
    
    col_link, col_input = st.columns([1, 2])
    with col_link:
        st.write("")
        # 목적: 학생들이 쉽게 검색할 수 있도록 네이버 링크 버튼을 제공합니다.
        st.link_button("🔍 네이버에서 검색하기", "https://www.naver.com")
        
    with col_input:
        # 목적: 사용자가 찾은 뉴스 제목과 카테고리를 입력받습니다.
        title_in = st.text_input("기사 제목을 입력하세요", value=st.session_state.news_title)
        
        # Selectbox 라인이 길어서 오류가 날 수 있으므로 분리
        categories = ["교통", "환경", "안전", "기타"]
        current_idx = categories.index(st.session_state.news_category)
        cat_in = st.selectbox("어떤 분야인가요?", categories, index=current_idx)
        
        if st.button("📝 기사 등록"):
            if len(title_in) > 1:
                # 입력값을 세션 상태에 저장하여 다른 탭에서도 참조할 수 있게 합니다.
                st.session_state.news_title = title_in
                st.session_state.news_category = cat_in
                
                with st.spinner("AI가 기사 내용을 분석하여 인터뷰 대상을 찾고 있습니다..."):
                      # AI 함수를 호출하여 뉴스 주제에 맞는 인터뷰 대상을 추천받습니다.
                      recommended_persona = analyze_persona_from_title(title_in)
                      st.session_state.current_persona = recommended_persona
                      st.session_state.chat_history = [] 
                      
                      # f-string 안전 처리
                      toast_msg = f"AI 추천: 이 뉴스는 '{recommended_persona}'와 대화하는 것이 좋겠어요!"
                      st.toast(toast_msg, icon="🤖") # 우측 상단에 팝업 알림을 띄웁니다.

                st.success("기사가 등록되었습니다! 아래 주민 인터뷰를 진행하세요.")
            else:
                st.warning("제목을 입력해주세요.")
                
    st.divider()
    st.subheader("Step 2. 가상 주민 인터뷰")
    
    if st.session_state.news_title:
        st.write("누구와 인터뷰할까요? 인물을 선택하면 새로운 대화가 시작됩니다.")
        
        # 목적: 4가지 역할 버튼을 제공하여, 클릭 시 해당 인물과 대화 모드로 전환합니다.
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
        
        # 인터뷰 대상이 선택된 경우 채팅 인터페이스를 표시합니다.
        if current_p:
            st.markdown(f"### 💬 지금 **'{current_p}'**님과 인터뷰 중입니다.")
            
            # 기존 대화 기록을 화면에 다시 그려줍니다 (Streamlit은 매번 새로 그리기 때문).
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            
            # 사용자가 질문을 입력했을 때 실행되는 로직
            if prompt := st.chat_input("질문을 입력하세요..."):
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # AI 답변 생성
                with st.chat_message("assistant"):
                    with st.spinner(f"{current_p}님이 생각 중입니다..."):
                        news_context = f"뉴스 제목: {st.session_state.news_title}, 분야: {st.session_state.news_category}"
                        history_text = ""
                        # 최근 대화 내용 일부를 AI에게 함께 보내 문맥을 유지합니다.
                        for msg in st.session_state.chat_history[-7:]:
                            role_label = "꼬마 시장" if msg['role'] == "user" else current_p
                            history_text += f"{role_label}: {msg['content']}\n"
                        
                        # AI에게 역할(페르소나)을 부여하는 시스템 프롬프트
                        system_prompt = (
                            f"당신은 '{current_p}'입니다. 우리 동네에 살고 있으며, '{news_context}' 문제로 인해 겪는 어려움을 말해주세요.\n"
                            f"사용자는 '꼬마 시장'입니다. 반드시 존댓말을 사용하세요.\n"
                            f"--- 대화 내역 ---\n"
                            f"{history_text}\n"
                            f"{current_p}:"
                        )
                        ai_reply = get_ai_response(system_prompt)
                        st.markdown(ai_reply)
                        
                st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})
        else:
             st.info("👆 위 버튼을 눌러 인터뷰하고 싶은 주민을 선택해주세요!")

        st.divider()
        # 목적: 인터뷰를 충분히(3회 이상) 진행했는지 확인하고, 보상(코인)을 지급합니다.
        if st.button("✅ 취재 완료 (코인 받기)"):
            user_msg_count = len([m for m in st.session_state.chat_history if m['role'] == 'user'])
            
            if not st.session_state.step1_status:
                if user_msg_count >= 3:
                    st.session_state.budget += 50
                    st.session_state.step1_status = True
                    st.balloons() # 축하 효과
                    st.success("취재비 50코인을 받았습니다! (정책 연구소로 이동하세요)")
                    time.sleep(1) 
                    st.rerun() # 예산 업데이트 반영을 위해 화면 새로고침
                else:
                    st.warning(f"인터뷰가 부족해요! 주민에게 최소 3가지 이상 질문을 해주세요. (현재: {user_msg_count}/3)")
            else:
                st.info("이미 예산을 수령했습니다.")
    else:
        st.caption("위에서 기사를 먼저 등록해주세요.")

# -----------------------------------------------------------------------------------------
# [Tab 2] 2단계: 정책 연구소
# -----------------------------------------------------------------------------------------
# 목적: 1단계에서 파악한 문제를 해결할 아이디어를 제안하고, AI의 평가 및 피드백을 받는 단계입니다.
with tab2:
    st.header("💡 정책 아이디어 연구소")
    st.write("해결책을 제안하고 예산을 확보하세요!")
    
    if st.session_state.news_title:
        st.success(f"📌 해결해야 할 문제: **{st.session_state.news_title}** [{st.session_state.news_category}]")
        
        # 인터뷰 내용이 있다면 요약하여 보여줌으로써 아이디어 구상을 돕습니다.
        if not st.session_state.interview_summary and st.session_state.chat_history:
             st.session_state.interview_summary = "인터뷰 요약 (임시): 주민들이 해당 문제에 대해 다양한 의견을 가지고 있습니다." 
        
        if st.session_state.interview_summary:
            st.info(f"💬 주민 인터뷰 요약: {st.session_state.interview_summary}")
    else:
        st.warning("1단계 뉴스룸을 먼저 완료하면, 더 정확한 정책 심사를 받을 수 있어요!")
    
    st.caption("💡 힌트: **What?** (어떤 정책?), **How?** (어떻게 실현?), **Why?** (왜 필요?) 내용을 포함하면 더 높은 점수를 받아요!")
    idea_in = st.text_area("나만의 아이디어를 적어주세요.", height=150)
    
    if st.button("🤖 AI 심사 받기"):
        # 아직 2단계를 완료하지 않은 경우에만 심사를 진행합니다.
        if not st.session_state.step2_status:
            with st.spinner("AI 심사위원이 정책을 분석 중입니다..."):
                problem_ctx = f"Problem: {st.session_state.news_title}, Category: {st.session_state.news_category}"
                # 작성된 아이디어를 AI에게 보내 점수와 피드백을 받아옵니다.
                score, good, improve = evaluate_policy_with_ai(idea_in, problem_ctx)
                
                st.session_state.policy_eval_result = {"score": score, "good": good, "improve": improve}
                
                # 점수 구간에 따라 지급할 예산을 차등 설정합니다.
                if score >= 80: score_acc = 100
                elif score >= 50: score_acc = 70
                else: score_acc = 40

            st.session_state.budget += score_acc
            st.session_state.step2_status = True
            st.balloons()
            time.sleep(1)
            st.rerun() 
        else:
            st.warning("이미 정책 지원금을 받았습니다.")

    # 심사 결과가 있는 경우 화면에 결과를 출력합니다.
    if st.session_state.step2_status and st.session_state.policy_eval_result:
        res = st.session_state.policy_eval_result
        st.divider()
        st.subheader(f"📊 심사 결과: {res['score']}점")
        st.success(f"✅ 잘한 점: {res['good']}")
        
        # 목적: 개선할 점이 있다면 추가 예산(보너스)을 걸고 아이디어 수정을 유도합니다 (학습 효과 증대).
        if res['improve']:
            st.warning(f"🔧 보완할 점: {res['improve']}")
            
            if not st.session_state.bonus_claimed:
                st.markdown("---")
                st.write("### 🧩 아이디어 보완하기 (+30코인)")
                st.write("심사위원의 피드백을 반영하여 아이디어를 더 멋지게 다듬어보세요!")
                
                refined_idea = st.text_area("보완된 아이디어 입력:", placeholder="피드백 내용을 반영해서 적어보세요.")
                
                if st.button("✨ 보완 제출"):
                    if len(refined_idea) > 5:
                        with st.spinner("AI가 보완 여부를 확인 중입니다..."):
                            # AI를 통해 피드백 반영 여부를 검사합니다.
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
# [Tab 3] 3단계: 꼬마 시장님
# -----------------------------------------------------------------------------------------
# 목적: 확보한 예산을 사용하여 실제 발생하는 5가지 마을 문제를 해결하는 시뮬레이션 게임입니다.
with tab3:
    st.header("🏛️ 꼬마 시장님 시뮬레이션")
    
    # 접근 제어: 1, 2단계를 완료하지 않으면 게임에 진입할 수 없도록 막습니다.
    if not st.session_state.step1_status or not st.session_state.step2_status:
        st.warning("⚠️ 1단계와 2단계를 먼저 완료해야 게임에 도전할 수 있어요!")
        if not st.session_state.step1_status:
            st.error("❌ 1단계 '뉴스룸'을 아직 완료하지 않았어요.")
        if not st.session_state.step2_status:
            st.error("❌ 2단계 '정책 연구소'를 아직 완료하지 않았어요.")
        st.stop() # 이후 코드 실행 중단
    
    # [문제 발생 지점 수정] 긴 문자열을 안전하게 처리 (줄바꿈 오류 방지)
    info_text = (
        "**📖 활동 안내**\n"
        "1, 2단계에서 모은 예산을 활용하여 발생한 5가지 마을 문제를 해결해보세요!\n"
        "각 선택은 '행복', '환경', '안전', '경제' 수치에 영향을 줍니다.\n\n"
        "**🎯 배울 수 있어요!**\n"
        "* **자원 관리**: 한정된 예산을 가장 필요한 곳에 쓰는 법을 배웁니다.\n"
        "* **가치 판단**: 편리함과 환경 보호 사이에서 어떤 가치가 더 중요한지 고민해봅니다.\n"
        "* **책임감**: 나의 결정이 우리 마을에 어떤 결과를 가져오는지 책임감을 느껴보세요."
    )
    st.info(info_text)
    
    st.image("assets/village_map.png", caption="우리 마을 지도", use_container_width=True)
    st.divider()
    
    # 게임 종료 시 최종 리포트 화면
    if st.session_state.game_over:
        st.error("게임이 종료되었습니다! 최종 결과를 확인하세요.")
        st.metric("최종 남은 예산", f"{st.session_state.budget} 코인")
        
        # AI를 통해 최종 성적표를 생성합니다 (1회만 생성 후 저장).
        if not st.session_state.final_report:
            with st.spinner("AI가 리포트를 작성 중입니다..."):
                st.session_state.final_report = generate_mayoral_report(st.session_state.stats, st.session_state.budget)
        
        st.markdown("### 🏆 최종 시장님 성적표")
        st.success(st.session_state.final_report)
        
        if st.button("🔄 게임 다시 시작하기"):
            reset_game()
            st.rerun()
    else:
        # 게임 진행 중: 남은 턴 표시
        st.write(f"남은 턴: {st.session_state.turns}")
        
        # 주민 반응 피드백 화면 (선택 직후 표시됨)
        if st.session_state.resident_reaction:
            st.divider()
            st.success(f"📢 정책 결과: {st.session_state.last_choice_msg}")
            st.markdown("### 🗣️ 주민들의 반응")
            st.info(st.session_state.resident_reaction)
            
            if st.button("➡️ 다음 문제로", key="continue_btn"):
                st.session_state.resident_reaction = None
                st.session_state.last_choice_msg = None
                st.rerun()
            st.stop() 
        
        # 현재 턴에 해당하는 문제를 가져와 화면에 표시합니다.
        current_idx = 5 - st.session_state.turns
        if current_idx < len(problems):
            prob = problems[current_idx]
            st.subheader(f"문제 {current_idx + 1}: {prob['title']}")
            if "image" in prob:
                st.image(prob["image"], use_container_width=True)
            st.write(prob['desc'])
            
            col1, col2 = st.columns(2)
            # 선택지 A 버튼 및 로직
            with col1:
                st.info(f"선택 A: {prob['A']['label']}")
                st.caption(f"효과: {prob['A']['effect']}")
                if st.button("선택 A 실행", key=f"btn_a_{current_idx}"):
                    # 예산 체크
                    if st.session_state.budget >= prob['A']['cost']:
                        st.session_state.budget -= prob['A']['cost']
                        # 능력치 업데이트 (0~100 범위 제한)
                        for k, v in prob['A']['effect'].items():
                            st.session_state.stats[k] = min(100, max(0, st.session_state.stats[k] + v))
                        
                        st.session_state.logs.append(f"A 선택: {prob['A']['msg']}")
                        st.session_state.solved_problems.append(prob['id'])
                        st.session_state.last_choice_msg = prob['A']['msg']
                        
                        # AI 주민 반응 생성
                        with st.spinner("주민 반응 확인 중..."):
                            reaction = generate_resident_reactions(prob['title'], prob['A']['label'], str(prob['A']['effect']), prob['A']['msg'])
                            st.session_state.resident_reaction = reaction
                        
                        # 턴 감소 및 게임 종료 여부 확인
                        st.session_state.turns -= 1
                        if st.session_state.turns == 0: st.session_state.game_over = True
                        st.rerun()
                    else:
                        st.error("예산이 부족해요!")
            
            # 선택지 B 버튼 및 로직 (A와 구조 동일)
            with col2:
                st.info(f"선택 B: {prob['B']['label']}")
                st.caption(f"효과: {prob['B']['effect']}")
                if st.button("선택 B 실행", key=f"btn_b_{current_idx}"):
                    if st.session_state.budget >= prob['B']['cost']:
                        st.session_state.budget -= prob['B']['cost']
                        for k, v in prob['B']['effect'].items():
                            st.session_state.stats[k] = min(100, max(0, st.session_state.stats[k] + v))
                        
                        st.session_state.logs.append(f"B 선택: {prob['B']['msg']}")
                        st.session_state.solved_problems.append(prob['id'])
                        st.session_state.last_choice_msg = prob['B']['msg']
                        
                        with st.spinner("주민 반응 확인 중..."):
                            reaction = generate_resident_reactions(prob['title'], prob['B']['label'], str(prob['B']['effect']), prob['B']['msg'])
                            st.session_state.resident_reaction = reaction
                        
                        st.session_state.turns -= 1
                        if st.session_state.turns == 0: st.session_state.game_over = True
                        st.rerun()
                    else:
                        st.error("예산이 부족해요!")
