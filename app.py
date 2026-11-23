from __future__ import annotations

import html
import math
from datetime import date, datetime, timezone
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

# ==================== إعدادات Swiss Ephemeris ====================
swe.set_ephe_path('')  # استخدام وضع Moshier الافتراضي للتقويم الفلكي الدقيق
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
    color: #FFFFFF;
}

/* عناوين الحقول والنصوص في الشاشة الرئيسية */
.stApp label,
.stApp [data-testid="stWidgetLabel"] p,
.stApp [data-testid="stWidgetLabel"] span,
.stApp [data-testid="stCaptionContainer"],
.stApp .stMarkdown p {
    color: #FFFFFF !important;
    font-weight: 600;
}

/* التبويبات (st.tabs) في الشاشة الرئيسية */
.stApp [data-baseweb="tab-list"] button,
.stApp [data-baseweb="tab"] p,
.stApp [data-baseweb="tab"] span,
.stApp [data-baseweb="tab"] div {
    color: #E8EEF9 !important;
    font-weight: 700;
}

/* وضوح النص داخل حقول الإدخال والقوائم المنسدلة الفاتحة */
.stApp input,
.stApp textarea,
.stApp [data-baseweb="select"] span,
.stApp [data-baseweb="select"] div {
    color: #0F172A !important;
}

/* القائمة الجانبية */
[data-testid="stSidebar"] {
    background-color: #0A0F20;
    border-left: 1px solid #E8EEF9;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] span,
[data-testid="stSidebar"] .stRadio label p,
[data-testid="stSidebar"] .stRadio label span,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] .stMarkdown p {
    color: #FFFFFF !important;
    font-weight: 600;
}
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] div {
    color: #0F172A !important;
}

/* الأزرار الثانوية وأزرار التحميل في الشاشة الرئيسية */
.stApp .stButton > button:not([kind="primary"]),
.stApp .stDownloadButton > button {
    background-color: #162038 !important;
    color: #FFFFFF !important;
    border: 1px solid #3B4E7A !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
}
.stApp .stButton > button:not([kind="primary"]):hover,
.stApp .stDownloadButton > button:hover {
    background-color: #223154 !important;
    color: #FFFFFF !important;
    border-color: #64748B !important;
}

/* الأزرار الأساسية (Primary) */
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
# ==================== الثوابت المثبتة لطبقات رادار كاليبر (إيريس · نبتون · زحل) ====================
# كل طبقة تُقاس بانحراف (العمر ÷ K) عن أقرب عدد صحيح من الدورات، والعتبة EPSILON كسر من الدورة.
# السنة تُعلَّم فقط إذا حققت كل الطبقات الفعّالة (ACTIVE_LAYERS) معاً: الانحراف ≤ EPSILON لكل منها.
# النتيجة سنة كاملة فقط (سنة الميلاد + العمر)، بلا أشهر ولا أيام.
K_ERIS = 9.30
K_NEPTUNE = 10.77
K_SATURN = 4.4
EPSILON = 0.30
ACTIVE_LAYERS = ("eris", "saturn", "neptune")
LAYER_AR = {"eris": "إيريس", "neptune": "نبتون", "saturn": "زحل"}
LAYER_K = {"eris": K_ERIS, "neptune": K_NEPTUNE, "saturn": K_SATURN}
LAYER_ROLE = {"saturn": "زحل (هيكلة)", "neptune": "نبتون (نهايات)", "eris": "إيريس (فرض)"}

TROPICAL_YEAR = 365.2421904
NAIBOD_PER_DAY = 360.0 / TROPICAL_YEAR / TROPICAL_YEAR  # = 0.9856 درجة/سنة

STATUS_NORMAL = "Normal"
STATUS_FOUR_AXIS = "FOUR_AXIS"
ACTIVE_RADAR = {STATUS_FOUR_AXIS}

STATUS_LABELS: Dict[str, Tuple[str, str, str]] = {
    STATUS_FOUR_AXIS: ("سنة تغيير (طبقات رادار كاليبر)", " + ".join(LAYER_ROLE[l] for l in ("saturn", "neptune", "eris") if l in ACTIVE_LAYERS), "#F59E0B"),
    STATUS_NORMAL: ("سنة اعتيادية", "مسار طبيعي", "#64748B"),
}

ZODIAC_SIGNS = [
    "الحمل", "الثور", "الجوزاء", "السرطان", "الأسد", "العذراء",
    "الميزان", "العقرب", "القوس", "الجدي", "الدلو", "الحوت",
]
SIGN_GLYPHS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
SIGN_RULERS = ["MAR", "VEN", "MER", "MOON", "SUN", "MER", "VEN", "MAR", "JUP", "SAT", "SAT", "JUP"]

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
# طبيعة الكوكب (+ منفعة / - مضرّة) ووزن نشاطه في تقييم البيوت
PLANET_NATURE = {
    "JUP": 1.0, "VEN": 1.0, "SUN": 0.5, "MER": 0.2, "MOON": 0.2, "NN": 0.3, "SN": -0.3,
    "MAR": -1.0, "SAT": -1.0, "PLU": -0.8, "URA": -0.6, "NEP": -0.4,
}
PLANET_ACT = {
    "SUN": 1.0, "MOON": 0.7, "MER": 0.8, "VEN": 1.2, "MAR": 1.5,
    "JUP": 1.5, "SAT": 2.0, "URA": 2.0, "NEP": 2.0, "PLU": 2.0,
}

# أوتاد/رؤوس البيوت الاثني عشر بنظام كل برج بيت (من برج الشمس)
HOUSE_SIG = {1: "AS", 2: "H2", 3: "H3", 4: "IC", 5: "H5", 6: "H6", 7: "DS", 8: "H8", 9: "H9", 10: "MC", 11: "H11", 12: "H12"}
SIG_HOUSE = {v: k for k, v in HOUSE_SIG.items()}
FACTOR_AR = {
    "AS": "الطالع الشمسي (البيت 1)", "H2": "البيت 2", "H3": "البيت 3",
    "IC": "وتد الأرض IC (البيت 4)", "H5": "البيت 5", "H6": "البيت 6",
    "DS": "الغارب DS (البيت 7)", "H8": "البيت 8", "H9": "البيت 9",
    "MC": "وتد السماء MC (البيت 10)", "H11": "البيت 11", "H12": "البيت 12",
}
ASPECT_AR = {
    0: "اقتران", 30: "نصف تسديس", 45: "نصف تربيع", 60: "تسديس",
    90: "تربيع", 120: "تثليث", 135: "تربيع ونصف", 150: "مقارنة ساقطة", 180: "مقابلة",
}

