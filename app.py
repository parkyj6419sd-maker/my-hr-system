import streamlit as st
import pandas as pd
import base64
from datetime import datetime, date, timedelta
from supabase import create_client, Client

# 1. 페이지 설정
st.set_page_config(page_title="Enterprise HR Portal", page_icon="🏢", layout="wide")

# 2. 클라우드 DB 연결 (Secrets 사용)
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    st.error("보안 설정(Secrets)을 찾을 수 없습니다.")
    st.stop()

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# 3. 커스텀 CSS
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; background-color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #000000 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child { display: none !important; }
    [data-testid="stSidebar"] [data-baseweb="radio"] { padding: 12px 15px !important; margin-bottom: 6px !important; border-radius: 4px !important; cursor: pointer !important; width: 100% !important; }
    [data-testid="stSidebar"] [data-baseweb="radio"] p { font-size: 16px !important; font-weight: 600 !important; margin: 0 !important; }
    [data-testid="stSidebar"] [data-baseweb="radio"]:has(input[aria-checked="true"]) { background-color: #E0E0E0 !important; }
    [data-testid="stSidebar"] [data-baseweb="radio"]:has(input[aria-checked="true"]) * { color: #000000 !important; font-weight: 800 !important; }
    [data-testid="stSidebar"] .stButton > button { padding: 2px 10px !important; font-size: 11px !important; height: 26px !important; line-height: 1 !important; width: auto !important; min-width: 60px !important; background-color: transparent !important; border: 1px solid #444 !important; color: #999 !important; border-radius: 4px !important; margin-bottom: 20px !important; float: left; }
    [data-testid="stSidebar"] .stButton > button:hover { color: #ffffff !important; border-color: #ffffff !important; background-color: #333333 !important; }
    .stApp > header { border-top: 6px solid #86BC25; }
    div[data-testid="metric-container"] { background-color: #f8f9fa; border: 1px solid #eeeeee; padding: 20px; border-left: 6px solid #86BC25; }
    div[data-testid="stMainBlockContainer"] .stButton > button:first-child { background-color: #000000; color: #86BC25; border: 1px solid #86BC25; border-radius: 0px; font-weight: 700; height: 3em; }
    div[data-testid="stMainBlockContainer"] .stButton > button:first-child:hover { background-color: #86BC25; color: #000000; }
    .login-box { border: 1px solid #EAEAEA; padding: 40px; border-top: 6px solid #86BC25; background-color: #FAFAFA; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .profile-info { line-height: 1.8; }
    .profile-name { font-size: 28px; font-weight: 800; margin-bottom: 10px; color: #1A1A1A; }
    .profile-label { font-weight: 700; color: #000000; width: 100px; display: inline-block; }
    .profile-value { color: #555555; }
    .empty-image-box { width: 150px; height: 180px; border: 2px dashed #cccccc; background-color: #f8f9fa; display: flex; align-items: center; justify-content: center; color: #888888; font-weight: 600; font-size: 14px; margin-bottom: 10px; text-align: center; }
    .approval-card { border: 1px solid #EAEAEA; border-left: 4px solid #86BC25; padding: 15px; margin-bottom: 10px; background-color: #FAFAFA; }
    .status-badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; background-color: #E0E0E0; color: #333; }
    .highlight-id { font-size: 20px; font-weight: 900; color: #86BC25; background-color: #1A1A1A; padding: 5px 15px; border-radius: 4px; display: inline-block; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8-sig')

POS_MAP = {"인턴": "10", "사원": "20", "대리": "30", "과장": "40", "차장": "50", "부장": "60", "임원": "70"}
DEPT_MAP = {"회계감사본부": "AUD", "세무자문본부": "TAX", "경영자문본부": "CON", "재무자문본부": "FAS", "리스크자문본부": "RSK", "HR본부": "HRM"}

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# =====================================================================
# 로그인 & 회원가입
# =====================================================================
if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center; color:#000000; font-weight:800; font-size:36px; margin-bottom:0;'>HR Portal</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#86BC25; font-weight:600; margin-bottom:20px;'>Enterprise Management System</p>", unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["로그인", "신규 계정 생성"])
        
        with tab_login:
            with st.form("login"):
                input_id = st.text_input("사번 (Employee ID)")
                input_pw = st.text_input("비밀번호 (Password)", type="password")
                if st.form_submit_button("로그인", use_container_width=True):
                    res = supabase.table("accounts").select("*").eq("emp_id", input_id).eq("password", input_pw).execute()
                    if res.data:
                        emp_res = supabase.table("employees").select("*").eq("emp_id", input_id).execute()
                        if emp_res.data:
                            st.session_state.user = {**emp_res.data[0], "role": res.data[0]['role']}
                            st.session_state.logged_in = True
                            st.rerun()
                        else:
                            st.error("직원 상세 정보가 없습니다. 관리자에게 문의하세요.")
                    else: st.error("사번 또는 비밀번호가 일치하지 않습니다.")
        
        with tab_register:
            with st.form("register"):
                reg_name = st.text_input("성명")
                reg_pw = st.text_input("비밀번호", type="password")
                col_r1, col_r2 = st.columns(2)
                with col_r1: reg_pos = st.selectbox("직급", list(POS_MAP.keys()))
                with col_r2: reg_dept = st.selectbox("소속 부서", list(DEPT_MAP.keys()))
                reg_date = st.date_input("입사일")
                
                if st.form_submit_button("사번 발급 및 가입", use_container_width=True):
                    if reg_name and reg_pw:
                        prefix = f"{reg_date.year}-{POS_MAP[reg_pos]}-{DEPT_MAP[reg_dept]}"
                        existing = supabase.table("employees").select("emp_id").like("emp_id", f"{prefix}%").execute()
                        new_id = f"{prefix}-{(len(existing.data)+1):03d}"
                        
                        supabase.table("accounts").insert({"emp_id": new_id, "password": reg_pw, "role": "USER"}).execute()
                        supabase.table("employees").insert({"emp_id": new_id, "name": reg_name, "position": reg_pos, "dept": reg_dept, "hire_date": str(reg_date), "total_leaves": 15}).execute()
                        st.success("계정이 생성되었습니다. 로그인 탭에서 접속해주세요.")
                        st.markdown(f"<div style='text-align:center;'>발급된 사번<br><span class='highlight-id'>{new_id}</span></div>", unsafe_allow_html=True)
                    else: st.warning("이름과 비밀번호를 입력해주세요.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# =====================================================================
# 메인 어플리케이션 화면
# =====================================================================
user = st.session_state.user

st.sidebar.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
if st.sidebar.button("로그아웃"):
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()

menu_options = ["대시보드", "개인정보 관리", "주간 타임시트", "근태 예외 기안", "연장근무 신청", "내 결재함"]
if user['role'] in ['MANAGER', 'HR']: menu_options.append("전사 감사 콘솔")
if user['role'] == 'HR': menu_options.append("직원 및 권한 관리(HR)")

menu = st.sidebar.radio("메뉴 선택", menu_options)

st.markdown(f"<div style='padding-top:10px; font-weight:bold; font-size:16px;'>🏢 {user['dept']} <span style='color:#86BC25;'>{user['name']}</span>님, 환영합니다. (권한: {user['role']})</div>", unsafe_allow_html=True)
st.divider()

def get_approver_list():
    res = supabase.table("employees").select("emp_id, name, position, dept").neq("emp_id", user['emp_id']).execute()
    options = {"선택 안함 (없음)": None}
    for e in res.data: options[f"{e['name']} {e['position']} ({e['dept']})"] = (e['emp_id'], e['name'])
    return options

# --- 메뉴 1: 대시보드 ---
if menu == "대시보드":
    st.markdown("<h2>Dashboard</h2>", unsafe_allow_html=True)
    
    # 프로필 사진 불러오기
    photo_res = supabase.table("user_profile").select("photo_url").eq("emp_id", user['emp_id']).execute()
    current_photo = base64.b64decode(photo_res.data[0]['photo_url']) if photo_res.data and photo_res.data[0]['photo_url'] else None

    prof_col1, prof_col2 = st.columns([1, 4])
    with prof_col1:
        if current_photo: st.image(current_photo, width=150)
        else: st.markdown("<div class='empty-image-box'>이미지를<br>등록하세요</div>", unsafe_allow_html=True)
    
    with prof_col2:
        st.markdown(f"""
            <div class='profile-info'>
                <div class='profile-name'>{user['name']}</div>
                <span class='profile-label'>사번</span> <span class='profile-value'>{user['emp_id']}</span><br>
                <span class='profile-label'>직급</span> <span class='profile-value'>{user['position']}</span><br>
                <span class='profile-label'>부서</span> <span class='profile-value'>{user['dept']}</span><br>
            </div>
        """, unsafe_allow_html=True)
    st.divider()
    
    today = date.today()
    wl_res = supabase.table("work_logs").select("hours").eq("emp_id", user['emp_id']).like("work_date", f"{today.year}-{today.month:02d}%").execute()
    m_hours = sum(r['hours'] for r in wl_res.data) if wl_res.data else 0.0
    
    lv_res = supabase.table("leave_requests").select("id").eq("emp_id", user['emp_id']).eq("final_status", "승인 완료").execute()
    used_leaves = len(lv_res.data) if lv_res.data else 0
    
    col1, col2 = st.columns(2)
    with col1: st.metric("이번 달 누적 근무 시간", f"{m_hours} 시간")
    with col2: st.metric("잔여 연차", f"{user['total_leaves'] - used_leaves} 일")

# --- 메뉴 2: 개인정보 관리 (복구됨) ---
elif menu == "개인정보 관리":
    st.markdown("<h2>개인정보 관리</h2>", unsafe_allow_html=True)
    with st.form("profile_form"):
        st.info("이름, 부서 등 핵심 인사 정보는 HR 부서만 수정할 수 있습니다.")
        new_photo = st.file_uploader("프로필 사진 업데이트 (JPG/PNG)", type=['jpg', 'jpeg', 'png'])
        
        if st.form_submit_button("사진 저장하기") and new_photo:
            # 사진을 문자열(Base64)로 변환
            b64_str = base64.b64encode(new_photo.read()).decode()
            
            existing = supabase.table("user_profile").select("emp_id").eq("emp_id", user['emp_id']).execute()
            if existing.data:
                supabase.table("user_profile").update({"photo_url": b64_str}).eq("emp_id", user['emp_id']).execute()
            else:
                supabase.table("user_profile").insert({"emp_id": user['emp_id'], "photo_url": b64_str}).execute()
                
            st.success("사진 업데이트 완료!")
            st.rerun()

# --- 메뉴 3: 주간 타임시트 ---
elif menu == "주간 타임시트":
    st.markdown("<h2>주간 타임시트</h2>", unsafe_allow_html=True)
    col_date, _ = st.columns([1, 3])
    with col_date: selected_ref_date = st.date_input("조회 기준일", value=date.today())
    start_of_week = selected_ref_date - timedelta(days=selected_ref_date.weekday())
    week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
    st.divider()
    
    cols = st.columns(7)
    week_days = ["월", "화", "수", "목", "금", "토", "일"]
    for i, col in enumerate(cols):
        d_date = week_dates[i]
        wl_res = supabase.table("work_logs").select("*").eq("emp_id", user['emp_id']).eq("work_date", str(d_date)).execute()
        cur_val = wl_res.data[0]['hours'] if wl_res.data else 0.0
        
        with col:
            st.markdown(f"<div style='text-align:center; background-color:#000000; color:#86BC25; padding:10px;'><b>{week_days[i]}</b><br>{d_date.strftime('%m/%d')}</div>", unsafe_allow_html=True)
            days_diff = (date.today() - d_date).days
            is_locked = days_diff > 7 or days_diff < 0
            n_hrs = st.number_input("시간", min_value=0.0, max_value=24.0, value=cur_val, step=0.5, key=f"in_{d_date}", disabled=is_locked, label_visibility="collapsed")
            
            if not is_locked and n_hrs != cur_val:
                if st.button("저장", key=f"bt_{d_date}", use_container_width=True):
                    if wl_res.data: supabase.table("work_logs").update({"hours": n_hrs}).eq("id", wl_res.data[0]['id']).execute()
                    else: supabase.table("work_logs").insert({"emp_id": user['emp_id'], "name": user['name'], "work_date": str(d_date), "hours": n_hrs}).execute()
                    st.rerun()

# --- 메뉴 4: 휴가 관리 ---
elif menu == "휴가 관리":
    st.markdown("<h2>휴가 관리</h2>", unsafe_allow_html=True)
    approver_opts = get_approver_list(); app_keys = list(approver_opts.keys())
    
    with st.form("leave_form"):
        l_type = st.selectbox("종류", ["연차", "오전 반차", "오후 반차", "월차", "병가"])
        c1, c2 = st.columns(2)
        with c1: s_date = st.date_input("시작일")
        with c2: e_date = st.date_input("종료일")
        reason = st.text_input("사유")
        st.markdown("#### 결재 라인 지정")
        app_c1, app_c2 = st.columns(2)
        with app_c1: a1_sel = st.selectbox("1차 결재자 (필수)", app_keys[1:]) 
        with app_c2: a2_sel = st.selectbox("2차 결재자 (선택)", app_keys)
        
        if st.form_submit_button("기안 상신"):
            a1_data = approver_opts[a1_sel]; a2_data = approver_opts[a2_sel]
            a2_id = a2_data[0] if a2_data else None; a2_name = a2_data[1] if a2_data else None
            insert_data = {
                "emp_id": user['emp_id'], "name": user['name'], "type": l_type, 
                "start_date": str(s_date), "end_date": str(e_date), "reason": reason,
                "app1_id": a1_data[0], "app1_name": a1_data[1], "app2_id": a2_id, "app2_name": a2_name,
                "app1_status": "대기", "app2_status": "대기", "final_status": "진행중"
            }
            supabase.table("leave_requests").insert(insert_data).execute()
            st.success("상신이 완료되었습니다.")
            
    st.markdown("#### 내 기안 진행 현황")
    my_lv = supabase.table("leave_requests").select("type, start_date, end_date, app1_name, app1_status, app2_name, app2_status, final_status").eq("emp_id", user['emp_id']).order('id', desc=True).execute()
    if my_lv.data:
        df_my = pd.DataFrame(my_lv.data)
        df_my.columns = ['종류', '시작일', '종료일', '1차결재자', '1차상태', '2차결재자', '2차상태', '최종상태']
        st.dataframe(df_my, use_container_width=True)
        st.download_button("📥 엑셀 추출", data=convert_df_to_csv(df_my), file_name='my_leaves.csv', mime='text/csv')

# --- 메뉴 5: 연장근무 신청 ---
elif menu == "연장근무 신청":
    st.markdown("<h2>연장근무 신청</h2>", unsafe_allow_html=True)
    approver_opts = get_approver_list(); app_keys = list(approver_opts.keys())
    
    with st.form("ot_form"):
        ot_date = st.date_input("일자")
        ot_hours = st.number_input("시간", min_value=0.5, max_value=8.0, step=0.5)
        ot_reason = st.text_area("사유")
        st.markdown("#### 결재 라인 지정")
        app_c1, app_c2 = st.columns(2)
        with app_c1: a1_sel = st.selectbox("1차 결재자", app_keys[1:])
        with app_c2: a2_sel = st.selectbox("2차 결재자", app_keys)
        
        if st.form_submit_button("기안 상신"):
            a1_data = approver_opts[a1_sel]; a2_data = approver_opts[a2_sel]
            a2_id = a2_data[0] if a2_data else None; a2_name = a2_data[1] if a2_data else None
            insert_data = {
                "emp_id": user['emp_id'], "name": user['name'], "date": str(ot_date), "hours": ot_hours, "reason": ot_reason,
                "app1_id": a1_data[0], "app1_name": a1_data[1], "app2_id": a2_id, "app2_name": a2_name,
                "app1_status": "대기", "app2_status": "대기", "final_status": "진행중"
            }
            supabase.table("overtime_logs").insert(insert_data).execute()
            st.success("상신이 완료되었습니다.")
            
    st.markdown("#### 내 연장근무 신청 현황")
    my_ot = supabase.table("overtime_logs").select("date, hours, reason, app1_name, app1_status, app2_name, app2_status, final_status").eq("emp_id", user['emp_id']).order('id', desc=True).execute()
    if my_ot.data:
        df_ot = pd.DataFrame(my_ot.data)
        df_ot.columns = ['일자', '시간', '사유', '1차결재자', '1차상태', '2차결재자', '2차상태', '최종상태']
        st.dataframe(df_ot, use_container_width=True)
        st.download_button("📥 엑셀 추출", data=convert_df_to_csv(df_ot), file_name='my_overtime.csv', mime='text/csv')

# --- 메뉴 6: 내 결재함 ---
elif menu == "내 결재함":
    st.markdown("<h2>내 결재함 (Approval Inbox)</h2>", unsafe_allow_html=True)
    
    app1_req = supabase.table("leave_requests").select("*").eq("app1_id", user['emp_id']).eq("app1_status", "대기").execute()
    app2_req = supabase.table("leave_requests").select("*").eq("app2_id", user['emp_id']).eq("app1_status", "승인").eq("app2_status", "대기").execute()
    
    my_tasks = []
    for r in app1_req.data: my_tasks.append((r, '1차'))
    for r in app2_req.data: my_tasks.append((r, '2차'))
    
    if not my_tasks: st.info("대기 중인 결재 건이 없습니다.")
    else:
        for req, step in my_tasks:
            st.markdown(f"<div class='approval-card'><span class='status-badge'>{step} 결재 대기</span><br><br><b>기안자:</b> {req['name']} &nbsp;|&nbsp; <b>종류:</b> {req['type']}<br><b>일정:</b> {req['start_date']} ~ {req['end_date']}<br><b>사유:</b> {req['reason']}</div>", unsafe_allow_html=True)
            b1, b2, _ = st.columns([1,1,6])
            with b1:
                if st.button("승인", key=f"app_{req['id']}"):
                    if step == '1차':
                        if req['app2_id']: supabase.table("leave_requests").update({"app1_status": "승인"}).eq("id", req['id']).execute()
                        else: supabase.table("leave_requests").update({"app1_status": "승인", "final_status": "승인 완료"}).eq("id", req['id']).execute()
                    else: supabase.table("leave_requests").update({"app2_status": "승인", "final_status": "승인 완료"}).eq("id", req['id']).execute()
                    st.rerun()
            with b2:
                if st.button("반려", key=f"rej_{req['id']}"):
                    if step == '1차': supabase.table("leave_requests").update({"app1_status": "반려", "final_status": "반려"}).eq("id", req['id']).execute()
                    else: supabase.table("leave_requests").update({"app2_status": "반려", "final_status": "반려"}).eq("id", req['id']).execute()
                    st.rerun()

# --- 메뉴 7: 전사 감사 콘솔 ---
elif menu == "전사 감사 콘솔":
    st.markdown("<h2>전사 데이터 감사 (Audit)</h2>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["휴가 기안 내역", "연장근무 내역", "타임시트 원본"])
    
    with tab1:
        lv_all = supabase.table("leave_requests").select("emp_id, name, type, start_date, end_date, final_status").order('id', desc=True).execute()
        if lv_all.data:
            df_lv = pd.DataFrame(lv_all.data)
            df_lv.columns = ['사번', '성명', '종류', '시작일', '종료일', '최종상태']
            st.dataframe(df_lv, use_container_width=True)
            st.download_button("📥 엑셀 추출", data=convert_df_to_csv(df_lv), file_name='audit_leave.csv', mime='text/csv')
            
    with tab2:
        ot_all = supabase.table("overtime_logs").select("emp_id, name, date, hours, final_status").order('id', desc=True).execute()
        if ot_all.data:
            df_ot = pd.DataFrame(ot_all.data)
            df_ot.columns = ['사번', '성명', '일자', '시간', '최종상태']
            st.dataframe(df_ot, use_container_width=True)
            st.download_button("📥 엑셀 추출", data=convert_df_to_csv(df_ot), file_name='audit_overtime.csv', mime='text/csv')
            
    with tab3:
        wl_all = supabase.table("work_logs").select("emp_id, name, work_date, hours").order('work_date', desc=True).execute()
        if wl_all.data:
            df_wl = pd.DataFrame(wl_all.data)
            df_wl.columns = ['사번', '성명', '일자', '시간']
            st.dataframe(df_wl, use_container_width=True)
            st.download_button("📥 엑셀 추출", data=convert_df_to_csv(df_wl), file_name='audit_work.csv', mime='text/csv')

# --- 메뉴 8: 직원 및 권한 관리 ---
elif menu == "직원 및 권한 관리(HR)":
    st.markdown("<h2>직원 및 시스템 권한 관리</h2>", unsafe_allow_html=True)
    
    emps = supabase.table("employees").select("*").order('hire_date', desc=True).execute().data
    accs = supabase.table("accounts").select("emp_id, role").execute().data
    
    df_emps = pd.DataFrame(emps)
    df_accs = pd.DataFrame(accs)
    
    if not df_emps.empty and not df_accs.empty:
        df_merged = pd.merge(df_emps, df_accs, on="emp_id")
        user_dict = {f"[{row['role']}] {row['name']} ({row['emp_id']})": row['emp_id'] for _, row in df_merged.iterrows()}
        
        with st.form("role_update_form"):
            col1, col2 = st.columns(2)
            with col1: target_user = st.selectbox("직원 선택", list(user_dict.keys()))
            with col2: new_role = st.selectbox("변경할 권한", ["USER", "MANAGER", "HR"])
            if st.form_submit_button("권한 업데이트"):
                supabase.table("accounts").update({"role": new_role}).eq("emp_id", user_dict[target_user]).execute()
                st.success("권한이 성공적으로 변경되었습니다.")
                st.rerun()
                
        df_display = df_merged[['emp_id', 'name', 'position', 'dept', 'role']]
        df_display.columns = ['사번', '성명', '직급', '부서', '권한']
        st.dataframe(df_display, use_container_width=True)
