from __future__ import annotations

import html
import math
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

import geonamescache
import numpy as np
import pandas as pd
import streamlit as st
import swisseph as swe
from timezonefinder import TimezoneFinder
import os
import uuid
# ==================== 1. Security (Fixed) ====================
KEY_FILE = "license.key"

def get_machine_id():
    return hex(uuid.getnode())

def generate_password(mid):
    # مطابقة تامة لمنطق أداة فك الحماية الثابتة
    digits = ''.join(filter(str.isdigit, mid))
    if not digits: 
        try:
            digits = str(int(mid, 16))
        except:
            return "Error"
    num = int(digits)
    result = round(abs(num / 2 * 3.14))
    return str(result)[:6]

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = os.path.exists(KEY_FILE)

if not st.session_state['authenticated']:
    st.set_page_config(page_title="Security", layout="centered")
    st.title("Security Activation - Ask the programmer for your password")
    st.warning("Send your Machine ID to programmer email : mulham81ahmed@gmail.com ")

    mid = get_machine_id()
    st.info(f"Machine ID: {mid}")
    pwd = st.text_input("Enter Activation Key:", type="password")
    
    if st.button("Activate"):
        if pwd == generate_password(mid):
            with open(KEY_FILE, "w") as f: 
                f.write(pwd)
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error("Invalid Activation Key.")
            
    st.stop()

