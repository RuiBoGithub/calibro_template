
import re
import pandas as pd
from pathlib import Path

# =============================================================
# 1. READ FIRST TABULARX TABLE
# =============================================================

def read_first_latex_table(tex_path):
    tex_path = Path(tex_path)
    txt = tex_path.read_text()

    pattern = r"\\begin{tabularx}.*?}(.*?)\\end{tabularx}"
    m = re.search(pattern, txt, flags=re.DOTALL | re.IGNORECASE)
    if not m:
        raise ValueError("No tabularx environment found.")

    tbl = m.group(1)
    cleaned = []
    for line in tbl.splitlines():
        line = line.strip()
        if not line or line.startswith('\\hline'):
            continue
        cleaned.append(line)

    t = " ".join(cleaned)
    rows = [r.strip() for r in t.split('\\') if r.strip()]
    parts = [re.split(r"\s*&\s*", r) for r in rows]

    raw_header = parts[0]
    header = []
    for h in raw_header:
        h2 = h.strip()
        if h2.startswith('{X|ccc}'):
            h2 = h2.replace('{X|ccc}', '').strip() or 'PARAMETER'
        header.append(h2)

    if header[0] != 'PARAMETER':
        header[0] = 'PARAMETER'

    return pd.DataFrame(parts[1:], columns=header)

# =============================================================
# 2. REBUILD SEGMENTED PARAMETERS
# =============================================================

def rebuild_parameters(df):
    params, est, low, up = [], [], [], []
    buffer = []

    for _, row in df.iterrows():
        name = row['PARAMETER']
        val = row['ESTIMATE']

        if val is None or val == '' or str(val).lower() == 'none':
            buffer.append(name)
            continue

        buffer.append(name)
        fullname = ''.join(buffer)
        buffer = []

        params.append(fullname)
        est.append(row['ESTIMATE'])
        low.append(row['LOWER'])
        up.append(row['UPPER'])

    return pd.DataFrame({'PARAMETER': params, 'ESTIMATE': est, 'LOWER': low, 'UPPER': up})

# =============================================================
# 3. PARAMETER MAP
# =============================================================

def build_param_map(df):
    return dict(zip(df['PARAMETER'], df['ESTIMATE'].astype(str)))

# =============================================================
# 4. PLACEH OLDER REPLACEMENT
# =============================================================

def replace_in_string(s, value_map):
    matches = re.findall(r"{{(.*?)}}", s)
    for m in matches:
        if m in value_map:
            val = value_map[m]
            s = s.replace(f"{{{{{m}}}}}", val)
    return s

def replace_placeholders(item, value_map):
    if isinstance(item, str):
        return replace_in_string(item, value_map)
    return tuple(replace_in_string(x, value_map) if isinstance(x, str) else x for x in item)

# =============================================================
# 5. DETECT UNRESOLVED PLACEHOLDERS
# =============================================================

def contains_unresolved_placeholder(item):
    if isinstance(item, str):
        return '{{' in item
    return any(isinstance(x, str) and '{{' in x for x in item)

# =============================================================
# 6. FILTER: KEEP SCHEDULE ENTRIES
# =============================================================

def is_schedule(item):
    return isinstance(item, tuple) and item[0].startswith("htg_sch_office_br__")

# =============================================================
# SCHEDULE PARAMETER REGISTRY (EXTENSIBLE d1–d4, m1–m4)
# =============================================================

schedule_defaults = {
    "d1_htgsp_office": 18,
    "d2_htgsp_office_st": 15,
    "d3_htgsp_office_peak": 20,
    "d4_htgsp_office_late": 17,

    "m1_clgsp_office": 24,
    "m2_clgsp_office_st": 28,
    "m3_clgsp_office_peak": 22,
    "m4_clgsp_office_late": 26,
}

# =============================================================
# BUILD FINAL VALUE MAP (LaTeX + defaults)
# =============================================================

def build_schedule_value_map(param_map):
    value_map = param_map.copy()
    for key, default in schedule_defaults.items():
        if key not in value_map:
            value_map[key] = str(default)
    return value_map

# =============================================================
# 7. FULL PIPELINE (Generalised d1–d4, m1–m4)
# =============================================================

def process_all(tex_file, ReUnit_HVAC, ReClass_HVAC, drop_missing=True, overwrite_with_derived=True):
    df_raw = read_first_latex_table(tex_file)
    df = rebuild_parameters(df_raw)
    param_map = build_param_map(df)

    # Build unified replacement map (calibrated + defaults)
    value_map = build_schedule_value_map(param_map)

    if overwrite_with_derived:
        # Apply replacements with derived values
        ReUnit_new = [replace_placeholders(x, value_map) for x in ReUnit_HVAC]
        ReClass_new = [replace_placeholders(x, value_map) for x in ReClass_HVAC]
        
        # Remove unresolved placeholders only when we're replacing values
        if drop_missing:
            ReUnit_new = [x for x in ReUnit_new if is_schedule(x) or not contains_unresolved_placeholder(x)]
            ReClass_new = [x for x in ReClass_new if not contains_unresolved_placeholder(x)]
    else:
        # Keep original double-braced placeholders
        ReUnit_new = ReUnit_HVAC.copy()
        ReClass_new = ReClass_HVAC.copy()
        
        # When NOT overwriting but drop_missing is True, we need to identify
        # which entries would have been resolved and only keep those
        if drop_missing:
            # Create a temporary version with replacements to check what WOULD resolve
            ReUnit_temp = [replace_placeholders(x, value_map) for x in ReUnit_HVAC]
            ReClass_temp = [replace_placeholders(x, value_map) for x in ReClass_HVAC]
            
            # Filter original lists based on what would resolve in the temp version
            ReUnit_new = [ReUnit_HVAC[i] for i, temp_item in enumerate(ReUnit_temp) 
                         if is_schedule(temp_item) or not contains_unresolved_placeholder(temp_item)]
            ReClass_new = [ReClass_HVAC[i] for i, temp_item in enumerate(ReClass_temp) 
                          if not contains_unresolved_placeholder(temp_item)]

    return df, param_map, ReUnit_new, ReClass_new