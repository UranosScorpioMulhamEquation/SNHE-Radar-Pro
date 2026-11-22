import base64
import html
import math
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st
import swisseph as swe
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

# ==================== 1. الثوابت المثبتة للنموذج ====================
K_HAUMEA = 6.19
K_ERIS = 9.30
K_NEPTUNE = 10.78
K_SATURN = 4.48
EPSILON = 0.30
MAX_AGE = 90
SATURN_CYCLES = 15
APEX_CYCLE = 10
CRITICAL_CYCLE = 9

# الثوابت الفيزيائية الكبلرية لهوميا وإيريس
T_HAUMEA = 283.28
T_ERIS = 558.0
E_HAUMEA = 0.1964
E_ERIS = 0.43607
M0_HAUMEA_DEG = 216.0
M0_ERIS_DEG = 197.6

STATUS_NORMAL = "Normal"
STATUS_PHASE_HARMONIC = "PHASE_HARMONIC"
STATUS_CRITICAL = "CRITICAL"
STATUS_FOUR_AXIS = "FOUR_AXIS"
STATUS_UNIFIED = "UNIFIED"
STATUS_APEX = "APEX"

SATURN_CONFIRMED = {STATUS_FOUR_AXIS, STATUS_UNIFIED, STATUS_APEX}
ACTIVE_RADAR = SATURN_CONFIRMED | {STATUS_CRITICAL, STATUS_PHASE_HARMONIC}

STATUS_UI = {
    STATUS_APEX: ("ذروة زحل (APEX)", "#f59e0b"),
    STATUS_UNIFIED: ("تقاطع موحّد (UNIFIED)", "#06b6d4"),
    STATUS_FOUR_AXIS: ("توافق رباعي المحاور (Δ_Saturn ≤ ε)", "#38bdf8"),
    STATUS_CRITICAL: ("حرجة ثلاثية (CRITICAL)", "#f43f5e"),
    STATUS_PHASE_HARMONIC: ("رنين طوري-توافقي مطوّر (علاج الفجوة)", "#10b981"),
    STATUS_NORMAL: ("عادية (Normal)", "#64748b"),
}

ZODIAC_SIGNS = [
    "الحمل", "الثور", "الجوزاء", "السرطان",
    "الأسد", "العذراء", "الميزان", "العقرب",
    "القوس", "الجدي", "الدلو", "الحوت",
]

OUTER_PLANETS = {
    swe.SATURN: "زحل",
    swe.JUPITER: "المشتري",
    swe.URANUS: "أورانوس",
    swe.NEPTUNE: "نبتون",
    swe.PLUTO: "بلوتو",
}

