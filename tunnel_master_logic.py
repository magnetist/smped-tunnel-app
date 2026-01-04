import sys
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict
from enum import Enum

sys.stdout.reconfigure(encoding='utf-8')

class TunnelType(Enum):
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

    @staticmethod
    def from_label(label):
        for t in TunnelType:
            if t.label == label: return t
        return TunnelType.NATM_RC

@dataclass
class MaterialDefects:
    spalling_grade: str = 'a'
    efflorescence_grade: str = 'a'
    rebar_grade: str = 'a'
    carbonation_grade: str = 'a'
    
    def get_worst_grade(self) -> str:
        return max([self.spalling_grade, self.efflorescence_grade, self.rebar_grade, self.carbonation_grade])

@dataclass
class InspectionData:
    location: str = "전구간"
    crack_width: float = 0.0
    leakage_grade: str = 'a'
    breakage_grade: str = 'a'
    soil_leak: bool = False
    material: MaterialDefects = field(default_factory=MaterialDefects)
    sur_drain: int = 0
    sur_ground: int = 0
    sur_portal: int = 0
    sur_util: int = 0
    sur_special: int = 0
    aux_score: float = 0.1
    photo_name: str = ""

    @staticmethod
    def from_dict(d):
        # [안전장치] 키가 없어도 기본값 {} 처리
        mat_data = d.pop('material', {})
        # [안전장치] 과거 데이터에 없는 필드가 있어도 에러 안 나게 처리
        valid_keys = InspectionData.__annotations__.keys()
        filtered_d = {k: v for k, v in d.items() if k in valid_keys}
        
        obj = InspectionData(**filtered_d)
        obj.material = MaterialDefects(**mat_data)
        return obj

@dataclass
class TunnelSpan:
    span_no: int
    length: float
    data: InspectionData = field(default_factory=InspectionData)
    result_cache: dict = field(default_factory=dict)

    def to_dict(self): return asdict(self)
    @staticmethod
    def from_dict(d):
        data_dict = d.pop('data', {})
        obj = TunnelSpan(**d)
        obj.data = InspectionData.from_dict(data_dict)
        return obj

@dataclass
class TunnelSection:
    id: int
    type: TunnelType
    total_length: float
    unit_length: float
    spans: List[TunnelSpan] = field(default_factory=list)

    def to_dict(self):
        d = asdict(self)
        d['type'] = self.type.label
        d['spans'] = [s.to_dict() for s in self.spans]
        return d

    @staticmethod
    def from_dict(d):
        t_label = d.pop('type', "NATM (철근)")
        spans_data = d.pop('spans', [])
        # [안전장치] unit_length가 없을 경우 기본값 20.0
        obj = TunnelSection(
            id=d.get('id', 1), 
            total_length=d.get('total_length', 100.0), 
            unit_length=d.get('unit_length', 20.0), 
            type=TunnelType.from_label(t_label)
        )
        obj.spans = [TunnelSpan.from_dict(s) for s in spans_data]
        return obj

@dataclass
class ProjectMetadata:
    id: str
    name: str
    inspector: str
    position: str
    company: str
    date_str: str
    opinion: str = ""
    sections: List[TunnelSection] = field(default_factory=list)
    next_section_id: int = 1

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "inspector": self.inspector,
            "position": self.position, "company": self.company, "date_str": self.date_str,
            "opinion": self.opinion, "next_section_id": self.next_section_id,
            "sections": [s.to_dict() for s in self.sections]
        }

    @staticmethod
    def from_dict(d):
        secs = [TunnelSection.from_dict(s) for s in d.pop('sections', [])]
        # [안전장치] opinion 필드가 없는 구버전 데이터 호환
        obj = ProjectMetadata(
            id=d.get('id', ''), name=d.get('name', ''), inspector=d.get('inspector', ''),
            position=d.get('position', ''), company=d.get('company', ''), date_str=d.get('date_str', ''),
            opinion=d.get('opinion', ''), next_section_id=d.get('next_section_id', 1)
        )
        obj.sections = secs
        return obj

