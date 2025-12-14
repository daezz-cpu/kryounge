import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 설정
st.set_page_config(page_title="현명한 꼬마 시장님", layout="wide")

# -----------------------------------------------------------------------------------------
# 1. Game Data (문제 및 시민 반응 데이터)
# 1. Game Data (문제 및 시민 반응 데이터)
# 실제 사용할 때는 assets 폴더에 해당 이미지 파일(png/jpg)을 넣어주세요.
HEADER_IMAGE = "assets/village_map.png"

problems = {
    "스쿨존 주차난": {
        "image": "assets/school_zone.jpg",
        "description": "학교 앞 스쿨존에 불법 주차된 차들이 너무 많아요. 아이들이 등하굣길에 위험해요!",
        "A": {
            "label": "튼튼한 펜스 설치 (코인 15개)",
            "cost": 15,
            "effect": {"🛡️안전": 25, "💰경제": -10, "😊행복": -5},
            "msg": "학교 앞은 안전해졌지만, 가게 앞이 막혀서 상인들이 불만이에요.",
            "reactions": [
                {"char": "👦초등학생", "msg": "와! 차가 없어서 뛰어가도 안전해요!"},
                {"char": "🏪상점주인", "msg": "펜스 때문에 손님이 차를 못 대서 장사가 안 돼요 ㅠㅠ"}
            ]
        },
        "B": {
            "label": "공영 주차장 건설 (코인 45개)",
            "cost": 45,
            "effect": {"💰경제": 20, "😊행복": 15, "🌳환경": -10},
            "msg": "주차는 편해졌지만, 예산을 많이 쓰고 공사 먼지가 날려요.",
            "reactions": [
                {"char": "🚗운전자", "msg": "주차장이 넓어서 정말 편해요!"},
                {"char": "🌳환경운동가", "msg": "주차장 짓느라 나무를 베어서 슬퍼요."}
            ]
        }
    },
    "쓰레기 악취": {
        "image": "assets/trash_pile.jpg",
        "description": "골목길에 쓰레기가 쌓여서 냄새가 심해요. 파리도 꼬이고 주민들이 코를 막고 다녀요.",
        "A": {
            "label": "예쁜 쓰레기통 설치 (코인 5개)",
            "cost": 5,
            "effect": {"🌳환경": 15, "😊행복": -5},
            "msg": "거리는 깨끗해졌지만, 내 집 앞에 쓰레기통이 있다고 주민들이 다퉈요. (님비현상)",
            "reactions": [
                {"char": "🧹청소부", "msg": "일하기 훨씬 편해졌네요!"},
                {"char": "🏠집주인", "msg": "왜 하필 우리 집 앞에 쓰레기통을 둬요? 냄새나요! 😡"}
            ]
        },
        "B": {
            "label": "CCTV 감시 카메라 (코인 25개)",
            "cost": 25,
            "effect": {"🌳환경": 10, "🛡️안전": 10, "😊행복": -15},
            "msg": "쓰레기는 줄었지만, 감시당하는 기분이라 주민들이 불편해해요.",
            "reactions": [
                {"char": "👵할머니", "msg": "카메라가 나를 찍는 것 같아서 영 찝찝해."},
                {"char": "🛡️경찰관", "msg": "범죄 예방에도 도움이 되니 일석이조입니다!"}
            ]
        }
    },
    "낡은 놀이터": {
        "image": "assets/old_playground.jpg",
        "description": "놀이터 그네가 녹슬고 미끄럼틀이 부서졌어요. 아이들이 놀 곳이 없어요.",
        "A": {
            "label": "신나는 워터파크 개조 (코인 35개)",
            "cost": 35,
            "effect": {"😊행복": 35, "🌳환경": -10},
            "msg": "아이들은 신났지만, 밤늦게까지 시끄러워서 소음 신고가 들어왔어요.",
            "reactions": [
                {"char": "👦어린이", "msg": "매일매일 물놀이 할래요! 시장님 최고!"},
                {"char": "📚수험생", "msg": "너무 시끄러워서 공부에 집중을 못 하겠어요 ㅠㅠ"}
            ]
        },
        "B": {
            "label": "조용한 어린이 도서관 (코인 15개)",
            "cost": 15,
            "effect": {"💰경제": 5, "😊행복": 15},
            "msg": "분위기는 차분해졌지만, 뛰어놀고 싶은 아이들은 조금 심심해요.",
            "reactions": [
                {"char": "👩학부모", "msg": "아이들이 책을 읽을 수 있어서 정말 좋아요."},
                {"char": "⚽개구쟁이", "msg": "도서관은 뛰지도 못하고... 재미없어요."}
            ]
        }
    },
    "길고양이 갈등": {
        "image": "assets/stray_cats.jpg",
        "description": "배고픈 길고양이들이 쓰레기 봉투를 뜯고 울어서 주민들끼리 싸움이 났어요.",
        "A": {
            "label": "고양이 급식소 설치 (코인 5개)",
            "cost": 5,
            "effect": {"😊행복": 15, "🌳환경": -5},
            "msg": "생명을 존중하는 마을이 되었지만, 고양이 울음소리가 여전해요.",
            "reactions": [
                {"char": "😺고양이", "msg": "야옹~ (맛있는 밥 고마워요!)"},
                {"char": "😠이웃주민", "msg": "밥 주니까 고양이가 더 모이잖아요! 시끄러워요!"}
            ]
        },
        "B": {
            "label": "중성화(TNR) 수술 지원 (코인 25개)",
            "cost": 25,
            "effect": {"🌳환경": 15},
            "msg": "장기적으로는 개체 수가 줄겠지만, 당장 눈에 띄는 효과는 없어요.",
            "reactions": [
                {"char": "👨‍⚕️수의사", "msg": "건강하게 공존하는 가장 좋은 방법입니다."},
                {"char": "💰예산담당", "msg": "효과가 바로 나타나지 않아서 주민 설득이 어렵네요."}
            ]
        }
    },
    "어두운 밤길": {
        "image": "assets/dark_street.jpg",
        "description": "가로등이 없어서 밤길이 너무 깜깜해요. 무서워서 다닐 수가 없어요.",
        "A": {
            "label": "대낮 같은 강력 LED (코인 15개)",
            "cost": 15,
            "effect": {"🛡️안전": 25, "🌳환경": -10},
            "msg": "범죄는 사라졌지만, 불빛이 너무 밝아서 잠을 못 자겠대요.",
            "reactions": [
                {"char": "👩퇴근길시민", "msg": "이제 밤 늦게 다녀도 하나도 안 무서워요!"},
                {"char": "🥱피곤한주민", "msg": "커튼을 쳐도 대낮같이 밝아서 잠을 설쳤어요."}
            ]
        },
        "B": {
            "label": "우리 동네 순찰대 (코인 35개)",
            "cost": 35,
            "effect": {"🛡️안전": 20, "💰경제": 15},
            "msg": "일자리는 늘어났지만, 매달 월급을 줘야 해서 코인이 계속 나가요.",
            "reactions": [
                {"char": "👮순찰대원", "msg": "우리 동네 안전은 제가 지킵니다! (일자리 감사해요)"},
                {"char": "🧾세금담당", "msg": "인건비가 너무 비싸서 다른 사업을 못 하겠어요."}
            ]
        }
    },
    "공장 매연 문제": {
        "image": "assets/factory_smoke.jpg",
        "description": "우리 마을 공장에서 연기가 너무 많이 나와요. 공기는 나빠지지만 공장은 돈을 많이 벌고 있어요.",
        "A": {
            "label": "친환경 필터 설치 지원 (코인 30개)",
            "cost": 30,
            "effect": {"🌳환경": 25, "😊행복": 10},
            "msg": "공기는 상쾌해졌지만 예산을 너무 많이 썼어요.",
            "reactions": [
                {"char": "😷마을주민", "msg": "이제 마스크 안 쓰고 산책할 수 있어요! 맑은 공기 최고!"},
                {"char": "💰예산팀장", "msg": "필터 값이 너무 비싸서 다른 사업 예산이 부족합니다..."}
            ]
        },
        "B": {
            "label": "공장 가동 시간 단축 (코인 0개)", # 비용 없음 (경제 감소로 대체)
            "cost": 0,
            "effect": {"💰경제": -20, "🌳환경": 15, "😊행복": -10},
            "msg": "공기는 좀 나아졌지만, 월급이 줄어든 공장 직원들이 화가 났어요.",
            "reactions": [
                {"char": "🏭공장직원", "msg": "시장님! 일하는 시간이 줄어서 월급이 깎였어요 ㅠㅠ"},
                {"char": "🏭공장사장", "msg": "생산량이 줄어서 지역 경제가 타격을 입을 겁니다."}
            ]
        }
    },
    "불편한 버스 배차": {
        "image": "assets/bus_stop.jpg",
        "description": "버스가 너무 늦게 와서 학교 가고 시장 가기가 힘들어요. 마을버스를 늘려달래요!",
        "A": {
            "label": "버스 10대 추가 구매 (코인 40개)",
            "cost": 40,
            "effect": {"😊행복": 30, "💰경제": 10},
            "msg": "버스가 5분마다 와서 너무 좋지만, 금고가 텅 비었어요!",
            "reactions": [
                {"char": "🕒지각생", "msg": "이제 학교 늦을 걱정 없어요! 버스가 바로 와요!"},
                {"char": "🧾재무장관", "msg": "버스 유지비랑 기름값은 어떡합니까... 파산 직전입니다."}
            ]
        },
        "B": {
            "label": "'100원 행복택시' 운영 (코인 10개)",
            "cost": 10,
            "effect": {"😊행복": 10, "💰경제": 5},
            "msg": "할머니들은 편해지셨지만, 학교 가는 학생들은 여전히 버스를 기다려야 해요.",
            "reactions": [
                {"char": "👵할머니", "msg": "아이고 고마워라. 병원 갈 때 택시 타니까 정말 편해."},
                {"char": "🧑‍🎓학생", "msg": "저는 택시 못 타잖아요... 아침마다 버스 전쟁이에요."}
            ]
        }
    }
}

