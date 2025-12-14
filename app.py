import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 설정
st.set_page_config(page_title="현명한 꼬마 시장님", layout="wide")

# 1. State Management (Session State 초기화)
if 'budget' not in st.session_state:
    st.session_state.budget = 100 # 초기 예산 100억
if 'turns' not in st.session_state:
    st.session_state.turns = 3 # 정책 시행 가능 횟수
if 'stats' not in st.session_state:
    st.session_state.stats = {
        '😊행복': 50,
        '🌳환경': 50,
        '🛡️안전': 50,
        '💰경제': 50
    }
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'game_over' not in st.session_state:
    st.session_state.game_over = False

# 2. Problem & Solution Data (문제 데이터 정의)
# 2. Problem & Solution Data (문제 데이터 정의)
problems = {
    "학교 앞 불법 주차": {
        "description": "학교 앞에 차들이 맘대로 세워져 있어서 친구들이 위험해요!",
        "A": {
            "label": "튼튼한 울타리 설치 (코인 15개)",
            "cost": 15,
            "effect": {"🛡️안전": 25, "💰경제": -10, "😊행복": -5},
            "msg": "학교 앞은 안전해졌지만, 가게 앞이 막혀서 아저씨들이 화가 났어요! 😡"
        },
        "B": {
            "label": "주차장 만들기 (코인 45개)",
            "cost": 45,
            "effect": {"💰경제": 20, "😊행복": 15, "🌳환경": -10},
            "msg": "주차하기는 편해졌지만, 공사 때문에 먼지가 날리고 코인을 너무 많이 썼어요."
        }
    },
    "골목길 쓰레기 냄새": {
        "description": "골목길에 쓰레기가 너무 많아서 냄새가 나요. 코를 막고 다녀야 해요!",
        "A": {
            "label": "쓰레기통 많이 놓기 (코인 5개)",
            "cost": 5,
            "effect": {"🌳환경": 15, "😊행복": -5}, 
            "msg": "거리는 깨끗해졌지만, 내 집 앞 쓰레기통 때문에 주민들이 화가 났어요! 😡"
        },
        "B": {
            "label": "카메라로 감시하기 (코인 25개)",
            "cost": 25,
            "effect": {"🌳환경": 10, "🛡️안전": 10, "😊행복": -15},
            "msg": "쓰레기는 줄었지만, 감시당하는 기분이라 기분이 안 좋아요."
        }
    },
    "오래된 놀이터": {
        "description": "우리 동네 놀이터가 너무 낡아서 놀이기구가 삐걱거려요.",
        "A": {
            "label": "최신 물놀이장 만들기 (코인 35개)",
            "cost": 35,
            "effect": {"😊행복": 35, "🌳환경": -20},
            "msg": "신나게 놀 수 있지만, 밤늦게까지 시끄러워서 주민들이 화가 났어요! 😡"
        },
        "B": {
            "label": "작은 도서관 만들기 (코인 15개)",
            "cost": 15,
            "effect": {"💰경제": 10, "😊행복": 15}, 
            "msg": "조용해서 좋지만, 뛰어놀고 싶은 친구들은 조금 실망했어요."
        }
    },
    "길고양이 친구들": {
        "description": "길고양이들을 싫어하는 사람들과 좋아하는 사람들이 다투고 있어요.",
        "A": {
            "label": "고양이 급식소 만들기 (코인 5개)",
            "cost": 5,
            "effect": {"😊행복": 15, "🌳환경": -5},
            "msg": "고양이들은 배부르지만, 울음소리 때문에 잠못드는 주민들이 화가 났어요! 😡"
        },
        "B": {
            "label": "병원 데려가기 수술 (코인 25개)",
            "cost": 25,
            "effect": {"🌳환경": 15}, 
            "msg": "미래를 위해서는 좋지만, 당장 눈에 띄는 변화가 없어서 심심해요."
        }
    },
    "컴컴한 밤길": {
        "description": "밤길이 너무 어두워서 집에 가기 무서워요.",
        "A": {
            "label": "대낮처럼 밝은 가로등 (코인 15개)",
            "cost": 15,
            "effect": {"🛡️안전": 25, "🌳환경": -10},
            "msg": "밤에도 환해서 좋지만, 너무 눈부셔서 잠을 못 자겠다는 주민들이 화가 났어요! 😡"
        },
        "B": {
            "label": "안심 귀가 보디가드 (코인 35개)",
            "cost": 35,
            "effect": {"🛡️안전": 25, "💰경제": 15},
            "msg": "일자리는 늘었지만, 매년 내야 하는 월급이 너무 많아요."
        }
    }
}

