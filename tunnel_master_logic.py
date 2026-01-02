import sys
from dataclasses import dataclass
from typing import List
from enum import Enum

sys.stdout.reconfigure(encoding='utf-8')

# =========================================================
# 1. 기준 정보 (Criteria)
# =========================================================
class TunnelType(Enum):
    """터널 형식 및 배점 기준 (세부지침 2.4.1)"""
    ASSM_BRICK = ("재래식 (조적)", 26, 33)
    ASSM_PLAIN = ("재래식 (무근)", 27, 34)
    NATM_PLAIN = ("NATM (무근)", 27, 34)
    NATM_RC = ("NATM (철근)", 36, 43)
    TBM_SEGMENT = ("TBM (세그먼트)", 36, 43)
    OPEN_CUT = ("개착식 (BOX)", 36, 42)

    def __init__(self, label, lining_denom, total_denom):
        self.label = label
        self.lining_denom = lining_denom
        self.total_denom = total_denom

# =========================================================
# 2. 입력 데이터 모델 (DTO)
# =========================================================
@dataclass
class MaterialDefects:
    """재질열화 세부 항목 (최악 등급 선정용)"""
    spalling_grade: str     # 박리/박락
    efflorescence_grade: str # 백태
    rebar_grade: str        # 철근노출
    carbonation_grade: str  # 탄산화
    
    def get_worst_grade(self) -> str:
        """가장 불리한 등급 반환"""
        grades = [self.spalling_grade, self.efflorescence_grade, self.rebar_grade, self.carbonation_grade]
        return max(grades)

@dataclass
class SurroundingsInput:
    """주변상태 세부 평가 항목 (5종)"""
    drainage_score: float   # 배수
    ground_score: float     # 지반
    portal_score: float     # 갱문
    utility_score: float    # 공동구
    special_score: float    # 특수조건

    def get_total_score(self) -> float:
        return self.drainage_score + self.ground_score + self.portal_score + self.utility_score + self.special_score

@dataclass
class RawInspectionData:
    """현장 조사 데이터"""
    span_id: int
    crack_width_mm: float
    leakage_grade: str
    breakage_grade: str
    material_details: MaterialDefects 

@dataclass
class AuxiliaryInput:
    """부대시설 데이터"""
    name: str
    f_score: float

# =========================================================
# 3. 평가 및 계산 로직
# =========================================================
class DefectEvaluator:
    GRADE_SCORE_MAP = {'a': 1.0, 'b': 4.0, 'c': 7.0, 'd': 10.0, 'e': 13.0}

    @staticmethod
    def evaluate_crack(width_mm: float, t_type: TunnelType) -> dict:
        """형식별 균열 등급 판정"""
        # 무근 기준
        if t_type in [TunnelType.ASSM_PLAIN, TunnelType.ASSM_BRICK, TunnelType.NATM_PLAIN]:
            if width_mm <= 0.1: return {"grade": "a", "score": 1.0}
            elif width_mm <= 0.3: return {"grade": "b", "score": 4.0}
            elif width_mm <= 1.0: return {"grade": "c", "score": 7.0}
            elif width_mm <= 3.0: return {"grade": "d", "score": 10.0}
            else: return {"grade": "e", "score": 13.0}
        # 철근 기준
        else:
            if width_mm <= 0.1: return {"grade": "a", "score": 1.0}
            elif width_mm <= 0.3: return {"grade": "b", "score": 4.0}
            elif width_mm <= 0.5: return {"grade": "c", "score": 7.0}
            elif width_mm <= 1.0: return {"grade": "d", "score": 10.0}
            else: return {"grade": "e", "score": 13.0}

    @staticmethod
    def get_score(grade_char: str) -> float:
        return DefectEvaluator.GRADE_SCORE_MAP.get(grade_char.lower(), 0.0)

class TunnelSafetySystem:
    def __init__(self, tunnel_type: TunnelType):
        self.type = tunnel_type

    def calculate_span(self, data: RawInspectionData):
        """1단계 라이닝 결함지수 산정"""
        scores = {}
        alerts = []

        # 1. 균열
        crack_eval = DefectEvaluator.evaluate_crack(data.crack_width_mm, self.type)
        scores['crack'] = crack_eval['score']
        if crack_eval['grade'] >= 'd':
            alerts.append(f"진행성 균열 '{crack_eval['grade']}'등급 (중대결함 의심)")

        # 2. 재질열화 (최악등급 적용)
        worst_mat_grade = data.material_details.get_worst_grade()
        scores['material'] = DefectEvaluator.get_score(worst_mat_grade)
        if data.material_details.rebar_grade >= 'e':
             alerts.append("철근노출 상태 심각 ('e'등급) - 즉시 보강 필요")

        # 3. 기타 항목
        scores['leakage'] = DefectEvaluator.get_score(data.leakage_grade)
        scores['breakage'] = DefectEvaluator.get_score(data.breakage_grade)

        # 4. 합계 및 지수(f)
        total_score = sum(scores.values())
        f_value = total_score / self.type.lining_denom

        return {
            "total_score": total_score,
            "f_value": round(f_value, 4),
            "mat_grade": worst_mat_grade,
            "alerts": alerts
        }

    def calculate_auxiliary_weight(self, aux_list: List[AuxiliaryInput]) -> float:
        """부대시설 가중치(w) 산정"""
        if not aux_list: return 1.0
        avg_f = sum(a.f_score for a in aux_list) / len(aux_list)
        if avg_f < 0.15: return 1.0
        elif avg_f < 0.30: return 1.0
        elif avg_f < 0.55: return 1.02
        elif avg_f < 0.75: return 1.05
        else: return 1.10

    def calculate_final_grade(self, f_value: float) -> str:
        """최종 등급 판정"""
        if f_value < 0.15: return "A (우수)"
        elif f_value < 0.30: return "B (양호)"
        elif f_value < 0.55: return "C (보통)"
        elif f_value < 0.75: return "D (미흡)"
        else: return "E (불량)"