class DataManager:
    DB_FILE = "smped_tunnel_db.json"
    @staticmethod
    def load_all_projects() -> Dict[str, ProjectMetadata]:
        try:
            with open(DataManager.DB_FILE, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                return {k: ProjectMetadata.from_dict(v) for k, v in raw_data.items()}
        except Exception: 
            return {} # 파일 없거나 깨지면 빈 딕셔너리 반환

    @staticmethod
    def save_all_projects(projects: Dict[str, ProjectMetadata]):
        raw_data = {k: v.to_dict() for k, v in projects.items()}
        with open(DataManager.DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=4)

class DefectEvaluator:
    GRADE_SCORE_MAP = {'a': 1.0, 'b': 4.0, 'c': 7.0, 'd': 10.0, 'e': 13.0}
    @staticmethod
    def evaluate_crack(width_mm: float, t_type: TunnelType) -> dict:
        # 터널 형식별 균열 기준 적용
        if t_type in [TunnelType.ASSM_PLAIN, TunnelType.ASSM_BRICK, TunnelType.NATM_PLAIN]:
            if width_mm <= 0.1: return {"grade": "a", "score": 1.0}
            elif width_mm <= 0.3: return {"grade": "b", "score": 4.0}
            elif width_mm <= 1.0: return {"grade": "c", "score": 7.0}
            elif width_mm <= 3.0: return {"grade": "d", "score": 10.0}
            else: return {"grade": "e", "score": 13.0}
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
    def calculate_span(self, span: TunnelSpan, t_type: TunnelType):
        d = span.data
        scores = {}
        alerts = []

        crack_eval = DefectEvaluator.evaluate_crack(d.crack_width, t_type)
        scores['crack'] = crack_eval['score']
        if crack_eval['grade'] >= 'd': alerts.append("진행성 균열(d등급 이상)")
        
        worst_mat = d.material.get_worst_grade()
        scores['material'] = DefectEvaluator.get_score(worst_mat)
        if d.material.rebar_grade >= 'e': alerts.append("철근노출 심각(e등급)")

        scores['leakage'] = DefectEvaluator.get_score(d.leakage_grade)
        scores['breakage'] = DefectEvaluator.get_score(d.breakage_grade)
        if d.soil_leak and d.leakage_grade >= 'd': alerts.append("토립자 유출 동반 누수")

        lining_total = sum(scores.values())
        surround_total = d.sur_drain + d.sur_ground + d.sur_portal + d.sur_util + d.sur_special
        
        # [안전장치] 분모가 0일 경우 대비 (사실상 없지만 방어코드)
        denom = t_type.total_denom if t_type.total_denom > 0 else 1
        f_basic = (lining_total + surround_total) / denom
        
        w = 1.0
        if d.aux_score < 0.15: w = 1.0
        elif d.aux_score < 0.30: w = 1.0
        elif d.aux_score < 0.55: w = 1.02
        elif d.aux_score < 0.75: w = 1.05
        else: w = 1.10
        
        f_final = f_basic * w
        
        result = {
            "f_value": f_final, "grade": self.get_grade_str(f_final),
            "alerts": alerts, "details": {"lining": lining_total, "surround": surround_total, "w": w}
        }
        span.result_cache = result
        return result

    def get_grade_str(self, f_value: float) -> str:
        if f_value < 0.15: return "A (우수)"
        elif f_value < 0.30: return "B (양호)"
        elif f_value < 0.55: return "C (보통)"
        elif f_value < 0.75: return "D (미흡)"
        else: return "E (불량)"

    def calculate_project_summary(self, sections: List[TunnelSection]):
        if not sections: return None
        all_spans = []
        for sec in sections:
            for span in sec.spans:
                self.calculate_span(span, sec.type)
                all_spans.append({
                    "sec_id": sec.id, "type": sec.type.label,
                    "span_no": span.span_no, "length": span.length,
                    "data": span.data, "result": span.result_cache
                })
        
        if not all_spans: return None
        total_weighted_f = sum(s['result']['f_value'] * s['length'] for s in all_spans)
        total_len = sum(s['length'] for s in all_spans)
        
        # [안전장치] 총 연장이 0일 경우 대비
        final_f = total_weighted_f / total_len if total_len > 0 else 0
        
        return {
            "final_f": final_f, "final_grade": self.get_grade_str(final_f),
            "total_length": total_len, "span_results": all_spans,
            "alerts": [f"[Sec {s['sec_id']}-No.{s['span_no']}] {msg}" for s in all_spans for msg in s['result']['alerts']]
        }