# ==================== إعداد الصفحة وتصميم الواجهة العربية RTL ====================
st.set_page_config(
    page_title="رادار كايبر التنبؤي المتقدم — تطوير استرو رادار",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&family=IBM+Plex+Mono:wght@400;600;700&display=swap');
html, body, [class*="css"], .stApp {
    direction: rtl;
    text-align: right;
    font-family: 'Cairo', system-ui, -apple-system, sans-serif;
    background-color: #060914;
    color: #E8EEF9;
}
[data-testid="stSidebar"] {
    background-color: #0A0F20;
    border-left: 1px solid #1F2A48;
}
.stButton > button[kind="primary"] {
    background-color: #F5B942;
    color: #140E00;
    font-weight: 800;
    border: none;
    border-radius: 10px;
}
.stButton > button[kind="primary"]:hover {
    background-color: #FBD38D;
    color: #140E00;
}
.kuiper-card {
    background: #0E1426;
    border: 1px solid #1F2A48;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.kuiper-hero {
    background: #0B1020;
    border: 1px solid #1F2A48;
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 16px;
}
.kuiper-kpi-label { font-size: 12px; color: #94A3B8; }
.kuiper-kpi-val { font-size: 20px; font-weight: 800; color: #FFFFFF; margin-top: 4px; }
</style>
"""

# ==================== الثوابت المثبتة لمحرك زحل-نبتون-هوميا-إيريس ====================
K_HAUMEA = 6.19
K_ERIS = 9.30
K_NEPTUNE = 10.78
K_SATURN = 4.48
EPSILON = 0.30
SATURN_CYCLES = 28
APEX_CYCLE = 10
CRITICAL_CYCLE = 9

T_HAUMEA = 283.28
T_ERIS = 558.0
E_HAUMEA = 0.1964
E_ERIS = 0.43607
M0_HAUMEA_DEG = 216.0
M0_ERIS_DEG = 197.6

TROPICAL_YEAR = 365.2421904
NAIBOD_PER_DAY = 360.0 / TROPICAL_YEAR / TROPICAL_YEAR

STATUS_NORMAL = "Normal"
STATUS_PHASE_HARMONIC = "PHASE_HARMONIC"
STATUS_CRITICAL = "CRITICAL"
STATUS_FOUR_AXIS = "FOUR_AXIS"
STATUS_UNIFIED = "UNIFIED"
STATUS_APEX = "APEX"

SATURN_CONFIRMED = {STATUS_FOUR_AXIS, STATUS_UNIFIED, STATUS_APEX}
ACTIVE_RADAR = SATURN_CONFIRMED | {STATUS_CRITICAL, STATUS_PHASE_HARMONIC}

STATUS_LABELS: Dict[str, Tuple[str, str, str]] = {
    STATUS_APEX: ("توافق رباعي المحاور", "ذروة زحل (APEX)", "#F59E0B"),
    STATUS_UNIFIED: ("توافق رباعي المحاور", "تقاطع موحّد (UNIFIED)", "#06B6D4"),
    STATUS_FOUR_AXIS: ("توافق رباعي المحاور", "Δ_Saturn ≤ ε", "#38BDF8"),
    STATUS_CRITICAL: ("سنة حرجة ثلاثية", "CRITICAL (هوميا · إيريس · نبتون)", "#F43F5E"),
    STATUS_PHASE_HARMONIC: ("رنين طوري-توافقي", "علاج الفجوة الكبلرية", "#10B981"),
    STATUS_NORMAL: ("سنة اعتيادية", "مسار طبيعي", "#64748B"),
}

ZODIAC_SIGNS = [
    "الحمل", "الثور", "الجوزاء", "السرطان", "الأسد", "العذراء",
    "الميزان", "العقرب", "القوس", "الجدي", "الدلو", "الحوت",
]
SIGN_GLYPHS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
SIGN_RULERS = ["MAR", "VEN", "MER", "MOON", "SUN", "MER", "VEN", "MAR", "JUP", "SAT", "SAT", "JUP"]
AR_MONTHS = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]

PLANETS = ["SUN", "MOON", "MER", "VEN", "MAR", "JUP", "SAT", "URA", "NEP", "PLU", "NN", "SN"]
PLANET_IDS = {
    "SUN": swe.SUN, "MOON": swe.MOON, "MER": swe.MERCURY, "VEN": swe.VENUS, "MAR": swe.MARS,
    "JUP": swe.JUPITER, "SAT": swe.SATURN, "URA": swe.URANUS, "NEP": swe.NEPTUNE, "PLU": swe.PLUTO,
}
PLANET_AR = {
    "SUN": "الشمس", "MOON": "القمر", "MER": "عطارد", "VEN": "الزهرة", "MAR": "المريخ",
    "JUP": "المشتري", "SAT": "زحل", "URA": "أورانوس", "NEP": "نبتون", "PLU": "بلوتو",
    "NN": "العقدة الشمالية", "SN": "العقدة الجنوبية",
}
PLANET_GLYPH = {
    "SUN": "☉", "MOON": "☽", "MER": "☿", "VEN": "♀", "MAR": "♂", "JUP": "♃",
    "SAT": "♄", "URA": "♅", "NEP": "♆", "PLU": "♇", "NN": "☊", "SN": "☋",
}
FACTOR_AR = {
    "AS": "الطالع AS", "MC": "وتد السماء MC", "DS": "الغارب DS", "IC": "وتد الأرض IC",
    "EP": "النقطة الشرقية EP", "POF": "سهم السعادة POF", "POS": "سهم الغيب POS",
    "H2": "البيت 2", "H3": "البيت 3", "H5": "البيت 5", "H6": "البيت 6",
    "H8": "البيت 8", "H9": "البيت 9", "H11": "البيت 11", "H12": "البيت 12",
}
ASPECT_AR = {
    0: "اقتران", 30: "نصف تسديس", 45: "نصف تربيع", 60: "تسديس",
    90: "تربيع", 120: "تثليث", 135: "تربيع ونصف", 150: "مقارنة ساقطة", 180: "مقابلة",
}

TECH_CODES = ("PD", "SA", "SD", "AP", "TR", "SR")
TECH_AR = {
    "PD": "1. الاتجاهات الأولية (PD)",
    "SA": "2. الأقواس الشمسية (SA)",
    "SD": "3. التقدمية الثانوية (SD)",
    "AP": "4. الانتهاء السنوي والشهري (AP)",
    "TR": "5. العبور الكوكبي (TR)",
    "SR": "6. العودة الشمسية (SR)",
}
TECH_COLORS = {
    "PD": "#6366F1", "SA": "#0EA5E9", "SD": "#14B8A6",
    "AP": "#F59E0B", "TR": "#EC4899", "SR": "#8B5CF6",
}
ENTITY_LABELS = {"individual": "فرد", "country": "دولة", "company": "شركة"}

# ثوابت تقييم الخرائط الست
ASPECTS = (0, 30, 45, 60, 90, 120, 135, 150, 180)
MAJOR_ASPECTS = (0, 60, 90, 120, 180)
ASPECT_W = {0: 1.0, 180: 1.0, 90: 0.85, 120: 0.85, 60: 0.8, 30: 0.4, 45: 0.45, 135: 0.45, 150: 0.45}

PD_ORB_MAJOR, PD_ORB_MINOR = 12.0, 6.0
SA_ORB_MAJOR, SA_ORB_MINOR = 14.0, 7.0
TR_ORB = 60.0
SR_ORB_MAJOR, SR_ORB_MINOR = 50.0, 25.0
AP_ORB_MAJOR, AP_ORB_MINOR = 35.0, 18.0
BASE_SCORE = 25.0
SEC_ORB = {
    "SUN": 12.0, "MOON": 36.0, "MER": 12.0, "VEN": 12.0, "MAR": 12.0,
    "JUP": 9.0, "SAT": 9.0, "URA": 5.0, "NEP": 5.0, "PLU": 5.0, "NN": 5.0, "SN": 5.0,
}
SEC_ORB_MOON = (36.0, 20.0)

OUTER_PLANETS = [("SAT", "زحل"), ("JUP", "المشتري"), ("URA", "أورانوس"), ("NEP", "نبتون"), ("PLU", "بلوتو")]
TRANSIT_ASPECTS = [
    (0.0, "اقتران (0°)", 6.5),
    (180.0, "تقابل (180°)", 6.0),
    (90.0, "تربيع (90°)", 5.5),
    (120.0, "تثليث (120°)", 5.5),
    (60.0, "تسديس (60°)", 4.5),
]
PHASE_ANGLES = [
    (0.0, "اقتران زاوي (0°)"),
    (45.0, "نصف تربيع طوري (45°)"),
    (60.0, "تسديس طوري (60°)"),
    (90.0, "تربيع طوري حرج (90°)"),
    (120.0, "تثليث طوري (120°)"),
    (135.0, "تربيع ونصف طوري (135°)"),
    (180.0, "مقابلة طورية (180°)"),
]

# ==================== قواميس السنوية ====================
HOUSES_MEANINGS: Dict[str, Dict[int, str]] = {
    "individual": {
        1: "الذات، الطاقة الجسدية، المبادرات الشخصية",
        2: "المال المكتسب، الممتلكات والسيولة",
        3: "التنقل الداخلي، الإخوة، التواصل والدراسات القصيرة",
        4: "الأسرة، الوالدين، السكن والعقارات",
        5: "العاطفة، العلاقات العابرة، الأبناء والمشاريع الإبداعية",
        6: "بيئة العمل اليومي، الصحة، والروتين اليومي",
        7: "الشراكات، الزواج، العقود، والأعداء الظاهرون",
        8: "أموال الشراكات والقروض، العمليات، والأزمات العميقة",
        9: "السفر البعيد، الهجرة، التعليم العالي والتوسع الفكري",
        10: "المكانة المهنية، الترقية، السمعة وعلاقتك بالمسؤولين",
        11: "الأصدقاء، الدعم الاجتماعي، وتحقيق الأماني الكبرى",
        12: "العزلة، المستشفيات، المؤامرات الخفية والراحة النفسية",
    },
    "country": {
        1: "الشعب، الهوية الوطنية، وصورة الدولة العالمية",
        2: "الخزينة العامة، الاقتصاد الوطني والقدرة الشرائية",
        3: "الإعلام، النقل والمواصلات، والتجارة الداخلية",
        4: "الأراضي، المحاصيل، المعارضة والنسيج الداخلي",
        5: "قطاع الاستثمار والترفيه والأسواق المالية",
        6: "القوات المسلحة (الأمن الداخلي)، الصحة العامة والنقابات",
        7: "العلاقات الدبلوماسية، المعاهدات الدولية أو النزاعات",
        8: "الديون السيادية، المخابرات، ومعدلات الوفيات والضرائب",
        9: "القضاء الأعلى، التجارة الخارجية، والشحن الدولي",
        10: "الحكومة، رئيس الدولة، والسلطة التنفيذية العليا",
        11: "البرلمان، التحالفات الدولية والدول الصديقة",
        12: "التهديدات السرية، السجون، وحركات التخريب الخفية",
    },
    "company": {
        1: "العلامة التجارية (Brand)، مكانة الشركة التأسيسية",
        2: "الإيرادات، السيولة النقدية، والأصول السائلة",
        3: "التسويق والمبيعات اليومية، العلاقات العامة",
        4: "المقر الرئيسي، الأصول العقارية والمخازن",
        5: "الابتكار والبحث والتطوير (R&D) والاستثمارات الجريئة",
        6: "فريق العمل التشغيلي، الروتين وظروف العمل الداخلية",
        7: "الشراكات التجارية (B2B)، العقود، والمنافسين المباشرين",
        8: "التمويل البنكي، الضرائب، الاندماجات والاستحواذات",
        9: "التوسع الدولي، التراخيص القانونية، والملكية الفكرية",
        10: "المدير التنفيذي (CEO)، مجلس الإدارة والقيادة",
        11: "المساهمون، قاعدة العملاء المخلصين وشبكة العلاقات",
        12: "الالتزامات الخفية، المنافسة غير الشريفة ومخاطر التسريب",
    },
}

PLANETS_MEANINGS: Dict[str, Dict[str, str]] = {
    "individual": {
        "الشمس": "الوضوح، التقدير، واكتساب الأهمية والريادة",
        "القمر": "تغيرات مشاعرية، تقلبات، وحاجة للأمان",
        "عطارد": "حركة فكرية سريعة، عقود، اتصالات ومفاوضات",
        "الزهرة": "وفرة مالية، بهجة، حب، تسهيل ومصالحات",
        "المريخ": "طاقة تنافسية عالية، شجاعة، توترات ومواجهات",
        "المشتري": "توسع استثنائي، حظوظ مباركة، وانفراجات كبرى",
        "زحل": "مسؤوليات ثقيلة، تأخيرات، إعادة تنظيم، وصبر مفروض",
        "أورانوس": "تغيرات مفاجئة غير متوقعة، ثورات وحرية جديدة",
        "نبتون": "إلهام روحي وفني، أو ضبابية وتشتت وغموض",
        "بلوتو": "تحولات جذرية، نهاية حاسمة لمرحلة وبداية جديدة",
    },
    "country": {
        "الشمس": "رئيس الدولة ومصدر القرار السيادي",
        "القمر": "المزاج الشعبي والجمهور العام",
        "عطارد": "الصحافة، الاتصالات، والتجارة",
        "الزهرة": "المناخ الدبلوماسي والثقافي الإيجابي",
        "المريخ": "المؤسسة العسكرية والجاهزية القتالية",
        "المشتري": "النمو الاقتصادي والازدهار والعدالة",
        "زحل": "القوانين الصارمة، البنية التحتية، والبيروقراطية",
        "أورانوس": "الابتكار الرقمي، أو الاضطرابات المفاجئة",
        "نبتون": "الموارد البحرية والنفط، أو الشائعات والبروباغندا",
        "بلوتو": "أجهزة الأمن السيادية والثروات الباطنية الاستراتيجية",
    },
    "company": {
        "الشمس": "الرئيس التنفيذي (CEO) والقيادة الإستراتيجية",
        "القمر": "رضا العملاء والمناخ العام للموظفين",
        "عطارد": "العقود والصفقات وتحليلات البيانات",
        "الزهرة": "تصميم المنتجات وراحة بيئة العمل",
        "المريخ": "الحملات الهجومية وقوة اختراق السوق",
        "المشتري": "جلب الاستثمارات والنمو المالي والانتشار",
        "زحل": "إدارة المخاطر، الالتزام المؤسسي والحوكمة",
        "أورانوس": "التحول التكنولوجي وإعادة الهيكلة السريعة",
        "نبتون": "الصورة الذهنية للعلامة التجارية والمسؤولية المجتمعية",
        "بلوتو": "الاستحواذات الكبرى أو الإنقاذ في الأزمات العاصفة",
    },
}

SHORT_MEANINGS_MAP: Dict[str, Dict[str, str]] = {
    "individual": {
        "الشمس": "الوضوح والريادة", "القمر": "المشاعر والحركة", "عطارد": "التواصل والاتفاقات",
        "الزهرة": "المال والعاطفة", "المريخ": "الجهد والمواجهة", "المشتري": "التوسع والوفرة",
        "زحل": "الانضباط والتحدي", "أورانوس": "المفاجآت والتحول", "نبتون": "الإلهام أو الحيرة", "بلوتو": "التحول الجذري",
    },
    "country": {
        "الشمس": "القيادة السياسية", "القمر": "الشعب", "عطارد": "الإعلام والتجارة",
        "الزهرة": "الدبلوماسية", "المريخ": "القوة العسكرية", "المشتري": "الازدهار المالي",
        "زحل": "النظام والقانون", "أورانوس": "المتغيرات التقنية/الشعبية", "نبتون": "الموارد والنفط", "بلوتو": "المخابرات والتحولات",
    },
    "company": {
        "الشمس": "الرؤية والقيادة", "القمر": "العملاء والموظفون", "عطارد": "المبيعات والبيانات",
        "الزهرة": "التصميم والتجربة", "المريخ": "المنافسة والسرعة", "المشتري": "الاستثمار والتوسع",
        "زحل": "الحوكمة والمخاطر", "أورانوس": "الابتكار الرقمي", "نبتون": "البراند والسمعة", "بلوتو": "إعادة الهيكلة والاندماج",
    },
}

AR_COUNTRY_HINTS = {
    "SY": "سوريا", "AE": "الإمارات", "SA": "السعودية", "EG": "مصر", "JO": "الأردن",
    "LB": "لبنان", "IQ": "العراق", "KW": "الكويت", "QA": "قطر", "BH": "البحرين",
    "OM": "عمان", "YE": "اليمن", "PS": "فلسطين", "MA": "المغرب", "DZ": "الجزائر",
    "TN": "تونس", "LY": "ليبيا", "SD": "السودان", "US": "الولايات المتحدة", "GB": "المملكة المتحدة",
    "FR": "فرنسا", "DE": "ألمانيا", "TR": "تركيا", "RU": "روسيا", "CN": "الصين", "JP": "اليابان",
}


# ==================== الجغرافيا (الدولة والمدن مرتبة حسب الكثافة السكانية) ====================
@st.cache_resource
def load_geo():
    gc = geonamescache.GeonamesCache()
    countries = gc.get_countries()
    cities = gc.get_cities()
    tf = TimezoneFinder()
    return countries, cities, tf


def get_cities_sorted_by_population(cities: dict, country_code: str) -> List[dict]:
    matched = [c for c in cities.values() if c.get("countrycode") == country_code and c.get("population", 0) >= 15000]
    if not matched:
        matched = [c for c in cities.values() if c.get("countrycode") == country_code]
    return sorted(matched, key=lambda c: c.get("population", 0), reverse=True)


# ==================== المحرك الفلكي المرجعي (Swiss Ephemeris) ====================
def mod360(x: float) -> float:
    return x % 360.0


def wrap180(x: float) -> float:
    return ((x + 180.0) % 360.0) - 180.0


def angular_sep(a: float, b: float) -> float:
    d = abs((a % 360.0) - (b % 360.0))
    return 360.0 - d if d > 180.0 else d


def zodiac_info(lon: float) -> Tuple[int, str, float]:
    lon = mod360(lon)
    idx = int(lon // 30) % 12
    return idx, ZODIAC_SIGNS[idx], lon % 30.0


def whole_sign_house_of(asc_sign_idx: int, target_sign_idx: int) -> int:
    return ((target_sign_idx - asc_sign_idx) % 12) + 1


def describe_lon(lon: float) -> str:
    _, sign_name, deg = zodiac_info(lon)
    d = int(deg)
    m = int((deg - d) * 60.0)
    return f"{d:02d}°{m:02d}′ {sign_name}"


def get_obliquity(jd: float) -> float:
    res = swe.calc_ut(jd, swe.ECL_NUT)[0]
    return float(res[0])


def get_ramc(jd: float, lon_deg: float) -> float:
    gmst_hours = swe.sidtime(jd)
    return mod360(gmst_hours * 15.0 + lon_deg)


def get_lons(jd: float) -> Dict[str, float]:
    out = {k: float(swe.calc_ut(jd, pid)[0][0]) % 360.0 for k, pid in PLANET_IDS.items()}
    out["NN"] = float(swe.calc_ut(jd, swe.MEAN_NODE)[0][0]) % 360.0
    out["SN"] = (out["NN"] + 180.0) % 360.0
    return out


def get_speeds(jd: float) -> Dict[str, float]:
    out = {k: float(swe.calc_ut(jd, pid, swe.FLG_SPEED)[0][3]) for k, pid in PLANET_IDS.items()}
    out["NN"] = float(swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SPEED)[0][3])
    out["SN"] = out["NN"]
    return out


def jd_to_datetime_utc(jd: float) -> datetime:
    y, m, d, fh = swe.revjul(jd)
    hh = int(fh)
    mm = int((fh - hh) * 60.0)
    ss = int(((fh - hh) * 60.0 - mm) * 60.0)
    return datetime(y, m, d, hh, mm, ss, tzinfo=timezone.utc)


def ecl_to_equatorial(lon_deg: float, lat_ecl_deg: float, eps_deg: float) -> Tuple[float, float]:
    lam = math.radians(lon_deg)
    beta = math.radians(lat_ecl_deg)
    eps = math.radians(eps_deg)
    ra = math.atan2(math.sin(lam) * math.cos(eps) - math.tan(beta) * math.sin(eps), math.cos(lam))
    dec = math.asin(max(-1.0, min(1.0, math.sin(beta) * math.cos(eps) + math.cos(beta) * math.sin(eps) * math.sin(lam))))
    return mod360(math.degrees(ra)), math.degrees(dec)


def ra_of_lon(lon_deg: float, eps_deg: float) -> float:
    lam = math.radians(lon_deg)
    eps = math.radians(eps_deg)
    return mod360(math.degrees(math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))))


def topo_cusp_lon(ramc_deg: float, lat_deg: float, eps_deg: float, offset_deg: float, pole_factor: float) -> float:
    theta = mod360(ramc_deg + offset_deg)
    tan_phi = math.tan(math.radians(lat_deg)) * pole_factor
    eps = math.radians(eps_deg)
    th = math.radians(theta)
    s_th, c_th = math.sin(th), math.cos(th)
    c_ep, s_ep = math.cos(eps), math.sin(eps)
    x = c_th
    y = s_th * c_ep + tan_phi * s_ep
    if abs(x) < 1e-12 and abs(y) < 1e-12:
        return 0.0
    return mod360(math.degrees(math.atan2(y, x)))


def all_cusps_topocentric(ramc_deg: float, lat_deg: float, eps_deg: float) -> Dict[str, float]:
    tan_lat = math.tan(math.radians(lat_deg))
    f1 = math.atan(tan_lat / 3.0) / math.radians(lat_deg) if abs(lat_deg) > 0.01 else 1.0 / 3.0
    f2 = math.atan(2.0 * tan_lat / 3.0) / math.radians(lat_deg) if abs(lat_deg) > 0.01 else 2.0 / 3.0
    if abs(lat_deg) > 0.01 and abs(tan_lat) > 1e-9:
        f1 = (tan_lat / 3.0) / tan_lat
        f2 = (2.0 * tan_lat / 3.0) / tan_lat
    mc = topo_cusp_lon(ramc_deg, lat_deg, eps_deg, 0.0, 0.0)
    as_deg = topo_cusp_lon(ramc_deg, lat_deg, eps_deg, 90.0, 1.0)
    return {
        "MC": mc, "IC": mod360(mc + 180.0),
        "AS": as_deg, "DS": mod360(as_deg + 180.0),
        "H11": topo_cusp_lon(ramc_deg, lat_deg, eps_deg, 30.0, f1),
        "H12": topo_cusp_lon(ramc_deg, lat_deg, eps_deg, 60.0, f2),
        "H2": topo_cusp_lon(ramc_deg, lat_deg, eps_deg, 120.0, f2),
        "H3": topo_cusp_lon(ramc_deg, lat_deg, eps_deg, 150.0, f1),
        "H5": mod360(topo_cusp_lon(ramc_deg, lat_deg, eps_deg, 30.0, f1) + 180.0),
        "H6": mod360(topo_cusp_lon(ramc_deg, lat_deg, eps_deg, 60.0, f2) + 180.0),
        "H8": mod360(topo_cusp_lon(ramc_deg, lat_deg, eps_deg, 120.0, f2) + 180.0),
        "H9": mod360(topo_cusp_lon(ramc_deg, lat_deg, eps_deg, 150.0, f1) + 180.0),
        "EP": topo_cusp_lon(ramc_deg, 0.0, eps_deg, 90.0, 0.0),
    }


def compute_whole_sign_solar_cusps(sun_lon: float, ramc_deg: float, eps_deg: float) -> Dict[str, float]:
    """تثبيت الطالع على البرج الشمسي بنظام كل برج بيت."""
    sun_sign_idx = int(mod360(sun_lon) // 30) % 12
    asc_deg = sun_sign_idx * 30.0
    mc_deg = topo_cusp_lon(ramc_deg, 0.0, eps_deg, 0.0, 0.0)
    return {
        "AS": asc_deg,
        "H2": mod360(asc_deg + 30.0),
        "H3": mod360(asc_deg + 60.0),
        "IC": mod360(asc_deg + 90.0),
        "H5": mod360(asc_deg + 120.0),
        "H6": mod360(asc_deg + 150.0),
        "DS": mod360(asc_deg + 180.0),
        "H8": mod360(asc_deg + 210.0),
        "H9": mod360(asc_deg + 240.0),
        "MC": mc_deg,
        "H11": mod360(asc_deg + 300.0),
        "H12": mod360(asc_deg + 330.0),
        "EP": mod360(asc_deg + 15.0),
    }


def compute_arabic_lots(asc_deg: float, sun_lon: float, moon_lon: float) -> Tuple[bool, float, float]:
    diff_sun_asc = mod360(sun_lon - asc_deg)
    is_day = diff_sun_asc > 180.0 or diff_sun_asc < 0.0
    pof = mod360(asc_deg + moon_lon - sun_lon) if is_day else mod360(asc_deg + sun_lon - moon_lon)
    pos = mod360(asc_deg + sun_lon - moon_lon) if is_day else mod360(asc_deg + moon_lon - sun_lon)
    return is_day, pof, pos


def direct_planet(lon_deg: float, ramc_deg: float, lat_deg: float, eps_deg: float, arc_deg: float) -> float:
    ra, dec = ecl_to_equatorial(lon_deg, 0.0, eps_deg)
    if abs(dec) > 23.44:
        dec = math.copysign(23.44, dec)
    d = mod360(ra - ramc_deg)
    if d <= 90.0:
        md, sign_md, is_upper = d, 1.0, True
    elif d <= 180.0:
        md, sign_md, is_upper = 180.0 - d, 1.0, False
    elif d <= 270.0:
        md, sign_md, is_upper = d - 180.0, -1.0, False
    else:
        md, sign_md, is_upper = 360.0 - d, -1.0, True

    tan_phi = math.tan(math.radians(lat_deg))
    tan_dec = math.tan(math.radians(dec))
    ad_0 = math.degrees(math.asin(max(-0.9999, min(0.9999, tan_phi * tan_dec))))
    sa_semi = (90.0 + ad_0) if is_upper else (90.0 - ad_0)
    sa_semi = max(10.0, min(170.0, sa_semi))
    pole_frac = md / sa_semi

    ramc_new = mod360(ramc_deg + arc_deg)
    tan_pole = pole_frac * tan_phi
    if is_upper:
        ad_p = math.degrees(math.asin(max(-0.9999, min(0.9999, tan_pole * tan_dec))))
        oa_0 = ra - ad_0 * sign_md
        oa_new = oa_0 + arc_deg
        ra_new = oa_new + ad_p * sign_md
    else:
        ad_p = math.degrees(math.asin(max(-0.9999, min(0.9999, tan_pole * tan_dec))))
        oa_0 = ra + ad_0 * sign_md
        oa_new = oa_0 + arc_deg
        ra_new = oa_new - ad_p * sign_md
    _ = ramc_new
    eps_r = math.radians(eps_deg)
    ra_r = math.radians(ra_new)
    return mod360(math.degrees(math.atan2(math.sin(ra_r), math.cos(ra_r) * math.cos(eps_r))))


def find_solar_return_jd(natal_sun_lon: float, target_year: int) -> float:
    jd_s = swe.julday(target_year, 1, 1, 0.0)
    jd_e = swe.julday(target_year, 12, 31, 23.99)
    for _ in range(52):
        jd_m = 0.5 * (jd_s + jd_e)
        lon_m = float(swe.calc_ut(jd_m, swe.SUN)[0][0]) % 360.0
        diff = mod360(lon_m - natal_sun_lon)
        if diff > 180.0:
            diff -= 360.0
        if diff < 0:
            jd_s = jd_m
        else:
            jd_e = jd_m
    return 0.5 * (jd_s + jd_e)


def get_solar_month_window(sr_dt: datetime, house_num: int) -> str:
    start_dt = sr_dt + timedelta(days=(house_num - 1) * 30.4368)
    end_dt = start_dt + timedelta(days=30.4368)
    m1 = AR_MONTHS[start_dt.month - 1]
    m2 = AR_MONTHS[end_dt.month - 1]
    return f"{m1} - {m2} {end_dt.year}"


# ==================== محرك الخرائط الست (تسيير) ====================
class TechAccumulator:
    def __init__(self) -> None:
        self.h1 = {t: 0.0 for t in TECH_CODES}
        self.h2 = {t: 0.0 for t in TECH_CODES}
        self.h3 = {t: 0.0 for t in TECH_CODES}
        self.hits: List[dict] = []

    def _push(self, tech: str, s: float) -> None:
        if s <= 0:
            return
        if s >= self.h1[tech]:
            self.h3[tech], self.h2[tech], self.h1[tech] = self.h2[tech], self.h1[tech], s
        elif s >= self.h2[tech]:
            self.h3[tech], self.h2[tech] = self.h2[tech], s
        elif s > self.h3[tech]:
            self.h3[tech] = s

    def add(
        self, tech: str, directed_factor: str, natal_target: str,
        lam_a: float, lam_b: float, factor: float, sub_w: float,
        lim_maj: float, lim_min: float, aspects: Sequence[int],
    ) -> None:
        d = mod360(lam_a - lam_b)
        for a in aspects:
            o_arc_min = min(abs(d - a), abs(d - (360.0 - a))) * 60.0
            lim = lim_maj if a in MAJOR_ASPECTS else lim_min
            if o_arc_min < lim:
                closeness = max(0.0, 1.0 - o_arc_min / lim) ** 1.25
                exact_boost = 1.3 if o_arc_min <= 3.0 else (1.12 if o_arc_min <= 8.0 else 1.0)
                strength = factor * sub_w * ASPECT_W.get(a, 0.5) * closeness * exact_boost
                if strength > 0:
                    self._push(tech, strength)
                    self.hits.append({
                        "tech_code": tech,
                        "tech_name": TECH_AR[tech],
                        "directed_factor": directed_factor,
                        "natal_target": natal_target,
                        "aspect_deg": a,
                        "aspect_name": ASPECT_AR.get(a, f"{a}°"),
                        "orb_arc_min": o_arc_min,
                        "strength": BASE_SCORE * strength,
                    })

    def get_percentages(self) -> Tuple[Dict[str, float], float]:
        pcts = {}
        for t in TECH_CODES:
            eff = self.h1[t] + 0.3 * (self.h2[t] + self.h3[t])
            pcts[t] = max(0.0, min(100.0, 100.0 * (1.0 - math.exp(-1.1 * eff))))
        return pcts, sum(pcts.values()) / len(TECH_CODES)


def get_annual_spec(entity_type: str) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]], str]:
    if entity_type == "country":
        return (
            [("MC", 1.0), ("AS", 1.0), ("H2", 0.9), ("H6", 0.85), ("H8", 0.85), ("DS", 0.8), ("IC", 0.7), ("H12", 0.65), ("EP", 0.55), ("POF", 0.65)],
            [("SAT", 1.0), ("JUP", 1.0), ("MAR", 0.95), ("SUN", 0.9), ("PLU", 0.9), ("URA", 0.85), ("NEP", 0.85), ("MOON", 0.8), ("MER", 0.65), ("VEN", 0.65), ("NN", 0.7)],
            "MC",
        )
    if entity_type == "company":
        return (
            [("MC", 1.0), ("H2", 1.0), ("AS", 0.95), ("H8", 0.9), ("DS", 0.85), ("H6", 0.8), ("H5", 0.75), ("H11", 0.7), ("EP", 0.55), ("POF", 0.7)],
            [("JUP", 1.0), ("SAT", 1.0), ("SUN", 0.95), ("MER", 0.9), ("VEN", 0.85), ("URA", 0.85), ("PLU", 0.85), ("MAR", 0.8), ("NEP", 0.7), ("NN", 0.7)],
            "H2",
        )
    return (
        [("AS", 1.0), ("MC", 1.0), ("DS", 0.95), ("IC", 0.9), ("H2", 0.85), ("H6", 0.8), ("H8", 0.75), ("H5", 0.75), ("H11", 0.7), ("EP", 0.55), ("POF", 0.7)],
        [("SUN", 1.0), ("MOON", 0.95), ("SAT", 1.0), ("JUP", 1.0), ("VEN", 0.9), ("MAR", 0.9), ("MER", 0.8), ("URA", 0.8), ("NEP", 0.8), ("PLU", 0.8), ("NN", 0.75)],
        "AS",
    )


def evaluate_six_charts_for_year(natal: dict, target_jd: float, target_year: int, entity_type: str) -> dict:
    acc = TechAccumulator()
    days = max(1.0, target_jd - natal["jd"])
    sig_list, pls_list, event_house_key = get_annual_spec(entity_type)
    pl_tr = get_lons(target_jd)

    # 1. الاتجاهات الأولية (PD)
    arc_naibod = days * NAIBOD_PER_DAY
    for sgn, dlab, tw_cusp in ((1, "مباشر", 1.05), (-1, "عكسي", 0.85)):
        arc = sgn * arc_naibod
        dc = all_cusps_topocentric(natal["ramc"] + arc, natal["lat"], natal["eps"])
        dc["POF"] = mod360(natal["pof"] + arc)
        for s, fs in sig_list:
            dc_val = dc.get(s, mod360(natal["cusps"][s] + arc))
            for p, fp in pls_list:
                acc.add("PD", f"{FACTOR_AR.get(s, s)} ({dlab})", f"{PLANET_AR[p]} أصلي", dc_val, natal["pl"][p], fs * fp, tw_cusp, PD_ORB_MAJOR, PD_ORB_MINOR, ASPECTS)
        prom_lab = "عكسي فلكي" if sgn == 1 else "مباشر فلكي"
        for p, fp in pls_list:
            ld = direct_planet(natal["pl"][p], natal["ramc"], natal["lat"], natal["eps"], arc)
            for s, fs in sig_list:
                acc.add("PD", f"{PLANET_AR[p]} ({prom_lab})", f"{FACTOR_AR.get(s, s)} أصلي", ld, natal["cusps"][s], fs * fp, 0.9, PD_ORB_MAJOR, PD_ORB_MINOR, ASPECTS)

    # 2. الأقواس الشمسية (SA)
    yrs = days / TROPICAL_YEAR
    sa_base = mod360(get_lons(natal["jd"] + yrs)["SUN"] - natal["pl"]["SUN"])
    for sgn, dlab, w_dir in ((1, "+قوس شمسي", 0.9), (-1, "-قوس عكسي", 0.65)):
        sa = sgn * sa_base
        for s, fs in sig_list:
            for p, fp in pls_list:
                acc.add("SA", f"{FACTOR_AR.get(s, s)} ({dlab})", f"{PLANET_AR[p]} أصلي", mod360(natal["cusps"][s] + sa), natal["pl"][p], fs * fp, w_dir, SA_ORB_MAJOR, SA_ORB_MINOR, ASPECTS)
                acc.add("SA", f"{PLANET_AR[p]} ({dlab})", f"{FACTOR_AR.get(s, s)} أصلي", mod360(natal["pl"][p] + sa), natal["cusps"][s], fs * fp, w_dir * 0.9, SA_ORB_MAJOR, SA_ORB_MINOR, ASPECTS)

    # 3. التقدمية الثانوية (SD)
    sun0_ra = ra_of_lon(natal["pl"]["SUN"], natal["eps"])
    for jdx, lab, tw in ((natal["jd"] + yrs, "تقدمي", 0.95), (natal["jd"] - yrs, "تراجعي", 0.7)):
        pl_sd = get_lons(jdx)
        arc_sd = wrap180(ra_of_lon(pl_sd["SUN"], natal["eps"]) - sun0_ra)
        dc = all_cusps_topocentric(natal["ramc"] + arc_sd, natal["lat"], natal["eps"])
        _, dc["POF"], _ = compute_arabic_lots(dc["AS"], pl_sd["SUN"], pl_sd["MOON"])
        for p, fp in pls_list:
            lmj, lmn = SEC_ORB_MOON if p == "MOON" else (SEC_ORB[p], SEC_ORB[p])
            for s, fs in sig_list:
                acc.add("SD", f"{FACTOR_AR.get(s, s)} ({lab})", f"{PLANET_AR[p]} أصلي", dc.get(s, mod360(natal["cusps"][s] + arc_sd)), natal["pl"][p], fs * fp, tw, lmj, lmn, ASPECTS)
                acc.add("SD", f"{PLANET_AR[p]} ({lab})", f"{FACTOR_AR.get(s, s)} أصلي", pl_sd[p], natal["cusps"][s], fs * fp, tw * 0.95, lmj, lmn, ASPECTS)

    # 4. الانتهاء السنوي والشهري (AP)
    age_int = int(yrs)
    frac_yr = yrs - age_int
    prof_arc_yr = mod360(yrs * 30.0)
    prof_arc_mo = mod360(age_int * 30.0 + frac_yr * 360.0)
    prof_as = mod360(natal["cusps"]["AS"] + prof_arc_yr)
    prof_mc = mod360(natal["cusps"]["MC"] + prof_arc_yr)
    prof_pof = mod360(natal["pof"] + prof_arc_yr)
    prof_as_mo = mod360(natal["cusps"]["AS"] + prof_arc_mo)

    for p, fp in pls_list:
        acc.add("AP", "انتهاء الطالع السنوي", f"{PLANET_AR[p]} أصلي", prof_as, natal["pl"][p], fp, 0.95, AP_ORB_MAJOR, AP_ORB_MINOR, MAJOR_ASPECTS)
        acc.add("AP", "انتهاء العاشر السنوي", f"{PLANET_AR[p]} أصلي", prof_mc, natal["pl"][p], fp, 0.85, AP_ORB_MAJOR, AP_ORB_MINOR, MAJOR_ASPECTS)
        acc.add("AP", "انتهاء سهم السعادة", f"{PLANET_AR[p]} أصلي", prof_pof, natal["pl"][p], fp, 0.75, AP_ORB_MAJOR, AP_ORB_MINOR, MAJOR_ASPECTS)
        if p != "MOON":
            acc.add("AP", "انتهاء الطالع السنوي", f"{PLANET_AR[p]} عابر", prof_as, pl_tr[p], fp, 0.8, AP_ORB_MAJOR, AP_ORB_MINOR, MAJOR_ASPECTS)
            acc.add("AP", "انتهاء الطالع الشهري", f"{PLANET_AR[p]} عابر", prof_as_mo, pl_tr[p], fp, 0.65, AP_ORB_MAJOR, AP_ORB_MINOR, MAJOR_ASPECTS)

    prof_sign_idx = (natal["sun_sign_idx"] + age_int) % 12
    lord_of_year = SIGN_RULERS[prof_sign_idx]
    ev_house_sign = int(natal["cusps"][event_house_key] // 30.0) % 12
    lord_of_house = SIGN_RULERS[ev_house_sign]
    acc.add("AP", "رب السنة عابر", "الطالع الشمسي AS أصلي", pl_tr[lord_of_year], natal["cusps"]["AS"], 1.0, 0.95, TR_ORB, TR_ORB, MAJOR_ASPECTS)
    acc.add("AP", "رب السنة عابر", "وتد السماء MC أصلي", pl_tr[lord_of_year], natal["cusps"]["MC"], 1.0, 0.85, TR_ORB, TR_ORB, MAJOR_ASPECTS)
    acc.add("AP", "رب بيت الكيان عابر", "الطالع الشمسي AS أصلي", pl_tr[lord_of_house], natal["cusps"]["AS"], 1.0, 0.9, TR_ORB, TR_ORB, MAJOR_ASPECTS)
    acc.add("AP", "انتهاء الطالع السنوي", "رب السنة أصلي", prof_as, natal["pl"][lord_of_year], 1.0, 1.0, AP_ORB_MAJOR, AP_ORB_MINOR, MAJOR_ASPECTS)

    # 5. العبور الكوكبي (TR)
    pl_pre = get_lons(2.0 * natal["jd"] - target_jd)
    for lab, pl_set, tw in (("مباشر", pl_tr, 0.9), ("ما قبل الولادة", pl_pre, 0.65)):
        for p, fp in pls_list:
            if p == "MOON":
                continue
            for s, fs in sig_list:
                acc.add("TR", f"{PLANET_AR[p]} عابر ({lab})", f"{FACTOR_AR.get(s, s)} أصلي", pl_set[p], natal["cusps"][s], fs * fp, tw, TR_ORB, TR_ORB, MAJOR_ASPECTS)

    # 6. العودة الشمسية (SR)
    sr_jd = find_solar_return_jd(natal["pl"]["SUN"], target_year)
    eps_sr = get_obliquity(sr_jd)
    ramc_sr = get_ramc(sr_jd, natal["lon"])
    pl_sr = get_lons(sr_jd)
    speeds_sr = get_speeds(sr_jd)
    sr_topo = all_cusps_topocentric(ramc_sr, natal["lat"], eps_sr)
    _, sr_topo["POF"], _ = compute_arabic_lots(sr_topo["AS"], pl_sr["SUN"], pl_sr["MOON"])

    for sr_ang in ("AS", "MC", "DS", "IC", "POF"):
        for nat_s, fs in sig_list[:4]:
            acc.add("SR", f"{FACTOR_AR[sr_ang]} عودة شمسية", f"{FACTOR_AR.get(nat_s, nat_s)} أصلي", sr_topo[sr_ang], natal["cusps"][nat_s], fs, 1.0, SR_ORB_MAJOR, SR_ORB_MINOR, MAJOR_ASPECTS)
        for p, fp in pls_list:
            acc.add("SR", f"{FACTOR_AR[sr_ang]} عودة شمسية", f"{PLANET_AR[p]} أصلي", sr_topo[sr_ang], natal["pl"][p], fp, 0.9, SR_ORB_MAJOR, SR_ORB_MINOR, ASPECTS)

    for p, fp in pls_list:
        for nat_s, fs in sig_list[:4]:
            acc.add("SR", f"{PLANET_AR[p]} في العودة الشمسية", f"{FACTOR_AR.get(nat_s, nat_s)} أصلي", pl_sr[p], natal["cusps"][nat_s], fs * fp, 0.8, SR_ORB_MAJOR, SR_ORB_MINOR, MAJOR_ASPECTS)

    sr_asc_idx, sr_asc_name, _ = zodiac_info(pl_sr["SUN"])
    planet_rows = []
    for code in [p for p in PLANETS if p not in ("NN", "SN")]:
        lon = pl_sr[code]
        s_idx, s_name, deg_in = zodiac_info(lon)
        planet_rows.append({
            "code": code,
            "name_ar": PLANET_AR[code],
            "longitude": lon,
            "sign_index": s_idx,
            "sign_name": s_name,
            "deg_in_sign": deg_in,
            "house": whole_sign_house_of(sr_asc_idx, s_idx),
            "is_retrograde": speeds_sr[code] < 0,
        })

    tech_pcts, mean_pct = acc.get_percentages()
    sorted_hits = sorted(acc.hits, key=lambda x: x["strength"], reverse=True)
    return {
        "tech_percents": tech_pcts,
        "mean_percent": mean_pct,
        "hits": sorted_hits,
        "profection_sign_index": prof_sign_idx,
        "profection_sign_name": ZODIAC_SIGNS[prof_sign_idx],
        "lord_of_year": lord_of_year,
        "lord_of_year_ar": PLANET_AR[lord_of_year],
        "solar_return": {
            "jd": sr_jd,
            "date_utc": jd_to_datetime_utc(sr_jd),
            "solar_asc_deg": sr_asc_idx * 30.0,
            "solar_asc_sign": f"{sr_asc_name} (كل برج بيت - الطالع الشمسي)",
            "solar_asc_sign_index": sr_asc_idx,
            "solar_mc_deg": sr_topo["MC"],
            "planet_rows": planet_rows,
        },
    }


# ==================== محرك رادار زحل-نبتون-هوميا-إيريس والكبلري ====================
def solve_kepler_true_anomaly_deg(mean_anom_deg: float, ecc: float) -> float:
    m_rad = math.radians(mod360(mean_anom_deg))
    e = m_rad + ecc * math.sin(m_rad)
    for _ in range(8):
        e -= (e - ecc * math.sin(e) - m_rad) / (1.0 - ecc * math.cos(e))
    nu = 2.0 * math.atan2(math.sqrt(1.0 + ecc) * math.sin(e / 2.0), math.sqrt(1.0 - ecc) * math.cos(e / 2.0))
    return mod360(math.degrees(nu))


def kepler_true_shift_deg(birth_jd: float, target_jd: float, period_years: float, ecc: float, m0_deg: float) -> float:
    j2000 = 2451545.0
    yb = (birth_jd - j2000) / 365.25
    yt = (target_jd - j2000) / 365.25
    nu_b = solve_kepler_true_anomaly_deg(m0_deg + (yb / period_years) * 360.0, ecc)
    nu_t = solve_kepler_true_anomaly_deg(m0_deg + (yt / period_years) * 360.0, ecc)
    return mod360(nu_t - nu_b)


def compute_true_phase_coupling(birth_jd: float, target_jd: float, sun0: float, sat0: float, nep0: float) -> dict:
    tr = get_lons(target_jd)
    pairs = [
        (tr["SAT"], sat0, "زحل العابر مع زحل الأصلي", (0, 90, 180), 1.0),
        (tr["NEP"], nep0, "نبتون العابر مع نبتون الأصلي", (0, 45, 60, 90, 120, 180), 1.0),
        (tr["NEP"], sun0, "نبتون العابر مع الشمس الأصلية", (0, 60, 90, 120, 180), 1.05),
        (tr["SAT"], sun0, "زحل العابر مع الشمس الأصلية", (0, 90, 180), 1.05),
    ]
    best_eff, best_raw, best_label = 90.0, 90.0, "طور مداري محايد"
    for t_lon, n_lon, p_name, allowed, wt in pairs:
        sep = angular_sep(t_lon, n_lon)
        for ang in allowed:
            orb = abs(sep - ang)
            eff = orb * wt
            if eff < best_eff:
                best_eff = eff
                best_raw = orb
                ang_lbl = next((lbl for a, lbl in PHASE_ANGLES if a == ang), f"{ang}°")
                best_label = f"{ang_lbl} · {p_name}"
    return {
        "true_phase_dev": min(0.5, best_eff / 18.0),
        "best_orb_deg": best_raw,
        "phase_label": best_label,
        "haumea_kepler_shift": kepler_true_shift_deg(birth_jd, target_jd, T_HAUMEA, E_HAUMEA, M0_HAUMEA_DEG),
        "eris_kepler_shift": kepler_true_shift_deg(birth_jd, target_jd, T_ERIS, E_ERIS, M0_ERIS_DEG),
    }


def focus_for_house(entity_type: str, house: int) -> str:
    if entity_type == "individual":
        if house in (6, 12):
            return "ضغوط صحية أو جسدية تستدعي إعادة ضبط نمط الحياة والاستشفاء"
        if house in (10, 1):
            return "ترقية أو تغيّر في المسؤوليات والواجهة والمكانة الاجتماعية"
        if house == 4:
            return "تحولات عميقة في العائلة أو السكن أو الأهل"
        if house == 7:
            return "مرحلة مفصلية في الشريك والزواج والعقود"
        if house in (2, 8):
            return "إعادة ترتيب المال المكتسب أو الديون والموارد المشتركة"
        return "إعادة هيكلة عامة للمسار الشخصي والاجتماعي"
    if entity_type == "company":
        if house in (2, 8):
            return "تحولات اقتصادية في الأرباح والسيولة والتمويل"
        if house in (10, 1):
            return "تغيير هيكلي في الإدارة العليا أو العلامة التجارية"
        if house in (6, 12):
            return "إعادة هيكلة تشغيلية ومعالجة مخاطر كامنة"
        if house in (7, 11):
            return "شراكات استراتيجية أو تحالفات أو صفقات اندماج"
        return "إعادة تنظيم إداري واقتصادي شاملة"
    if house in (6, 8, 12):
        return "توترات في الوضع الأمني - العسكري وإعادة تقييم استراتيجي"
    if house in (11, 1, 7):
        return "حراك شعبي أو تحول في الرأي العام والعلاقات الدولية"
    if house in (2, 10):
        return "تحولات اقتصادية وإصلاحات في الخزينة والمؤسسات السيادية"
    return "تحولات شاملة في السياسات الوطنية والمجتمع"


def score_houses(house_nums: Sequence[int], planet_rows: List[dict]) -> str:
    weights = {"المشتري": 2, "الزهرة": 2, "الشمس": 1, "القمر": 1, "عطارد": 1, "المريخ": -2, "زحل": -2, "بلوتو": -2, "أورانوس": -1, "نبتون": -1}
    active = [r for r in planet_rows if r["house"] in house_nums]
    score = sum(weights.get(r["name_ar"], 0) for r in active)
    if score >= 2:
        return "إيجابي داعم"
    if score <= -2:
        return "ضاغط يتطلب حذراً"
    if any(r["code"] in ("PLU", "URA") for r in active):
        return "تحوّل جوهري"
    return "متوازن"


def build_entity_advisory(entity_type: str, status: str, six_charts: dict, phase_label: str) -> dict:
    sr_rows = six_charts["solar_return"]["planet_rows"]
    sr_dt = six_charts["solar_return"]["date_utc"]
    w = lambda h: get_solar_month_window(sr_dt, h)
    p_in = lambda h: [r["name_ar"] for r in sr_rows if r["house"] == h]
    has_any = lambda hs, names: any(p in names for h in hs for p in p_in(h))

    evals, advice, warnings = [], [], []
    if entity_type == "individual":
        evals.append({"category": "العائلة", "rating": score_houses((4, 5, 3), sr_rows), "summary": "استقرار ووفرة عائلية وتحسين في السكن أو العقار" if has_any((4,), ("المشتري", "الزهرة")) else ("مسؤوليات عائلية مضاعفة واهتمام بصحة الوالدين وشؤون البيت" if has_any((4,), ("زحل", "المريخ", "بلوتو")) else "أجواء عائلية متوازنة مع تركيز على التواصل مع الأهل"), "period": f"{w(4)} · {w(5)}"})
        evals.append({"category": "المال", "rating": score_houses((2, 8), sr_rows), "summary": "فرص تدفق مالي ومكاسب أو موارد إضافية" if has_any((2, 8), ("المشتري", "الزهرة", "الشمس")) else ("تقلبات مالية أو التزامات تتطلب ضبط النفقات وتجنب القروض" if has_any((2, 8), ("زحل", "المريخ", "أورانوس")) else "تدفق مالي مستقر يحتاج إلى تخطيط وموازنة"), "period": f"{w(2)} · {w(8)}"})
        evals.append({"category": "العمل", "rating": score_houses((10, 6), sr_rows), "summary": "صعود مهني أو ترقية وتقدير في موقع المسؤولية" if has_any((10,), ("المشتري", "الشمس")) else ("تحول مفاجئ أو إعادة هيكلة في المسار الوظيفي" if has_any((10, 6), ("أورانوس", "بلوتو")) else ("ضغط مهني وتحديات إدارية تتطلب الصبر والانضباط" if has_any((10, 6), ("زحل", "المريخ")) else "انتظام في المهام المهنية وبناء تدريجي")), "period": f"{w(6)} · {w(10)}"})
        evals.append({"category": "الشريك", "rating": score_houses((7, 5), sr_rows), "summary": "انسجام في الشراكات أو فرص ارتباط رسمي وعقود مثمرة" if has_any((7,), ("الزهرة", "المشتري")) else ("اختبار حاسم للعلاقات الزوجية والمهنية يتطلب الهدوء وتجنب القطيعة" if has_any((7,), ("المريخ", "أورانوس", "بلوتو")) else "شراكات مستقرة تقوم على الوضوح والتفاهم"), "period": f"{w(7)} · {w(5)}"})
        evals.append({"category": "الوضع الاجتماعي", "rating": score_houses((11, 1, 9), sr_rows), "summary": "توسع شبكة العلاقات والدعم الاجتماعي وفرص سفر أو تعليم" if has_any((11, 9, 1), ("المشتري", "الشمس", "الزهرة")) else "حركة اجتماعية انتقائية مع تركيز على جودة التحالفات", "period": f"{w(11)} · {w(9)}"})
        s_prim, s_sub, _ = STATUS_LABELS[status]
        evals.append({"category": "التحولات العميقة", "rating": "تحوّل جوهري" if status != STATUS_NORMAL else score_houses((8, 12), sr_rows), "summary": f"{s_prim} ({s_sub}) بالتزامن مع رب السنة {six_charts['lord_of_year_ar']} ({six_charts['profection_sign_name']})", "period": f"{w(8)} · {w(12)}"})
        evals.append({"category": "الصحة", "rating": score_houses((6, 8, 12), sr_rows), "summary": "مؤشرات إجهاد تتطلب فحوصات دورية وتجنب الإرهاق البدني والنفسي" if has_any((6, 8, 12), ("المريخ", "زحل", "نبتون", "بلوتو")) else "مؤشرات صحية مستقرة مع أهمية الحفاظ على اللياقة والنوم المنتظم", "period": f"{w(6)} · {w(12)}"})

        for r in sr_rows:
            h = r["house"]
            if r["name_ar"] == "المشتري":
                advice.append(f"استثمر فرص التوسع والوفرة في شؤون البيت {h} ({HOUSES_MEANINGS['individual'][h]}) خلال {w(h)}.")
            elif r["name_ar"] == "الزهرة":
                advice.append(f"وظّف الدبلوماسية والمصالحات لتحقيق مكاسب في البيت {h} خلال {w(h)}.")
            elif r["name_ar"] == "زحل":
                warnings.append(f"التزم بالصبر والانضباط وتجنب المجازفة في شؤون البيت {h} ({w(h)}).")
            elif r["name_ar"] == "المريخ":
                warnings.append(f"تجنب الانفعال والصدامات في البيت {h} خاصة أثناء {w(h)}.")
            elif r["name_ar"] == "أورانوس":
                warnings.append(f"احتفظ بخطط بديلة أمام التقلبات المفاجئة في البيت {h} ({w(h)}).")
        advice.append(f"تفعيل برج الانتهاء السنوي ({six_charts['profection_sign_name']}) تحت قيادة {six_charts['lord_of_year_ar']} — ركّز على قرارات الحسم المدروسة.")
        if status in (STATUS_CRITICAL, STATUS_APEX, STATUS_UNIFIED):
            warnings.append(f"سنة مفصلية في رادار زحل-نبتون-هوميا-إيريس ({phase_label}): تجنب القرارات الاندفاعية غير القابلة للتراجع.")

    elif entity_type == "country":
        evals.append({"category": "الوضع الامني - العسكري", "rating": score_houses((6, 7, 8, 12), sr_rows), "summary": "جاهزية أمنية وعسكرية قصوى مع تحديات حدودية أو سيبرانية تتطلب اليقظة الاستخباراتية" if has_any((6, 7, 8, 12), ("المريخ", "بلوتو", "أورانوس", "زحل")) else "استقرار أمني ودفاعي وتوازن في الاتفاقيات الحدودية والعسكرية", "period": f"{w(6)} · {w(7)} · {w(12)}"})
        s_prim, _, _ = STATUS_LABELS[status]
        evals.append({"category": "شامل", "rating": "تحوّل جوهري" if status != STATUS_NORMAL else score_houses((10, 1, 9), sr_rows), "summary": f"حالة الرادار ({s_prim}) مع طالع سنوي في {six_charts['solar_return']['solar_asc_sign'].split(' ')[0]} ورب السنة {six_charts['lord_of_year_ar']} ({six_charts['mean_percent']:.0f}% رنين الخرائط الست)", "period": f"{w(1)} · {w(10)}"})
        evals.append({"category": "شعبي", "rating": score_houses((1, 4, 11), sr_rows), "summary": "حراك وطني إيجابي وزيادة في الثقة الشعبية بالمشاريع التنموية" if has_any((1, 4, 11), ("المشتري", "الزهرة", "الشمس")) else "مراقبة مطالب الرأي العام ومعالجة ضغوط المعيشة والخدمات", "period": f"{w(1)} · {w(4)}"})
        evals.append({"category": "اقتصادي", "rating": score_houses((2, 5, 8, 9), sr_rows), "summary": "نمو في الخزينة العامة وجذب للاستثمارات والتبادل التجاري" if has_any((2, 5), ("المشتري", "الزهرة")) else "سياسات نقدية حذرة لحماية العملة ومكافحة التضخم وإدارة الديون السيادية", "period": f"{w(2)} · {w(8)}"})
        advice.append(f"تعزيز التحالفات الاقتصادية والإقليمية خلال {w(11)} وإطلاق مشاريع البنية التحتية في {w(10)}.")
        advice.append(f"دعم الاستقرار النقدي والخزينة العامة وتطوير التجارة الخارجية في {w(2)} و{w(9)}.")
        warnings.append(f"رفع الجاهزية الأمنية ومواجهة الشائعات والحرب النفسية خلال {w(12)} و{w(8)}.")
        warnings.append(f"تأمين سلاسل الإمداد الغذائي والطبي ومتابعة الجاهزية العسكرية في {w(6)} و{w(7)}.")
    else:
        evals.append({"category": "هيكلي", "rating": score_houses((10, 6, 1, 7), sr_rows), "summary": "إعادة هيكلة إدارية أو تحول رقمي وقيادي يغيّر موقع الشركة في السوق" if has_any((10, 1, 6), ("أورانوس", "بلوتو", "الشمس")) else ("توسع مؤسسي وشراكات استراتيجية كبرى وتعزيز العلامة التجارية" if has_any((10, 7), ("المشتري", "الزهرة")) else "ضبط الحوكمة التشغيلية ورفع كفاءة الفرق الداخلية"), "period": f"{w(10)} · {w(6)} · {w(7)}"})
        evals.append({"category": "اقتصادي", "rating": score_houses((2, 8, 5, 3), sr_rows), "summary": "تحسن في الإيرادات والسيولة وفرص تمويل واستثمارات مجزية" if has_any((2, 8, 5), ("المشتري", "الزهرة")) else "تشديد الرقابة المالية وحماية السيولة وإدارة التزامات الضرائب والتمويل", "period": f"{w(2)} · {w(8)}"})
        advice.append(f"تسريع الابتكار وإطلاق الحملات التسويقية وتطوير المنتجات خلال {w(5)} و{w(3)}.")
        advice.append(f"توسيع الشراكات التجارية (B2B) وإبرام العقود الاستراتيجية في {w(7)} و{w(11)}.")
        warnings.append(f"الالتزام الصارم بإدارة المخاطر والامتثال المالي والضريبي خلال {w(8)} و{w(12)}.")
        warnings.append(f"حماية الكوادر التشغيلية وتجنب الصدامات الإدارية أثناء التحولات في {w(6)} و{w(10)}.")

    if len(advice) < 2:
        advice.append(f"اعتماد التخطيط المرحلي المتدرج مع مراقبة تقاطعات الخرائط الست ({six_charts['mean_percent']:.1f}%).")
    if len(warnings) < 2:
        warnings.append("تجنب التسرع في القرارات الكبرى أثناء فترات المربعات والمقابلات الكوكبية.")

    return {
        "evaluations": evals,
        "overall_summary": " · ".join(f"{e['category']}: {e['rating']}" for e in evals),
        "advice_list": advice[:4],
        "warnings_list": warnings[:4],
    }


def build_house_evaluations(six_charts: dict, entity_type: str) -> List[dict]:
    weights = {"المشتري": 2, "الزهرة": 2, "الشمس": 1, "القمر": 1, "عطارد": 1, "المريخ": -2, "زحل": -2, "بلوتو": -2, "أورانوس": -1, "نبتون": -1}
    buckets = {h: {"planets": [], "score": 0} for h in range(1, 13)}
    for r in six_charts["solar_return"]["planet_rows"]:
        buckets[r["house"]]["planets"].append(r["name_ar"])
        buckets[r["house"]]["score"] += weights.get(r["name_ar"], 0)
    out = []
    for h in range(1, 13):
        b = buckets[h]
        if not b["planets"]:
            status = "مستقر واعتيادي (بؤرة هادئة)"
        elif b["score"] >= 2:
            status = "ممتاز ومبارك (وفرة وتسهيلات كبرى)"
        elif b["score"] == 1:
            status = "جيد ونشط (حركة بناءة)"
        elif b["score"] == 0:
            status = "مختلط (فرص وتحديات تتطلب التوازن)"
        elif b["score"] == -1:
            status = "متقلب (يتطلب التركيز واليقظة)"
        else:
            status = "ضاغط ومليء بالتحديات (يتطلب الصبر والحكمة)"
        out.append({
            "house": h,
            "meaning": HOUSES_MEANINGS[entity_type][h],
            "planets": b["planets"],
            "score": b["score"],
            "status": status,
            "month_window": get_solar_month_window(six_charts["solar_return"]["date_utc"], h),
        })
    return out


def run_complete_annual_radar(name: str, entity_type: str, birth_date: date, city_label: str, lat: float, lon: float, tz_name: str) -> dict:
    max_age = 84 if entity_type == "individual" else 120
    birth_jd = swe.julday(birth_date.year, birth_date.month, birth_date.day, 12.0)
    eps0 = get_obliquity(birth_jd)
    ramc0 = get_ramc(birth_jd, lon)
    pl0 = get_lons(birth_jd)
    sun_idx, sun_sign, _ = zodiac_info(pl0["SUN"])
    cusps0 = compute_whole_sign_solar_cusps(pl0["SUN"], ramc0, eps0)
    is_day0, pof0, pos0 = compute_arabic_lots(cusps0["AS"], pl0["SUN"], pl0["MOON"])
    cusps0["POF"], cusps0["POS"] = pof0, pos0
    natal = {
        "jd": birth_jd, "ramc": ramc0, "eps": eps0, "lat": lat, "lon": lon,
        "sun_sign_idx": sun_idx, "sun_sign_name": sun_sign, "pl": pl0, "cusps": cusps0,
        "is_day": is_day0, "pof": pof0, "pos": pos0,
    }
    natal_pts = [(pl0["SUN"], "الشمس الأصلية"), (pl0["SAT"], "زحل الأصلي"), (pl0["JUP"], "المشتري الأصلي")]

    all_years, active_years = [], []
    active_serial = 0
    for age in range(1, max_age + 1):
        h_dev = abs((age / K_HAUMEA) - round(age / K_HAUMEA))
        e_dev = abs((age / K_ERIS) - round(age / K_ERIS))
        n_dev = abs((age / K_NEPTUNE) - round(age / K_NEPTUNE))
        nep_crit = (h_dev <= EPSILON and e_dev <= EPSILON and n_dev <= EPSILON)

        sat_ratio = age / K_SATURN
        sat_cycle = round(sat_ratio)
        sat_dev = abs(sat_ratio - sat_cycle)
        sat_marker = "Normal"
        for c in range(1, SATURN_CYCLES + 1):
            if int(c * K_SATURN) == age:
                sat_marker = "Apex Resonance" if c == APEX_CYCLE else ("Critical" if c == CRITICAL_CYCLE else "Cycle Point")
                break

        if not nep_crit:
            base_status = STATUS_NORMAL
        elif sat_marker == "Apex Resonance":
            base_status = STATUS_APEX
        elif sat_marker == "Critical":
            base_status = STATUS_UNIFIED
        elif sat_dev <= EPSILON:
            base_status = STATUS_FOUR_AXIS
        else:
            base_status = STATUS_CRITICAL

        offset_days = int(h_dev * 12) * 30 + int(e_dev * 30)
        try:
            base_d = date(birth_date.year + age, birth_date.month, birth_date.day)
        except ValueError:
            base_d = date(birth_date.year + age, 2, 28)
        target_d = base_d + timedelta(days=offset_days)
        target_jd = swe.julday(target_d.year, target_d.month, target_d.day, 12.0)

        rms = math.sqrt((h_dev ** 2 + e_dev ** 2 + n_dev ** 2 + sat_dev ** 2) / 4.0)
        phase_info = compute_true_phase_coupling(birth_jd, target_jd, pl0["SUN"], pl0["SAT"], pl0["NEP"])
        hybrid_dev = 0.55 * rms + 0.45 * phase_info["true_phase_dev"]
        status = STATUS_PHASE_HARMONIC if (base_status == STATUS_NORMAL and hybrid_dev <= 0.23 and phase_info["true_phase_dev"] <= EPSILON) else base_status

        is_active = status in ACTIVE_RADAR
        if is_active:
            active_serial += 1

        six_charts = evaluate_six_charts_for_year(natal, target_jd, target_d.year, entity_type)

        # تحليل العبور الأقوى
        tr_pl = get_lons(target_jd)
        if status in (STATUS_APEX, STATUS_UNIFIED, STATUS_FOUR_AXIS):
            sat_lon = tr_pl["SAT"]
            sat_idx, sat_sign, sat_deg = zodiac_info(sat_lon)
            sat_house = whole_sign_house_of(sun_idx, sat_idx)
            prefix = f"ذروة زحل الدورة {APEX_CYCLE}" if status == STATUS_APEX else (f"تقاطع موحّد الدورة {CRITICAL_CYCLE}" if status == STATUS_UNIFIED else f"توافق رباعي المحاور (الدورة {sat_cycle} × {K_SATURN})")
            transit_details = f"{prefix} — زحل في {sat_sign} ({sat_deg:.1f}°) بالبيت {sat_house} | {focus_for_house(entity_type, sat_house)} | أقوى خريطة: رنين سداسي {six_charts['mean_percent']:.1f}% (العودة: {six_charts['solar_return']['solar_asc_sign'].split(' ')[0]})."
        else:
            best_score, dom = -1.0, None
            for code, pname in OUTER_PLANETS:
                plon = tr_pl[code]
                z_idx, z_sign, z_deg = zodiac_info(plon)
                house = whole_sign_house_of(sun_idx, z_idx)
                ang_w = 3.0 if house in (1, 4, 7, 10) else (2.0 if house in (2, 5, 8, 11) else 1.2)
                best_asp_str, best_asp_txt = 0.0, ""
                for n_lon, n_lbl in natal_pts:
                    sep = angular_sep(plon, n_lon)
                    for a_deg, a_name, max_orb in TRANSIT_ASPECTS:
                        orb = abs(sep - a_deg)
                        if orb <= max_orb:
                            stren = 1.0 - orb / max_orb
                            if stren > best_asp_str:
                                best_asp_str = stren
                                best_asp_txt = f" ({a_name} مع {n_lbl}، جرم {orb:.1f}°)"
                sc = ang_w + best_asp_str * 4.5 + (0.45 if code == "SAT" else 0.0)
                if sc > best_score:
                    best_score = sc
                    dom = (pname, z_sign, z_deg, house, best_asp_txt)
            prefix = "رنين طوري-توافقي · " if status == STATUS_PHASE_HARMONIC else ""
            top_hit = six_charts["hits"][0] if six_charts["hits"] else None
            hit_txt = f" | أبرز اتصال سداسي [{top_hit['tech_code']}]: {top_hit['directed_factor']} {top_hit['aspect_name']} {top_hit['natal_target']}" if top_hit else ""
            transit_details = f"{prefix}العبور الأقوى: {dom[0]} في {dom[1]} ({dom[2]:.1f}°) بالبيت {dom[3]}{dom[4]} — {focus_for_house(entity_type, dom[3])}{hit_txt}."

        advisory = build_entity_advisory(entity_type, status, six_charts, phase_info["phase_label"])
        house_evals = build_house_evaluations(six_charts, entity_type)
        s_prim, s_sub, s_col = STATUS_LABELS[status]

        row = {
            "serial": active_serial if is_active else age,
            "age": age,
            "target_year": target_d.year,
            "target_date_str": target_d.isoformat(),
            "entity_name": name,
            "entity_type": entity_type,
            "birth_date_str": birth_date.isoformat(),
            "status": status,
            "radar_primary": s_prim,
            "radar_sub": s_sub,
            "status_color": s_col,
            "haumea_dev": h_dev,
            "eris_dev": e_dev,
            "neptune_dev": n_dev,
            "saturn_dev": sat_dev,
            "saturn_cycle": sat_cycle,
            "harmonic_rms": rms,
            "true_phase_dev": phase_info["true_phase_dev"],
            "hybrid_dev": hybrid_dev,
            "phase_label": phase_info["phase_label"],
            "phase_orb_deg": phase_info["best_orb_deg"],
            "haumea_kepler_shift": phase_info["haumea_kepler_shift"],
            "eris_kepler_shift": phase_info["eris_kepler_shift"],
            "six_charts": six_charts,
            "evaluations": advisory["evaluations"],
            "overall_summary": advisory["overall_summary"],
            "transit_details": transit_details,
            "advice_list": advisory["advice_list"],
            "warnings_list": advisory["warnings_list"],
            "house_evaluations": house_evals,
        }
        all_years.append(row)
        if is_active:
            active_years.append(row)

    return {
        "entity_name": name, "entity_type": entity_type, "birth_date_str": birth_date.isoformat(),
        "city_label": city_label, "lat": lat, "lon": lon, "timezone": tz_name,
        "max_age": max_age, "natal": natal, "all_years": all_years, "active_years": active_years,
    }


# ==================== الرسوم الفلكية (عجلة البروج SVG والتقرير القابل للطباعة) ====================
def render_zodiac_wheel_svg(year_row: dict) -> str:
    cx, cy, r_out, r_sign, r_in = 220, 220, 195, 165, 105
    asc = year_row["six_charts"]["solar_return"]["solar_asc_deg"]
    xy = lambda lon, r: (cx + r * math.cos(math.radians(180.0 - mod360(lon - asc))), cy + r * math.sin(math.radians(180.0 - mod360(lon - asc))))
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 440" width="380" height="380" style="background:#0A0F20;border-radius:14px;border:1px solid #1F2A48;display:block;margin:0 auto;">',
        f'<circle cx="{cx}" cy="{cy}" r="{r_out}" fill="none" stroke="#334155" stroke-width="1.5"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{r_sign}" fill="none" stroke="#334155" stroke-width="1"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{r_in}" fill="#0F172E" stroke="#475569" stroke-width="1.5"/>',
    ]
    for i in range(12):
        x1, y1 = xy(i * 30, r_in)
        x2, y2 = xy(i * 30, r_out)
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#24325B" stroke-width="1"/>')
        tx, ty = xy(i * 30 + 15, (r_out + r_sign) / 2.0)
        parts.append(f'<text x="{tx:.1f}" y="{ty + 6:.1f}" text-anchor="middle" fill="#F5B942" font-size="16">{SIGN_GLYPHS[i]}</text>')
    for pr in year_row["six_charts"]["solar_return"]["planet_rows"]:
        px, py = xy(pr["longitude"], 134)
        parts.append(f'<text x="{px:.1f}" y="{py + 5:.1f}" text-anchor="middle" fill="#38BDF8" font-size="15">{PLANET_GLYPH[pr["code"]]}</text>')
    parts.append(f'<text x="{cx}" y="{cy - 12}" text-anchor="middle" fill="#FFFFFF" font-size="12" font-weight="bold">{html.escape(year_row["entity_name"])}</text>')
    parts.append(f'<text x="{cx}" y="{cy + 10}" text-anchor="middle" fill="#F5B942" font-size="13" font-weight="bold">{year_row["target_year"]} (عمر {year_row["age"]})</text>')
    parts.append(f'<text x="{cx}" y="{cy + 28}" text-anchor="middle" fill="#34D399" font-size="11">{year_row["six_charts"]["mean_percent"]:.1f}% رنين</text>')
    parts.append("</svg>")
    return "".join(parts)


def build_unified_html_report(run: dict, rows_to_display: List[dict]) -> str:
    """بناء التقرير النهائي القابل للطباعة بدون بند 2 (التحليل التفصيلي) وبدون بند تقييم البيوت الـ 12 الشهرية."""
    entity_label = ENTITY_LABELS[run["entity_type"]]
    matrix_rows = []
    for r in rows_to_display:
        eval_html = "".join(f"<div><b>{html.escape(e['category'])} ({html.escape(e['rating'])}):</b> {html.escape(e['summary'])}</div>" for e in r["evaluations"])
        adv_html = "".join(f"<li>{html.escape(a)}</li>" for a in r["advice_list"])
        warn_html = "".join(f"<li>{html.escape(w)}</li>" for w in r["warnings_list"])
        matrix_rows.append(f"""
        <tr>
            <td class="num">{r['serial']}</td>
            <td><b>{html.escape(r['entity_name'])}</b></td>
            <td class="num">{html.escape(r['birth_date_str'])}<br><small>المستهدف: {html.escape(r['target_date_str'])} (عمر {r['age']})</small></td>
            <td><span style="color:{r['status_color']};font-weight:800;">{html.escape(r['radar_primary'])}</span><br><small>{html.escape(r['radar_sub'])}</small><br><small>السداسي: {r['six_charts']['mean_percent']:.1f}%</small></td>
            <td>{eval_html}</td>
            <td>{html.escape(r['transit_details'])}</td>
            <td><ul>{adv_html}</ul></td>
            <td><ul>{warn_html}</ul></td>
        </tr>""")

    return f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>رادار كايبر التنبؤي المتقدم — {html.escape(run['entity_name'])}</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
@page {{ size: A4 landscape; margin: 10mm; }}
body {{ font-family: 'Cairo', Tahoma, sans-serif; background: #F1F5F9; color: #0F172A; margin: 0; padding: 20px; line-height: 1.6; }}
.toolbar {{ position: sticky; top: 0; background: #0B1124; color: #fff; padding: 10px 18px; display: flex; justify-content: space-between; align-items: center; border-radius: 8px; margin-bottom: 16px; }}
.toolbar button {{ background: #F59E0B; color: #1B1300; border: 0; padding: 8px 18px; font-weight: 800; border-radius: 6px; cursor: pointer; font-family: inherit; }}
.paper {{ background: #fff; padding: 24px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
h1 {{ color: #1E1B4B; margin: 0 0 6px; font-size: 22px; }}
h2 {{ color: #312E81; border-bottom: 2px solid #E0E7FF; padding-bottom: 6px; margin-top: 20px; font-size: 17px; }}
.meta-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; background: #F8FAFC; border: 1px solid #CBD5E1; padding: 12px; border-radius: 8px; font-size: 13px; margin-bottom: 18px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 11.5px; margin-top: 10px; }}
th {{ background: #1E1B4B; color: #fff; padding: 8px 6px; text-align: right; border: 1px solid #312E81; }}
td {{ padding: 7px 6px; border: 1px solid #CBD5E1; vertical-align: top; }}
tr:nth-child(even) td {{ background: #F8FAFC; }}
td ul {{ margin: 0; padding-right: 16px; }}
.num {{ font-family: monospace; direction: ltr; text-align: right; }}
@media print {{ body {{ background: #fff; padding: 0; }} .toolbar {{ display: none; }} .paper {{ box-shadow: none; padding: 0; }} }}
</style>
</head>
<body>
<div class="toolbar">
  <span>رادار كايبر التنبؤي المتقدم — تطوير استرو رادار ({html.escape(run['entity_name'])})</span>
  <button onclick="window.print()">طباعة / حفظ PDF</button>
</div>
<div class="paper">
  <h1>التقرير الفلكي الاستشاري الموحد للسنوات ({html.escape(entity_label)})</h1>
  <div class="meta-grid">
    <div><b>الاسم:</b> {html.escape(run['entity_name'])}</div>
    <div><b>تاريخ الميلاد / التأسيس:</b> {html.escape(run['birth_date_str'])}</div>
    <div><b>الموقع:</b> {html.escape(run['city_label'])} ({run['lat']:.2f}°, {run['lon']:.2f}°)</div>
    <div><b>الطالع الشمسي (كل برج بيت):</b> {html.escape(run['natal']['sun_sign_name'])}</div>
    <div><b>مدى المسح:</b> حتى {run['max_age']} سنة</div>
    <div><b>السنوات النشطة:</b> {len(run['active_years'])} سنة</div>
    <div><b>ثوابت المحرك:</b> هوميا {K_HAUMEA} · إيريس {K_ERIS} · نبتون {K_NEPTUNE} · زحل {K_SATURN} · ε={EPSILON}</div>
    <div><b>تطوير:</b> استرو رادار</div>
  </div>
  <h2>مصفوفة التوقعات السنوية الشاملة</h2>
  <table>
    <thead>
      <tr>
        <th>#</th><th>الاسم</th><th>تاريخ الميلاد / التأسيس</th><th>حالة الرادار</th>
        <th>التقييم العام للسنة</th><th>تفاصيل العبور</th><th>أهم النصائح</th><th>أهم التحذيرات</th>
      </tr>
    </thead>
    <tbody>{"".join(matrix_rows)}</tbody>
  </table>
  <p style="margin-top:20px;font-size:11px;color:#64748B;">هذا التقرير مخرَج تحليلي فلكي يدمج نظرية زحل-نبتون-هوميا-إيريس مع الاتجاهات الأولية و الأقواس الشمسية و التقدمية الثانوية و الانتهاء السنوي و العبور و العودة الشمسية ولا يُعد بديلاً عن الاستشارة المتخصصة.</p>
</div>
</body>
</html>"""


# ==================== واجهة Streamlit الرئيسية ====================
def main() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    countries, cities, tf = load_geo()
    country_opts = sorted(
        [(f"{AR_COUNTRY_HINTS.get(k, v['name'])} — {v['name']} ({k})", k) for k, v in countries.items()],
        key=lambda x: x[0],
    )
    default_c_idx = next((i for i, x in enumerate(country_opts) if x[1] == "SY"), 0)

    with st.sidebar:
        st.markdown(
            """
            <div style="padding-bottom:12px;border-bottom:1px solid #1F2A48;margin-bottom:14px;">
                <div style="font-size:16px;font-weight:800;color:#FFFFFF;">رادار كايبر التنبؤي المتقدم</div>
                <div style="font-size:12px;color:#94A3B8;margin-top:2px;">تطوير استرو رادار</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        entity_label = st.radio("نوع الكيان والمدى الزمني:", ["فرد (84 سنة)", "دولة (120 سنة)", "شركة (120 سنة)"], horizontal=True)
        entity_type = "individual" if "فرد" in entity_label else ("country" if "دولة" in entity_label else "company")

        name_lbl = "اسم الفرد" if entity_type == "individual" else ("اسم الدولة" if entity_type == "country" else "اسم الشركة / المؤسسة")
        name = st.text_input(name_lbl, value="دراسة حالة استشارية")

        date_lbl = "تاريخ الميلاد" if entity_type == "individual" else "تاريخ التأسيس / الاستقلال"
        birth_date = st.date_input(date_lbl, value=date(1981, 4, 17), min_value=date(1800, 1, 1), max_value=date(2035, 12, 31))

        st.markdown("---")
        _, c_code = st.selectbox("الدولة (تحميل تلقائي)", country_opts, index=default_c_idx, format_func=lambda x: x[0])
        sorted_cities = get_cities_sorted_by_population(cities, c_code)
        city_obj = st.selectbox(
            "المدينة (مرتبة تلقائياً حسب الكثافة السكانية)",
            sorted_cities,
            format_func=lambda c: f"{c['name']} ({c.get('population', 0):,} نسمة)",
        )
        lat = float(city_obj["latitude"])
        lon = float(city_obj["longitude"])
        tz_name = tf.timezone_at(lat=lat, lng=lon) or "UTC"
        st.caption(f"الإحداثيات: {lat:.3f}°, {lon:.3f}° · المنطقة الزمنية: {tz_name}")

        run_btn = st.button("تشغيل رادار كايبر", type="primary", use_container_width=True)

    st.markdown(
        """
        <div class="kuiper-hero">
            <h1 style="margin:0;font-size:24px;color:#FFFFFF;">رادار كايبر التنبؤي المتقدم</h1>
            <p style="margin:4px 0 0;font-size:13px;color:#94A3B8;">
                تطوير الفلكي الدكتور استرو رادار · دمج محرك نظرية زحل-نبتون-هوميا-إيريس مع الاتجاهات الأولية و الأقواس الشمسية و التقدمية الثانوية و الانتهاء السنوي و العبور و العودة الشمسية
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if run_btn or "kuiper_run" not in st.session_state:
        if not name.strip():
            st.error("يرجى إدخال الاسم قبل التشغيل.")
            return
        with st.spinner("جاري الحساب الفلكي الكبلري وتقييم الخرائط الست..."):
            st.session_state["kuiper_run"] = run_complete_annual_radar(
                name=name.strip(),
                entity_type=entity_type,
                birth_date=birth_date,
                city_label=f"{city_obj['name']} ({c_code})",
                lat=lat,
                lon=lon,
                tz_name=tz_name,
            )

    run = st.session_state["kuiper_run"]
    peak_row = max(run["active_years"], key=lambda r: r["six_charts"]["mean_percent"], default=None)

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f'<div class="kuiper-card"><div class="kuiper-kpi-label">الطالع الشمسي (كل برج بيت)</div><div class="kuiper-kpi-val" style="color:#F5B942;">{run["natal"]["sun_sign_name"]}</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="kuiper-card"><div class="kuiper-kpi-label">نطاق البحث السنوي</div><div class="kuiper-kpi-val">{run["max_age"]} سنة</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="kuiper-card"><div class="kuiper-kpi-label">السنوات النشطة بالرادار</div><div class="kuiper-kpi-val" style="color:#34D399;">{len(run["active_years"])} سنة</div></div>', unsafe_allow_html=True)
    peak_txt = f"{peak_row['target_year']} ({peak_row['six_charts']['mean_percent']:.1f}%)" if peak_row else "—"
    k4.markdown(f'<div class="kuiper-card"><div class="kuiper-kpi-label">ذروة رنين الخرائط الست</div><div class="kuiper-kpi-val" style="color:#38BDF8;">{peak_txt}</div></div>', unsafe_allow_html=True)

    # تصفية الجدول
    fc1, fc2 = st.columns([2, 1])
    filter_choice = fc1.selectbox(
        "تصفية مصفوفة السنوات:",
        ["السنوات النشطة بالرادار", "توافق رباعي المحاور", "رنين طوري-توافقي", "سنة حرجة ثلاثية", f"كامل السجل (1–{run['max_age']})"],
    )
    search_q = fc2.text_input("بحث بالسنة أو العبور:", placeholder="مثال: 2025 أو زحل...")

    if filter_choice.startswith("كامل"):
        rows_filtered = run["all_years"]
    elif filter_choice == "توافق رباعي المحاور":
        rows_filtered = [r for r in run["active_years"] if r["status"] in SATURN_CONFIRMED]
    elif filter_choice == "رنين طوري-توافقي":
        rows_filtered = [r for r in run["active_years"] if r["status"] == STATUS_PHASE_HARMONIC]
    elif filter_choice == "سنة حرجة ثلاثية":
        rows_filtered = [r for r in run["active_years"] if r["status"] == STATUS_CRITICAL]
    else:
        rows_filtered = run["active_years"]

    if search_q.strip():
        q = search_q.strip().lower()
        rows_filtered = [
            r for r in rows_filtered
            if q in str(r["target_year"]) or q in str(r["age"]) or q in r["radar_primary"].lower() or q in r["transit_details"].lower() or q in r["overall_summary"].lower()
        ]

    st.subheader(f"مصفوفة التوقعات السنوية الشاملة ({len(rows_filtered)} سنة)")
    df_rows = [{
        "#": r["serial"],
        "الاسم": r["entity_name"],
        "تاريخ الميلاد / التأسيس": f"{r['birth_date_str']} | {r['target_year']} (عمر {r['age']})",
        "حالة الرادار": f"{r['radar_primary']} ({r['radar_sub']}) — {r['six_charts']['mean_percent']:.1f}%",
        "التقييم العام للسنة": " | ".join(f"{e['category']} ({e['rating']}): {e['summary']}" for e in r["evaluations"]),
        "تفاصيل العبور": r["transit_details"],
        "أهم النصائح": " • ".join(r["advice_list"][:2]),
        "أهم التحذيرات": " • ".join(r["warnings_list"][:2]),
    } for r in rows_filtered]
    st.dataframe(pd.DataFrame(df_rows), use_container_width=True, hide_index=True)

    # الفحص التفصيلي التفاعلي في الواجهة
    if rows_filtered:
        st.markdown("---")
        sel_age = st.selectbox(
            "اختر سنة للفحص التفصيلي التفاعلي:",
            [r["age"] for r in rows_filtered],
            format_func=lambda a: next((f"السنة {r['target_year']} (عمر {r['age']}) — {r['radar_primary']}" for r in rows_filtered if r["age"] == a), str(a)),
        )
        sel_row = next(r for r in rows_filtered if r["age"] == sel_age)

        t1, t2, t3, t4 = st.tabs(["الخريطة والتقييم العام", "تحليل الخرائط الست", "منحنى الرادار والطور الكبلري", "التقرير النهائي القابل للطباعة"])
        with t1:
            col_w, col_e = st.columns([1, 1.4])
            with col_w:
                st.markdown(render_zodiac_wheel_svg(sel_row), unsafe_allow_html=True)
                st.caption(f"طالع العودة: {sel_row['six_charts']['solar_return']['solar_asc_sign']} · رب السنة: {sel_row['six_charts']['lord_of_year_ar']}")
            with col_e:
                for ev in sel_row["evaluations"]:
                    st.markdown(f'<div class="kuiper-card"><b>{ev["category"]}</b> — <span style="color:#F5B942;">{ev["rating"]}</span><br><small>{ev["summary"]}</small><br><span style="color:#94A3B8;font-size:11px;">فترة التفعيل: {ev["period"]}</span></div>', unsafe_allow_html=True)
            st.info(f"**تفاصيل العبور:** {sel_row['transit_details']}")
            ca, cw = st.columns(2)
            with ca:
                st.success("**أهم النصائح:**\n" + "\n".join(f"- {a}" for a in sel_row["advice_list"]))
            with cw:
                st.warning("**أهم التحذيرات:**\n" + "\n".join(f"- {w}" for w in sel_row["warnings_list"]))

        with t2:
            for tc in TECH_CODES:
                pct = sel_row["six_charts"]["tech_percents"][tc]
                st.progress(min(100, int(round(pct))), text=f"{TECH_AR[tc]}: {pct:.1f}%")
            c_h, c_p = st.columns(2)
            with c_h:
                st.markdown("**أقوى اتصالات الخرائط الست**")
                hits_df = pd.DataFrame([{
                    "الخريطة": h["tech_code"], "الدليل": h["directed_factor"], "الزاوية": f"{h['aspect_name']} ({h['aspect_deg']}°)",
                    "النقطة الأصلية": h["natal_target"], "الفارق": f"{h['orb_arc_min']:.1f}′",
                } for h in sel_row["six_charts"]["hits"][:30]])
                st.dataframe(hits_df, use_container_width=True, hide_index=True)
            with c_p:
                st.markdown("**مواقع الكواكب في العودة الشمسية (كل برج بيت)**")
                sr_df = pd.DataFrame([{
                    "الكوكب": p["name_ar"], "الموقع": describe_lon(p["longitude"]),
                    "البيت": f"البيت {p['house']}", "الحركة": "متراجع" if p["is_retrograde"] else "مباشر",
                } for p in sel_row["six_charts"]["solar_return"]["planet_rows"]])
                st.dataframe(sr_df, use_container_width=True, hide_index=True)

        with t3:
            curve_df = pd.DataFrame({
                "العمر": [r["age"] for r in run["all_years"]],
                "الانحراف الهجين": [r["hybrid_dev"] for r in run["all_years"]],
                "الطور الحقيقي": [r["true_phase_dev"] for r in run["all_years"]],
                "متوسط الخرائط الست (نسبة)": [r["six_charts"]["mean_percent"] / 100.0 for r in run["all_years"]],
            }).set_index("العمر")
            st.line_chart(curve_df)
            st.caption(f"اقتران الطور: {sel_row['phase_label']} (جرم {sel_row['phase_orb_deg']:.2f}°) · إزاحة هوميا الكبلرية: {sel_row['haumea_kepler_shift']:.2f}° · إزاحة إيريس الكبلرية: {sel_row['eris_kepler_shift']:.2f}°")

        with t4:
            html_report = build_unified_html_report(run, rows_filtered)
            csv_bytes = pd.DataFrame(df_rows).to_csv(index=False).encode("utf-8-sig")
            d1, d2 = st.columns(2)
            d1.download_button(
                "تنزيل التقرير النهائي القابل للطباعة (HTML / PDF)",
                data=html_report.encode("utf-8"),
                file_name=f"KuiperRadar_{run['entity_name']}.html",
                mime="text/html",
                use_container_width=True,
            )
            d2.download_button(
                "تنزيل مصفوفة النتائج (CSV)",
                data=csv_bytes,
                file_name=f"KuiperRadar_Matrix_{run['entity_name']}.csv",
                mime="text/csv",
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
