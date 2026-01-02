import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# 로직 엔진 불러오기
from tunnel_master_logic import TunnelType, TunnelSafetySystem, RawInspectionData, AuxiliaryInput, MaterialDefects, SurroundingsInput

# =========================================================
# 1. 페이지 설정
# =========================================================
st.set_page_config(
    page_title="SM-PED Tunnel System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# 2. 전문적 디자인을 위한 CSS (다크모드 대응 적용)
# =========================================================
st.markdown("""
    <style>
    /* 전체 폰트 설정 */
    .main { font-family: 'Pretendard', sans-serif; }
    
    /* 상단 헤더 바 (다크 네이비 - 고정색) */
    .header-bar {
        padding: 20px 30px;
        background-color: #002b5c; 
        border-bottom: 3px solid #b38f00; /* Gold Accent */
        color: white;
        margin-bottom: 20px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .brand-title { font-size: 26px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; }
    .brand-sub { font-size: 14px; color: #ced4da; font-weight: 400; margin-left: 15px; border-left: 1px solid #6c757d; padding-left: 15px;}
    .user-info { text-align: right; font-size: 12px; line-height: 1.4; color: #e9ecef; }
    
    /* 섹션 헤더 스타일 */
    .section-header {
        font-size: 18px; font-weight: 700; color: var(--text-color); /* 테마에 따라 글자색 변경 */
        border-left: 5px solid #002b5c; padding-left: 10px; margin: 20px 0 10px 0;
    }

    /* KPI 카드 (배경색을 테마에 맞춤) */
    .kpi-box {
        background-color: var(--secondary-background-color); /* 다크모드 대응 */
        border: 1px solid var(--secondary-background-color);
        border-radius: 4px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .kpi-label { font-size: 13px; color: var(--text-color); opacity: 0.7; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-value { font-size: 32px; font-weight: 800; color: var(--text-color); margin-top: 5px; }
    .kpi-sub { font-size: 12px; color: var(--text-color); opacity: 0.5; margin-top: 5px; }

    /* 경고 박스 */
    .critical-alert {
        background-color: #4a1b1b; /* 다크모드에서도 잘 보이는 짙은 빨강 배경 */
        border: 1px solid #c92a2a;
        color: #ffc9c9; /* 밝은 빨강 글씨 */
        padding: 15px;
        border-radius: 4px; font-weight: 600; margin-top: 15px;
    }
    .normal-alert {
        padding:15px; 
        background-color: var(--secondary-background-color); 
        border:1px solid var(--secondary-background-color); 
        color: var(--text-color); opacity: 0.8;
        border-radius:4px; margin-top:15px; text-align:center;
    }

    /* ★ 핵심 수정: 보고서 스타일 (다크모드 대응) ★ */
    .report-paper {
        background-color: var(--secondary-background-color); /* 배경색 자동 변경 */
        color: var(--text-color); /* 글자색 자동 변경 */
        padding: 40px;
        border: 1px solid rgba(128, 128, 128, 0.2); /* 테두리 투명도 조절 */
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
        max-width: 900px;
        margin: auto;
    }
    .report-title { 
        text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 30px; 
        text-decoration: underline; text-underline-offset: 8px; color: var(--text-color);
    }
    .report-table { width: 100%; border-collapse: collapse; margin-top: 20px; color: var(--text-color); }
    .report-table th { 
        background-color: rgba(128, 128, 128, 0.1); /* 헤더 배경 투명도 조절 */
        border: 1px solid rgba(128, 128, 128, 0.3); 
        padding: 10px; text-align: center; font-size: 13px; font-weight: bold;
    }
    .report-table td { 
        border: 1px solid rgba(128, 128, 128, 0.3); 
        padding: 10px; text-align: center; font-size: 13px; 
    }
    
    /* 테이블 강조색 및 최종 등급 색상 */
    .table-highlight-row { background-color: rgba(128, 128, 128, 0.05); }
    .final-score { font-weight:bold; color: #4a90e2; font-size:16px; } /* 다크모드에서도 잘 보이는 파랑 */
    .final-grade { font-weight:bold; color: #e57373; font-size:18px; } /* 다크모드에서도 잘 보이는 빨강 */
    
    /* 종합 의견 박스 */
    .opinion-box {
        border: 1px solid rgba(128, 128, 128, 0.3); 
        padding: 15px; font-size: 13px; min-height: 80px;
        background-color: rgba(128, 128, 128, 0.05);
        color: var(--text-color);
    }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# 3. 사이드바: 프로젝트 및 점검자 설정
# =========================================================
with st.sidebar:
    st.markdown("### [프로젝트 및 점검자 설정]")
    
    with st.container():
        proj_name = st.text_input("시설물명", "성남1터널 (상행선)")
        field_inspector = st.text_input("점검 책임자 (성명)", "홍길동")
        inspector_pos = st.text_input("직위 / 직급", "특급기술자")
        insp_company = st.text_input("소속 회사", "(주)다음기술단")
        insp_date = st.date_input("점검 수행일", datetime.now())
    
    st.markdown("---")
    st.markdown("### [구조물 제원 설정]")
    
    type_options = {
        "재래식 (무근 콘크리트)": TunnelType.ASSM_PLAIN,
        "재래식 (조적)": TunnelType.ASSM_BRICK,
        "NATM (철근 콘크리트)": TunnelType.NATM_RC,
        "개착식 (박스 구조물)": TunnelType.OPEN_CUT
    }
    selected_type_key = st.selectbox("터널 형식 선택", list(type_options.keys()))
    current_type = type_options[selected_type_key]
    
    st.info(f"적용 기준: 안전점검 세부지침(터널편)\n- 라이닝 분모: {current_type.lining_denom}\n- 종합 분모: {current_type.total_denom}")
    
    st.markdown("---")
    st.caption("SM-PED Version 2026-1.0")

# =========================================================
# 4. 상단 헤더 (Corporate Identity)
# =========================================================
st.markdown(f"""
    <div class="header-bar">
        <div style="display:flex; align-items:center;">
            <span class="brand-title">SM-PED Tunnel</span>
            <span class="brand-sub">Intelligent Safety Assessment System</span>
        </div>
        <div class="user-info">
            <b>(주)다음기술단 기술연구소</b><br>
            System Architect: 이승현 차장
        </div>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# 5. 메인 워크스페이스
# =========================================================
tab1, tab2 = st.tabs(["데이터 입력 및 분석", "종합 안전등급 보고서"])

# 로직 엔진 초기화
system = TunnelSafetySystem(current_type)

# ---------------------------------------------------------
# [Tab 1] 데이터 입력 및 분석
# ---------------------------------------------------------
with tab1:
    col_input, col_result = st.columns([1.1, 0.9], gap="large")
    
    # --- 좌측: 데이터 입력 패널 ---
    with col_input:
        st.markdown('<div class="section-header">1. 손상 현황 데이터 입력</div>', unsafe_allow_html=True)
        
        # 1. 라이닝 평가 (아코디언 기본 확장)
        with st.expander("라이닝(Lining) 주요 결함", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                crack_width = st.number_input("최대 균열폭 (mm)", 0.0, 10.0, 0.25, 0.05, format="%.2f")
            with c2:
                breakage_grade = st.select_slider("파손 및 손상 등급", ["a", "b", "c", "d", "e"], value="a")
            
            c3, c4 = st.columns(2)
            with c3:
                leakage_grade = st.selectbox("누수 상태 등급", ["a", "b", "c", "d", "e"])
                soil_leak = st.checkbox("토립자 유출 동반 (중대결함)", value=False)
            with c4:
                st.markdown("**재질열화 세부평가** (가장 불리한 등급 자동적용)")
                sub_c1, sub_c2 = st.columns(2)
                with sub_c1:
                    mat_spall = st.selectbox("박리/박락", ["a", "b", "c", "d", "e"], index=0)
                    mat_efflo = st.selectbox("백태", ["a", "b", "c", "d", "e"], index=0)
                with sub_c2:
                    mat_rebar = st.selectbox("철근노출", ["a", "b", "c", "d", "e"], index=0)
                    mat_carb = st.selectbox("탄산화/염화물", ["a", "b", "c", "d", "e"], index=0)

        # 2. 주변 및 부대시설 (아코디언 기본 확장)
        with st.expander("주변환경 및 부대시설 평가", expanded=True):
            surroundings_score = st.slider("주변상태 결함점수 합계 (배수/지반/갱문)", 0, 10, 2)
            
            st.markdown("**부대시설 가중치 산정**")
            ac1, ac2 = st.columns([2, 1])
            with ac1:
                aux_name = st.text_input("부대시설명", "피난연락갱", label_visibility="collapsed")
            with ac2:
                aux_score = st.number_input("결함지수(f)", 0.0, 1.0, 0.1, 0.05, label_visibility="collapsed")

    # --- 우측: 실시간 분석 결과 ---
    with col_result:
        st.markdown('<div class="section-header">2. 실시간 안전성 분석 결과</div>', unsafe_allow_html=True)
        
        # 1. 객체 생성
        mat_defects = MaterialDefects(mat_spall, mat_efflo, mat_rebar, mat_carb)
        
        # 2. 계산 실행
        span_res = system.calculate_span(
            RawInspectionData(1, crack_width, leakage_grade, breakage_grade, mat_defects)
        )
        if soil_leak and leakage_grade >= 'd':
            span_res['alerts'].append("누수 등급 d 이상 + 토립자 유출 확인")

        aux_list = [AuxiliaryInput(aux_name, aux_score)]
        F_basic = (span_res['total_score'] + surroundings_score) / current_type.total_denom
        w = system.calculate_auxiliary_weight(aux_list)
        F_total = F_basic * w
        final_grade_str = system.calculate_final_grade(F_total)
        short_grade = final_grade_str[0]

        # 3. KPI 박스 (다크모드 대응)
        kc1, kc2, kc3 = st.columns(3)
        kc1.markdown(f"""<div class="kpi-box"><div class="kpi-label">라이닝 지수(f)</div><div class="kpi-value">{span_res['f_value']:.4f}</div><div class="kpi-sub">점수합: {span_res['total_score']}</div></div>""", unsafe_allow_html=True)
        kc2.markdown(f"""<div class="kpi-box"><div class="kpi-label">가중치(w)</div><div class="kpi-value">{w:.2f}</div><div class="kpi-sub">대상: {aux_name}</div></div>""", unsafe_allow_html=True)
        kc3.markdown(f"""<div class="kpi-box" style="border-top: 3px solid #4a90e2;"><div class="kpi-label">종합 결함지수(F)</div><div class="kpi-value" style="color:#4a90e2;">{F_total:.4f}</div><div class="kpi-sub">등급: {short_grade}</div></div>""", unsafe_allow_html=True)

        st.write("") # 간격

        # 4. 게이지 차트 (다크모드 대응 색상)
        gauge_bar_color = "#4a90e2" # 밝은 파랑 (다크모드에서 잘 보임)
        gauge_axis_color = "#adb5bd" # 회색
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = F_total,
            title = {'text': f"종합 안전등급: {short_grade}", 'font': {'size': 18, 'color': gauge_axis_color, 'family': "Arial"}},
            gauge = {
                'axis': {'range': [0, 1.0], 'tickwidth': 1, 'tickcolor': gauge_axis_color},
                'bar': {'color': gauge_bar_color},
                'steps': [
                    {'range': [0, 0.15], 'color': "rgba(46, 204, 113, 0.3)"}, # A (Green transparent)
                    {'range': [0.15, 0.30], 'color': "rgba(52, 152, 219, 0.3)"}, # B (Blue transparent)
                    {'range': [0.30, 0.55], 'color': "rgba(241, 196, 15, 0.3)"}, # C (Yellow transparent)
                    {'range': [0.55, 0.75], 'color': "rgba(230, 126, 34, 0.3)"}, # D (Orange transparent)
                    {'range': [0.75, 1.0], 'color': "rgba(231, 76, 60, 0.3)"}   # E (Red transparent)
                ],
                'threshold': {'line': {'color': "#e57373", 'width': 4}, 'thickness': 0.75, 'value': F_total}
            }
        ))
        fig.update_layout(height=250, margin=dict(l=30, r=30, t=30, b=30), paper_bgcolor="rgba(0,0,0,0)", font={'color': gauge_axis_color})
        st.plotly_chart(fig, use_container_width=True)

        # 5. 경고 메시지 (다크모드 대응)
        if span_res['alerts']:
            alert_text = "<br>".join([f"• {msg}" for msg in span_res['alerts']])
            st.markdown(f"""<div class="critical-alert">[CRITICAL WARNING] 중대한 결함 감지<br><span style="font-weight:400; font-size:14px;">{alert_text}</span></div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="normal-alert">[NORMAL] 특이사항 없음 / 중대한 결함 징후 미발견</div>""", unsafe_allow_html=True)

# ---------------------------------------------------------
# [Tab 2] 종합 안전등급 보고서 (Report)
# ---------------------------------------------------------
with tab2:
    # A4 용지 느낌의 컨테이너 (다크모드 대응)
    st.markdown('<div class="report-paper">', unsafe_allow_html=True)
    
    # 1. 보고서 제목
    st.markdown(f'<div class="report-title">정밀안전진단 종합평가 보고서</div>', unsafe_allow_html=True)
    
    # 2. 개요 표
    st.markdown(f"""
    <table class="report-table">
        <tr>
            <th width="20%">시설물명</th>
            <td width="30%">{proj_name}</td>
            <th width="20%">점검 기준일</th>
            <td width="30%">{insp_date.strftime('%Y년 %m월 %d일')}</td>
        </tr>
        <tr>
            <th>구조 형식</th>
            <td>{selected_type_key}</td>
            <th>위치</th>
            <td>경기도 성남시</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)

    st.write("")
    
    # 3. 점검자 정보
    st.markdown('<h5 style="color: var(--text-color);">1. 점검 및 진단 수행자</h5>', unsafe_allow_html=True)
    st.markdown(f"""
    <table class="report-table">
        <tr>
            <th width="20%">소속</th>
            <td width="30%">{insp_company}</td>
            <th width="20%">성명</th>
            <td width="30%">{field_inspector}</td>
        </tr>
        <tr>
            <th>직위/직급</th>
            <td>{inspector_pos}</td>
            <th>서명</th>
            <td>(인)</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)
    
    st.write("")

    # 4. 종합 평가 결과
    st.markdown('<h5 style="color: var(--text-color);">2. 종합 상태평가 결과</h5>', unsafe_allow_html=True)
    
    opinion = ""
    if short_grade in ['A', 'B']: opinion = "대상 시설물은 전반적으로 양호한 상태를 유지하고 있으며, 현행 유지관리 수준을 지속적으로 수행하는 것이 바람직함."
    elif short_grade == 'C': opinion = "주요 부재에 경미한 결함이 발생하였으나 안전성에는 지장이 없으며, 내구성 증진을 위한 예방적 보수가 필요함."
    else: opinion = "주요 부재에 심각한 결함이 발생하여 긴급한 보수/보강 조치가 필요하며, 필요시 사용제한 조치를 검토해야 함."

    st.markdown(f"""
    <table class="report-table">
        <tr class="table-highlight-row">
            <th>구분</th>
            <th>산출 내역</th>
            <th>결과값</th>
            <th>비고</th>
        </tr>
        <tr>
            <td>1단계 라이닝 평가</td>
            <td>결함점수 합계 {span_res['total_score']}점 / 분모 {current_type.lining_denom}</td>
            <td>f = {span_res['f_value']:.4f}</td>
            <td>재질열화 등급: {span_res['mat_grade']}</td>
        </tr>
        <tr>
            <td>2단계 주변상태 평가</td>
            <td>주변상태 결함점수 합계</td>
            <td>{surroundings_score} 점</td>
            <td>배수, 지반 등</td>
        </tr>
        <tr>
            <td>3단계 기본시설 지수</td>
            <td>(라이닝평균 + 주변상태) / {current_type.total_denom}</td>
            <td>F_basic = {F_basic:.4f}</td>
            <td></td>
        </tr>
        <tr>
            <td>4단계 부대시설 가중치</td>
            <td>부대시설({aux_name}) 결함지수 {aux_score}</td>
            <td>w = {w}</td>
            <td>가중치 적용</td>
        </tr>
        <tr style="border-top: 2px solid var(--text-color);">
            <td style="font-weight:bold;">종합 결함지수(F)</td>
            <td colspan="2" class="final-score">{F_total:.4f}</td>
            <td></td>
        </tr>
        <tr>
            <td style="font-weight:bold;">최종 안전등급</td>
            <td colspan="2" class="final-grade">{final_grade_str}</td>
            <td></td>
        </tr>
    </table>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    # 5. 종합 의견
    st.markdown('<h5 style="color: var(--text-color);">3. 종합 의견 및 조치 사항</h5>', unsafe_allow_html=True)
    st.markdown(f"""<div class="opinion-box">{opinion}</div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True) # End of report-paper
    
    st.write("")
    
    # 다운로드 버튼
    c_btn1, c_btn2, c_null = st.columns([2, 2, 6])
    c_btn1.button("📄 PDF 보고서 생성", type="primary", use_container_width=True)
    c_btn2.button("🖨️ 인쇄 (Print)", use_container_width=True)