# 함수: 정책 실행
def execute_policy(problem_name, choice_key):
    problem = problems[problem_name]
    choice = problem[choice_key]
    
    # 예산 확인
    if st.session_state.budget < choice['cost']:
        st.error("코인이 부족해요! 저금통이 텅 비었어요 ㅠㅠ")
        return

    # 상태 업데이트
    st.session_state.budget -= choice['cost']
    st.session_state.turns -= 1
    
    # 능력치 업데이트
    bad_news = []
    for stat, value in choice['effect'].items():
        st.session_state.stats[stat] = max(0, min(100, st.session_state.stats[stat] + value))
        if value < 0:
            bad_news.append(f"{stat} (▼{abs(value)})")
    
    # 알림 메시지 (Toast)
    if bad_news:
         st.toast(f"앗! 나쁜 소식이 있어요: {', '.join(bad_news)}", icon="📉")
    else:
         st.toast("와우! 우리 동네가 더 살기 좋아졌어요!", icon="🎉")
    
    # 로그 기록
    st.session_state.logs.append(f"[{problem_name}] '{choice['label']}' 선택: {choice['msg']}")
    
    # 게임 종료 확인
    if st.session_state.turns <= 0:
        st.session_state.game_over = True
    
    st.rerun()

# 함수: 게임 리셋
def reset_game():
    st.session_state.budget = 100
    st.session_state.turns = 3
    st.session_state.stats = {'😊행복': 50, '🌳환경': 50, '🛡️안전': 50, '💰경제': 50}
    st.session_state.logs = []
    st.session_state.game_over = False
    st.rerun()

# 3. UI Layout
# Sidebar
with st.sidebar:
    st.title("📊 도시 현황")
    st.metric(label="💰 우리 동네 예산", value=f"{st.session_state.budget} 코인")
    st.metric(label="⏳ 남은 선택 기회", value=f"{st.session_state.turns}번")
    
    st.divider()
    
    # Radar Chart
    st.caption("모양이 둥글고 클수록 살기 좋은 동네예요!")
    df_stats = pd.DataFrame(dict(
        r=list(st.session_state.stats.values()),
        theta=list(st.session_state.stats.keys())
    ))
    fig = px.line_polar(df_stats, r='r', theta='theta', line_close=True, range_r=[0, 100])
    fig.update_traces(fill='toself')
    fig.update_layout(title="우리 동네 점수표", margin=dict(t=30, b=30, l=30, r=30))
    st.plotly_chart(fig, use_container_width=True)

# Main Area
st.title("👑 현명한 꼬마 시장님 (Wise Little Mayor)")
st.caption("한정된 예산으로 우리 도시의 문제를 해결해주세요!")

if st.session_state.game_over:
    st.header("🏁 임기 종료! 최종 성적표")
    
    # 최종 결과 성향 분석 (간단한 로직)
    stats = st.session_state.stats
    max_stat = max(stats, key=stats.get)
    if max_stat == "😊행복": title = "😁 스마일 시장님"
    elif max_stat == "🌳환경": title = "🌿 숲속의 시장님"
    elif max_stat == "🛡️안전": title = "🛡️ 보디가드 시장님"
    else: title = "💰 부자 시장님"
    
    st.subheader(f"당신의 별명은: {title}")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("😊행복", stats['😊행복'])
    col2.metric("🌳환경", stats['🌳환경'])
    col3.metric("🛡️안전", stats['🛡️안전'])
    col4.metric("💰경제", stats['💰경제'])
    
    st.subheader("📜 활동 기록")
    for log in st.session_state.logs:
        st.text(f"- {log}")
        
    st.button("🔄 다시 시작하기", on_click=reset_game)

else:
    # 진행 중 화면
    st.info("시민들이 시장님의 선택을 기다리고 있어요! 어떤 문제를 해결할까요?")
    
    selected_problem = st.selectbox("해결할 문제 선택", list(problems.keys()))
    
    if selected_problem:
        problem_data = problems[selected_problem]
        st.subheader(f"Q. {selected_problem}")
        st.write(problem_data['description'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Option A: {problem_data['A']['label']}**")
            # 스탯 변화 미리보기 (선택 사항, 여기선 숨김 or 힌트)
            if st.button("🅰️ 선택하기", key="btn_a"):
                execute_policy(selected_problem, "A")
                
        with col2:
            st.markdown(f"**Option B: {problem_data['B']['label']}**")
            if st.button("🅱️ 선택하기", key="btn_b"):
                execute_policy(selected_problem, "B")

    st.divider()
    st.subheader("📜 최근 활동 로그")
    if st.session_state.logs:
        for log in reversed(st.session_state.logs):
            st.caption(f"- {log}")
    else:
        st.caption("아직 수행한 정책이 없습니다.")