# -----------------------------------------------------------------------------------------
# 2. Helper Functions (함수)

def init_game():
    if 'budget' not in st.session_state:
        st.session_state.budget = 100
    if 'turns' not in st.session_state:
        st.session_state.turns = 5  # 총 5회 기회
    if 'stats' not in st.session_state:
        st.session_state.stats = {'😊행복': 50, '🌳환경': 50, '🛡️안전': 50, '💰경제': 50}
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    if 'game_over' not in st.session_state:
        st.session_state.game_over = False
    if 'last_feedback' not in st.session_state:
        st.session_state.last_feedback = None  # (problem, choice_label, result_msg, reactions)

def reset_game():
    st.session_state.budget = 100
    st.session_state.turns = 5
    st.session_state.stats = {'😊행복': 50, '🌳환경': 50, '🛡️안전': 50, '💰경제': 50}
    st.session_state.logs = []
    st.session_state.game_over = False
    st.session_state.last_feedback = None
    st.rerun()

def execute_policy(problem_name, choice_key):
    problem = problems[problem_name]
    choice = problem[choice_key]
    
    # 예산 확인
    if st.session_state.budget < choice['cost']:
        st.error("코인이 부족해요! 저금통이 텅 비었어요 ㅠㅠ")
        return

    # 1. 자원 업데이트
    st.session_state.budget -= choice['cost']
    st.session_state.turns -= 1
    
    # 2. 스탯 업데이트 & 알림 준비
    bad_news = []
    for stat, value in choice['effect'].items():
        st.session_state.stats[stat] = max(0, min(100, st.session_state.stats[stat] + value))
        if value < 0:
            bad_news.append(f"{stat} (▼{abs(value)})")
    
    # 3. 결과 메시지 생성 (Toast용)
    if bad_news:
         toast_msg = f"앗! 나쁜 소식이 있어요: {', '.join(bad_news)}"
         icon = "📉"
    else:
         toast_msg = "와우! 우리 동네가 더 살기 좋아졌어요!"
         icon = "🎉"
    
    st.toast(toast_msg, icon=icon)
    
    # 4. 로그 & 피드백 저장 (다음 화면 표시용)
    log_entry = f"[{problem_name}]에서 '{choice['label']}' 선택"
    st.session_state.logs.append(log_entry)
    
    st.session_state.last_feedback = {
        "problem": problem_name,
        "choice": choice['label'],
        "msg": choice['msg'],
        "reactions": choice['reactions']
    }
    
    # 5. 게임 종료 체크
    if st.session_state.turns <= 0:
        st.session_state.game_over = True
    
    st.rerun()

