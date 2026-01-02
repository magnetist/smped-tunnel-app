import streamlit as st
import uuid
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime
from tunnel_master_logic import TunnelType, TunnelSafetySystem, TunnelSection, TunnelSpan, DataManager, ProjectMetadata, InspectionData

# ---------------------------------------------------------
# 설정 및 스타일
# ---------------------------------------------------------
st.set_page_config(page_title="SM-PED Tunnel Pro", layout="wide")

if 'projects' not in st.session_state:
    st.session_state['projects'] = DataManager.load_all_projects()
if 'active_project_id' not in st.session_state:
    st.session_state['active_project_id'] = None

st.markdown("""
    <style>
    .main { font-family: 'Pretendard', sans-serif; }
    
    /* 헤더바 스타일 */
    .header-bar { 
        padding: 15px 30px; 
        background-color: #002b5c; 
        border-bottom: 3px solid #b38f00; 
        color: white; 
        display: flex; justify-content: space-between; align-items: center; 
    }
    
    /* 프로젝트 카드 */
    .project-card { 
        border: 1px solid #dee2e6; 
        padding: 20px; 
        border-radius: 8px; 
        margin-bottom: 15px; 
        background-color: var(--secondary-background-color); 
        transition: 0.3s; 
    }
    .project-card:hover { border-color: #002b5c; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    
    /* 입력 그룹 헤더 */
    .step-header { 
        font-size: 15px; font-weight: bold; color: #002b5c; margin-top: 10px; margin-bottom: 5px; 
        border-left: 4px solid #b38f00; padding-left: 8px; 
    }
    
    /* 저장 컨트롤 패널 */
    .save-control { 
        background-color: #f1f3f5; border: 1px solid #ced4da; border-radius: 8px; 
        padding: 10px; margin-bottom: 20px; text-align: center; color: black;
    }

    /* ★★★ [핵심] 보고서 스타일 강제 적용 (다크모드 무시) ★★★ */
    .report-container {
        background-color: #ffffff !important; /* 배경 무조건 흰색 */
        padding: 40px;
        border-radius: 4px;
        border: 1px solid #ddd;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        color: #000000 !important; /* 기본 글씨 검정 */
        margin-bottom: 30px;
    }
    
    /* 보고서 내부 모든 텍스트 강제 검정색 */
    .report-container h1, .report-container h2, .report-container h3, 
    .report-container h4, .report-container h5, .report-container p, 
    .report-container span, .report-container div, .report-container li {
        color: #000000 !important;
    }

    /* 보고서 테이블 스타일 */
    .report-table { 
        width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; 
        color: #000000 !important; 
        background-color: #ffffff !important;
    }
    .report-table th { 
        background-color: #f1f3f5 !important; /* 헤더 회색 배경 */
        border: 1px solid #888 !important; 
        padding: 10px; text-align: center; font-weight: bold; 
        color: #000000 !important; 
    }
    .report-table td { 
        border: 1px solid #888 !important; 
        padding: 8px; text-align: center; 
        color: #000000 !important; 
        background-color: #ffffff !important;
    }

    /* 의견 박스 */
    .opinion-box { 
        border: 1px solid #888 !important; 
        padding: 15px; min-height: 100px; font-size: 14px; 
        color: #000000 !important; 
        background-color: #ffffff !important;
        white-space: pre-wrap; /* 줄바꿈 보존 */
    }
    
    /* 종합 등급 박스 */
    .grade-box {
        padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;
        background-color: #fff !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown(f"""
    <div class="header-bar">
        <div><span style="font-size:22px; font-weight:800; letter-spacing:0.5px;">SM-PED Tunnel</span> <span style="font-size:13px; opacity:0.8; margin-left:10px;"></span></div>
        <div style="text-align:right; font-size:12px;">(주)다음기술단 기술연구소<br>Arch: 이승현 차장</div>
    </div><br>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 함수: 히트맵 (보고서용 - 흰 배경/검은 글씨 강제)
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
        fig.add_trace(go.Bar(
            x=[row['Finish'] - row['Start']], y=["Status"], base=[row['Start']], orientation='h',
            marker=dict(color=row['Color'], line=dict(color='black', width=1)), showlegend=False
        ))
    
    # ★ 다크모드 무시 설정: 배경 흰색, 글씨 검정색 ★
    fig.update_layout(
        height=120, margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(showticklabels=True, title="Distance (m)", color="black", gridcolor="#eee"), 
        yaxis=dict(showticklabels=False, color="black"), 
        title=dict(text="터널 상태 분포도 (Tunnel Status Map)", font=dict(size=14, color="black")),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color="black")
    )
    return fig

