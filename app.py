import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import numpy as np

# ============================================================
# CONFIGURACIÓN GLOBAL
# ============================================================
st.set_page_config(
    page_title="CEMIC · Simulador Financiero",
    layout="wide",
    page_icon="💰",
    initial_sidebar_state="auto"
)

# ============================================================
# SISTEMA DE DISEÑO
# ============================================================
ACCENT      = "#00BFA5"
ACCENT2     = "#FF6B6B"
ACCENT3     = "#FFB74D"
ACCENT4     = "#69F0AE"
BLUE_LIGHT  = "#4FC3F7"
BLUE_DARK   = "#0277BD"
CARD_BG     = "#1E2130"
BORDER      = "#2D3250"
TEXT_MUTED  = "#8B93A7"
BG_MAIN     = "#13151F"

PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#CDD6F4"),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)

MESES_FULL = {1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
              7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"}

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');
  html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif; }}
  #MainMenu, footer, header {{ visibility: hidden; }}
  .stApp {{ background-color: {BG_MAIN}; }}
  [data-testid="stSidebar"] {{
      background-color: #171925 !important; border-right: 1px solid {BORDER};
  }}
  [data-testid="stSidebar"] label {{
      font-size: 11px; font-weight: 600; letter-spacing: 0.08em;
      text-transform: uppercase; color: {TEXT_MUTED} !important;
  }}
  .kpi-card {{
      background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 12px;
      padding: 18px 20px; position: relative; overflow: hidden;
  }}
  .kpi-card::before {{
      content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
      background: linear-gradient(90deg, {ACCENT}, {BLUE_LIGHT});
  }}
  .kpi-card-danger::before  {{ background: linear-gradient(90deg, {ACCENT2}, #FF3333); }}
  .kpi-card-warning::before {{ background: linear-gradient(90deg, {ACCENT3}, #FF8F00); }}
  .kpi-card-success::before {{ background: linear-gradient(90deg, {ACCENT4}, {ACCENT}); }}
  .kpi-card-info::before    {{ background: linear-gradient(90deg, {BLUE_LIGHT}, {BLUE_DARK}); }}
  .kpi-label {{
      font-size: 11px; font-weight: 600; letter-spacing: 0.1em;
      text-transform: uppercase; color: {TEXT_MUTED}; margin-bottom: 6px;
  }}
  .kpi-value {{
      font-size: 26px; font-weight: 700; color: #CDD6F4;
      font-family: 'DM Mono', monospace; line-height: 1;
  }}
  .kpi-delta-pos {{ font-size: 12px; color: {ACCENT4}; margin-top: 5px; font-weight:500; }}
  .kpi-delta-neg {{ font-size: 12px; color: {ACCENT2}; margin-top: 5px; font-weight:500; }}
  .kpi-delta-neu {{ font-size: 12px; color: {ACCENT3}; margin-top: 5px; font-weight:500; }}
  .sec-title {{ font-size: 20px; font-weight: 700; color: #CDD6F4; margin-bottom: 4px; }}
  .sec-sub   {{ font-size: 13px; color: {TEXT_MUTED}; margin-bottom: 16px; }}
  .badge {{
      display: inline-block; background: rgba(0,191,165,0.15); color: {ACCENT};
      border: 1px solid rgba(0,191,165,0.3); border-radius: 20px;
      padding: 2px 10px; font-size: 12px; font-weight: 600;
  }}
  .badge-proj {{
      background: rgba(255,183,77,0.15); color: {ACCENT3}; border-color: rgba(255,183,77,0.3);
  }}
  .insight-box {{
      background: rgba(255,107,107,0.08); border: 1px solid rgba(255,107,107,0.25);
      border-left: 4px solid {ACCENT2}; border-radius: 8px;
      padding: 12px 16px; margin: 12px 0; font-size: 13px; color: #CDD6F4;
  }}
  .insight-box-teal  {{ background:rgba(0,191,165,0.08);  border-color:rgba(0,191,165,0.25);  border-left-color:{ACCENT}; }}
  .insight-box-amber {{ background:rgba(255,183,77,0.08); border-color:rgba(255,183,77,0.25); border-left-color:{ACCENT3}; }}
  .insight-box-blue  {{ background:rgba(79,195,247,0.08); border-color:rgba(79,195,247,0.25); border-left-color:{BLUE_LIGHT}; }}
  .stTabs [data-baseweb="tab-list"] {{
      background: {CARD_BG}; border-radius: 8px; padding: 4px; gap: 4px; border: 1px solid {BORDER};
  }}
  .stTabs [data-baseweb="tab"] {{ border-radius: 6px; font-size: 13px; font-weight: 500; color: {TEXT_MUTED}; }}
  .stTabs [aria-selected="true"] {{ background-color: {ACCENT} !important; color: #13151F !important; font-weight: 700; }}
  hr {{ border-color: {BORDER} !important; opacity: 0.5; }}
  [data-testid="stExpander"] {{ background: {CARD_BG}; border: 1px solid {BORDER} !important; border-radius: 10px; }}
  div[data-testid="stMetric"] {{ background-color:{CARD_BG}; border:1px solid {BORDER}; padding:14px 18px; border-radius:12px; }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# HELPERS
# ============================================================
def fmt_pesos(n):
    s = f"{abs(n):,.0f}".replace(",","X").replace(".","," ).replace("X",".")
    return f"$ {s}" if n >= 0 else f"- $ {s}"

def fmt_millones(n):
    if abs(n) >= 1_000_000_000: return f"$ {n/1e9:.1f}B"
    if abs(n) >= 1_000_000:     return f"$ {n/1e6:.1f}M"
    return fmt_pesos(n)

def fmt_fecha(ts):
    return f"{MESES_FULL[ts.month]} {ts.year}"

def kpi_card(label, value, delta=None, delta_label=None, variant="default", fmt_fn=fmt_pesos):
    val_str = fmt_fn(value)
    delta_html = ""
    if delta is not None:
        sign = "+" if delta >= 0 else ""
        cls  = "kpi-delta-pos" if delta > 0 else ("kpi-delta-neg" if delta < 0 else "kpi-delta-neu")
        icon = "▲" if delta > 0 else ("▼" if delta < 0 else "●")
        lbl  = delta_label if delta_label else f"{sign}{fmt_fn(delta)}"
        delta_html = f'<div class="{cls}">{icon} {lbl}</div>'
    card_cls = f"kpi-card kpi-card-{variant}" if variant != "default" else "kpi-card"
    return f"""
    <div class="{card_cls}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{val_str}</div>
        {delta_html}
    </div>"""

def apply_plotly_defaults(fig, title=""):
    fig.update_layout(**PLOTLY_LAYOUT)
    if title:
        fig.update_layout(title=dict(text=title, font=dict(size=14, color="#CDD6F4"), x=0, xanchor="left"))
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor=BORDER, zeroline=False)
    return fig

def generar_excel(df, nombre_hoja="Datos"):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=nombre_hoja[:31], index=False)
    return buf.getvalue()

def limpiar_df(df):
    num_cols = df.select_dtypes(include='number').columns
    df[num_cols] = df[num_cols].fillna(0)
    str_cols = df.select_dtypes(include='object').columns
    df[str_cols] = df[str_cols].fillna('')
    return df

# ============================================================
# CARGA DE DATOS
# ============================================================
@st.cache_data(ttl=300)
def cargar_datos():
    BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQHFwl-Dxn-Rw9KN_evkCMk2Er8lQqgZMzAtN4LuEkWcCeBVUNwgb8xeIFKvpyxMgeGTeJ3oEWKpMZj"
    df_of  = pd.read_csv(f"{BASE}/pub?gid=1524527213&single=true&output=csv")
    df_au  = pd.read_csv(f"{BASE}/pub?gid=2132722842&single=true&output=csv")
    df_val = pd.read_csv(f"{BASE}/pub?gid=554651129&single=true&output=csv")

    # BD_TURNOS_DADOS — URL completo publicado desde Google Sheets
    try:
        df_td = pd.read_csv("https://docs.google.com/spreadsheets/d/e/2PACX-1vQHFwl-Dxn-Rw9KN_evkCMk2Er8lQqgZMzAtN4LuEkWcCeBVUNwgb8xeIFKvpyxMgeGTeJ3oEWKpMZj/pub?gid=1285454147&single=true&output=csv")
    except Exception as e:
        st.warning(f"⚠️ No se pudo cargar BD_TURNOS_DADOS: {e}")
        df_td = pd.DataFrame(columns=['PERIODO','SERVICIO','TURNO_DADOS'])

    for df in [df_of, df_au, df_val, df_td]:
        df.columns = df.columns.str.strip()
        for col in ['SERVICIO','DEPARTAMENTO']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper()

    df_of['PERIODO']      = pd.to_datetime(df_of['PERIODO'],      dayfirst=True, errors='coerce')
    df_au['FECHA_INICIO'] = pd.to_datetime(df_au['FECHA_INICIO'], dayfirst=True, errors='coerce')
    df_val['PERIODO']     = pd.to_datetime(df_val['PERIODO'],     dayfirst=True, errors='coerce')
    if 'PERIODO' in df_td.columns:
        df_td['PERIODO']  = pd.to_datetime(df_td['PERIODO'],      dayfirst=True, errors='coerce')

    if 'VALOR_TURNO' in df_val.columns:
        df_val['VALOR_TURNO'] = pd.to_numeric(
            df_val['VALOR_TURNO'].astype(str)
                .str.replace('$','',regex=False)
                .str.replace('.','',regex=False)
                .str.replace(',','.',regex=False),
            errors='coerce').fillna(0)
    if 'RENDIMIENTO' in df_val.columns:
        df_val['RENDIMIENTO'] = pd.to_numeric(df_val['RENDIMIENTO'], errors='coerce').fillna(14)
    if 'TURNO_DADOS' in df_td.columns:
        df_td['TURNO_DADOS'] = pd.to_numeric(df_td['TURNO_DADOS'], errors='coerce').fillna(0)

    col_target = 'CONSULTORIOS_REALES' if 'CONSULTORIOS_REALES' in df_au.columns else 'DIAS_CAIDOS'
    df_au[col_target] = pd.to_numeric(df_au[col_target], errors='coerce').fillna(0)
    df_au['_COL_TARGET'] = df_au[col_target]

    for df in [df_of, df_au, df_val, df_td]:
        limpiar_df(df)

    return df_of, df_au, df_val, df_td

# ============================================================
# CÁLCULO CENTRAL
# ============================================================
def calcular_metricas(df_of, df_au, df_val, df_td_p=None, rend_override=None):
    # Facturación base (oferta × valor)
    df_ing = df_of.merge(df_val[['SERVICIO','VALOR_TURNO']], on='SERVICIO', how='left')
    df_ing['VALOR_TURNO']      = df_ing['VALOR_TURNO'].fillna(0)
    df_ing['FACTURACION_BASE'] = df_ing['TURNOS_MENSUAL'] * df_ing['VALOR_TURNO']

    # Pérdida por ausentismo profesional
    df_perd = df_au.merge(df_val[['SERVICIO','VALOR_TURNO','RENDIMIENTO']], on='SERVICIO', how='left')
    df_perd['VALOR_TURNO']       = df_perd['VALOR_TURNO'].fillna(0)
    df_perd['RENDIMIENTO_USADO'] = rend_override if rend_override else df_perd['RENDIMIENTO'].fillna(14)
    df_perd['TURNOS_PERDIDOS']   = df_perd['_COL_TARGET'] * df_perd['RENDIMIENTO_USADO']
    df_perd['DINERO_PERDIDO']    = df_perd['TURNOS_PERDIDOS'] * df_perd['VALOR_TURNO']

    total_base  = df_ing['FACTURACION_BASE'].sum()
    total_perd  = df_perd['DINERO_PERDIDO'].sum()
    turnos_of   = df_ing['TURNOS_MENSUAL'].sum()
    turnos_perd = df_perd['TURNOS_PERDIDOS'].sum()
    pct_fuga    = (total_perd / (total_base + total_perd) * 100) if (total_base + total_perd) > 0 else 0

    # Ocupación real (solo si hay dato de turnos dados)
    ocup = pd.DataFrame()
    tiene_dato_real = False
    if df_td_p is not None and not df_td_p.empty:
        of_serv = df_ing.groupby('SERVICIO').agg(
            TURNOS_OFERTA=('TURNOS_MENSUAL','sum'),
            VALOR_TURNO=('VALOR_TURNO','mean')
        ).reset_index()
        ocup = of_serv.merge(df_td_p[['SERVICIO','TURNO_DADOS']], on='SERVICIO', how='inner')
        ocup = ocup[(ocup['VALOR_TURNO'] > 0) & (ocup['TURNOS_OFERTA'] > 0)]
        ocup['TASA_OCUP']         = (ocup['TURNO_DADOS'] / ocup['TURNOS_OFERTA'] * 100).round(1)
        ocup['FACT_REAL']         = ocup['TURNO_DADOS'] * ocup['VALOR_TURNO']
        ocup['PERD_INASISTENCIA'] = (ocup['TURNOS_OFERTA'] - ocup['TURNO_DADOS']).clip(lower=0) * ocup['VALOR_TURNO']
        tiene_dato_real = not ocup.empty

    return dict(
        total_base=total_base, total_perd=total_perd,
        total_pot=total_base + total_perd,
        total_fact_real=ocup['FACT_REAL'].sum() if tiene_dato_real else None,
        total_perd_inasist=ocup['PERD_INASISTENCIA'].sum() if tiene_dato_real else None,
        tasa_ocup_prom=ocup['TASA_OCUP'].clip(upper=100).mean() if tiene_dato_real else None,
        tiene_dato_real=tiene_dato_real,
        turnos_of=turnos_of, turnos_perd=turnos_perd, pct_fuga=pct_fuga,
        df_ing=df_ing, df_perd=df_perd, df_ocup=ocup,
    )

# ============================================================
# CARGA INICIAL
# ============================================================
try:
    df_oferta, df_ausencia, df_valores, df_turnos_dados = cargar_datos()
except Exception as e:
    st.error(f"❌ Error cargando datos: {e}")
    st.stop()

tiene_td       = not df_turnos_dados.empty and 'TURNO_DADOS' in df_turnos_dados.columns
# Normalizar períodos a date para comparación robusta
periodos_reales = set(
    pd.to_datetime(df_turnos_dados['PERIODO'].dropna()).dt.to_period('M')
) if tiene_td else set()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding:10px 0 20px 0;">
        <img src="https://cemic.edu.ar/assets/img/logo/logo-cemic.png" width="120" style="filter:brightness(1.1);">
        <div style="font-size:10px; letter-spacing:0.15em; color:{TEXT_MUTED}; text-transform:uppercase; margin-top:8px; font-weight:600;">
            Simulador Financiero
        </div>
    </div>
    """, unsafe_allow_html=True)

    fechas_disp = sorted(df_valores['PERIODO'].dropna().unique())
    if not fechas_disp:
        st.error("Sin períodos disponibles.")
        st.stop()

    periodo_sel  = st.selectbox("PERÍODO", fechas_disp, index=len(fechas_disp)-1, format_func=fmt_fecha)
    es_dato_real = pd.Timestamp(periodo_sel).to_period('M') in periodos_reales

    if tiene_td:
        badge_txt = "✅ Dato real disponible" if es_dato_real else "📈 Sin dato real — modo estimación"
        badge_cls = "badge" if es_dato_real else "badge badge-proj"
        st.markdown(f'<div class="{badge_cls}" style="margin-bottom:8px;">{badge_txt}</div>', unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:8px;'>PARÁMETROS</div>", unsafe_allow_html=True)
    usar_slider = st.checkbox("Ajustar rendimiento manualmente", value=False)
    rend_manual = 14
    if usar_slider:
        rend_manual = st.slider("Pacientes por consultorio:", 1, 30, 14)
        st.caption(f"Ajustado: **{rend_manual}** pac/cons")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:11px;color:{TEXT_MUTED};'>Datos actualizados cada 5 min.</div>", unsafe_allow_html=True)

# ============================================================
# HELPERS DE FILTRADO
# ============================================================
def filtrar(p):
    dv = df_valores[df_valores['PERIODO'] == p]
    do = df_oferta[(df_oferta['PERIODO'].dt.year==p.year)  & (df_oferta['PERIODO'].dt.month==p.month)]
    da = df_ausencia[(df_ausencia['FECHA_INICIO'].dt.year==p.year) & (df_ausencia['FECHA_INICIO'].dt.month==p.month)]
    dt = df_turnos_dados[df_turnos_dados['PERIODO']==p] if tiene_td else None
    return do, da, dv, dt

df_of_f, df_au_f, df_val_f, df_td_f = filtrar(periodo_sel)

idx_ant    = fechas_disp.index(periodo_sel) - 1 if fechas_disp.index(periodo_sel) > 0 else None
periodo_ant = fechas_disp[idx_ant] if idx_ant is not None else None

# Tasa de ocupación promedio histórica (para estimación en períodos sin dato)
tasa_hist_prom = None
if tiene_td and periodos_reales:
    tasas = []
    for p in sorted(periodos_reales):
        try:
            p_ts = p.to_timestamp()
            do, da, dv, dt = filtrar(p_ts)
            mh = calcular_metricas(do, da, dv, dt)
            if mh['tasa_ocup_prom'] and not np.isnan(mh['tasa_ocup_prom']):
                tasas.append(mh['tasa_ocup_prom'])
        except:
            pass
    tasa_hist_prom = float(np.mean(tasas)) if tasas else None

# ============================================================
# MAIN
# ============================================================
try:
    m = calcular_metricas(df_of_f, df_au_f, df_val_f,
                          df_td_f if es_dato_real else None,
                          rend_override=rend_manual if usar_slider else None)

    m_ant = None
    if periodo_ant is not None:
        try:
            ant_real = pd.Timestamp(periodo_ant).to_period('M') in periodos_reales
            do_a, da_a, dv_a, dt_a = filtrar(periodo_ant)
            m_ant = calcular_metricas(do_a, da_a, dv_a, dt_a if ant_real else None)
        except:
            m_ant = None

    # ── Encabezado ─────────────────────────────────────────
    badge_per = "✅ Dato real" if es_dato_real else "📈 Estimado"
    badge_cls = "badge" if es_dato_real else "badge badge-proj"
    vs_str    = f"&nbsp;&nbsp;vs&nbsp;&nbsp;<span style='color:{TEXT_MUTED};'>{fmt_fecha(periodo_ant)}</span>" if periodo_ant else ""
    st.markdown(f"""
    <div style="display:flex; align-items:baseline; gap:12px; margin-bottom:4px;">
        <span style="font-size:26px; font-weight:700; color:#CDD6F4;">💰 Simulador de Impacto Económico</span>
    </div>
    <div style="font-size:13px; color:{TEXT_MUTED}; margin-bottom:20px;">
        Período analizado · <span class="badge">{fmt_fecha(periodo_sel)}</span>
        {vs_str}&nbsp;&nbsp;<span class="{badge_cls}">{badge_per}</span>
    </div>
    """, unsafe_allow_html=True)

    # ── KPIs ───────────────────────────────────────────────
    d_base = (m['total_base'] - m_ant['total_base']) if m_ant else None
    d_perd = (m['total_perd'] - m_ant['total_perd']) if m_ant else None

    c1, c2, c3, c4 = st.columns(4)

    c1.markdown(kpi_card(
        "💰 Facturación Base (Oferta)", m['total_base'],
        delta=d_base,
        delta_label=f"{'+' if d_base and d_base>=0 else ''}{fmt_millones(d_base) if d_base else ''} vs {fmt_fecha(periodo_ant) if periodo_ant else ''}",
        variant="success"
    ), unsafe_allow_html=True)
    c1.caption(f"{m['turnos_of']:,.0f} turnos ofertados")

    c2.markdown(kpi_card(
        "💸 Pérdida por Ausentismo Prof.", m['total_perd'],
        delta=d_perd,
        delta_label=f"{'+' if d_perd and d_perd>=0 else ''}{fmt_millones(d_perd) if d_perd else ''} vs {fmt_fecha(periodo_ant) if periodo_ant else ''}",
        variant="danger"
    ), unsafe_allow_html=True)
    c2.caption(f"{m['turnos_perd']:,.0f} turnos cancelados · {m['pct_fuga']:.1f}% del potencial")

    if m['tiene_dato_real']:
        d_real = (m['total_fact_real'] - m_ant['total_fact_real']) if (m_ant and m_ant.get('total_fact_real')) else None
        c3.markdown(kpi_card(
            "✅ Facturación Real", m['total_fact_real'],
            delta=d_real,
            delta_label=f"{'+' if d_real and d_real>=0 else ''}{fmt_millones(d_real) if d_real else ''} vs {fmt_fecha(periodo_ant) if periodo_ant else ''}",
            variant="success"
        ), unsafe_allow_html=True)
        c3.caption(f"Tasa de ocupación promedio: {m['tasa_ocup_prom']:.1f}%")

        c4.markdown(kpi_card(
            "📊 Brecha Oferta — Demanda Real", m['total_perd_inasist'], variant="danger"
        ), unsafe_allow_html=True)
        c4.caption("Diferencia entre turnos ofertados y turnos efectivamente dados")
    else:
        c3.markdown(kpi_card("🚀 Potencial Total", m['total_pot'], variant="default"), unsafe_allow_html=True)
        c3.caption("Escenario ideal sin ausentismo")
        c4.markdown(kpi_card("📅 Proyección Anual Pérdida", m['total_perd'] * 12, variant="warning"), unsafe_allow_html=True)
        c4.caption("Si el ausentismo de este mes se mantiene 12 meses")

        if tasa_hist_prom:
            fact_est = m['total_base'] * tasa_hist_prom / 100
            st.markdown(f"""
            <div class="insight-box insight-box-amber" style="margin-top:12px;">
                📈 <b>Estimación:</b> Basado en los meses anteriores, la tasa de ocupación promedio es
                <b>{tasa_hist_prom:.1f}%</b>. La facturación real estimada para este período sería
                <b>{fmt_millones(fact_est)}</b> — cargá los turnos dados para ver el dato exacto.
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Waterfall ──────────────────────────────────────────
    st.markdown('<div class="sec-title">📊 Composición Financiera del Período</div>', unsafe_allow_html=True)

    if m['tiene_dato_real']:
        st.markdown(f'<div class="sec-sub">Del potencial total, desglose de pérdidas por causa y facturación real · <span class="badge">✅ Dato real</span></div>', unsafe_allow_html=True)
        wf_x = ["Potencial\nTotal","Ausentismo\nProfesional","Brecha\nOferta-Demanda","Facturación\nReal"]
        wf_y = [m['total_pot'], -m['total_perd'], -m['total_perd_inasist'], 0]
        wf_t = [fmt_millones(m['total_pot']), f"- {fmt_millones(m['total_perd'])}",
                f"- {fmt_millones(m['total_perd_inasist'])}", fmt_millones(m['total_fact_real'])]
        wf_m = ["absolute","relative","relative","total"]
    else:
        st.markdown(f'<div class="sec-sub">Del potencial total, pérdida por ausentismo · <span class="badge badge-proj">📈 Estimado — cargá turnos dados para mayor precisión</span></div>', unsafe_allow_html=True)
        wf_x = ["Potencial\nTotal","Pérdida\nAusentismo","Facturación\nBase"]
        wf_y = [m['total_pot'], -m['total_perd'], 0]
        wf_t = [fmt_millones(m['total_pot']), f"- {fmt_millones(m['total_perd'])}", fmt_millones(m['total_base'])]
        wf_m = ["absolute","relative","total"]

    fig_wf = go.Figure(go.Waterfall(
        name="", orientation="v", measure=wf_m, x=wf_x, y=wf_y, text=wf_t,
        textposition="outside",
        connector=dict(line=dict(color=BORDER, width=1, dash="dot")),
        increasing=dict(marker=dict(color=BLUE_LIGHT)),
        decreasing=dict(marker=dict(color=ACCENT2, line=dict(color=ACCENT2, width=0))),
        totals=dict(marker=dict(color=ACCENT4, line=dict(color=ACCENT4, width=0))),
        textfont=dict(size=13, color="#CDD6F4"),
    ))
    apply_plotly_defaults(fig_wf)
    fig_wf.update_layout(height=360, showlegend=False, yaxis=dict(tickformat="$.3s"))
    st.plotly_chart(fig_wf, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Tasa de ocupación (solo si hay dato real) ───────────
    if m['tiene_dato_real'] and not m['df_ocup'].empty:
        st.markdown('<div class="sec-title">📋 Tasa de Ocupación por Servicio</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sec-sub">Turnos dados / turnos ofertados · Verde = buena ocupación · Rojo = baja ocupación · &gt;100% = alta demanda espontánea</div>', unsafe_allow_html=True)

        ocup = m['df_ocup'].sort_values('TASA_OCUP', ascending=True).copy()
        ocup['color'] = ocup['TASA_OCUP'].apply(
            lambda x: ACCENT2 if x < 60 else (ACCENT3 if x < 85 else ACCENT4))
        ocup['etiqueta'] = ocup['TASA_OCUP'].apply(lambda x: f"{x:.0f}%")

        baja = ocup[ocup['TASA_OCUP'] < 60].sort_values('PERD_INASISTENCIA', ascending=False).head(3)
        alta = ocup[ocup['TASA_OCUP'] > 100]
        if not baja.empty:
            perd_baja    = baja['PERD_INASISTENCIA'].sum()
            nombres_baja = ", ".join(baja['SERVICIO'].tolist())
            st.markdown(f"""
            <div class="insight-box insight-box-blue">
                📊 <b>Brecha oferta-demanda:</b> Los servicios con menor ocupación son
                <b>{nombres_baja}</b> — representan <b>{fmt_millones(perd_baja)}</b> de diferencia
                entre turnos ofertados y dados. Puede deberse a turnos no reservados,
                cancelaciones del paciente u oferta que supera la demanda.
            </div>
            """, unsafe_allow_html=True)
        if not alta.empty:
            st.markdown(f"""
            <div class="insight-box insight-box-teal">
                ⚡ <b>{len(alta)} servicio(s) superan el 100% de ocupación</b> — tienen alta demanda
                espontánea. Considera ampliar la oferta: {", ".join(alta['SERVICIO'].tolist())}.
            </div>
            """, unsafe_allow_html=True)

        fig_ocup = go.Figure(go.Bar(
            x=ocup['TASA_OCUP'], y=ocup['SERVICIO'], orientation='h',
            text=ocup['etiqueta'], textposition='outside',
            marker=dict(color=ocup['color'], line_width=0),
            customdata=np.stack([ocup['TURNO_DADOS'], ocup['TURNOS_OFERTA'],
                                 ocup['FACT_REAL'], ocup['PERD_INASISTENCIA']], axis=1),
            hovertemplate=(
                "<b>%{y}</b><br>Tasa: %{x:.1f}%<br>"
                "Turnos dados: %{customdata[0]:,.0f}<br>"
                "Turnos ofertados: %{customdata[1]:,.0f}<br>"
                "Facturación real: $%{customdata[2]:,.0f}<br>"
                "Brecha oferta-demanda: $%{customdata[3]:,.0f}<extra></extra>"
            )
        ))
        fig_ocup.add_vline(x=100, line_width=1, line_dash="dash", line_color=TEXT_MUTED,
                           annotation_text="100%", annotation_font_color=TEXT_MUTED)
        apply_plotly_defaults(fig_ocup, "Tasa de ocupación por servicio")
        fig_ocup.update_layout(height=max(420, len(ocup)*22), xaxis_ticksuffix="%")
        st.plotly_chart(fig_ocup, use_container_width=True)
        st.markdown("<hr>", unsafe_allow_html=True)

    # ── Top pérdidas por ausentismo profesional ─────────────
    st.markdown('<div class="sec-title">📉 Pérdida por Ausentismo del Profesional</div>', unsafe_allow_html=True)

    grp = m['df_perd'].groupby('SERVICIO')[['DINERO_PERDIDO','TURNOS_PERDIDOS']].sum().reset_index()
    grp = grp[grp['DINERO_PERDIDO'] > 0].sort_values('DINERO_PERDIDO', ascending=False)

    if grp.empty:
        st.info("Sin pérdidas por ausentismo en este período.")
    else:
        top3 = grp.head(3)
        pct_p = (top3['DINERO_PERDIDO'].sum() / m['total_perd'] * 100) if m['total_perd'] > 0 else 0
        st.markdown(f"""
        <div class="insight-box">
            ⚠️ <b>Regla de Pareto:</b> El <b>{pct_p:.0f}%</b> de la pérdida por ausentismo
            se concentra en: <b>{", ".join(top3["SERVICIO"].tolist())}</b>.
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["📊  Top 10 servicios", "📋  Todos los servicios"])
        with tab1:
            top10 = grp.head(10).sort_values('DINERO_PERDIDO', ascending=True).copy()
            top10['etiqueta'] = top10['DINERO_PERDIDO'].apply(fmt_millones)
            top10['pct']      = (top10['DINERO_PERDIDO'] / m['total_perd'] * 100).round(1)
            fig_b = px.bar(top10, x='DINERO_PERDIDO', y='SERVICIO', orientation='h',
                           text='etiqueta', color='DINERO_PERDIDO',
                           color_continuous_scale=[[0,"#FF8A65"],[0.5,ACCENT2],[1,"#B71C1C"]],
                           custom_data=['TURNOS_PERDIDOS','pct'])
            fig_b.update_traces(textposition='outside', marker_line_width=0,
                hovertemplate="<b>%{y}</b><br>Pérdida: %{x:$,.0f}<br>Turnos: %{customdata[0]:,.0f}<br>% total: %{customdata[1]:.1f}%<extra></extra>")
            fig_b.update_coloraxes(showscale=False)
            apply_plotly_defaults(fig_b, "Top 10 — pérdida por ausentismo profesional")
            fig_b.update_layout(height=420)
            st.plotly_chart(fig_b, use_container_width=True)
        with tab2:
            dt = grp.copy()
            dt['% del total']     = (dt['DINERO_PERDIDO'] / m['total_perd'] * 100).round(1).fillna(0)
            dt['Pérdida ($)']     = dt['DINERO_PERDIDO'].apply(lambda x: f"$ {x:,.0f}")
            dt['Turnos Perdidos'] = dt['TURNOS_PERDIDOS'].apply(lambda x: f"{x:,.0f}")
            st.dataframe(
                dt[['SERVICIO','Pérdida ($)','Turnos Perdidos','% del total']]
                    .style.bar(subset=['% del total'], color=ACCENT2, vmin=0, vmax=100),
                use_container_width=True, hide_index=True
            )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Simulador de estrategia ─────────────────────────────
    st.markdown('<div class="sec-title">🎯 Simulador de Estrategia de Recupero</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sec-sub">¿Cuánto dinero se recuperaría reduciendo el ausentismo del profesional?</div>', unsafe_allow_html=True)

    tipo_sim = st.radio("Alcance:", ["🏢  Global (todo CEMIC)", "🔬  Por servicio"], horizontal=True)

    if "Por servicio" in tipo_sim and not grp.empty:
        servicio_sel    = st.selectbox("Servicio a intervenir:", grp['SERVICIO'].tolist())
        base_calc       = grp[grp['SERVICIO']==servicio_sel]['DINERO_PERDIDO'].values[0]
        turnos_base     = grp[grp['SERVICIO']==servicio_sel]['TURNOS_PERDIDOS'].values[0]
        pct_sobre_total = (base_calc / m['total_perd'] * 100) if m['total_perd'] > 0 else 0
        st.markdown(f"""
        <div class="insight-box insight-box-amber">
            📌 <b>{servicio_sel}</b> — pérdida: <b>{fmt_millones(base_calc)}</b>
            ({turnos_base:,.0f} turnos · {pct_sobre_total:.1f}% del total).
        </div>
        """, unsafe_allow_html=True)
        texto_base = servicio_sel
    else:
        base_calc   = m['total_perd']
        turnos_base = m['turnos_perd']
        texto_base  = "todo CEMIC"

    col_sl, col_res = st.columns([3, 1])
    with col_sl:
        meta_pct = st.slider(f"¿Qué % de la pérdida de {texto_base} se puede recuperar?",
                             0, 100, 25, key="slider_rec")
        st.progress(meta_pct / 100)
    with col_res:
        dinero_rec = base_calc * (meta_pct / 100)
        turnos_rec = turnos_base * (meta_pct / 100)
        st.markdown(kpi_card("Ingreso Extra Estimado", dinero_rec,
                             delta_label=f"{turnos_rec:,.0f} turnos recuperados",
                             variant="success"), unsafe_allow_html=True)

    anual_rec = dinero_rec * 12
    cm, ca    = st.columns(2)
    cm.markdown(kpi_card("Impacto Mensual", dinero_rec, variant="success"), unsafe_allow_html=True)
    ca.markdown(kpi_card("Proyección Anual del Recupero", anual_rec, variant="success"), unsafe_allow_html=True)
    ca.caption("Si se mantiene la mejora los 12 meses")

    if "Por servicio" in tipo_sim and not grp.empty:
        impacto = (dinero_rec / m['total_perd'] * 100) if m['total_perd'] > 0 else 0
        st.markdown(f"""
        <div class="insight-box insight-box-teal" style="margin-top:12px;">
            💡 Gestionando solo <b>{servicio_sel}</b> al <b>{meta_pct}%</b>,
            se resuelve el <b>{impacto:.1f}%</b> del problema.
            Proyectado anualmente: <b>{fmt_millones(anual_rec)}</b>.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Evolución histórica ─────────────────────────────────
    st.markdown('<div class="sec-title">📈 Evolución Histórica</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sec-sub">Barras verdes oscuras = dato real · Barras transparentes = estimado por oferta · Línea = pérdida por ausentismo</div>', unsafe_allow_html=True)

    hist_rows = []
    for p in fechas_disp:
        try:
            do, da, dv, dt = filtrar(p)
            real = pd.Timestamp(p).to_period('M') in periodos_reales
            mh   = calcular_metricas(do, da, dv, dt if real else None)
            hist_rows.append({
                'Período'    : p, 'Label': fmt_fecha(p),
                'Facturación': mh['total_fact_real'] if (real and mh['total_fact_real']) else mh['total_base'],
                'Pérdida'    : mh['total_perd'],
                '% Fuga'     : mh['pct_fuga'],
                'Tasa Ocup'  : mh['tasa_ocup_prom'] if real else None,
                'es_real'    : real,
            })
        except:
            pass

    if len(hist_rows) >= 2:
        df_hist = pd.DataFrame(hist_rows).sort_values('Período')
        df_real = df_hist[df_hist['es_real']]
        df_est  = df_hist[~df_hist['es_real']]

        fig_evo = go.Figure()
        if not df_real.empty:
            fig_evo.add_trace(go.Bar(x=df_real['Label'], y=df_real['Facturación'],
                name='Facturación real', marker_color=ACCENT4, opacity=0.9, marker_line_width=0))
        if not df_est.empty:
            fig_evo.add_trace(go.Bar(x=df_est['Label'], y=df_est['Facturación'],
                name='Facturación estimada', marker_color=ACCENT4, opacity=0.3, marker_line_width=0))
        fig_evo.add_trace(go.Scatter(x=df_hist['Label'], y=df_hist['Pérdida'],
            name='Pérdida ausentismo', line=dict(color=ACCENT2, width=2), mode='lines+markers'))

        df_con_tasa = df_hist[df_hist['Tasa Ocup'].notna()]
        if not df_con_tasa.empty:
            fig_evo.add_trace(go.Scatter(x=df_con_tasa['Label'], y=df_con_tasa['Tasa Ocup'],
                name='Tasa ocupación %', yaxis='y2',
                line=dict(color=ACCENT3, width=2, dash='dot'), mode='lines+markers+text',
                text=df_con_tasa['Tasa Ocup'].apply(lambda x: f"{x:.0f}%"),
                textposition='top center'))

        apply_plotly_defaults(fig_evo, "Facturación y pérdida mensual")
        fig_evo.update_layout(barmode='overlay', height=360,
            yaxis2=dict(overlaying='y', side='right', showgrid=False,
                        title='Tasa Ocup %', color=ACCENT3, ticksuffix='%'))
        st.plotly_chart(fig_evo, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Detalle y exportación ───────────────────────────────
    with st.expander("📄 Ver detalle completo y exportar"):
        df_exp = m['df_perd'].copy()
        cols   = [c for c in ['FECHA_INICIO','SERVICIO','PROFESIONAL','_COL_TARGET',
                               'RENDIMIENTO_USADO','TURNOS_PERDIDOS','DINERO_PERDIDO'] if c in df_exp.columns]
        df_exp = df_exp[cols].sort_values('DINERO_PERDIDO', ascending=False)
        st.dataframe(df_exp.style.format({
            'DINERO_PERDIDO':'$ {:,.0f}','TURNOS_PERDIDOS':'{:,.0f}',
            '_COL_TARGET':'{:,.0f}','RENDIMIENTO_USADO':'{:,.0f}'}),
            use_container_width=True, hide_index=True)
        st.markdown("<br>", unsafe_allow_html=True)
        cx, cc, _ = st.columns([1,1,4])
        cx.download_button("⬇️ Excel", generar_excel(df_exp,"Pérdidas"),
            f"perdidas_{fmt_fecha(periodo_sel).replace(' ','_')}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        cc.download_button("⬇️ CSV", df_exp.to_csv(index=False).encode('utf-8'),
            f"perdidas_{fmt_fecha(periodo_sel).replace(' ','_')}.csv",
            "text/csv", use_container_width=True)

except Exception as e:
    st.error(f"❌ Error de cálculo: {e}")
    st.exception(e)