# -----------------------------------------------------------------------------------------
# 3. UI Layout (화면 구성)

init_game()

# Sidebar
with st.sidebar:
    st.title("📊 내 주머니 & 동네 점수")
    st.metric(label="💰 남은 코인", value=f"{st.session_state.budget}개")
    st.metric(label="⏳ 남은 선택 기회", value=f"{st.session_state.turns}번")
    
    st.divider()
    
    st.caption("모양이 둥글고 클수록 훌륭한 시장님!")
    df_stats = pd.DataFrame(dict(
        r=list(st.session_state.stats.values()),
        theta=list(st.session_state.stats.keys())
    ))
    fig = px.line_polar(df_stats, r='r', theta='theta', line_close=True, range_r=[0, 100])
    fig.update_traces(fill='toself')
    fig.update_layout(title="우리 동네 점수표", margin=dict(t=30, b=30, l=30, r=30))
    st.plotly_chart(fig, use_container_width=True)

# Main Area
st.image(HEADER_IMAGE, use_column_width=True, caption="평화로운 우리 마을 전경")
st.title("👑 현명한 꼬마 시장님 (Wise Little Mayor)")

# Game Over Screen
if st.session_state.game_over:
    st.header("🎓 시장님의 임기가 끝났습니다!")
    
    st.success("""
    "완벽한 해결책은 없었죠? 하나를 얻으면 하나를 양보해야 하는 것이 지역 문제 해결의 과정입니다.
    하지만 여러분이 고민한 만큼 우리 마을은 더 살기 좋은 곳이 되었을 거예요.
    중요한 건 결과보다, 이웃을 위해 고민했던 시장님의 따뜻한 마음입니다! 👏"
    """)
    
    # 최종 성적표
    stats = st.session_state.stats
    max_stat = max(stats, key=stats.get)
    if max_stat == "😊행복": title = "😁 스마일 시장님"
    elif max_stat == "🌳환경": title = "🌿 숲속의 시장님"
    elif max_stat == "🛡️안전": title = "🛡️ 보디가드 시장님"
    else: title = "💰 부자 시장님"
    
    st.subheader(f"당신의 별명은: {title}")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("😊행복", stats['😊행복'])
    c2.metric("🌳환경", stats['🌳환경'])
    c3.metric("🛡️안전", stats['🛡️안전'])
    c4.metric("💰경제", stats['💰경제'])
    
    st.subheader("📜 내가 한 일들")
    for log in st.session_state.logs:
        st.text(f"- {log}")
        
    if st.button("🔄 새로운 임기 시작하기 (다시 하기)"):
        reset_game()