# ---------------------------------------------------------
# 함수: 히트맵 (화면용 - 입력 탭용)
# ---------------------------------------------------------
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
        fig.add_trace(go.Bar(
            x=[row['Finish'] - row['Start']], y=["Status"], base=[row['Start']], orientation='h',
            marker=dict(color=row['Color'], line=dict(color='white', width=1)),
            hovertemplate=f"<b>{row['Section']}</b><br>Span No.{row['Task'].split()[-1]}<br>등급: {row['Grade']}<br>F: {row['F_Value']:.4f}<extra></extra>",
            showlegend=False
        ))
    fig.update_layout(height=120, margin=dict(l=10, r=10, t=30, b=10), xaxis=dict(title="터널 거리 (m)", showgrid=True), yaxis=dict(showticklabels=False), title=dict(text="[터널 전체 구간별 안전등급 현황도]", font=dict(size=14, color="#002b5c")), plot_bgcolor='rgba(0,0,0,0)')
    return fig

# ---------------------------------------------------------
# [MODE 1] 프로젝트 선택
# ---------------------------------------------------------
if st.session_state['active_project_id'] is None:
    st.title("프로젝트 관리 Dashboard")
    st.info("본 시스템은 수동 저장(Manual Save) 방식입니다. 작업 후 반드시 [저장] 버튼을 눌러주세요.")

    col1, col2 = st.columns([2, 1], gap="large")
    with col2:
        st.markdown("### 신규 프로젝트")
        with st.form("create_proj"):
            name = st.text_input("시설물명", placeholder="예: 판교1터널")
            inspector = st.text_input("점검자", "홍길동")
            if st.form_submit_button("생성", type="primary", use_container_width=True):
                if name:
                    pid = str(uuid.uuid4())[:8]
                    st.session_state['projects'][pid] = ProjectMetadata(pid, name, inspector, "특급", "(주)다음기술단", datetime.now().strftime("%Y-%m-%d"))
                    DataManager.save_all_projects(st.session_state['projects'])
                    st.rerun()

    with col1:
        st.markdown("### 내 프로젝트 목록")
        if not st.session_state['projects']: st.warning("등록된 프로젝트가 없습니다.")
        else:
            for pid, p in st.session_state['projects'].items():
                with st.container():
                    st.markdown(f"""<div class="project-card"><div style="display:flex; justify-content:space-between;"><div><h4 style="margin:0; color:#002b5c;">{p.name}</h4><small style="color:gray;">{p.date_str} | {p.inspector}</small></div><div style="text-align:right;"><span style="font-size:12px; background:#e9ecef; padding:4px 8px; border-radius:4px; font-weight:bold;">구간: {len(p.sections)}개</span></div></div></div>""", unsafe_allow_html=True)
                    c1, c2, c3 = st.columns([2, 1, 1])
                    if c1.button(f"작업 열기", key=f"op_{pid}", type="primary", use_container_width=True):
                        st.session_state['active_project_id'] = pid
                        st.rerun()
                    if c3.button("삭제", key=f"del_{pid}", use_container_width=True):
                        del st.session_state['projects'][pid]
                        DataManager.save_all_projects(st.session_state['projects'])
                        st.rerun()