ASPECTS = [
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

DISCLAIMER = (
    "هذا النموذج بحثي واسترشادي، ولا يُعدّ بديلاً عن الاستشارة الطبية أو المالية "
    "أو القانونية المتخصصة."
)


# ==================== 2. الدوال الفلكية والكبلرية ====================
def get_zodiac_sign(longitude: float):
    longitude = longitude % 360.0
    sign_index = int(longitude // 30) % 12
    degree = longitude % 30.0
    return sign_index, ZODIAC_SIGNS[sign_index], degree


def get_planet_longitude(jd: float, planet_id: int) -> float:
    res, _ = swe.calc_ut(jd, planet_id)
    return float(res[0]) % 360.0


def transit_house_of(anchor_sign_idx: int, transit_sign_idx: int) -> int:
    """رقم البيت (Whole Sign) حيث البيت الأول هو البرج الشمسي تلقائياً"""
    return (transit_sign_idx - anchor_sign_idx) % 12 + 1


def angular_separation(lon_a: float, lon_b: float) -> float:
    diff = abs((lon_a % 360.0) - (lon_b % 360.0))
    return 360.0 - diff if diff > 180.0 else diff


def solve_kepler_true_anomaly_deg(mean_anomaly_deg: float, eccentricity: float) -> float:
    """حل معادلة كبلر M = E - e*sin(E) لحساب الشذوذ الحقيقي للأجرام الإهليلجية"""
    m_rad = math.radians(mean_anomaly_deg % 360.0)
    e_anom = m_rad + eccentricity * math.sin(m_rad)
    for _ in range(8):
        f = e_anom - eccentricity * math.sin(e_anom) - m_rad
        fp = 1.0 - eccentricity * math.cos(e_anom)
        e_anom -= f / fp
    nu = 2.0 * math.atan2(
        math.sqrt(1.0 + eccentricity) * math.sin(e_anom / 2.0),
        math.sqrt(1.0 - eccentricity) * math.cos(e_anom / 2.0),
    )
    return math.degrees(nu) % 360.0


def kepler_true_shift_deg(
    birth_jd: float, target_jd: float, period_years: float, eccentricity: float, m0_deg: float
) -> float:
    j2000_jd = 2451545.0
    years_b = (birth_jd - j2000_jd) / 365.25
    years_t = (target_jd - j2000_jd) / 365.25
    nu_b = solve_kepler_true_anomaly_deg(m0_deg + (years_b / period_years) * 360.0, eccentricity)
    nu_t = solve_kepler_true_anomaly_deg(m0_deg + (years_t / period_years) * 360.0, eccentricity)
    return (nu_t - nu_b) % 360.0


def find_strongest_aspect(transit_lon: float, natal_points: list):
    best = None
    for target_lon, target_name in natal_points:
        sep = angular_separation(transit_lon, target_lon)
        for angle, asp_name, max_orb in ASPECTS:
            orb = abs(sep - angle)
            if orb <= max_orb:
                strength = 1.0 - (orb / max_orb)
                if best is None or strength > best["strength"]:
                    best = {
                        "name": asp_name,
                        "target": target_name,
                        "orb": orb,
                        "strength": strength,
                    }
    return best


def compute_true_phase_coupling(
    birth_jd: float, target_jd: float, sun_lon0: float, sat_lon0: float, nep_lon0: float
):
    sat_lon = get_planet_longitude(target_jd, swe.SATURN)
    nep_lon = get_planet_longitude(target_jd, swe.NEPTUNE)

    pairs = [
        (sat_lon, sat_lon0, "زحل العابر مع زحل الأصلي", (0.0, 90.0, 180.0), 1.0),
        (nep_lon, nep_lon0, "نبتون العابر مع نبتون الأصلي", (0.0, 45.0, 60.0, 90.0, 120.0, 180.0), 1.0),
        (nep_lon, sun_lon0, "نبتون العابر مع الشمس الأصلية", (0.0, 60.0, 90.0, 120.0, 180.0), 1.05),
        (sat_lon, sun_lon0, "زحل العابر مع الشمس الأصلية", (0.0, 90.0, 180.0), 1.05),
    ]

    best_eff = 90.0
    best_raw = 90.0
    best_label = "طور مداري محايد"

    for t_lon, n_lon, pair_name, allowed, weight in pairs:
        sep = angular_separation(t_lon, n_lon)
        for angle in allowed:
            orb = abs(sep - angle)
            eff = orb * weight
            if eff < best_eff:
                best_eff = eff
                best_raw = orb
                ang_lbl = next((lbl for a, lbl in PHASE_ANGLES if a == angle), f"{angle}°")
                best_label = f"{ang_lbl} · {pair_name}"

    true_phase_dev = min(0.5, best_eff / 18.0)
    return {
        "true_phase_dev": true_phase_dev,
        "best_orb_deg": best_raw,
        "phase_label": best_label,
        "haumea_kepler_shift": kepler_true_shift_deg(birth_jd, target_jd, T_HAUMEA, E_HAUMEA, M0_HAUMEA_DEG),
        "eris_kepler_shift": kepler_true_shift_deg(birth_jd, target_jd, T_ERIS, E_ERIS, M0_ERIS_DEG),
    }


def safe_add_years_and_days(birth_date: date, years: int, offset_days: int) -> date:
    target_year = birth_date.year + years
    try:
        base = date(target_year, birth_date.month, birth_date.day)
    except ValueError:
        base = date(target_year, 2, 28)
    return base + timedelta(days=offset_days)


# ==================== 3. محرك الرادار المطوّر (زحل 4.48 + الرنين المستمر + الطور) ====================
def fractional_deviation(age: int, k: float) -> float:
    ratio = age / k
    return abs(ratio - round(ratio))


def saturn_layer(age: int):
    ratio = age / K_SATURN
    cycle_no = round(ratio)
    marker = "Normal"
    for c in range(1, SATURN_CYCLES + 1):
        if int(c * K_SATURN) == age:
            if c == APEX_CYCLE:
                marker = "Apex Resonance"
            elif c == CRITICAL_CYCLE:
                marker = "Critical"
            else:
                marker = "Cycle Point"
            break
    return {
        "SaturnDev": abs(ratio - cycle_no),
        "SaturnCycle": cycle_no,
        "SaturnMarker": marker,
    }


def classify_base_status(neptune_critical: bool, saturn: dict) -> str:
    if not neptune_critical:
        return STATUS_NORMAL
    if saturn["SaturnMarker"] == "Apex Resonance":
        return STATUS_APEX
    if saturn["SaturnMarker"] == "Critical":
        return STATUS_UNIFIED
    if saturn["SaturnDev"] <= EPSILON:
        return STATUS_FOUR_AXIS
    return STATUS_CRITICAL


def run_upgraded_usm_engine(birth_date: date, birth_jd: float, sun_lon0: float, sat_lon0: float, nep_lon0: float):
    results = []
    for i in range(1, MAX_AGE + 1):
        homo_dev = fractional_deviation(i, K_HAUMEA)
        eris_dev = fractional_deviation(i, K_ERIS)
        neptune_dev = fractional_deviation(i, K_NEPTUNE)

        neptune_critical = (
            homo_dev <= EPSILON and eris_dev <= EPSILON and neptune_dev <= EPSILON
        )
        saturn = saturn_layer(i)
        base_status = classify_base_status(neptune_critical, saturn)

        offset_days = int(homo_dev * 12) * 30 + int(eris_dev * 30)
        target_date = safe_add_years_and_days(birth_date, i, offset_days)
        target_jd = swe.julday(target_date.year, target_date.month, target_date.day, 12.0)

        harmonic_rms = math.sqrt(
            (homo_dev ** 2 + eris_dev ** 2 + neptune_dev ** 2 + saturn["SaturnDev"] ** 2) / 4.0
        )
        phase_info = compute_true_phase_coupling(birth_jd, target_jd, sun_lon0, sat_lon0, nep_lon0)
        hybrid_dev = 0.55 * harmonic_rms + 0.45 * phase_info["true_phase_dev"]

        status = base_status
        if base_status == STATUS_NORMAL and hybrid_dev <= 0.23 and phase_info["true_phase_dev"] <= EPSILON:
            status = STATUS_PHASE_HARMONIC

        results.append({
            "DateStr": target_date.strftime("%Y-%m-%d"),
            "YearDate": target_date,
            "Age": i,
            "Status": status,
            "ClassicStatus": base_status,
            "HaumeaDev": homo_dev,
            "ErisDev": eris_dev,
            "NeptuneDev": neptune_dev,
            "SaturnDev": saturn["SaturnDev"],
            "SaturnCycle": saturn["SaturnCycle"],
            "HarmonicRms": harmonic_rms,
            "TruePhaseDev": phase_info["true_phase_dev"],
            "HybridDev": hybrid_dev,
            "PhaseLabel": phase_info["phase_label"],
            "PhaseOrbDeg": phase_info["best_orb_deg"],
        })
    return results


# ==================== 4. العبور الفلكي المصحّح (البيت أولاً) ====================
def focus_for_house(entity_type: str, house: int) -> str:
    if entity_type == "شخص":
        if house in (6, 12):
            return "ضغوط صحية أو جسدية تستدعي إعادة ضبط نمط الحياة والاستشفاء"
        if house in (10, 1):
            return "ترقية أو تغيّر في المسؤوليات والواجهة والمكانة العامة"
        if house == 4:
            return "تحولات في العائلة أو السكن أو الجذور"
        if house == 7:
            return "مرحلة مفصلية في الشراكة أو الزواج"
        if house in (2, 8):
            return "إعادة ترتيب الدخل أو الديون أو الموارد المشتركة"
        return "إعادة هيكلة عامة للمسار الشخصي"
    if entity_type == "شركة":
        if house in (2, 8):
            return "تحولات في الأرباح والسيولة والتمويل"
        if house in (10, 1):
            return "تغيير في الإدارة العليا أو الواجهة العامة للشركة"
        if house in (6, 12):
            return "إعادة هيكلة تشغيلية أو معالجة مخاطر كامنة"
        if house in (7, 11):
            return "شراكات أو تحالفات أو صفقات اندماج"
        return "إعادة تنظيم إداري شاملة"
    if house in (6, 8, 12):
        return "توترات أمنية أو دفاعية وإعادة تقييم استراتيجي للأمن القومي"
    if house in (11, 1, 7):
        return "حراك شعبي أو تحول في الرأي العام والعلاقات الدولية"
    if house in (2, 10):
        return "تحولات اقتصادية وإصلاحات في الموارد والمؤسسات"
    return "تحولات سياسية واجتماعية واسعة"


def evaluate_dominant_transit(jd: float, sun_sign_idx: int, natal_points: list):
    ranked = []
    for planet_id, planet_name in OUTER_PLANETS.items():
        lon = get_planet_longitude(jd, planet_id)
        sign_idx, sign_name, deg = get_zodiac_sign(lon)
        house = transit_house_of(sun_sign_idx, sign_idx)
        angular_w = 3.0 if house in (1, 4, 7, 10) else (2.0 if house in (2, 5, 8, 11) else 1.2)
        aspect = find_strongest_aspect(lon, natal_points)
        aspect_w = aspect["strength"] * 4.5 if aspect else 0.0
        saturn_w = 0.45 if planet_id == swe.SATURN else 0.0
        ranked.append({
            "planet_name": planet_name,
            "sign_name": sign_name,
            "deg": deg,
            "house": house,
            "aspect": aspect,
            "score": angular_w + aspect_w + saturn_w,
        })
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[0]


def analyze_reference_transit(
    entity_type: str,
    sun_sign_idx: int,
    natal_points: list,
    target_date: date,
    status: str,
    saturn_cycle: int,
) -> str:
    jd = swe.julday(target_date.year, target_date.month, target_date.day, 12.0)

    if status in SATURN_CONFIRMED:
        sat_lon = get_planet_longitude(jd, swe.SATURN)
        sign_idx, sign_name, deg = get_zodiac_sign(sat_lon)
        house = transit_house_of(sun_sign_idx, sign_idx)
        aspect = find_strongest_aspect(sat_lon, natal_points)
        asp_txt = (
            f" · {aspect['name']} مع {aspect['target']} (جرم {aspect['orb']:.1f}°)"
            if aspect else ""
        )
        focus = focus_for_house(entity_type, house)
        if status == STATUS_APEX:
            prefix = f"ذروة زحل: الدورة العاشرة (10 × {K_SATURN})"
        elif status == STATUS_UNIFIED:
            prefix = f"تقاطع موحّد: الدورة التاسعة (9 × {K_SATURN})"
        else:
            prefix = f"توافق رباعي المحاور (الدورة {saturn_cycle} × {K_SATURN})"
        return (
            f"{prefix} — عبور زحل الفعلي في برج {sign_name} ({deg:.1f}°) "
            f"بالبيت {house}{asp_txt}. المجال المرافق: {focus}."
        )

    dominant = evaluate_dominant_transit(jd, sun_sign_idx, natal_points)
    focus = focus_for_house(entity_type, dominant["house"])
    asp = dominant["aspect"]
    asp_txt = (
        f" ({asp['name']} مع {asp['target']}، جرم {asp['orb']:.1f}°)"
        if asp else ""
    )
    prefix = "رنين طوري-توافقي مسترد · " if status == STATUS_PHASE_HARMONIC else ""
    return (
        f"{prefix}العبور الأقوى فلكياً: {dominant['planet_name']} في برج {dominant['sign_name']} "
        f"({dominant['deg']:.1f}°) بالبيت {dominant['house']}{asp_txt} — {focus}."
    )


# ==================== 5. التقرير القابل للطباعة (بدون عمود نوع التغيير) ====================
def build_html_report(name, entity_type, birth_date, sun_sign_name, df_results, age_label):
    name_esc = html.escape(name)
    entity_esc = html.escape(entity_type)
    report = f"""<!doctype html>
<html dir="rtl" lang="ar">
<head>
  <meta charset="utf-8">
  <title>تقرير السنوات الحرجة والطور التوافقي (زحل - نبتون - هوميا - إيريس) - {name_esc}</title>
  <style>
    body {{ font-family: 'Cairo', Tahoma, sans-serif; padding: 30px; color: #1e293b; background: #fff; }}
    h1 {{ color: #0f172a; text-align: center; }}
    .meta {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 10px; text-align: right; font-size: 13px; }}
    th {{ background-color: #0f172a; color: #fff; }}
    tr:nth-child(even) {{ background-color: #f8fafc; }}
    .footer {{ margin-top: 30px; text-align: center; font-size: 12px; color: #64748b; }}
  </style>
</head>
<body>
  <h1>تقرير السنوات الحرجة والطور التوافقي: زحل - نبتون - هوميا - إيريس</h1>
  <div class="meta">
    <p><strong>اسم الكيان:</strong> {name_esc} ({entity_esc})</p>
    <p><strong>تاريخ الميلاد / التأسيس:</strong> {birth_date}</p>
    <p><strong>البرج الشمسي تلقائياً (Whole Sign):</strong> {html.escape(sun_sign_name)}</p>
    <p><strong>نطاق العرض:</strong> السنوات الحرجة والطور التوافقي (زحل - نبتون - هوميا - إيريس)</p>
    <p><strong>الثوابت المثبتة:</strong> هوميا {K_HAUMEA} | إيريس {K_ERIS} | نبتون {K_NEPTUNE} | زحل {K_SATURN} | ε = {EPSILON:.2f}</p>
    <p><strong>تاريخ إصدار التقرير:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
  </div>
  <table>
    <tr>
      <th>{html.escape(age_label)}</th>
      <th>التاريخ المستهدف</th>
      <th>حالة الرادار</th>
      <th>زحل 4.48 / الهجين</th>
      <th>العبور المرجعي والتفاصيل</th>
    </tr>
"""
    for _, row in df_results.iterrows():
        status_label, status_color = STATUS_UI[row["Status"]]
        saturn_cell = f"الدورة {row['SaturnCycle']} | Δ_s={row['SaturnDev']:.3f} | Δ_hyb={row['HybridDev']:.3f}"
        report += f"""
    <tr>
      <td>{int(row['Age'])}</td>
      <td>{html.escape(str(row['Date']))}</td>
      <td style="color: {status_color}; font-weight: bold;">{html.escape(status_label)}</td>
      <td>{html.escape(saturn_cell)}</td>
      <td>{html.escape(str(row['Detail']))} · {html.escape(str(row['PhaseLabel']))}</td>
    </tr>
"""
    report += f"""
  </table>
  <div class="footer">
    <p>{html.escape(DISCLAIMER)}</p>
  </div>
</body>
</html>"""
    return report


def safe_file_stem(name: str) -> str:
    stem = "".join(ch for ch in name if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_")
    return stem or "report"


# ==================== 6. واجهة Streamlit ====================
def main():
    st.set_page_config(
        page_title="رادار السنوات الحرجة والطور التوافقي: زحل - نبتون - هوميا - إيريس",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown("<style>html, body, [class*='css'] { direction: rtl; text-align: right; }</style>", unsafe_allow_html=True)
    st.title("رادار السنوات الحرجة والطور التوافقي: زحل - نبتون - هوميا - إيريس")

    with st.sidebar:
        st.header("إعدادات الإدخال")
        preset = st.selectbox("نماذج مرجعية:", ["نموذج الورقة (1981-04-17)", "شركة أبل (1976-04-01)", "مثال عن دولة (1970-11-13)"])
        if preset.startswith("مثال عن دولة"):
            def_type, def_name, def_y, def_m, def_d = "دولة", "مثال عن دولة", 1970, 11, 13
        elif preset.startswith("شركة"):
            def_type, def_name, def_y, def_m, def_d = "شركة", "شركة Apple Inc.", 1976, 4, 1
        else:
            def_type, def_name, def_y, def_m, def_d = "شخص", "دراسة حالة الورقة البحثية", 1981, 4, 17

        entity_type = st.selectbox("نوع الكيان:", ["شخص", "شركة", "دولة"], index=["شخص", "شركة", "دولة"].index(def_type))
        name_input = st.text_input("اسم الكيان:", value=def_name)
        year = st.number_input("السنة", min_value=1800, max_value=date.today().year, value=def_y)
        month = st.number_input("الشهر", min_value=1, max_value=12, value=def_m)
        day = st.number_input("اليوم", min_value=1, max_value=31, value=def_d)
        st.info("المعايير المثبتة: زحل 4.48 · ε = 0.30 · البرج الشمسي تلقائياً · البيت أولاً · الرنين المستمر + الطور الزاوي الحقيقي")
        run_btn = st.button("تشغيل الرادار المطور", type="primary", use_container_width=True)

    if not run_btn:
        st.info("اضغط على «تشغيل الرادار المطور» لعرض مصفوفة السنوات الحرجة والطور التوافقي.")
        return

    try:
        birth_date = date(int(year), int(month), int(day))
    except ValueError:
        st.error("تاريخ الميلاد / التأسيس غير صالح.")
        return

    birth_jd = swe.julday(birth_date.year, birth_date.month, birth_date.day, 12.0)
    sun_lon = get_planet_longitude(birth_jd, swe.SUN)
    sat_lon = get_planet_longitude(birth_jd, swe.SATURN)
    jup_lon = get_planet_longitude(birth_jd, swe.JUPITER)
    nep_lon = get_planet_longitude(birth_jd, swe.NEPTUNE)
    sun_sign_idx, sun_sign_name, _ = get_zodiac_sign(sun_lon)
    natal_points = [(sun_lon, "الشمس الأصلية"), (sat_lon, "زحل الأصلي"), (jup_lon, "المشتري الأصلي")]

    all_rows = run_upgraded_usm_engine(birth_date, birth_jd, sun_lon, sat_lon, nep_lon)
    active_rows = [r for r in all_rows if r["Status"] in ACTIVE_RADAR]
    age_label = "عمر الشخص" if entity_type == "شخص" else "عمر الكيان"
    processed = []
    for row in active_rows:
        detail = analyze_reference_transit(
            entity_type, sun_sign_idx, natal_points, row["YearDate"], row["Status"], row["SaturnCycle"]
        )
        processed.append({
            "Age": row["Age"],
            "Date": row["DateStr"],
            "Status": row["Status"],
            "SaturnCycle": row["SaturnCycle"],
            "SaturnDev": row["SaturnDev"],
            "HybridDev": row["HybridDev"],
            "PhaseLabel": f"{row['PhaseLabel']} (جرم {row['PhaseOrbDeg']:.2f}°)",
            "Detail": detail,
        })

    df_results = pd.DataFrame(processed)
    st.dataframe(df_results, use_container_width=True)

    html_report = build_html_report(name_input, entity_type, birth_date, sun_sign_name, df_results, age_label)
    b64 = base64.b64encode(html_report.encode("utf-8")).decode("utf-8")
    st.markdown(
        f'<a href="data:text/html;base64,{b64}" download="USM_Report_{safe_file_stem(name_input)}.html">تنزيل التقرير القابل للطباعة (HTML)</a>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
