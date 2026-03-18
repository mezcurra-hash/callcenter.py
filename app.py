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
# SISTEMA DE DISEÑO — IDÉNTICO AL TABLERO PRINCIPAL
# ============================================================
ACCENT      = "#00BFA5"
ACCENT2     = "#FF6B6B"
ACCENT3     = "#FFB74D"
ACCENT4     = "#69F0AE"   # Verde más suave para positivos financieros
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
      background-color: #171925 !important;
      border-right: 1px solid {BORDER};
  }}
  [data-testid="stSidebar"] label {{
      font-size: 11px; font-weight: 600;
      letter-spacing: 0.08em; text-transform: uppercase;
      color: {TEXT_MUTED} !important;
  }}

  /* KPI cards */
  .kpi-card {{
      background: {CARD_BG}; border: 1px solid {BORDER};
      border-radius: 12px; padding: 18px 20px;
      position: relative; overflow: hidden;
  }}
  .kpi-card::before {{
      content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
      background: linear-gradient(90deg, {ACCENT}, {BLUE_LIGHT});
  }}
  .kpi-card-danger::before {{
      background: linear-gradient(90deg, {ACCENT2}, #FF3333);
  }}
  .kpi-card-warning::before {{
      background: linear-gradient(90deg, {ACCENT3}, #FF8F00);
  }}
  .kpi-card-success::before {{
      background: linear-gradient(90deg, {ACCENT4}, {ACCENT});
  }}
  .kpi-label {{
      font-size: 11px; font-weight: 600; letter-spacing: 0.1em;
      text-transform: uppercase; color: {TEXT_MUTED}; margin-bottom: 6px;
  }}
  .kpi-value {{
      font-size: 28px; font-weight: 700; color: #CDD6F4;
      font-family: 'DM Mono', monospace; line-height: 1;
  }}
  .kpi-delta-pos  {{ font-size: 12px; font-weight: 500; color: {ACCENT4}; margin-top: 5px; }}
  .kpi-delta-neg  {{ font-size: 12px; font-weight: 500; color: {ACCENT2}; margin-top: 5px; }}
  .kpi-delta-neu  {{ font-size: 12px; font-weight: 500; color: {ACCENT3}; margin-top: 5px; }}
  .kpi-help       {{ font-size: 11px; color: {TEXT_MUTED}; margin-top: 4px; }}

  /* Section titles */
  .sec-title {{
      font-size: 20px; font-weight: 700; color: #CDD6F4; margin-bottom: 4px;
  }}
  .sec-sub {{
      font-size: 13px; color: {TEXT_MUTED}; margin-bottom: 16px;
  }}
  .badge {{
      display: inline-block; background: rgba(0,191,165,0.15);
      color: {ACCENT}; border: 1px solid rgba(0,191,165,0.3);
      border-radius: 20px; padding: 2px 10px;
      font-size: 12px; font-weight: 600;
  }}
  .badge-red {{
      background: rgba(255,107,107,0.15); color: {ACCENT2};
      border-color: rgba(255,107,107,0.3);
  }}
  .badge-amber {{
      background: rgba(255,183,77,0.15); color: {ACCENT3};
      border-color: rgba(255,183,77,0.3);
  }}

  /* Insight box */
  .insight-box {{
      background: rgba(255,107,107,0.08); border: 1px solid rgba(255,107,107,0.25);
      border-left: 4px solid {ACCENT2}; border-radius: 8px;
      padding: 12px 16px; margin: 12px 0; font-size: 13px; color: #CDD6F4;
  }}
  .insight-box-teal {{
      background: rgba(0,191,165,0.08); border: 1px solid rgba(0,191,165,0.25);
      border-left: 4px solid {ACCENT};
  }}
  .insight-box-amber {{
      background: rgba(255,183,77,0.08); border: 1px solid rgba(255,183,77,0.25);
      border-left: 4px solid {ACCENT3};
  }}

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {{
      background: {CARD_BG}; border-radius: 8px; padding: 4px;
      gap: 4px; border: 1px solid {BORDER};
  }}
  .stTabs [data-baseweb="tab"] {{
      border-radius: 6px; font-size: 13px; font-weight: 500; color: {TEXT_MUTED};
  }}
  .stTabs [aria-selected="true"] {{
      background-color: {ACCENT} !important; color: #13151F !important; font-weight: 700;
  }}

  hr {{ border-color: {BORDER} !important; opacity: 0.5; }}

  [data-testid="stExpander"] {{
      background: {CARD_BG}; border: 1px solid {BORDER} !important; border-radius: 10px;
  }}
  div[data-testid="stMetric"] {{
      background-color: {CARD_BG}; border: 1px solid {BORDER};
      padding: 14px 18px; border-radius: 12px;
  }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# HELPERS
# ============================================================
def fmt_pesos(n):
    """Formatea como $ 1.234.567 en español."""
    s = f"{abs(n):,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"$ {s}" if n >= 0 else f"- $ {s}"

def fmt_millones(n):
    if abs(n) >= 1_000_000_000:
        return f"$ {n/1e9:.1f}B"
    elif abs(n) >= 1_000_000:
        return f"$ {n/1e6:.1f}M"
    return fmt_pesos(n)

def fmt_fecha(ts):
    return f"{MESES_FULL[ts.month]} {ts.year}"

def kpi_card(label, value, delta=None, delta_label=None, help_text=None,
             variant="default", fmt_fn=fmt_pesos):
    val_str = fmt_fn(value)
    delta_html = ""
    if delta is not None:
        sign = "+" if delta >= 0 else ""
        cls  = "kpi-delta-pos" if delta > 0 else ("kpi-delta-neg" if delta < 0 else "kpi-delta-neu")
        icon = "▲" if delta > 0 else ("▼" if delta < 0 else "●")
        lbl  = delta_label if delta_label else f"{sign}{fmt_fn(delta)}"
        delta_html = f'<div class="{cls}">{icon} {lbl}</div>'
    help_html = f'<div class="kpi-help">{help_text}</div>' if help_text else ""
    card_cls = f"kpi-card kpi-card-{variant}" if variant != "default" else "kpi-card"
    return f"""
    <div class="{card_cls}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{val_str}</div>
        {delta_html}
        {help_html}
    </div>"""

def apply_plotly_defaults(fig, title=""):
    fig.update_layout(**PLOTLY_LAYOUT)
    if title:
        fig.update_layout(title=dict(text=title, font=dict(size=14, color="#CDD6F4"),
                                     x=0, xanchor="left"))
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor=BORDER, zeroline=False)
    return fig

def generar_excel(df: pd.DataFrame, nombre_hoja: str = "Datos") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=nombre_hoja[:31], index=False)
    return buf.getvalue()

# ============================================================
# CARGA DE DATOS
# ============================================================
@st.cache_data(ttl=300)
def cargar_datos():
    url_oferta   = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQHFwl-Dxn-Rw9KN_evkCMk2Er8lQqgZMzAtN4LuEkWcCeBVUNwgb8xeIFKvpyxMgeGTeJ3oEWKpMZj/pub?gid=1524527213&single=true&output=csv"
    url_ausencias = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQHFwl-Dxn-Rw9KN_evkCMk2Er8lQqgZMzAtN4LuEkWcCeBVUNwgb8xeIFKvpyxMgeGTeJ3oEWKpMZj/pub?gid=2132722842&single=true&output=csv"
    url_valores  = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQHFwl-Dxn-Rw9KN_evkCMk2Er8lQqgZMzAtN4LuEkWcCeBVUNwgb8xeIFKvpyxMgeGTeJ3oEWKpMZj/pub?gid=554651129&single=true&output=csv"

    df_of  = pd.read_csv(url_oferta)
    df_au  = pd.read_csv(url_ausencias)
    df_val = pd.read_csv(url_valores)

    for df in [df_of, df_au, df_val]:
        df.columns = df.columns.str.strip()
        for col in ['SERVICIO','DEPARTAMENTO']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper()

    df_of['PERIODO']        = pd.to_datetime(df_of['PERIODO'],        dayfirst=True, errors='coerce')
    df_au['FECHA_INICIO']   = pd.to_datetime(df_au['FECHA_INICIO'],   dayfirst=True, errors='coerce')
    df_val['PERIODO']       = pd.to_datetime(df_val['PERIODO'],       dayfirst=True, errors='coerce')

    if 'VALOR_TURNO' in df_val.columns:
        df_val['VALOR_TURNO'] = pd.to_numeric(
            df_val['VALOR_TURNO'].astype(str)
                .str.replace('$','',regex=False)
                .str.replace('.','',regex=False)
                .str.replace(',','.',regex=False),
            errors='coerce').fillna(0)

    if 'RENDIMIENTO' in df_val.columns:
        df_val['RENDIMIENTO'] = pd.to_numeric(df_val['RENDIMIENTO'], errors='coerce').fillna(14)

    col_target = 'CONSULTORIOS_REALES' if 'CONSULTORIOS_REALES' in df_au.columns else 'DIAS_CAIDOS'
    df_au[col_target] = pd.to_numeric(df_au[col_target], errors='coerce').fillna(0)
    df_au['_COL_TARGET'] = df_au[col_target]

    # ── Limpieza global de NaN ──────────────────────────────
    # Columnas numéricas: rellenar con 0
    for df in [df_of, df_au, df_val]:
        num_cols = df.select_dtypes(include='number').columns
        df[num_cols] = df[num_cols].fillna(0)
        # Columnas de texto: rellenar con string vacío
        str_cols = df.select_dtypes(include='object').columns
        df[str_cols] = df[str_cols].fillna('')

    return df_of, df_au, df_val

# ============================================================
# SIDEBAR
# ============================================================
try:
    df_oferta, df_ausencia, df_valores = cargar_datos()
except Exception as e:
    st.error(f"❌ Error cargando datos: {e}")
    st.stop()

with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding:10px 0 20px 0;">
        <img src="https://cemic.edu.ar/assets/img/logo/logo-cemic.png" width="120"
             style="filter:brightness(1.1);">
        <div style="font-size:10px; letter-spacing:0.15em; color:{TEXT_MUTED};
                    text-transform:uppercase; margin-top:8px; font-weight:600;">
            Simulador Financiero
        </div>
    </div>
    """, unsafe_allow_html=True)

    fechas_disp = sorted(df_valores['PERIODO'].dropna().unique())
    if not fechas_disp:
        st.error("Sin períodos disponibles.")
        st.stop()

    periodo_sel = st.selectbox(
        "PERÍODO",
        fechas_disp,
        index=len(fechas_disp)-1,
        format_func=fmt_fecha
    )

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:8px;'>PARÁMETROS</div>", unsafe_allow_html=True)
    usar_slider = st.checkbox("Ajustar rendimiento manualmente", value=False)
    rend_manual = 14
    if usar_slider:
        rend_manual = st.slider("Pacientes por consultorio:", 1, 30, 14)
        st.caption(f"Valor actual del dataset: 14 prom. · Ajustado: **{rend_manual}**")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:11px;color:{TEXT_MUTED};'>Datos actualizados cada 5 min.</div>", unsafe_allow_html=True)

# ============================================================
# FILTRADO DE DATOS
# ============================================================
df_val_f = df_valores[df_valores['PERIODO'] == periodo_sel]
df_of_f  = df_oferta[
    (df_oferta['PERIODO'].dt.year  == periodo_sel.year) &
    (df_oferta['PERIODO'].dt.month == periodo_sel.month)
]
df_au_f  = df_ausencia[
    (df_ausencia['FECHA_INICIO'].dt.year  == periodo_sel.year) &
    (df_ausencia['FECHA_INICIO'].dt.month == periodo_sel.month)
]

# Período anterior para deltas
idx_ant = fechas_disp.index(periodo_sel) - 1 if fechas_disp.index(periodo_sel) > 0 else None
if idx_ant is not None:
    periodo_ant = fechas_disp[idx_ant]
    df_val_ant  = df_valores[df_valores['PERIODO'] == periodo_ant]
    df_of_ant   = df_oferta[
        (df_oferta['PERIODO'].dt.year  == periodo_ant.year) &
        (df_oferta['PERIODO'].dt.month == periodo_ant.month)
    ]
    df_au_ant   = df_ausencia[
        (df_ausencia['FECHA_INICIO'].dt.year  == periodo_ant.year) &
        (df_ausencia['FECHA_INICIO'].dt.month == periodo_ant.month)
    ]
else:
    periodo_ant = df_val_ant = df_of_ant = df_au_ant = None

# ============================================================
# CÁLCULOS PRINCIPALES
# ============================================================
def calcular_metricas(df_of, df_au, df_val, rend_override=None):
    df_ing = df_of.merge(df_val[['SERVICIO','VALOR_TURNO']], on='SERVICIO', how='left')
    df_ing['VALOR_TURNO']     = df_ing['VALOR_TURNO'].fillna(0)
    df_ing['FACTURACION_REAL'] = df_ing['TURNOS_MENSUAL'] * df_ing['VALOR_TURNO']

    df_perd = df_au.merge(df_val[['SERVICIO','VALOR_TURNO','RENDIMIENTO']], on='SERVICIO', how='left')
    df_perd['VALOR_TURNO']  = df_perd['VALOR_TURNO'].fillna(0)
    df_perd['RENDIMIENTO_USADO'] = rend_override if rend_override else df_perd['RENDIMIENTO'].fillna(14)
    df_perd['TURNOS_PERDIDOS'] = df_perd['_COL_TARGET'] * df_perd['RENDIMIENTO_USADO']
    df_perd['DINERO_PERDIDO']  = df_perd['TURNOS_PERDIDOS'] * df_perd['VALOR_TURNO']

    total_fact  = df_ing['FACTURACION_REAL'].sum()
    total_perd  = df_perd['DINERO_PERDIDO'].sum()
    total_pot   = total_fact + total_perd
    turnos_real = df_ing['TURNOS_MENSUAL'].sum()
    turnos_perd = df_perd['TURNOS_PERDIDOS'].sum()
    pct_fuga    = (total_perd / total_pot * 100) if total_pot > 0 else 0

    return dict(
        total_fact=total_fact, total_perd=total_perd, total_pot=total_pot,
        turnos_real=turnos_real, turnos_perd=turnos_perd, pct_fuga=pct_fuga,
        df_ing=df_ing, df_perd=df_perd
    )

try:
    m = calcular_metricas(df_of_f, df_au_f, df_val_f,
                          rend_override=rend_manual if usar_slider else None)

    m_ant = None
    if periodo_ant is not None:
        try:
            m_ant = calcular_metricas(df_of_ant, df_au_ant, df_val_ant)
        except:
            m_ant = None

    # ============================================================
    # ENCABEZADO
    # ============================================================
    st.markdown(f"""
    <div style="display:flex; align-items:baseline; gap:12px; margin-bottom:4px;">
        <span style="font-size:26px; font-weight:700; color:#CDD6F4;">💰 Simulador de Impacto Económico</span>
    </div>
    <div style="font-size:13px; color:{TEXT_MUTED}; margin-bottom:20px;">
        Período analizado · <span class="badge">{fmt_fecha(periodo_sel)}</span>
        {"&nbsp;&nbsp;vs&nbsp;&nbsp;<span style='color:"+TEXT_MUTED+"'>"+fmt_fecha(periodo_ant)+"</span>" if periodo_ant else ""}
    </div>
    """, unsafe_allow_html=True)

    # ============================================================
    # KPIs PRINCIPALES
    # ============================================================
    c1, c2, c3, c4 = st.columns(4)

    d_fact = (m['total_fact'] - m_ant['total_fact']) if m_ant else None
    d_perd = (m['total_perd'] - m_ant['total_perd']) if m_ant else None

    c1.markdown(kpi_card(
        "💰 Facturación Base", m['total_fact'],
        delta=d_fact,
        delta_label=f"{'+' if d_fact and d_fact>=0 else ''}{fmt_millones(d_fact) if d_fact else ''} vs {fmt_fecha(periodo_ant) if periodo_ant else ''}",
        variant="success"
    ), unsafe_allow_html=True)
    c1.caption(f"{m['turnos_real']:,.0f} turnos × valor por servicio")

    c2.markdown(kpi_card(
        "💸 Dinero No Ingresado", m['total_perd'],
        delta=d_perd,
        delta_label=f"{'+' if d_perd and d_perd>=0 else ''}{fmt_millones(d_perd) if d_perd else ''} vs {fmt_fecha(periodo_ant) if periodo_ant else ''}",
        variant="danger"
    ), unsafe_allow_html=True)
    c2.caption(f"{m['turnos_perd']:,.0f} turnos perdidos · {m['pct_fuga']:.1f}% del potencial")

    c3.markdown(kpi_card(
        "🚀 Potencial Total", m['total_pot'],
        variant="default"
    ), unsafe_allow_html=True)
    c3.caption("Escenario ideal sin ausentismo")

    c4.markdown(kpi_card(
        "📅 Proyección Anual Pérdida", m['total_perd'] * 12,
        variant="warning"
    ), unsafe_allow_html=True)
    c4.caption("Si el ausentismo de este mes se mantiene 12 meses")

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    # GRÁFICO WATERFALL
    # ============================================================
    st.markdown('<div class="sec-title">📊 Composición Financiera del Período</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sec-sub">Del potencial total disponible, ¿cuánto se perdió y cuánto se facturó?</div>', unsafe_allow_html=True)

    # Lógica: Potencial → resta Pérdida → llega a Facturación Real
    fig_wf = go.Figure(go.Waterfall(
        name="",
        orientation="v",
        measure=["absolute", "relative", "total"],
        x=["Potencial\nTotal", "Pérdida por\nAusentismo", "Facturación\nRealizada"],
        y=[m['total_pot'], -m['total_perd'], 0],
        text=[fmt_millones(m['total_pot']),
              f"- {fmt_millones(m['total_perd'])}",
              fmt_millones(m['total_fact'])],
        textposition="outside",
        connector=dict(line=dict(color=BORDER, width=1, dash="dot")),
        increasing=dict(marker=dict(color=BLUE_LIGHT)),
        decreasing=dict(marker=dict(color=ACCENT2, line=dict(color=ACCENT2, width=1))),
        totals=dict(marker=dict(color=ACCENT4, line=dict(color=ACCENT4, width=1))),
        textfont=dict(size=13, color="#CDD6F4"),
    ))
    apply_plotly_defaults(fig_wf)
    fig_wf.update_layout(
        height=340, showlegend=False,
        yaxis=dict(tickformat="$.3s"),
    )
    st.plotly_chart(fig_wf, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ============================================================
    # ANÁLISIS DE FUGA — TOP SERVICIOS
    # ============================================================
    st.markdown('<div class="sec-title">📉 Fuga de Dinero por Servicio</div>', unsafe_allow_html=True)

    grp = m['df_perd'].groupby('SERVICIO')[['DINERO_PERDIDO','TURNOS_PERDIDOS']].sum().reset_index()
    grp = grp[grp['DINERO_PERDIDO'] > 0].sort_values('DINERO_PERDIDO', ascending=False)

    if grp.empty:
        st.info("Sin pérdidas registradas para este período.")
    else:
        # Insight de Pareto
        top3 = grp.head(3)
        pct_pareto = (top3['DINERO_PERDIDO'].sum() / m['total_perd'] * 100) if m['total_perd'] > 0 else 0
        nombres_top3 = ", ".join(top3['SERVICIO'].tolist())

        st.markdown(f"""
        <div class="insight-box">
            ⚠️ <b>Regla de Pareto:</b> El <b>{pct_pareto:.0f}%</b> de toda la pérdida financiera
            se concentra en solo 3 servicios: <b>{nombres_top3}</b>.
            Intervenir únicamente esos 3 resuelve el grueso del problema.
        </div>
        """, unsafe_allow_html=True)

        tab_top10, tab_todos = st.tabs(["📊  Top 10 servicios", "📋  Todos los servicios"])

        with tab_top10:
            top10 = grp.head(10).sort_values('DINERO_PERDIDO', ascending=True)
            top10['etiqueta'] = top10['DINERO_PERDIDO'].apply(fmt_millones)
            top10['pct'] = (top10['DINERO_PERDIDO'] / m['total_perd'] * 100).round(1)

            fig_bar = px.bar(
                top10, x='DINERO_PERDIDO', y='SERVICIO', orientation='h',
                text='etiqueta', color='DINERO_PERDIDO',
                color_continuous_scale=[[0, "#FF8A65"],[0.5, ACCENT2],[1, "#B71C1C"]],
                custom_data=['TURNOS_PERDIDOS','pct']
            )
            fig_bar.update_traces(
                textposition='outside', marker_line_width=0,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Pérdida: %{x:$,.0f}<br>"
                    "Turnos perdidos: %{customdata[0]:,.0f}<br>"
                    "% del total: %{customdata[1]:.1f}%"
                    "<extra></extra>"
                )
            )
            fig_bar.update_coloraxes(showscale=False)
            apply_plotly_defaults(fig_bar, "Top 10 servicios con mayor pérdida financiera")
            fig_bar.update_layout(height=420)
            st.plotly_chart(fig_bar, use_container_width=True)

        with tab_todos:
            df_tabla = grp.copy()
            df_tabla['% del total']     = (df_tabla['DINERO_PERDIDO'] / m['total_perd'] * 100).round(1).fillna(0)
            df_tabla['Pérdida ($)']     = df_tabla['DINERO_PERDIDO'].apply(lambda x: f"$ {x:,.0f}")
            df_tabla['Turnos Perdidos'] = df_tabla['TURNOS_PERDIDOS'].apply(lambda x: f"{x:,.0f}")
            df_show = df_tabla[['SERVICIO','Pérdida ($)','Turnos Perdidos','% del total']].copy()
            st.dataframe(
                df_show.style.bar(subset=['% del total'], color=ACCENT2, vmin=0, vmax=100),
                use_container_width=True, hide_index=True
            )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ============================================================
    # SIMULADOR DE ESTRATEGIA
    # ============================================================
    st.markdown('<div class="sec-title">🎯 Simulador de Estrategia de Recupero</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sec-sub">¿Cuánto dinero se recuperaría si se gestionara el ausentismo?</div>', unsafe_allow_html=True)

    tipo_sim = st.radio(
        "Alcance:",
        ["🏢  Global (todo CEMIC)", "🔬  Por servicio"],
        horizontal=True
    )

    if "Por servicio" in tipo_sim and not grp.empty:
        servicios_lista = grp['SERVICIO'].tolist()
        servicio_sel = st.selectbox("Servicio a intervenir:", servicios_lista)
        base_calc    = grp[grp['SERVICIO'] == servicio_sel]['DINERO_PERDIDO'].values[0]
        turnos_base  = grp[grp['SERVICIO'] == servicio_sel]['TURNOS_PERDIDOS'].values[0]
        pct_sobre_total = (base_calc / m['total_perd'] * 100) if m['total_perd'] > 0 else 0
        st.markdown(f"""
        <div class="insight-box insight-box-amber">
            📌 <b>{servicio_sel}</b> representa una fuga de <b>{fmt_millones(base_calc)}</b>
            ({turnos_base:,.0f} turnos · {pct_sobre_total:.1f}% del total institucional).
        </div>
        """, unsafe_allow_html=True)
        texto_base = servicio_sel
    else:
        base_calc   = m['total_perd']
        turnos_base = m['turnos_perd']
        texto_base  = "todo CEMIC"

    col_sl, col_res = st.columns([3, 1])

    with col_sl:
        meta_pct = st.slider(
            f"¿Qué % de la pérdida de {texto_base} se puede recuperar?",
            0, 100, 25, key="slider_recupero"
        )
        st.progress(meta_pct / 100)

    with col_res:
        dinero_rec  = base_calc * (meta_pct / 100)
        turnos_rec  = turnos_base * (meta_pct / 100)
        st.markdown(kpi_card(
            "Ingreso Extra Estimado",
            dinero_rec,
            delta_label=f"{turnos_rec:,.0f} turnos recuperados",
            variant="success"
        ), unsafe_allow_html=True)

    # Proyección anual del recupero
    anual_rec = dinero_rec * 12
    col_m, col_a = st.columns(2)
    col_m.markdown(kpi_card("Impacto Mensual", dinero_rec, variant="success"), unsafe_allow_html=True)
    col_a.markdown(kpi_card("Proyección Anual del Recupero", anual_rec, variant="success"), unsafe_allow_html=True)
    col_a.caption("Si se mantiene la mejora los 12 meses")

    if "Por servicio" in tipo_sim and not grp.empty:
        impacto = (dinero_rec / m['total_perd'] * 100) if m['total_perd'] > 0 else 0
        st.markdown(f"""
        <div class="insight-box insight-box-teal" style="margin-top:12px;">
            💡 Gestionando solo <b>{servicio_sel}</b> al <b>{meta_pct}%</b>,
            se resuelve el <b>{impacto:.1f}%</b> del problema financiero total del hospital.
            Proyectado anualmente: <b>{fmt_millones(anual_rec)}</b>.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ============================================================
    # EVOLUCIÓN HISTÓRICA DE PÉRDIDAS
    # ============================================================
    st.markdown('<div class="sec-title">📈 Evolución Histórica de Pérdida Financiera</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sec-sub">Tendencia mensual del dinero no ingresado por ausentismo</div>', unsafe_allow_html=True)

    # Recalcular para todos los períodos disponibles
    hist_rows = []
    for p in fechas_disp:
        try:
            dv = df_valores[df_valores['PERIODO'] == p]
            do = df_oferta[(df_oferta['PERIODO'].dt.year==p.year) & (df_oferta['PERIODO'].dt.month==p.month)]
            da = df_ausencia[(df_ausencia['FECHA_INICIO'].dt.year==p.year) & (df_ausencia['FECHA_INICIO'].dt.month==p.month)]
            mh = calcular_metricas(do, da, dv)
            hist_rows.append({
                'Período': p,
                'Pérdida': mh['total_perd'],
                'Facturación': mh['total_fact'],
                '% Fuga': mh['pct_fuga'],
            })
        except:
            pass

    if len(hist_rows) >= 2:
        df_hist = pd.DataFrame(hist_rows).sort_values('Período')
        df_hist['Label'] = df_hist['Período'].apply(fmt_fecha)

        fig_evo = go.Figure()
        fig_evo.add_trace(go.Scatter(
            x=df_hist['Label'], y=df_hist['Facturación'],
            name='Facturación', fill='tozeroy',
            line=dict(color=ACCENT4, width=2),
            fillcolor='rgba(105,240,174,0.1)',
        ))
        fig_evo.add_trace(go.Scatter(
            x=df_hist['Label'], y=df_hist['Pérdida'],
            name='Pérdida', fill='tozeroy',
            line=dict(color=ACCENT2, width=2),
            fillcolor='rgba(255,107,107,0.15)',
        ))
        fig_evo.add_trace(go.Scatter(
            x=df_hist['Label'], y=df_hist['% Fuga'],
            name='% Fuga', yaxis='y2',
            line=dict(color=ACCENT3, width=2, dash='dot'),
            mode='lines+markers',
        ))
        apply_plotly_defaults(fig_evo, "Facturación vs Pérdida mensual")
        fig_evo.update_layout(
            height=320,
            yaxis2=dict(overlaying='y', side='right', showgrid=False,
                        title='% Fuga', color=ACCENT3, ticksuffix='%'),
        )
        st.plotly_chart(fig_evo, use_container_width=True)
    else:
        st.info("Se necesitan al menos 2 períodos cargados para mostrar la evolución.")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ============================================================
    # DETALLE Y EXPORTACIÓN
    # ============================================================
    with st.expander("📄 Ver detalle completo y exportar"):
        df_export = m['df_perd'][['FECHA_INICIO','SERVICIO','PROFESIONAL' if 'PROFESIONAL' in m['df_perd'].columns else 'SERVICIO',
                                   'TURNOS_PERDIDOS','DINERO_PERDIDO']].copy()
        # Renombrar columnas duplicadas si es necesario
        df_export = m['df_perd'].copy()
        cols_mostrar = [c for c in ['FECHA_INICIO','SERVICIO','PROFESIONAL','_COL_TARGET',
                                     'RENDIMIENTO_USADO','TURNOS_PERDIDOS','DINERO_PERDIDO']
                        if c in df_export.columns]
        df_export = df_export[cols_mostrar].sort_values('DINERO_PERDIDO', ascending=False)

        st.dataframe(
            df_export.style.format({
                'DINERO_PERDIDO': '$ {:,.0f}',
                'TURNOS_PERDIDOS': '{:,.0f}',
                '_COL_TARGET': '{:,.0f}',
                'RENDIMIENTO_USADO': '{:,.0f}',
            }),
            use_container_width=True, hide_index=True
        )

        st.markdown("<br>", unsafe_allow_html=True)
        col_dl1, col_dl2, _ = st.columns([1, 1, 4])

        excel_bytes = generar_excel(df_export, "Pérdidas")
        col_dl1.download_button(
            label="⬇️ Excel",
            data=excel_bytes,
            file_name=f"perdidas_cemic_{fmt_fecha(periodo_sel).replace(' ','_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        csv_bytes = df_export.to_csv(index=False).encode('utf-8')
        col_dl2.download_button(
            label="⬇️ CSV",
            data=csv_bytes,
            file_name=f"perdidas_cemic_{fmt_fecha(periodo_sel).replace(' ','_')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

except Exception as e:
    st.error(f"❌ Error de cálculo: {e}")
    st.exception(e)