# ---------------------------------------------------------
# [MODE 2] 작업 공간
# ---------------------------------------------------------
else:
    pid = st.session_state['active_project_id']
    proj = st.session_state['projects'][pid]
    system = TunnelSafetySystem()
    
    with st.sidebar:
        if st.button("< 목록으로"): 
            st.session_state['active_project_id'] = None
            st.rerun()
        st.markdown("---")
        st.markdown("""<div class="save-control"><b>데이터 저장 제어</b><br><span style="font-size:11px; color:#555;">변경 사항은 저장 버튼을 눌러야 반영됩니다.</span></div>""", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if c1.button("저장", type="primary", use_container_width=True):
            DataManager.save_all_projects(st.session_state['projects'])
            st.toast("저장 완료!", icon="💾")
        if c2.button("복구", use_container_width=True):
            st.session_state['projects'] = DataManager.load_all_projects()
            st.rerun()

        st.markdown("---")
        st.markdown(f"**{proj.name}**")
        
        if proj.sections:
            st.caption(f"총 {len(proj.sections)}개 구간 작업 중")

        with st.expander("구간 추가", expanded=not proj.sections):
            with st.form("add_sec"):
                sType = st.selectbox("형식", ["NATM (철근)", "NATM (무근)", "개착식 (BOX)", "TBM (세그먼트)", "재래식 (무근)"])
                tLen = st.number_input("총연장", 10.0, 5000.0, 100.0)
                uLen = st.number_input("단위", 5.0, 50.0, 20.0)
                if st.form_submit_button("생성"):
                    tm = {"NATM (철근)": TunnelType.NATM_RC, "NATM (무근)": TunnelType.NATM_PLAIN, "개착식 (BOX)": TunnelType.OPEN_CUT, "TBM (세그먼트)": TunnelType.TBM_SEGMENT, "재래식 (무근)": TunnelType.ASSM_PLAIN}
                    new_sec = TunnelSection(proj.next_section_id, tm[sType], tLen, uLen)
                    cnt = int(tLen // uLen)
                    for i in range(cnt): new_sec.spans.append(TunnelSpan(i+1, uLen))
                    if tLen % uLen > 0: new_sec.spans.append(TunnelSpan(cnt+1, tLen % uLen))
                    proj.sections.append(new_sec)
                    proj.next_section_id += 1
                    DataManager.save_all_projects(st.session_state['projects'])
                    st.rerun()

        st.markdown("#### 위치 선택")
        if not proj.sections: st.warning("구간 필요")
        if 'sel_sec_idx' not in st.session_state: st.session_state['sel_sec_idx'] = 0
        if 'sel_span_idx' not in st.session_state: st.session_state['sel_span_idx'] = 0
        
        sec_opts = [f"Sec {s.id} ({s.type.label})" for s in proj.sections]
        if sec_opts:
            s_idx = st.selectbox("구간", range(len(sec_opts)), format_func=lambda x: sec_opts[x])
            st.session_state['sel_sec_idx'] = s_idx
            curr_sec = proj.sections[s_idx]
            span_opts = [f"No.{sp.span_no} [{sp.result_cache.get('grade', 'A')[0]}]" for sp in curr_sec.spans]
            sp_idx = st.radio("스판", range(len(span_opts)), format_func=lambda x: span_opts[x])
            st.session_state['sel_span_idx'] = sp_idx
    
    # -----------------------------------------------------
    # 메인 탭 구성
    # -----------------------------------------------------
    if proj.sections:
        curr_sec = proj.sections[st.session_state['sel_sec_idx']]
        curr_span = curr_sec.spans[st.session_state['sel_span_idx']]
        d = curr_span.data
        
        # 상단 히트맵 (화면용 - 다크모드 적응)
        fig_map = draw_screen_heatmap(proj.sections)
        if fig_map: st.plotly_chart(fig_map, use_container_width=True)
        
        tab1, tab2 = st.tabs(["현장 입력 (Input)", "종합 보고서 (Report)"])
        
        # [TAB 1] 입력
        with tab1:
            col_title, col_copy = st.columns([3, 1])
            with col_title: st.markdown(f"#### 상세 조사 : Sec {curr_sec.id} - Span No.{curr_span.span_no}")
            with col_copy:
                if curr_span.span_no > 1:
                    if st.button("이전값 복사"):
                        import copy
                        prev = curr_sec.spans[st.session_state['sel_span_idx']-1]
                        curr_span.data = copy.deepcopy(prev.data)
                        st.success("복사됨 (저장필요)")
                        st.rerun()

            c1, c2 = st.columns(2, gap="medium")
            with c1:
                st.markdown('<div class="step-header">1. 라이닝 평가</div>', unsafe_allow_html=True)
                d.location = st.selectbox("위치", ["전구간", "천정부", "우측벽", "좌측벽", "바닥"], index=["전구간", "천정부", "우측벽", "좌측벽", "바닥"].index(d.location))
                d.crack_width = st.number_input("균열(mm)", 0.0, 10.0, d.crack_width, 0.1)
                d.leakage_grade = st.select_slider("누수", ["a","b","c","d","e"], value=d.leakage_grade)
                d.breakage_grade = st.select_slider("파손", ["a","b","c","d","e"], value=d.breakage_grade)
                
                st.caption("재질열화 (최악조건)")
                d.material.spalling_grade = st.select_slider("박리", ["a","b","c","d","e"], value=d.material.spalling_grade)
                d.material.efflorescence_grade = st.select_slider("백태", ["a","b","c","d","e"], value=d.material.efflorescence_grade)
                d.material.rebar_grade = st.select_slider("철근", ["a","b","c","d","e"], value=d.material.rebar_grade)
                d.material.carbonation_grade = st.select_slider("탄산", ["a","b","c","d","e"], value=d.material.carbonation_grade)

            with c2:
                st.markdown('<div class="step-header">2. 주변 & 부대</div>', unsafe_allow_html=True)
                d.sur_drain = st.slider("배수(0~4)", 0, 4, d.sur_drain)
                d.sur_ground = st.slider("지반(0~4)", 0, 4, d.sur_ground)
                is_p = (curr_span.span_no==1) or (curr_span.span_no==len(curr_sec.spans))
                d.sur_portal = st.slider("갱문(0~4)", 0, 4, d.sur_portal if is_p else 0, disabled=not is_p)
                d.aux_score = st.slider("부대시설(f)", 0.0, 1.0, d.aux_score, 0.05)
                st.file_uploader("사진", key=f"p_{curr_span.span_no}")

            res = system.calculate_span(curr_span, curr_sec.type)
            st.info(f"판정: [{res['grade']}] F={res['f_value']:.4f}")

        # [TAB 2] 보고서 (흰색 종이 스타일 강제 적용)
        with tab2:
            summary = system.calculate_project_summary(proj.sections)
            if summary:
                # 1. 의견 입력란 (화면 기본 스타일)
                st.markdown("#### 📝 종합 의견 작성")
                proj.opinion = st.text_area("점검자 소견 및 조치사항", value=proj.opinion, height=100)
                
                # 2. 엑셀 다운로드
                data_list = []
                for s in summary['span_results']:
                    data_list.append({
                        "구간": s['sec_id'], "형식": s['type'], "Span": s['span_no'], "길이": s['length'],
                        "균열": s['data'].crack_width, "누수": s['data'].leakage_grade, "등급": s['result']['grade']
                    })
                df = pd.DataFrame(data_list)
                out = BytesIO()
                with pd.ExcelWriter(out, engine='xlsxwriter') as w: df.to_excel(w, index=False)
                st.download_button("엑셀 다운로드", data=out.getvalue(), file_name=f"{proj.name}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
                st.divider()
                
                # 3. 진짜 보고서 뷰 (다크모드에서도 흰 종이처럼 보이게 강제함)
                st.markdown('<div class="report-container">', unsafe_allow_html=True)
                
                # 제목
                st.markdown(f'<div style="text-align:center;"><h2 style="color:black !important; text-decoration:underline;">{proj.name} 정밀안전진단 결과보고서</h2></div><br>', unsafe_allow_html=True)
                
                # 개요 테이블
                st.markdown(f"""
                <table class="report-table">
                    <tr><th width="20%">시설물명</th><td width="30%">{proj.name}</td><th width="20%">점검일자</th><td width="30%">{proj.date_str}</td></tr>
                    <tr><th>점검자</th><td>{proj.inspector}</td><th>소속</th><td>{proj.company} ({proj.position})</td></tr>
                    <tr><th>총 연장</th><td>{summary['total_length']} m</td><th>구간 수</th><td>{len(proj.sections)} 개</td></tr>
                </table><br>
                """, unsafe_allow_html=True)
                
                # 종합 등급 박스
                fg = summary['final_grade']
                color_code = "#e74c3c" if "D" in fg or "E" in fg else "#3498db"
                st.markdown(f"""
                <div class="grade-box" style="border: 2px solid {color_code};">
                    <strong style="font-size:16px; color:black;">종합 안전등급</strong><br>
                    <span style="font-size:32px; font-weight:800; color:{color_code};">{fg}</span><br>
                    <span style="font-size:14px; color:black;">(종합 결함지수 F = {summary['final_f']:.4f})</span>
                </div><br>
                """, unsafe_allow_html=True)
                
                # 차트 (배경 흰색/글씨 검정색 강제)
                st.markdown('<h4 style="color:black !important;">[터널 상태 분포도]</h4>', unsafe_allow_html=True)
                fig_report = draw_report_heatmap(proj.sections)
                if fig_report: st.plotly_chart(fig_report, use_container_width=True)
                
                # 종합 의견
                st.markdown('<br><h4 style="color:black !important;">[종합 의견 및 조치사항]</h4>', unsafe_allow_html=True)
                op_text = proj.opinion if proj.opinion else "(작성된 의견이 없습니다)"
                st.markdown(f"""<div class="opinion-box">{op_text}</div><br>""", unsafe_allow_html=True)
                
                # 세부 내역
                st.markdown('<h4 style="color:black !important;">[주요 구간 세부 평가 내역]</h4>', unsafe_allow_html=True)
                rows = ""
                # 데이터가 너무 많으면 상위 20개만 표시 (보고서 길이 조절)
                limit_rows = summary['span_results'][:20] 
                for s in limit_rows:
                    rows += f"<tr><td>{s['sec_id']}</td><td>{s['type']}</td><td>{s['span_no']}</td><td>{s['result']['grade']}</td><td>{s['result']['f_value']:.4f}</td></tr>"
                
                st.markdown(f"""
                <table class="report-table">
                    <thead><tr><th>구간</th><th>형식</th><th>Span No</th><th>안전등급</th><th>결함지수(F)</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
                """, unsafe_allow_html=True)
                if len(summary['span_results']) > 20:
                     st.markdown('<p style="text-align:center; color:#666; font-size:12px;">(전체 데이터는 엑셀 파일을 참조하세요)</p>', unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True) # End report-container
