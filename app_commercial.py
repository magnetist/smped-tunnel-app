import streamlit as st
import uuid
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
from io import BytesIO
from datetime import datetime
from tunnel_master_logic import TunnelType, TunnelSafetySystem, TunnelSection, TunnelSpan, DataManager, ProjectMetadata, InspectionData

# ---------------------------------------------------------
# 1. 설정 및 스타일
# ---------------------------------------------------------
st.set_page_config(page_title="SM-PED Tunnel Tablet", layout="wide")

if 'projects' not in st.session_state:
    st.session_state['projects'] = DataManager.load_all_projects()
if 'active_project_id' not in st.session_state:
    st.session_state['active_project_id'] = None

def reset_indices():
    st.session_state['sel_sec_idx'] = 0
    st.session_state['sel_span_idx'] = 0

st.markdown("""
    <style>
    .main { font-family: 'Pretendard', sans-serif; }
    .header-bar { padding: 20px; background-color: #002b5c; border-bottom: 4px solid #b38f00; color: white; margin-bottom: 20px; }
    .stSelectbox label, .stNumberInput label, .stSlider label { font-size: 16px !important; font-weight: bold !important; }
    .input-card {
        background-color: var(--secondary-background-color);
        padding: 20px; border-radius: 12px;
        border: 1px solid rgba(128,128,128, 0.2);
        margin-bottom: 20px;
    }
    div.stButton > button {
        height: 50px; font-size: 16px; font-weight: bold; border-radius: 8px; width: 100%;
    }
    .report-container { background-color: #ffffff !important; padding: 40px; color: #000000 !important; }
    .report-table th { background-color: #f8f9fa !important; color: #000000 !important; font-size: 14px; padding: 12px; }
    .report-table td { color: #000000 !important; font-size: 14px; padding: 12px; }
    
    /* 제원 관리 테이블 스타일 */
    .structure-box { background-color: #e3f2fd; padding: 15px; border-radius: 8px; border: 1px solid #90caf9; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.markdown(f"""
    <div class="header-bar">
        <div style="font-size:24px; font-weight:800;">SM-PED Tunnel <span style="font-size:16px; font-weight:400; opacity:0.8;"></span></div>
    </div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 차트 함수
# ---------------------------------------------------------
def draw_report_heatmap(sections):
    data = []
    current_dist = 0
    color_map = {'A': '#2ecc71', 'B': '#3498db', 'C': '#f1c40f', 'D': '#e67e22', 'E': '#e74c3c'}
    for sec in sections:
        for span in sec.spans:
            grade = span.result_cache.get('grade', 'A')[0]
            data.append(dict(Task=f"Span {span.span_no}", Start=current_dist, Finish=current_dist + span.length, Grade=grade, Color=color_map.get(grade, '#ccc')))
            current_dist += span.length
    if not data: return None
    df = pd.DataFrame(data)
    fig = go.Figure()
    for _, row in df.iterrows():
        fig.add_trace(go.Bar(x=[row['Finish'] - row['Start']], y=["Status"], base=[row['Start']], orientation='h', marker=dict(color=row['Color'], line=dict(color='black', width=1)), showlegend=False))
    fig.update_layout(height=120, margin=dict(l=10, r=10, t=25, b=10), xaxis=dict(showticklabels=True, title="Distance (m)", color="black", gridcolor="#eee"), yaxis=dict(showticklabels=False, color="black"), title=dict(text="터널 상태 분포도", font=dict(size=14, color="black")), plot_bgcolor='white', paper_bgcolor='white', font=dict(color="black"))
    return fig

def draw_screen_heatmap(sections):
    data = []
    current_dist = 0
    color_map = {'A': '#2ecc71', 'B': '#3498db', 'C': '#f1c40f', 'D': '#e67e22', 'E': '#e74c3c'}
    for sec in sections:
        for span in sec.spans:
            grade = span.result_cache.get('grade', 'A')[0]
            f_val = span.result_cache.get('f_value', 0.0)
            data.append(dict(Task=f"Span {span.span_no}", Start=current_dist, Finish=current_dist + span.length, Grade=grade, F_Value=f_val, Section=f"Sec {sec.id} ({sec.type.label})", Color=color_map.get(grade, '#ccc')))
            current_dist += span.length
    if not data: return None
    df = pd.DataFrame(data)
    fig = go.Figure()
    for _, row in df.iterrows():
        fig.add_trace(go.Bar(x=[row['Finish'] - row['Start']], y=["Status"], base=[row['Start']], orientation='h', marker=dict(color=row['Color'], line=dict(color='white', width=1)), hovertemplate=f"<b>{row['Section']}</b><br>Span No.{row['Task'].split()[-1]}<br>등급: {row['Grade']}<br>F: {row['F_Value']:.4f}<extra></extra>", showlegend=False))
    fig.update_layout(height=120, margin=dict(l=10, r=10, t=30, b=10), xaxis=dict(title="터널 거리 (m)", showgrid=True), yaxis=dict(showticklabels=False), title=dict(text="[터널 전체 구간별 안전등급 현황도]", font=dict(size=14, color="#002b5c")), plot_bgcolor='rgba(0,0,0,0)')
    return fig

# ---------------------------------------------------------
# [MODE 1] 프로젝트 선택
# ---------------------------------------------------------
if st.session_state['active_project_id'] is None:
    st.info("Daum Engineering")
    
    col1, col2 = st.columns([2, 1], gap="large")
    with col2:
        st.markdown("### 🆕 신규 프로젝트")
        with st.form("create_proj_form", border=True):
            name = st.text_input("시설물명", placeholder="예: 판교1터널")
            inspector = st.text_input("점검자", "홍길동")
            st.write("") 
            if st.form_submit_button("프로젝트 생성 (Create)", type="primary", use_container_width=True):
                if name:
                    pid = str(uuid.uuid4())[:8]
                    st.session_state['projects'][pid] = ProjectMetadata(pid, name, inspector, "특급", "(주)다음기술단", datetime.now().strftime("%Y-%m-%d"))
                    DataManager.save_all_projects(st.session_state['projects'])
                    st.rerun()
                else:
                    st.error("시설물명을 입력해주세요.")

    with col1:
        st.markdown("### 📂 내 프로젝트 목록")
        if not st.session_state['projects']: 
            st.warning("등록된 프로젝트가 없습니다.")
        else:
            for pid, p in st.session_state['projects'].items():
                with st.container(border=True):
                    c_info, c_btn = st.columns([3, 1])
                    with c_info:
                        st.markdown(f"**{p.name}**")
                        st.caption(f"{p.date_str} | {p.inspector} | 구간: {len(p.sections)}개")
                    with c_btn:
                        if st.button("열기 ▶", key=f"op_{pid}", type="primary", use_container_width=True):
                            st.session_state['active_project_id'] = pid
                            reset_indices()
                            st.rerun()
                        if st.button("삭제", key=f"del_{pid}", use_container_width=True):
                            del st.session_state['projects'][pid]
                            DataManager.save_all_projects(st.session_state['projects'])
                            st.rerun()

# ---------------------------------------------------------
# [MODE 2] 작업 공간
# ---------------------------------------------------------
else:
    pid = st.session_state['active_project_id']
    if pid not in st.session_state['projects']:
        st.session_state['active_project_id'] = None
        st.rerun()
        
    proj = st.session_state['projects'][pid]
    system = TunnelSafetySystem()
    
    with st.sidebar:
        if st.button("◀ 목록으로", use_container_width=True): 
            st.session_state['active_project_id'] = None
            st.rerun()
        st.divider()
        st.markdown(f"**{proj.name}**")
        
        c1, c2 = st.columns(2)
        if c1.button("💾 저장", type="primary", use_container_width=True):
            DataManager.save_all_projects(st.session_state['projects'])
            st.toast("저장 완료!")
        if c2.button("↩ 복구", use_container_width=True):
            st.session_state['projects'] = DataManager.load_all_projects()
            reset_indices()
            st.rerun()

        st.markdown("---")
        with st.expander("➕ 구간 관리", expanded=not proj.sections):
            with st.form("add_sec"):
                sType = st.selectbox("형식", ["NATM (철근)", "NATM (무근)", "개착식 (BOX)", "TBM (세그먼트)", "재래식 (무근)"])
                tLen = st.number_input("총연장(m)", 100.0)
                uLen = st.number_input("기준 단위(m)", 20.0)
                if st.form_submit_button("구간 생성"):
                    if tLen > 0 and uLen > 0:
                        tm = {"NATM (철근)": TunnelType.NATM_RC, "NATM (무근)": TunnelType.NATM_PLAIN, "개착식 (BOX)": TunnelType.OPEN_CUT, "TBM (세그먼트)": TunnelType.TBM_SEGMENT, "재래식 (무근)": TunnelType.ASSM_PLAIN}
                        new_sec = TunnelSection(proj.next_section_id, tm[sType], tLen, uLen)
                        cnt = int(tLen // uLen)
                        for i in range(cnt): new_sec.spans.append(TunnelSpan(i+1, uLen))
                        if tLen % uLen > 0: new_sec.spans.append(TunnelSpan(cnt+1, tLen % uLen))
                        proj.sections.append(new_sec)
                        proj.next_section_id += 1
                        DataManager.save_all_projects(st.session_state['projects'])
                        st.rerun()
            
            if proj.sections and st.button("마지막 구간 삭제", use_container_width=True):
                proj.sections.pop()
                reset_indices()
                DataManager.save_all_projects(st.session_state['projects'])
                st.rerun()

    # [MAIN] 상단 내비게이션
    col_nav1, col_nav2, col_save_big = st.columns([2, 2, 1])
    
    if not proj.sections: 
        st.warning("👈 사이드바에서 구간을 생성해주세요.")
    else:
        if st.session_state['sel_sec_idx'] >= len(proj.sections): st.session_state['sel_sec_idx'] = 0
        
        with col_nav1:
            sec_opts = [f"Sec {s.id} ({s.type.label})" for s in proj.sections]
            s_idx = st.selectbox("1️⃣ 구간 선택", range(len(sec_opts)), format_func=lambda x: sec_opts[x], key="nav_sec")
            st.session_state['sel_sec_idx'] = s_idx
        
        with col_nav2:
            curr_sec = proj.sections[s_idx]
            if st.session_state['sel_span_idx'] >= len(curr_sec.spans): st.session_state['sel_span_idx'] = 0
            span_opts = [f"No.{sp.span_no} ({sp.result_cache.get('grade', 'A')[0]})" for sp in curr_sec.spans]
            sp_idx = st.selectbox("2️⃣ 스판 선택", range(len(span_opts)), format_func=lambda x: span_opts[x], key="nav_span")
            st.session_state['sel_span_idx'] = sp_idx
            
        with col_save_big:
            if st.button("💾 저장하기", type="primary", use_container_width=True, key="main_save"):
                DataManager.save_all_projects(st.session_state['projects'])
                st.toast("저장되었습니다!")

        curr_span = curr_sec.spans[st.session_state['sel_span_idx']]
        d = curr_span.data

        # 히트맵
        fig_map = draw_screen_heatmap(proj.sections)
        if fig_map: st.plotly_chart(fig_map, use_container_width=True)

        # [NEW] 스판 제원 일괄 관리 (Structure Manager)
        with st.expander("📏 스판 길이(m) 일괄 변경"):
            st.markdown('<div class="structure-box">', unsafe_allow_html=True)
            st.info("아래 표에서 각 스판의 길이를 직접 수정할 수 있습니다. (예: 20m -> 15.5m)")
            
            # 데이터프레임 생성
            span_data = [{"Span No": s.span_no, "Length (m)": s.length} for s in curr_sec.spans]
            df_struct = pd.DataFrame(span_data)
            
            # 데이터 에디터 (수정 가능)
            edited_df = st.data_editor(
                df_struct, 
                column_config={"Span No": st.column_config.NumberColumn(disabled=True), "Length (m)": st.column_config.NumberColumn(min_value=0.1, max_value=100.0, step=0.1)},
                use_container_width=True,
                hide_index=True
            )
            
            if st.button("변경된 길이 적용하기"):
                # 수정된 데이터 반영
                new_lengths = edited_df["Length (m)"].tolist()
                total_len_calc = 0
                for i, span in enumerate(curr_sec.spans):
                    span.length = new_lengths[i]
                    total_len_calc += span.length
                
                # 구간 전체 연장도 자동 업데이트
                curr_sec.total_length = total_len_calc
                DataManager.save_all_projects(st.session_state['projects'])
                st.success(f"적용 완료! 구간 총 연장이 {total_len_calc:.2f}m로 업데이트되었습니다.")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # 탭 구성
        tab1, tab2 = st.tabs(["🖊️ 현장 입력 (Input)", "📄 보고서 (Report)"])
        
        # [TAB 1] 입력
        with tab1:
            c_len, c_copy = st.columns([3, 1])
            with c_len:
                unique_key = f"{curr_sec.id}_{curr_span.span_no}"
                # 개별 길이 수정도 가능 (양쪽 동기화)
                curr_span.length = st.number_input("📏 현재 스판 길이 (m)", value=curr_span.length, key=f"len_{unique_key}")
            with c_copy:
                if curr_span.span_no > 1:
                    if st.button("📋 이전값 복사", use_container_width=True):
                        import copy
                        prev = curr_sec.spans[st.session_state['sel_span_idx']-1]
                        curr_span.data = copy.deepcopy(prev.data)
                        st.success("복사됨 (저장필요)")
                        st.rerun()

            col_left, col_right = st.columns(2, gap="medium")
            
            with col_left:
                st.markdown('<div class="input-card">', unsafe_allow_html=True)
                st.markdown("##### 1. 라이닝 평가")
                d.location = st.selectbox("📍 손상위치", ["전구간", "천정부(Arch)", "우측벽(Right)", "좌측벽(Left)", "바닥(Invert)"], index=["전구간", "천정부(Arch)", "우측벽(Right)", "좌측벽(Left)", "바닥(Invert)"].index(d.location), key=f"loc_{unique_key}")
                d.crack_width = st.number_input("⚡ 최대 균열폭 (mm)", 0.0, 10.0, d.crack_width, 0.1, key=f"cw_{unique_key}")
                st.markdown("---")
                d.leakage_grade = st.select_slider("💧 누수 상태", ["a","b","c","d","e"], value=d.leakage_grade, key=f"lg_{unique_key}")
                d.breakage_grade = st.select_slider("🔨 파손/손상", ["a","b","c","d","e"], value=d.breakage_grade, key=f"bg_{unique_key}")
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="input-card">', unsafe_allow_html=True)
                st.markdown("##### 2. 재질열화 (Worst Case 자동)")
                d.material.spalling_grade = st.select_slider("박리/박락", ["a","b","c","d","e"], value=d.material.spalling_grade, key=f"msp_{unique_key}")
                d.material.efflorescence_grade = st.select_slider("백태", ["a","b","c","d","e"], value=d.material.efflorescence_grade, key=f"mef_{unique_key}")
                d.material.rebar_grade = st.select_slider("철근노출", ["a","b","c","d","e"], value=d.material.rebar_grade, key=f"mr_{unique_key}")
                d.material.carbonation_grade = st.select_slider("탄산화", ["a","b","c","d","e"], value=d.material.carbonation_grade, key=f"mca_{unique_key}")
                st.markdown('</div>', unsafe_allow_html=True)

            with col_right:
                st.markdown('<div class="input-card">', unsafe_allow_html=True)
                st.markdown("##### 3. 주변상태 & 부대시설")
                d.sur_drain = st.slider("배수 상태 (0~4점)", 0, 4, d.sur_drain, key=f"sd_{unique_key}")
                d.sur_ground = st.slider("지반 상태 (0~4점)", 0, 4, d.sur_ground, key=f"sg_{unique_key}")
                is_p = (curr_span.span_no==1) or (curr_span.span_no==len(curr_sec.spans))
                d.sur_portal = st.slider("갱문 상태 (0~4점)", 0, 4, d.sur_portal if is_p else 0, disabled=not is_p, key=f"sp_{unique_key}")
                st.markdown("---")
                d.aux_score = st.slider("💡 부대시설 결함(f)", 0.0, 1.0, d.aux_score, 0.05, key=f"aux_{unique_key}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="input-card">', unsafe_allow_html=True)
                st.markdown("##### 📷 사진 기록")
                st.file_uploader("사진 업로드", key=f"p_{unique_key}")
                st.markdown('</div>', unsafe_allow_html=True)

            res = system.calculate_span(curr_span, curr_sec.type)
            msg_color = "red" if res['grade'] in ['D (미흡)', 'E (불량)'] else "green" if res['grade'] == 'A (우수)' else "blue"
            st.markdown(f"""<div style="background-color:#fff; border-left: 10px solid {msg_color}; padding:20px; border-radius:8px; box-shadow:0 2px 10px rgba(0,0,0,0.1);"><h3 style="margin:0; color:black;">판정 결과: <span style="color:{msg_color};">{res['grade']}</span> (F={res['f_value']:.4f})</h3><small style="color:gray;">{ " / ".join(res['alerts']) if res['alerts'] else "특이사항 없음" }</small></div>""", unsafe_allow_html=True)

        # [TAB 2] 보고서
        with tab2:
            summary = system.calculate_project_summary(proj.sections)
            if summary:
                st.markdown("#### 📝 종합 의견 작성")
                proj.opinion = st.text_area("점검자 소견", value=proj.opinion, height=150, key=f"op_{pid}")
                
                data_list = []
                for s in summary['span_results']:
                    data_list.append({
                        "구간": s['sec_id'], "형식": s['type'], "Span": s['span_no'], "길이(m)": s['length'],
                        "균열": s['data'].crack_width, "누수": s['data'].leakage_grade, "등급": s['result']['grade']
                    })
                df = pd.DataFrame(data_list)
                
                safe_name = re.sub(r'[\\/*?:"<>|]', "", proj.name)
                
                # 엑셀 예외처리
                try:
                    out = BytesIO()
                    with pd.ExcelWriter(out, engine='xlsxwriter') as w: df.to_excel(w, index=False)
                    st.download_button("📥 엑셀 다운로드", data=out.getvalue(), file_name=f"{safe_name}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                except ModuleNotFoundError:
                    st.error("xlsxwriter 라이브러리가 필요합니다.")
                
                st.divider()
                st.markdown('<div class="report-container">', unsafe_allow_html=True)
                st.markdown(f'<div style="text-align:center;"><h2 style="color:black !important; text-decoration:underline;">{proj.name} 정밀안전진단 결과보고서</h2></div><br>', unsafe_allow_html=True)
                st.markdown(f"""
                <table class="report-table">
                    <tr><th width="20%">시설물명</th><td width="30%">{proj.name}</td><th width="20%">점검일자</th><td width="30%">{proj.date_str}</td></tr>
                    <tr><th>점검자</th><td>{proj.inspector}</td><th>소속</th><td>{proj.company} ({proj.position})</td></tr>
                    <tr><th>총 연장</th><td>{summary['total_length']:.1f} m</td><th>구간 수</th><td>{len(proj.sections)} 개</td></tr>
                </table><br>
                """, unsafe_allow_html=True)
                fg = summary['final_grade']
                color_code = "#e74c3c" if "D" in fg or "E" in fg else "#3498db"
                st.markdown(f"""
                <div style="border: 2px solid {color_code}; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0; background-color: #fff !important;">
                    <strong style="font-size:16px; color:black;">종합 안전등급</strong><br>
                    <span style="font-size:32px; font-weight:800; color:{color_code};">{fg}</span><br>
                    <span style="font-size:14px; color:black;">(종합 결함지수 F = {summary['final_f']:.4f})</span>
                </div><br>
                """, unsafe_allow_html=True)
                st.markdown('<h4 style="color:black !important;">[터널 상태 분포도]</h4>', unsafe_allow_html=True)
                fig_report = draw_report_heatmap(proj.sections)
                if fig_report: st.plotly_chart(fig_report, use_container_width=True)
                st.markdown('<br><h4 style="color:black !important;">[종합 의견 및 조치사항]</h4>', unsafe_allow_html=True)
                op_text = proj.opinion if proj.opinion else "(작성된 의견이 없습니다)"
                st.markdown(f"""<div class="opinion-box">{op_text}</div><br>""", unsafe_allow_html=True)
                st.markdown('<h4 style="color:black !important;">[주요 구간 세부 평가 내역]</h4>', unsafe_allow_html=True)
                rows = ""
                limit_rows = summary['span_results'][:20] 
                for s in limit_rows:
                    rows += f"<tr><td>{s['sec_id']}</td><td>{s['type']}</td><td>{s['span_no']}</td><td>{s['result']['grade']}</td><td>{s['result']['f_value']:.4f}</td></tr>"
                st.markdown(f"""<table class="report-table"><thead><tr><th>구간</th><th>형식</th><th>Span No</th><th>안전등급</th><th>결함지수(F)</th></tr></thead><tbody>{rows}</tbody></table>""", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