else:
    # Active Game Screen
    
    # 1. Last Turn Feedback (시민 반응 보여주기)
    if st.session_state.last_feedback:
        fb = st.session_state.last_feedback
        with st.container(border=True):
            st.subheader(f"📢 방금 선택의 결과 ({fb['problem']})")
            st.info(f"**결과:** {fb['msg']}")
            
            st.markdown("**💬 시민들의 한마디:**")
            cols = st.columns(len(fb['reactions']))
            for idx, reaction in enumerate(fb['reactions']):
                with cols[idx]:
                    st.chat_message("user", avatar="👤") # 간단한 아바타 처리
                    st.markdown(f"**{reaction['char']}**: {reaction['msg']}")

    st.divider()
    
    # 2. New Problem Selection
    st.subheader("🚩 해결할 문제를 골라주세요!")
    
    # 아직 해결하지 않은 문제만 보여주고 싶다면 필터링 로직 추가 가능하지만,
    # 여기선 5번의 기회 동안 자유롭게 선택하도록 함 (단, 선택 시 로그가 쌓임)
    selected_problem_name = st.selectbox("어디로 가볼까요?", list(problems.keys()))
    
    if selected_problem_name:
        p_data = problems[selected_problem_name]
        
        col_img, col_desc = st.columns([1, 1.5])
        with col_img:
            st.image(p_data['image'], caption=selected_problem_name, use_column_width=True)
        with col_desc:
            st.markdown(f"### Q. {selected_problem_name}")
            st.write(p_data['description'])
        
        st.write("---")
        
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"**🅰️ {p_data['A']['label']}**")
            # 미리보기 힌트 (선택 사항)
            # st.caption(f"예상 효과: {p_data['A']['effect']}") 
            if st.button("🅰️ 이 방법 선택!", key="btn_a", use_container_width=True):
                execute_policy(selected_problem_name, "A")
                
        with c2:
            st.warning(f"**🅱️ {p_data['B']['label']}**")
            if st.button("🅱️ 저 방법 선택!", key="btn_b", use_container_width=True):
                execute_policy(selected_problem_name, "B")