TECH_CODES = ("PD", "SA", "SD", "AP", "TR", "SR")
TECH_AR = {
    "PD": "1. الاتجاهات (PD) - رمزية بمفتاح نيبود",
    "SA": "2. الأقواس الشمسية (SA)",
    "SD": "3. التقدمية الثانوية (SD)",
    "AP": "4. الانتهاء السنوي (AP)",
    "TR": "5. العبور الكوكبي (TR)",
    "SR": "6. العودة الشمسية (SR)",
}
ENTITY_LABELS = {"individual": "فرد", "country": "دولة", "company": "شركة"}

# ثوابت تقييم الخرائط الست (الأجرام بالدقائق القوسية)
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
    "SUN": 12.0, "MER": 12.0, "VEN": 12.0, "MAR": 12.0,
    "JUP": 9.0, "SAT": 9.0, "URA": 5.0, "NEP": 5.0, "PLU": 5.0, "NN": 5.0,
}
TRANSIT_ASPECTS = [
    (0.0, "اقتران (0°)", 6.5),
    (180.0, "تقابل (180°)", 6.0),
    (90.0, "تربيع (90°)", 5.5),
    (120.0, "تثليث (120°)", 5.5),
    (60.0, "تسديس (60°)", 4.5),
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




# ==================== أدوات فلكية (Swiss Ephemeris) ====================
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


def house_of_lon(sun_sign_idx: int, lon: float) -> int:
    """رقم البيت (كل برج بيت) لنقطة طولها lon، والبيت الأول هو برج الشمس الأصلية."""
    return whole_sign_house_of(sun_sign_idx, int(mod360(lon) // 30) % 12)


def describe_lon(lon: float) -> str:
    _, sign_name, deg = zodiac_info(lon)
    d = int(deg)
    m = int((deg - d) * 60.0)
    return f"{d:02d}°{m:02d}′ {sign_name}"


def get_obliquity(jd: float) -> float:
    res = swe.calc_ut(jd, swe.ECL_NUT)[0]
    return float(res[0])


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


def ra_of_lon(lon_deg: float, eps_deg: float) -> float:
    lam = math.radians(lon_deg)
    eps = math.radians(eps_deg)
    return mod360(math.degrees(math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))))


def compute_whole_sign_cusps(sun_lon: float) -> Dict[str, float]:
    """بيوت كل برج بيت: الطالع = بداية برج الشمس، وكل بيت يبدأ عند 0° من برجه.
    لا يوجد وقت ميلاد، لذلك لا وجود لوتد سماء حقيقي: MC هو رأس البيت العاشر."""
    asc = int(mod360(sun_lon) // 30) % 12 * 30.0
    return {HOUSE_SIG[h]: mod360(asc + 30.0 * (h - 1)) for h in range(1, 13)}


def find_solar_return_jd(natal_sun_lon: float, target_year: int) -> float:
    jd_s = swe.julday(target_year, 1, 1, 0.0)
    jd_e = swe.julday(target_year, 12, 31, 23.99)
    for _ in range(52):
        jd_m = 0.5 * (jd_s + jd_e)
        lon_m = float(swe.calc_ut(jd_m, swe.SUN)[0][0]) % 360.0
        diff = wrap180(lon_m - natal_sun_lon)
        if diff < 0:
            jd_s = jd_m
        else:
            jd_e = jd_m
    return 0.5 * (jd_s + jd_e)




# ==================== المحرك الثلاثي (إيريس · نبتون · زحل) ====================
def layer_dev(age: float, k: float) -> float:
    """انحراف العمر عن أقرب عدد صحيح من الدورات (كسر من الدورة)."""
    return abs((age / k) - round(age / k))


def radar_layer_devs(age: int) -> Dict[str, float]:
    return {
        "eris": layer_dev(age, K_ERIS),
        "neptune": layer_dev(age, K_NEPTUNE),
        "saturn": layer_dev(age, K_SATURN),
    }


def is_four_axis(devs: Dict[str, float]) -> bool:
    """اسم الدالة قديم؛ تتحقق الآن من الطبقات الفعّالة فقط (ACTIVE_LAYERS)."""
    return all(devs[l] <= EPSILON for l in ACTIVE_LAYERS)


def radar_target_year(birth_date: date, age: int) -> int:
    """سنة الهدف = سنة الميلاد + العمر، بلا أشهر ولا أيام."""
    return birth_date.year + age


# ==================== محرك الخرائط الست (تفسير السنوات المعلَّمة) ====================
def aspect_valence(aspect: int, nature: float) -> float:
    """اتجاه الاتصال: التناغم (تسديس/تثليث) يميل للإيجاب، والتوتر (تربيع/مقابلة) للسلب، والاقتران يتبع طبيعة الكوكب."""
    if aspect == 0:
        return nature
    if aspect in (60, 120):
        return 0.6 + 0.4 * nature
    if aspect in (90, 180, 45, 135):
        return -0.6 + 0.4 * nature
    return 0.0


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
        house: Optional[int] = None, planet: Optional[str] = None,
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
                    nature = PLANET_NATURE.get(planet, 0.0) if planet else 0.0
                    self.hits.append({
                        "tech_code": tech,
                        "tech_name": TECH_AR[tech],
                        "directed_factor": directed_factor,
                        "natal_target": natal_target,
                        "aspect_deg": a,
                        "aspect_name": ASPECT_AR.get(a, f"{a}°"),
                        "orb_arc_min": o_arc_min,
                        "strength": BASE_SCORE * strength,
                        "house": house,
                        "planet": planet,
                        "valence": aspect_valence(a, nature) if planet else 0.0,
                    })

    def get_percentages(self) -> Tuple[Dict[str, float], float]:
        pcts = {}
        for t in TECH_CODES:
            eff = self.h1[t] + 0.3 * (self.h2[t] + self.h3[t])
            pcts[t] = max(0.0, min(100.0, 100.0 * (1.0 - math.exp(-1.1 * eff))))
        return pcts, sum(pcts.values()) / len(TECH_CODES)


def get_annual_spec(entity_type: str) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]], str]:
    """(دلائل البيوت الاثنا عشر وأوزانها، الكواكب وأوزانها، بيت الكيان). القمر مستبعد: لا وقت ميلاد."""
    if entity_type == "country":
        sigs = [("MC", 1.0), ("AS", 1.0), ("H2", 0.9), ("H6", 0.85), ("H8", 0.85), ("DS", 0.8),
                ("IC", 0.7), ("H3", 0.7), ("H9", 0.7), ("H11", 0.7), ("H12", 0.65), ("H5", 0.65)]
        pls = [("SAT", 1.0), ("JUP", 1.0), ("MAR", 0.95), ("SUN", 0.9), ("PLU", 0.9), ("URA", 0.85),
               ("NEP", 0.85), ("MER", 0.65), ("VEN", 0.65), ("NN", 0.7)]
        return sigs, pls, "MC"
    if entity_type == "company":
        sigs = [("MC", 1.0), ("H2", 1.0), ("AS", 0.95), ("H8", 0.9), ("DS", 0.85), ("H6", 0.8),
                ("H5", 0.75), ("H11", 0.7), ("IC", 0.7), ("H3", 0.7), ("H9", 0.7), ("H12", 0.65)]
        pls = [("JUP", 1.0), ("SAT", 1.0), ("SUN", 0.95), ("MER", 0.9), ("VEN", 0.85), ("URA", 0.85),
               ("PLU", 0.85), ("MAR", 0.8), ("NEP", 0.7), ("NN", 0.7)]
        return sigs, pls, "H2"
    sigs = [("AS", 1.0), ("MC", 1.0), ("DS", 0.95), ("IC", 0.9), ("H2", 0.85), ("H6", 0.8),
            ("H8", 0.75), ("H5", 0.75), ("H3", 0.75), ("H9", 0.7), ("H11", 0.7), ("H12", 0.7)]
    pls = [("SUN", 1.0), ("SAT", 1.0), ("JUP", 1.0), ("VEN", 0.9), ("MAR", 0.9), ("MER", 0.8),
           ("URA", 0.8), ("NEP", 0.8), ("PLU", 0.8), ("NN", 0.75)]
    return sigs, pls, "AS"


