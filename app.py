import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client

# 1. 페이지 설정
st.set_page_config(page_title="Enterprise HR Portal", page_icon="🏢", layout="wide")

# 2. 보안 연결 설정 (Secrets 사용)
# 직접 입력했던 URL과 KEY 자리에 st.secrets를 넣어 웹상의 '금고'를 열도록 합니다.
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("보안 설정(Secrets)을 찾을 수 없습니다. Streamlit Cloud 설정에서 URL과 Key를 등록해주세요.")
    st.stop()

# 3. CSS 디자인 (기본 스타일 유지)
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }
    .stApp > header { border-top: 6px solid #86BC25; }
    .highlight-id { font-size: 20px; font-weight: 900; color: #86BC25; background-color: #1A1A1A; padding: 5px 15px; border-radius: 4px; display: inline-block; }
    .login-box { border: 1px solid #EAEAEA; padding: 40px; border-top: 6px solid #86BC25; background-color: #FAFAFA; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# --- 자동 사번 생성용 매핑 ---
POS_MAP = {"인턴": "10", "사원": "20", "대리": "30", "과장": "40", "차장": "50", "부장": "60", "임원": "70"}
DEPT_MAP = {"회계감사본부": "AUD", "세무자문본부": "TAX", "경영자문본부": "CON", "재무자문본부": "FAS", "리스크자문본부": "RSK", "HR본부": "HRM"}

# 4. 세션 관리
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# 5. 로그인 & 회원가입 로직 (Supabase 연동)
if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.header("HR Portal")
        tab_login, tab_register = st.tabs(["로그인", "신규 계정 생성"])
        
        with tab_login:
            with st.form("login"):
                input_id = st.text_input("사번")
                input_pw = st.text_input("비밀번호", type="password")
                if st.form_submit_button("로그인", use_container_width=True):
                    res = supabase.table("accounts").select("*").eq("emp_id", input_id).eq("password", input_pw).execute()
                    if res.data:
                        emp_res = supabase.table("employees").select("*").eq("emp_id", input_id).execute()
                        st.session_state.user = {**emp_res.data[0], "role": res.data[0]['role']}
                        st.session_state.logged_in = True
                        st.rerun()
                    else: st.error("정보가 일치하지 않습니다.")
        
        with tab_register:
            with st.form("register"):
                reg_name = st.text_input("성명")
                reg_pw = st.text_input("비밀번호", type="password")
                reg_pos = st.selectbox("직급", list(POS_MAP.keys()))
                reg_dept = st.selectbox("소속 부서", list(DEPT_MAP.keys()))
                reg_date = st.date_input("입사일")
                if st.form_submit_button("사번 발급 및 가입"):
                    # 사번 생성 로직
                    prefix = f"{reg_date.year}-{POS_MAP[reg_pos]}-{DEPT_MAP[reg_dept]}"
                    existing = supabase.table("employees").select("emp_id").like("emp_id", f"{prefix}%").execute()
                    new_id = f"{prefix}-{(len(existing.data)+1):03d}"
                    
                    supabase.table("accounts").insert({"emp_id": new_id, "password": reg_pw, "role": "USER"}).execute()
                    supabase.table("employees").insert({"emp_id": new_id, "name": reg_name, "position": reg_pos, "dept": reg_dept, "hire_date": str(reg_date), "total_leaves": 15}).execute()
                    st.success(f"가입 완료! 사번: {new_id}")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# 6. 메인 화면 (대시보드 예시)
user = st.session_state.user
st.sidebar.title(f"🏢 {user['name']}님")
if st.sidebar.button("로그아웃"):
    st.session_state.logged_in = False
    st.rerun()

st.title("Enterprise Dashboard")
col1, col2, col3 = st.columns(3)
col1.metric("사번", user['emp_id'])
col2.metric("직급", user['position'])
col3.metric("잔여 연차", f"{user['total_leaves']}일")

# (이후 타임시트, 결재 로직 등은 위와 동일한 방식으로 supabase.table().insert/select로 연동됩니다)