def build_natal(birth_date: date, lat: float, lon: float) -> dict:
    """الخريطة الأصلية بلا وقت ميلاد: الظهيرة UT، وبيوت كل برج بيت من برج الشمس."""
    birth_jd = swe.julday(birth_date.year, birth_date.month, birth_date.day, 12.0)
    pl0 = get_lons(birth_jd)
    sun_idx, sun_sign, _ = zodiac_info(pl0["SUN"])
    return {
        "jd": birth_jd, "birth_date": birth_date, "eps": get_obliquity(birth_jd), "lat": lat, "lon": lon,
        "sun_sign_idx": sun_idx, "sun_sign_name": sun_sign, "pl": pl0,
        "cusps": compute_whole_sign_cusps(pl0["SUN"]),
        "house_of": {p: house_of_lon(sun_idx, pl0[p]) for p in pl0},
    }


def evaluate_six_charts_for_year(natal: dict, target_jd: float, age: int, entity_type: str) -> dict:
    """target_jd هو لحظة العودة الشمسية لسنة الهدف؛ كل الحسابات تُجرى عندها (السنة تبدأ من العودة)."""
    acc = TechAccumulator()
    sig_list, pls_list, event_house_key = get_annual_spec(entity_type)
    cusps, npl, nh, sun_idx = natal["cusps"], natal["pl"], natal["house_of"], natal["sun_sign_idx"]
    sh = SIG_HOUSE
    days = max(1.0, target_jd - natal["jd"])
    yrs = days / TROPICAL_YEAR
    pl_tr = get_lons(target_jd)
    tr_house = lambda p: house_of_lon(sun_idx, pl_tr[p])

    # 1. الاتجاهات (PD): رمزية بمفتاح نيبود لأن وقت الميلاد غير متاح
    arc_naibod = days * NAIBOD_PER_DAY
    for sgn, dlab, tw in ((1, "مباشر", 1.05), (-1, "عكسي", 0.85)):
        arc = sgn * arc_naibod
        for s, fs in sig_list:
            for p, fp in pls_list:
                acc.add("PD", f"{FACTOR_AR[s]} ({dlab})", f"{PLANET_AR[p]} أصلي", mod360(cusps[s] + arc), npl[p], fs * fp, tw, PD_ORB_MAJOR, PD_ORB_MINOR, ASPECTS, house=sh[s], planet=p)
                acc.add("PD", f"{PLANET_AR[p]} ({dlab})", f"{FACTOR_AR[s]} أصلي", mod360(npl[p] + arc), cusps[s], fs * fp, 0.9, PD_ORB_MAJOR, PD_ORB_MINOR, ASPECTS, house=sh[s], planet=p)

    # 2. الأقواس الشمسية (SA)
    sa_base = mod360(get_lons(natal["jd"] + yrs)["SUN"] - npl["SUN"])
    for sgn, dlab, w_dir in ((1, "+قوس شمسي", 0.9), (-1, "-قوس عكسي", 0.65)):
        sa = sgn * sa_base
        for s, fs in sig_list:
            for p, fp in pls_list:
                acc.add("SA", f"{FACTOR_AR[s]} ({dlab})", f"{PLANET_AR[p]} أصلي", mod360(cusps[s] + sa), npl[p], fs * fp, w_dir, SA_ORB_MAJOR, SA_ORB_MINOR, ASPECTS, house=sh[s], planet=p)
                acc.add("SA", f"{PLANET_AR[p]} ({dlab})", f"{FACTOR_AR[s]} أصلي", mod360(npl[p] + sa), cusps[s], fs * fp, w_dir * 0.9, SA_ORB_MAJOR, SA_ORB_MINOR, ASPECTS, house=sh[s], planet=p)

    # 3. التقدمية الثانوية (SD)
    sun0_ra = ra_of_lon(npl["SUN"], natal["eps"])
    for jdx, lab, tw in ((natal["jd"] + yrs, "تقدمي", 0.95), (natal["jd"] - yrs, "تراجعي", 0.7)):
        pl_sd = get_lons(jdx)
        arc_sd = wrap180(ra_of_lon(pl_sd["SUN"], natal["eps"]) - sun0_ra)
        for p, fp in pls_list:
            orb = SEC_ORB[p]
            for s, fs in sig_list:
                acc.add("SD", f"{FACTOR_AR[s]} ({lab})", f"{PLANET_AR[p]} أصلي", mod360(cusps[s] + arc_sd), npl[p], fs * fp, tw, orb, orb, ASPECTS, house=sh[s], planet=p)
                acc.add("SD", f"{PLANET_AR[p]} ({lab})", f"{FACTOR_AR[s]} أصلي", pl_sd[p], cusps[s], fs * fp, tw * 0.95, orb, orb, ASPECTS, house=sh[s], planet=p)

    # 4. الانتهاء السنوي (AP): 30° لكل سنة عمر
    prof_arc_yr = age * 30.0
    prof_as = mod360(cusps["AS"] + prof_arc_yr)
    prof_mc = mod360(cusps["MC"] + prof_arc_yr)
    for p, fp in pls_list:
        acc.add("AP", "انتهاء الطالع السنوي", f"{PLANET_AR[p]} أصلي", prof_as, npl[p], fp, 0.95, AP_ORB_MAJOR, AP_ORB_MINOR, MAJOR_ASPECTS, house=nh[p], planet=p)
        acc.add("AP", "انتهاء العاشر السنوي", f"{PLANET_AR[p]} أصلي", prof_mc, npl[p], fp, 0.85, AP_ORB_MAJOR, AP_ORB_MINOR, MAJOR_ASPECTS, house=nh[p], planet=p)
        acc.add("AP", "انتهاء الطالع السنوي", f"{PLANET_AR[p]} عابر", prof_as, pl_tr[p], fp, 0.8, AP_ORB_MAJOR, AP_ORB_MINOR, MAJOR_ASPECTS, house=tr_house(p), planet=p)

    prof_sign_idx = (sun_idx + age) % 12
    lord_of_year = SIGN_RULERS[prof_sign_idx]
    lord_of_house = SIGN_RULERS[int(cusps[event_house_key] // 30.0) % 12]
    if lord_of_year != "MOON":
        acc.add("AP", "رب السنة عابر", "الطالع الشمسي AS أصلي", pl_tr[lord_of_year], cusps["AS"], 1.0, 0.95, TR_ORB, TR_ORB, MAJOR_ASPECTS, house=1, planet=lord_of_year)
        acc.add("AP", "رب السنة عابر", "وتد السماء MC أصلي", pl_tr[lord_of_year], cusps["MC"], 1.0, 0.85, TR_ORB, TR_ORB, MAJOR_ASPECTS, house=10, planet=lord_of_year)
        acc.add("AP", "انتهاء الطالع السنوي", "رب السنة أصلي", prof_as, npl[lord_of_year], 1.0, 1.0, AP_ORB_MAJOR, AP_ORB_MINOR, MAJOR_ASPECTS, house=nh[lord_of_year], planet=lord_of_year)
    if lord_of_house != "MOON":
        acc.add("AP", "رب بيت الكيان عابر", "الطالع الشمسي AS أصلي", pl_tr[lord_of_house], cusps["AS"], 1.0, 0.9, TR_ORB, TR_ORB, MAJOR_ASPECTS, house=1, planet=lord_of_house)

    # 5. العبور الكوكبي (TR)
    pl_pre = get_lons(2.0 * natal["jd"] - target_jd)
    for lab, pl_set, tw in (("مباشر", pl_tr, 0.9), ("ما قبل الولادة", pl_pre, 0.65)):
        for p, fp in pls_list:
            for s, fs in sig_list:
                acc.add("TR", f"{PLANET_AR[p]} عابر ({lab})", f"{FACTOR_AR[s]} أصلي", pl_set[p], cusps[s], fs * fp, tw, TR_ORB, TR_ORB, MAJOR_ASPECTS, house=sh[s], planet=p)

    # 6. العودة الشمسية (SR) لسنة الهدف. الشمس مستبعدة من الاتصالات لأنها ثابتة على موضعها الأصلي
    sr_jd = target_jd
    pl_sr = get_lons(sr_jd)
    speeds_sr = get_speeds(sr_jd)
    for p, fp in pls_list:
        if p == "SUN":
            continue
        for s, fs in sig_list:
            acc.add("SR", f"{PLANET_AR[p]} في العودة الشمسية", f"{FACTOR_AR[s]} أصلي", pl_sr[p], cusps[s], fs * fp, 0.8, SR_ORB_MAJOR, SR_ORB_MINOR, MAJOR_ASPECTS, house=sh[s], planet=p)
        for q, fq in pls_list:
            acc.add("SR", f"{PLANET_AR[p]} في العودة الشمسية", f"{PLANET_AR[q]} أصلي", pl_sr[p], npl[q], fp * fq, 0.7, SR_ORB_MAJOR, SR_ORB_MINOR, MAJOR_ASPECTS, house=nh[q], planet=p)

    planet_rows = []
    for code in [p for p in PLANETS if p not in ("NN", "SN")]:
        lon = pl_sr[code]
        s_idx, s_name, deg_in = zodiac_info(lon)
        planet_rows.append({
            "code": code, "name_ar": PLANET_AR[code], "longitude": lon,
            "sign_index": s_idx, "sign_name": s_name, "deg_in_sign": deg_in,
            "house": whole_sign_house_of(sun_idx, s_idx), "is_retrograde": speeds_sr[code] < 0,
        })

    tech_pcts, mean_pct = acc.get_percentages()
    return {
        "tech_percents": tech_pcts,
        "mean_percent": mean_pct,
        "hits": sorted(acc.hits, key=lambda x: x["strength"], reverse=True),
        "profection_sign_index": prof_sign_idx,
        "profection_sign_name": ZODIAC_SIGNS[prof_sign_idx],
        "profection_house": (age % 12) + 1,
        "lord_of_year": lord_of_year,
        "lord_of_year_ar": PLANET_AR[lord_of_year],
        "solar_return": {
            "jd": sr_jd,
            "date_utc": jd_to_datetime_utc(sr_jd),
            "solar_asc_deg": sun_idx * 30.0,
            "solar_asc_sign": f"{ZODIAC_SIGNS[sun_idx]} (كل برج بيت - الطالع الشمسي)",
            "solar_asc_sign_index": sun_idx,
            "planet_rows": planet_rows,
        },
    }


# ==================== طبقة التفسير: مجال التغيير والاتجاه والنصائح والتحذيرات ====================
HOUSE_LABELS: Dict[str, Dict[int, str]] = {
    "individual": {
        1: "الذات والجسد والهوية", 2: "المال والدخل", 3: "الأقارب والإخوة والتنقلات",
        4: "العائلة والوالدان والسكن", 5: "الأولاد والعاطفة", 6: "الصحة والعمل اليومي",
        7: "الشريك والزواج والعقود", 8: "الأزمات العميقة وأموال الشراكة والوفيات",
        9: "السفر والتعليم العالي والقانون", 10: "المهنة والمكانة", 11: "الأصدقاء والدعم والأماني",
        12: "العزلة والمستشفيات والخسائر الخفية",
    },
    "company": {
        1: "العلامة التجارية", 2: "الإيرادات والسيولة", 3: "التسويق والمبيعات", 4: "المقر والأصول",
        5: "الابتكار والاستثمار", 6: "الفريق التشغيلي", 7: "الشراكات والمنافسون",
        8: "التمويل والضرائب والاندماج", 9: "التوسع الدولي والتراخيص", 10: "الإدارة العليا والقيادة",
        11: "المساهمون والعملاء", 12: "المخاطر الخفية",
    },
    "country": {
        1: "الهوية الوطنية والشعب", 2: "الخزينة والاقتصاد", 3: "الإعلام والمواصلات والتجارة الداخلية",
        4: "الأرض والمعارضة والنسيج الداخلي", 5: "الاستثمار والأسواق", 6: "الأمن الداخلي والصحة العامة",
        7: "الدبلوماسية والنزاعات", 8: "الديون والمخابرات والضرائب", 9: "القضاء والتجارة الخارجية",
        10: "الحكومة والسلطة التنفيذية", 11: "البرلمان والتحالفات", 12: "التهديدات الخفية والسجون",
    },
}

# الشركات: هيكلي مقابل مالي (يُقارَن متوسط نشاط كل مجموعة لا مجموعها لاختلاف عدد البيوت)
COMPANY_GROUPS = {"هيكلي": (1, 3, 4, 6, 7, 9, 10, 12), "مالي": (2, 5, 8, 11)}
# الدول: أربعة قطاعات تغطي البيوت الاثني عشر
COUNTRY_GROUPS = {
    "الشعب والمجتمع": (1, 3, 4),
    "الاقتصاد": (2, 5, 8, 9),
    "الأمن والجيش": (6, 7, 12),
    "النظام السياسي": (10, 11),
}

IND_ADVICE = {
    1: "أعد تعريف أهدافك الشخصية واعتنِ بالجسد والطاقة قبل أي قرار كبير",
    2: "أعد بناء الميزانية ونوّع مصادر الدخل واحتفظ بسيولة احتياطية",
    3: "قوِّ الصلة بالإخوة والأقارب ووثّق الاتفاقات والمراسلات المهمة",
    4: "خصّص وقتاً للأسرة والوالدين وراجع شؤون السكن والعقار بهدوء",
    5: "أحط الأبناء بالرعاية والحوار ووجّه العاطفة والإبداع في مسار بنّاء",
    6: "التزم بفحوص دورية ونمط حياة منتظم ونظّم عبء العمل اليومي",
    7: "عزّز الحوار الصريح مع الشريك وراجع بنود العقود قبل التوقيع",
    8: "أعد ترتيب الديون والموارد المشتركة وجهّز خطة طوارئ مالية ونفسية",
    9: "خطّط للسفر أو الدراسة بعناية واستشر مختصاً في أي شأن قانوني",
    10: "وثّق إنجازاتك المهنية وابنِ علاقات جيدة مع المسؤولين وجهّز بدائل وظيفية",
    11: "اعتمد على شبكة علاقات موثوقة وحدّد أهدافاً واقعية للمرحلة",
    12: "خصّص وقتاً للراحة والتأمل وابتعد عن المخاطر الخفية والأسرار",
}
IND_WARN = {
    1: "تجنّب الإرهاق الجسدي والاندفاع في القرارات الشخصية",
    2: "احذر القروض والمجازفات والإنفاق غير المحسوب",
    3: "احذر سوء الفهم والخلاف مع الإخوة والأقارب وتأنَّ في التنقل",
    4: "احذر التوتر العائلي والبُعد عن الأهل وقرارات السكن المتعجلة",
    5: "احذر الانفعال العاطفي والمخاطرة وراقب أحوال الأبناء",
    6: "لا تهمل أي عَرَض صحي ولا تتجاهل الإجهاد المتراكم في العمل",
    7: "احذر القطيعة والنزاعات الزوجية أو التعاقدية",
    8: "احذر الأزمات المفاجئة والالتزامات المالية المشتركة وتأخير الفحوصات",
    9: "احذر المشكلات القانونية والتعثر في السفر أو الدراسة",
    10: "احذر فقدان الموقع أو الخلاف مع الإدارة أو تغيّر المسار المهني المفاجئ",
    11: "احذر خيبات الأصدقاء والتحالفات غير المضمونة",
    12: "احذر الاستنزاف النفسي والمشكلات الصحية الخفية",
}
COMPANY_KIND_ADVICE = {
    "تغيير هيكلي": "راجع الهيكل الإداري والحوكمة وحدّد الأدوار والمسؤوليات بوضوح",
    "تغيير مالي": "حافظ على السيولة وراجع التمويل والالتزامات الضريبية وسياسة الأسعار",
    "تغيير هيكلي ومالي معاً": "اربط إعادة الهيكلة بخطة مالية واضحة ولا تفصل بينهما",
}
COMPANY_KIND_WARN = {
    "تغيير هيكلي": "خطر صراعات إدارية أو تغيير في القيادة والعلامة التجارية",
    "تغيير مالي": "خطر ضغط على السيولة أو التمويل أو التزامات ضريبية",
    "تغيير هيكلي ومالي معاً": "خطر تزامن أزمة إدارية مع ضغط مالي، فاحذر القرارات الكبرى المتسرعة",
}
COUNTRY_GROUP_ADVICE = {
    "الشعب والمجتمع": "افتح حواراً مجتمعياً وعالج ضغوط المعيشة والخدمات الأساسية",
    "الاقتصاد": "احمِ الخزينة والاستقرار النقدي ونوّع الموارد وأدر الدين بحذر",
    "الأمن والجيش": "ارفع الجاهزية وأمّن الحدود وسلاسل الإمداد الحيوية",
    "النظام السياسي": "عزّز الشرعية المؤسسية وأدر التحالفات والبرلمان بشفافية",
}
COUNTRY_GROUP_WARN = {
    "الشعب والمجتمع": "خطر احتقان شعبي وتراجع الثقة العامة",
    "الاقتصاد": "خطر اضطراب نقدي أو ضغط ديون على الخزينة",
    "الأمن والجيش": "خطر توتر أمني أو عسكري أو اختراق خفي",
    "النظام السياسي": "خطر تغيّر في السلطة أو انقسام سياسي",
}
ADV_TPL = {
    "pos": "استثمر الزخم الإيجابي في مجال «{d}» وثبّت المكاسب بإجراءات رسمية",
    "mix": "أعد ترتيب أولويات «{d}» بخطوات مرحلية وراقب المؤشرات",
    "neg": "ضع خطة احتواء وبدائل واضحة لمجال «{d}» قبل اشتداد الضغط",
}
WARN_TPL = {
    "pos": "لا تبالغ في التفاؤل: مجال «{d}» يتغيّر جوهرياً حتى مع المؤشرات الجيدة",
    "mix": "توقّع تقلباً في «{d}» وتجنب الالتزامات طويلة الأجل غير المدروسة",
    "neg": "مجال «{d}» تحت ضغط مرتفع؛ تجنب القرارات الاندفاعية غير القابلة للتراجع",
}


def _clip(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _norm(d: Dict[int, float]) -> Dict[int, float]:
    s = sum(d.values())
    return {k: (v / s if s > 0 else 0.0) for k, v in d.items()}


def valence_key(v: float) -> str:
    return "pos" if v >= 0.12 else ("neg" if v <= -0.12 else "mix")


VALENCE_AR = {"pos": "إيجابي", "mix": "مختلط", "neg": "سلبي / ضاغط"}


def best_transit_aspect(plon: float, natal_pts: List[Tuple[float, str]]) -> str:
    best, txt = 0.0, ""
    for n_lon, n_lbl in natal_pts:
        sep = angular_sep(plon, n_lon)
        for a_deg, a_name, max_orb in TRANSIT_ASPECTS:
            orb = abs(sep - a_deg)
            if orb <= max_orb and 1.0 - orb / max_orb > best:
                best = 1.0 - orb / max_orb
                txt = f" ({a_name} مع {n_lbl}، جرم {orb:.1f}°)"
    return txt


def interpret_year(natal: dict, target_jd: float, age: int, entity_type: str, six: dict) -> dict:
    sun_idx = natal["sun_sign_idx"]
    labels = HOUSE_LABELS[entity_type]
    tr = get_lons(target_jd)
    sat_h, nep_h = house_of_lon(sun_idx, tr["SAT"]), house_of_lon(sun_idx, tr["NEP"])

    # (1) اتصالات الخرائط الست حسب البيت المتأثر
    hit_w = {h: 0.0 for h in range(1, 13)}
    hit_vw = {h: 0.0 for h in range(1, 13)}
    for ht in six["hits"]:
        h = ht.get("house")
        if h:
            hit_w[h] += ht["strength"]
            hit_vw[h] += ht["strength"] * ht["valence"]
    hit_val = {h: (hit_vw[h] / hit_w[h] if hit_w[h] > 0 else 0.0) for h in hit_w}

    # (2) كواكب العودة الشمسية في البيوت
    sr_w = {h: 0.0 for h in range(1, 13)}
    sr_nat = {h: 0.0 for h in range(1, 13)}
    for r in six["solar_return"]["planet_rows"]:
        sr_w[r["house"]] += PLANET_ACT[r["code"]]
        sr_nat[r["house"]] += PLANET_NATURE[r["code"]]

    # (3) بيتا زحل (هيكلة) ونبتون (نهايات) العابرين، و(4) بيت الانتهاء السنوي
    transit_w = {h: 0.0 for h in range(1, 13)}
    transit_w[sat_h] += 0.55
    transit_w[nep_h] += 0.45
    prof_w = {h: (1.0 if h == six["profection_house"] else 0.0) for h in range(1, 13)}

    hs, ts, ps, ss = _norm(hit_w), _norm(transit_w), _norm(prof_w), _norm(sr_w)
    score = {h: 0.30 * hs[h] + 0.30 * ts[h] + 0.15 * ps[h] + 0.25 * ss[h] for h in range(1, 13)}
    val = {}
    for h in range(1, 13):
        v = 0.6 * hit_val[h] + 0.4 * _clip(sr_nat[h] / 2.0)
        if h == sat_h:
            v -= 0.25
        if h == nep_h:
            v -= 0.15
        val[h] = _clip(v)
    total = sum(score.values()) or 1.0
    overall = sum(score[h] * val[h] for h in score) / total

    ranked = sorted(range(1, 13), key=lambda h: score[h], reverse=True)
    main_houses = [h for h in ranked[:3] if h == ranked[0] or score[h] >= 0.6 * score[ranked[0]]]
    domains = [{
        "house": h, "label": labels[h], "score": score[h], "valence": val[h],
        "valence_label": VALENCE_AR[valence_key(val[h])], "valence_key": valence_key(val[h]),
    } for h in main_houses]

    change_kind, sector_txt = "", ""
    advice, warnings = [], []
    if entity_type == "individual":
        names = " ثم ".join(d["label"] for d in domains)
        headline = f"التغيير يخص: {names} — الاتجاه العام: {VALENCE_AR[valence_key(overall)]}"
        for d in domains:
            advice.append(f"{d['label']}: {IND_ADVICE[d['house']]}.")
            warnings.append(f"{d['label']}: {IND_WARN[d['house']]}.")
    elif entity_type == "company":
        s_mean = sum(score[h] for h in COMPANY_GROUPS["هيكلي"]) / len(COMPANY_GROUPS["هيكلي"])
        f_mean = sum(score[h] for h in COMPANY_GROUPS["مالي"]) / len(COMPANY_GROUPS["مالي"])
        share_s = s_mean / (s_mean + f_mean) if (s_mean + f_mean) > 0 else 0.5
        change_kind = "تغيير هيكلي" if share_s >= 0.62 else ("تغيير مالي" if share_s <= 0.38 else "تغيير هيكلي ومالي معاً")
        names = " ثم ".join(d["label"] for d in domains)
        headline = f"{change_kind} — أبرز المجالات: {names} — الاتجاه العام: {VALENCE_AR[valence_key(overall)]}"
        advice.append(COMPANY_KIND_ADVICE[change_kind] + ".")
        warnings.append(COMPANY_KIND_WARN[change_kind] + ".")
        for d in domains:
            advice.append(ADV_TPL[d["valence_key"]].format(d=d["label"]) + ".")
            warnings.append(WARN_TPL[d["valence_key"]].format(d=d["label"]) + ".")
    else:
        g_score = {g: sum(score[h] for h in hs_) / len(hs_) for g, hs_ in COUNTRY_GROUPS.items()}
        g_rank = sorted(g_score, key=g_score.get, reverse=True)
        g_main = [g for g in g_rank[:2] if g == g_rank[0] or g_score[g] >= 0.8 * g_score[g_rank[0]]]
        sector_txt = " ثم ".join(g_main)
        g_val = {g: (sum(score[h] * val[h] for h in COUNTRY_GROUPS[g]) / (sum(score[h] for h in COUNTRY_GROUPS[g]) or 1.0)) for g in g_main}
        headline = (f"التغيير يخص قطاع: {sector_txt} — الاتجاه العام: {VALENCE_AR[valence_key(overall)]} "
                    f"(" + "، ".join(f"{g}: {VALENCE_AR[valence_key(g_val[g])]}" for g in g_main) + ")")
        for g in g_main:
            advice.append(COUNTRY_GROUP_ADVICE[g] + ".")
            warnings.append(COUNTRY_GROUP_WARN[g] + ".")
        for d in domains:
            advice.append(ADV_TPL[d["valence_key"]].format(d=d["label"]) + ".")
            warnings.append(WARN_TPL[d["valence_key"]].format(d=d["label"]) + ".")

    advice.append(f"برج الانتهاء السنوي ({six['profection_sign_name']}) برب السنة {six['lord_of_year_ar']}: ركّز على قرارات الحسم المدروسة.")
    warnings.append("سنة تغيير ضمن طبقات رادار كاليبر: تجنب القرارات الاندفاعية غير القابلة للتراجع.")

    # نص العبور: زحل (هيكلة) ونبتون (نهايات)
    natal_pts = [(natal["pl"]["SUN"], "الشمس الأصلية"), (natal["pl"]["SAT"], "زحل الأصلي"),
                 (natal["pl"]["NEP"], "نبتون الأصلي"), (natal["pl"]["JUP"], "المشتري الأصلي")]
    _, sat_sign, sat_deg = zodiac_info(tr["SAT"])
    _, nep_sign, nep_deg = zodiac_info(tr["NEP"])
    top_hit = six["hits"][0] if six["hits"] else None
    hit_txt = f" · أبرز اتصال سداسي [{top_hit['tech_code']}]: {top_hit['directed_factor']} {top_hit['aspect_name']} {top_hit['natal_target']}" if top_hit else ""
    transit_details = (
        f"زحل العابر في {sat_sign} ({sat_deg:.1f}°) بالبيت {sat_h} [{labels[sat_h]}] — تغيير هيكلي{best_transit_aspect(tr['SAT'], natal_pts)} · "
        f"نبتون العابر في {nep_sign} ({nep_deg:.1f}°) بالبيت {nep_h} [{labels[nep_h]}] — نهايات وتلاشٍ{best_transit_aspect(tr['NEP'], natal_pts)}"
        f"{hit_txt}."
    )
    return {
        "domains": domains, "house_scores": score, "house_valence": val,
        "overall_valence": overall, "overall_label": VALENCE_AR[valence_key(overall)],
        "change_kind": change_kind, "sector": sector_txt, "headline": headline,
        "transit_details": transit_details,
        "saturn_house": sat_h, "neptune_house": nep_h,
        "advice_list": advice[:5], "warnings_list": warnings[:5],
    }


def build_house_evaluations(interp: dict, entity_type: str) -> List[dict]:
    out = []
    for h in range(1, 13):
        out.append({
            "house": h, "meaning": HOUSES_MEANINGS[entity_type][h],
            "score": interp["house_scores"][h],
            "status": VALENCE_AR[valence_key(interp["house_valence"][h])],
        })
    return out


def run_complete_annual_radar(name: str, entity_type: str, birth_date: date, city_label: str, lat: float, lon: float, tz_name: str) -> dict:
    max_age = 84 if entity_type == "individual" else 120
    natal = build_natal(birth_date, lat, lon)
    all_years, active_years = [], []
    serial = 0
    for age in range(1, max_age + 1):
        devs = radar_layer_devs(age)
        four = is_four_axis(devs)
        status = STATUS_FOUR_AXIS if four else STATUS_NORMAL
        target_year = radar_target_year(birth_date, age)
        s_prim, s_sub, s_col = STATUS_LABELS[status]
        row = {
            "serial": age, "age": age, "target_year": target_year,
            "entity_name": name, "entity_type": entity_type,
            "birth_date_str": birth_date.isoformat(), "status": status,
            "radar_primary": s_prim, "radar_sub": s_sub, "status_color": s_col,
            "eris_dev": devs["eris"],
            "neptune_dev": devs["neptune"], "saturn_dev": devs["saturn"],
            "saturn_cycle": round(age / K_SATURN),
            "max_dev": max(devs.values()),
            "rms_dev": math.sqrt(sum(v * v for v in devs.values()) / len(devs)),
            "headline": "", "transit_details": "", "overall_summary": "", "advice_list": [], "warnings_list": [],
            "domains": [],
        }
        if four:
            serial += 1
            row["serial"] = serial
            target_jd = find_solar_return_jd(natal["pl"]["SUN"], target_year)
            six = evaluate_six_charts_for_year(natal, target_jd, age, entity_type)
            interp = interpret_year(natal, target_jd, age, entity_type, six)
            row.update({
                "six_charts": six,
                "domains": interp["domains"],
                "change_kind": interp["change_kind"],
                "sector": interp["sector"],
                "overall_label": interp["overall_label"],
                "overall_valence": interp["overall_valence"],
                "headline": interp["headline"],
                "overall_summary": interp["headline"],
                "transit_details": interp["transit_details"],
                "advice_list": interp["advice_list"],
                "warnings_list": interp["warnings_list"],
                "house_evaluations": build_house_evaluations(interp, entity_type),
            })
            active_years.append(row)
        all_years.append(row)

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
    """التقرير النهائي القابل للطباعة للسنوات المعلَّمة فقط."""
    entity_label = ENTITY_LABELS[run["entity_type"]]
    matrix_rows = []
    for r in rows_to_display:
        if not r.get("domains"):
            continue
        dom_html = "".join(
            f"<div><b>{html.escape(d['label'])}</b> ({html.escape(d['valence_label'])})</div>"
            for d in r["domains"]
        )
        adv_html = "".join(f"<li>{html.escape(a)}</li>" for a in r["advice_list"])
        warn_html = "".join(f"<li>{html.escape(w)}</li>" for w in r["warnings_list"])
        layers = _layers_text(r)
        matrix_rows.append(f"""
        <tr>
            <td class="num">{r['serial']}</td>
            <td><b>{html.escape(r['entity_name'])}</b></td>
            <td class="num"><b>{r['target_year']}</b><br><small>عمر {r['age']}</small></td>
            <td><span style="color:{r['status_color']};font-weight:800;">{html.escape(r['radar_primary'])}</span><br><small>{html.escape(layers)}</small><br><small>السداسي: {r['six_charts']['mean_percent']:.1f}%</small></td>
            <td><b>{html.escape(r['headline'])}</b>{dom_html}</td>
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
  <h1>التقرير الفلكي الاستشاري لسنوات التغيير — طبقات رادار كاليبر ({html.escape(entity_label)})</h1>
  <div class="meta-grid">
    <div><b>الاسم:</b> {html.escape(run['entity_name'])}</div>
    <div><b>تاريخ الميلاد / التأسيس:</b> {html.escape(run['birth_date_str'])}</div>
    <div><b>الموقع:</b> {html.escape(run['city_label'])}</div>
    <div><b>الطالع الشمسي (كل برج بيت):</b> {html.escape(run['natal']['sun_sign_name'])}</div>
    <div><b>مدى المسح:</b> حتى {run['max_age']} سنة</div>
    <div><b>سنوات التغيير المعلَّمة:</b> {len(run['active_years'])} سنة</div>
    <div><b>ثوابت المحرك:</b> {' · '.join(f'{LAYER_AR[l]} {LAYER_K[l]}' for l in ACTIVE_LAYERS)} · ε={EPSILON}</div>
    <div><b>تطوير:</b> استرو رادار</div>
  </div>
  <h2>مصفوفة سنوات التغيير</h2>
  <table>
    <thead>
      <tr>
        <th>#</th><th>الاسم</th><th>السنة</th><th>حالة الرادار</th>
        <th>مجال التغيير والاتجاه</th><th>تفاصيل العبور</th><th>أهم النصائح</th><th>أهم التحذيرات</th>
      </tr>
    </thead>
    <tbody>{"".join(matrix_rows)}</tbody>
  </table>
  <p style="margin-top:20px;font-size:11px;color:#64748B;">هذا التقرير مخرَج تحليلي فلكي يدمج نظرية الطبقات (زحل ونبتون وإيريس) مع الخرائط الست (الاتجاهات الرمزية والأقواس الشمسية والتقدمية الثانوية والانتهاء السنوي والعبور والعودة الشمسية) ولا يُعد بديلاً عن الاستشارة المتخصصة.</p>
</div>
</body>
</html>"""


# ==================== واجهة Streamlit الرئيسية ====================
def _layers_text(r: dict) -> str:
    return " · ".join(f"{LAYER_AR[l]} {r[l + '_dev']:.2f}" for l in ACTIVE_LAYERS)


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
        st.caption(f"الإحداثيات: {lat:.3f}°, {lon:.3f}° · المنطقة الزمنية: {tz_name} (للعرض فقط: البيوت كل برج بيت بلا وقت ميلاد)")

        run_btn = st.button("تشغيل رادار كايبر", type="primary", use_container_width=True)

    st.markdown(
        """
        <div class="kuiper-hero">
            <h1 style="margin:0;font-size:24px;color:#FFFFFF;">رادار كايبر التنبؤي المتقدم</h1>
            <p style="margin:4px 0 0;font-size:13px;color:#94A3B8;">
                تطوير الفلكي الدكتور استرو رادار · السنة تُعلَّم عند تقاطع الطبقات (زحل · نبتون · إيريس)، ثم تفسّرها العودة الشمسية والخرائط الست
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if run_btn or "kuiper_run" not in st.session_state:
        if not name.strip():
            st.error("يرجى إدخال الاسم قبل التشغيل.")
            return
        with st.spinner("جاري حساب الطبقات وتفسير السنوات..."):
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
    k3.markdown(f'<div class="kuiper-card"><div class="kuiper-kpi-label">سنوات التغيير المعلَّمة</div><div class="kuiper-kpi-val" style="color:#34D399;">{len(run["active_years"])} سنة</div></div>', unsafe_allow_html=True)
    peak_txt = f"{peak_row['target_year']} ({peak_row['six_charts']['mean_percent']:.1f}%)" if peak_row else "—"
    k4.markdown(f'<div class="kuiper-card"><div class="kuiper-kpi-label">أعلى رنين للخرائط الست</div><div class="kuiper-kpi-val" style="color:#38BDF8;">{peak_txt}</div></div>', unsafe_allow_html=True)

    fc1, fc2 = st.columns([2, 1])
    filter_choice = fc1.selectbox(
        "تصفية مصفوفة السنوات:",
        ["سنوات التغيير المعلَّمة", f"كامل السجل (1–{run['max_age']})"],
    )
    search_q = fc2.text_input("بحث بالسنة أو المجال:", placeholder="مثال: 2025 أو الصحة...")

    rows_filtered = run["all_years"] if filter_choice.startswith("كامل") else run["active_years"]
    if search_q.strip():
        q = search_q.strip().lower()
        rows_filtered = [
            r for r in rows_filtered
            if q in str(r["target_year"]) or q in str(r["age"]) or q in r["radar_primary"].lower()
            or q in r["transit_details"].lower() or q in r["headline"].lower()
        ]

    st.subheader(f"مصفوفة التوقعات السنوية ({len(rows_filtered)} سنة)")
    df_rows = [{
        "#": r["serial"],
        "الاسم": r["entity_name"],
        "السنة": f"{r['target_year']} (عمر {r['age']})",
        "حالة الرادار": f"{r['radar_primary']} — {_layers_text(r)}",
        "مجال التغيير والاتجاه": r["headline"] or "—",
        "تفاصيل العبور": r["transit_details"] or "—",
        "أهم النصائح": " • ".join(r["advice_list"][:2]),
        "أهم التحذيرات": " • ".join(r["warnings_list"][:2]),
    } for r in rows_filtered]
    st.dataframe(pd.DataFrame(df_rows), use_container_width=True, hide_index=True)

    if rows_filtered:
        st.markdown("---")
        sel_age = st.selectbox(
            "اختر سنة للفحص التفصيلي التفاعلي:",
            [r["age"] for r in rows_filtered],
            format_func=lambda a: next((f"السنة {r['target_year']} (عمر {r['age']}) — {r['radar_primary']}" for r in rows_filtered if r["age"] == a), str(a)),
        )
        sel_row = next(r for r in rows_filtered if r["age"] == sel_age)

        t1, t2, t3, t4 = st.tabs(["الخريطة والتقييم العام", "تحليل الخرائط الست", "منحنى الطبقات", "التقرير النهائي القابل للطباعة"])
        with t1:
            if "six_charts" not in sel_row:
                st.info(f"سنة اعتيادية: لم تتقاطع فيها الطبقات الفعّالة. {_layers_text(sel_row)}")
            else:
                col_w, col_e = st.columns([1, 1.4])
                with col_w:
                    st.markdown(render_zodiac_wheel_svg(sel_row), unsafe_allow_html=True)
                    st.caption(f"طالع العودة: {sel_row['six_charts']['solar_return']['solar_asc_sign']} · رب السنة: {sel_row['six_charts']['lord_of_year_ar']}")
                with col_e:
                    st.markdown(f'<div class="kuiper-card"><b>{sel_row["headline"]}</b></div>', unsafe_allow_html=True)
                    for d in sel_row["domains"]:
                        st.markdown(f'<div class="kuiper-card"><b>{d["label"]}</b> — <span style="color:#F5B942;">{d["valence_label"]}</span></div>', unsafe_allow_html=True)
                st.info(f"**تفاصيل العبور:** {sel_row['transit_details']}")
                ca, cw = st.columns(2)
                with ca:
                    st.success("**أهم النصائح:**\n" + "\n".join(f"- {a}" for a in sel_row["advice_list"]))
                with cw:
                    st.warning("**أهم التحذيرات:**\n" + "\n".join(f"- {w}" for w in sel_row["warnings_list"]))

        with t2:
            if "six_charts" not in sel_row:
                st.info("الخرائط الست تُحسب لسنوات التغيير المعلَّمة فقط.")
            else:
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
            curve_cols = {"العمر": [r["age"] for r in run["all_years"]]}
            for l in ACTIVE_LAYERS:
                curve_cols[LAYER_AR[l]] = [r[l + "_dev"] for r in run["all_years"]]
            curve_cols["العتبة ε"] = [EPSILON for _ in run["all_years"]]
            curve_df = pd.DataFrame(curve_cols).set_index("العمر")
            st.line_chart(curve_df)
            st.caption(f"تُعلَّم السنة عندما تكون انحرافات الطبقات الفعّالة كلها تحت خط العتبة ε={EPSILON}. هذه السنة: {_layers_text(sel_row)}")

        with t4:
            html_report = build_unified_html_report(run, run["active_years"])
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
