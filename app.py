import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # Agregamos graph_objects para gráficos más pro

# Configuración de página
st.set_page_config(page_title="Simulador Financiero CEMIC", layout="wide", page_icon="💰")

# ==============================================================================
# 0. ESTILOS CSS ADAPTABLES (LIGHT/DARK MODE & MOBILE) 📱🌗
# ==============================================================================
st.markdown("""
<style>
    /* Ocultar elementos innecesarios */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* KPI CARDS ADAPTABLES */
    /* Usamos variables CSS (--...) para que cambien solas según el tema */
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color); 
        border: 1px solid var(--text-color);
        border-radius: 10px;
        padding: 15px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        opacity: 0.95;
        border-color: rgba(128, 128, 128, 0.2); /* Borde sutil */
    }

    /* Ajuste para móviles: achicar texto de métricas si la pantalla es chica */
    @media (max-width: 768px) {
        div[data-testid="stMetricValue"] { font-size: 1.5rem !important; }
        div[data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
    }
</style>
""", unsafe_allow_html=True)

st.title("💰 Simulador de Impacto Económico")
st.markdown("Cálculo de facturación potencial y pérdidas por ausentismo.")
st.markdown("---")

# ==============================================================================
# 1. CARGA DE DATOS
# ==============================================================================
@st.cache_data
def cargar_datos_completo():
    url_oferta = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQHFwl-Dxn-Rw9KN_evkCMk2Er8lQqgZMzAtN4LuEkWcCeBVUNwgb8xeIFKvpyxMgeGTeJ3oEWKpMZj/pub?gid=1524527213&single=true&output=csv"
    url_ausencias = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQHFwl-Dxn-Rw9KN_evkCMk2Er8lQqgZMzAtN4LuEkWcCeBVUNwgb8xeIFKvpyxMgeGTeJ3oEWKpMZj/pub?gid=2132722842&single=true&output=csv"
    url_valores = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQHFwl-Dxn-Rw9KN_evkCMk2Er8lQqgZMzAtN4LuEkWcCeBVUNwgb8xeIFKvpyxMgeGTeJ3oEWKpMZj/pub?gid=554651129&single=true&output=csv"
    
    df_of = pd.read_csv(url_oferta)
    df_au = pd.read_csv(url_ausencias)
    df_val = pd.read_csv(url_valores)
    
    # Limpieza
    df_of['PERIODO'] = pd.to_datetime(df_of['PERIODO'], dayfirst=True, errors='coerce')
    df_au['FECHA_INICIO'] = pd.to_datetime(df_au['FECHA_INICIO'], dayfirst=True, errors='coerce')
    df_val['PERIODO'] = pd.to_datetime(df_val['PERIODO'], dayfirst=True, errors='coerce')
    
    for df in [df_of, df_au, df_val]:
        df.columns = df.columns.str.strip()
        if 'SERVICIO' in df.columns:
            df['SERVICIO'] = df['SERVICIO'].astype(str).str.strip().str.upper()

    if 'VALOR_TURNO' in df_val.columns:
        df_val['VALOR_TURNO'] = pd.to_numeric(df_val['VALOR_TURNO'].astype(str).str.replace('$','', regex=False).str.replace('.','', regex=False), errors='coerce').fillna(0)
    
    if 'RENDIMIENTO' in df_val.columns:
        df_val['RENDIMIENTO'] = pd.to_numeric(df_val['RENDIMIENTO'], errors='coerce').fillna(14)

    col_target = 'CONSULTORIOS_REALES'
    if col_target not in df_au.columns: df_au[col_target] = df_au['DIAS_CAIDOS']
    df_au[col_target] = pd.to_numeric(df_au[col_target], errors='coerce').fillna(0)

    return df_of, df_au, df_val

try:
    df_oferta, df_ausencia, df_valores = cargar_datos_completo()

    # ==============================================================================
    # 2. FILTROS
    # ==============================================================================
    with st.sidebar:
        st.header("🎛️ Configuración")
        fechas_disp = sorted(df_valores['PERIODO'].unique())
        if not fechas_disp: st.error("Sin fechas."); st.stop()

        periodo_sel = st.selectbox("Periodo:", fechas_disp, format_func=lambda x: x.strftime("%B %Y"))
        
        # Filtros DataFrames
        df_val_f = df_valores[df_valores['PERIODO'] == periodo_sel]
        df_of_f = df_oferta[(df_oferta['PERIODO'].dt.year == periodo_sel.year) & (df_oferta['PERIODO'].dt.month == periodo_sel.month)]
        df_au_f = df_ausencia[(df_ausencia['FECHA_INICIO'].dt.year == periodo_sel.year) & (df_ausencia['FECHA_INICIO'].dt.month == periodo_sel.month)]

        st.divider()
        st.caption("🔧 Ajuste de Parámetros")
        usar_slider = st.checkbox("¿Ajustar Rendimiento?", value=False)
        rend_manual = 14
        if usar_slider:
            rend_manual = st.slider("Pacientes/Cons:", 1, 30, 14)

    # ==============================================================================
    # 3. CÁLCULOS
    # ==============================================================================
    df_ingresos = df_of_f.merge(df_val_f[['SERVICIO', 'VALOR_TURNO']], on='SERVICIO', how='left')
    df_ingresos['VALOR_TURNO'] = df_ingresos['VALOR_TURNO'].fillna(0)
    df_ingresos['FACTURACION_REAL'] = df_ingresos['TURNOS_MENSUAL'] * df_ingresos['VALOR_TURNO']

    df_perdidas = df_au_f.merge(df_val_f[['SERVICIO', 'VALOR_TURNO', 'RENDIMIENTO']], on='SERVICIO', how='left')
    df_perdidas['VALOR_TURNO'] = df_perdidas['VALOR_TURNO'].fillna(0)
    
    if usar_slider:
        df_perdidas['RENDIMIENTO_USADO'] = rend_manual
    else:
        df_perdidas['RENDIMIENTO_USADO'] = df_perdidas['RENDIMIENTO'].fillna(14)
        
    df_perdidas['TURNOS_PERDIDOS'] = df_perdidas['CONSULTORIOS_REALES'] * df_perdidas['RENDIMIENTO_USADO']
    df_perdidas['DINERO_PERDIDO'] = df_perdidas['TURNOS_PERDIDOS'] * df_perdidas['VALOR_TURNO']

    # KPI MACRO
    total_facturado = df_ingresos['FACTURACION_REAL'].sum()
    total_perdido = df_perdidas['DINERO_PERDIDO'].sum()
    total_potencial = total_facturado + total_perdido
    
    turnos_reales = df_ingresos['TURNOS_MENSUAL'].sum()
    turnos_totales_perdidos = df_perdidas['TURNOS_PERDIDOS'].sum()
    
    pct_fuga = (total_perdido / total_potencial * 100) if total_potencial > 0 else 0
    proyeccion_anual = total_perdido * 12

    # ==============================================================================
    # 4. VISUALIZACIÓN
    # ==============================================================================
    
    # A. SEMÁFORO (KPIs)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("💰 Facturación Base", f"$ {total_facturado:,.0f}", f"{turnos_reales:,.0f} Turnos")
    kpi2.metric("💸 Dinero Perdido", f"$ {total_perdido:,.0f}", f"-{turnos_totales_perdidos:,.0f} Turnos ({pct_fuga:.1f}%)", delta_color="inverse")
    kpi3.metric("🚀 Potencial Total", f"$ {total_potencial:,.0f}", help="Escenario ideal")
    kpi4.metric("📅 Proy. Anual Pérdida", f"$ {proyeccion_anual:,.0f}", "Tendencia 12 meses", delta_color="inverse")

    st.markdown("---")

    # ... (Aquí sigue la sección B: st.info("🎯 Estrategia de Recupero..."))
    # B. SIMULADOR Y RECUPERO
    st.info("🎯 **Estrategia de Recupero:** Simulador de impacto financiero por gestión.")
    
    meta_recupero = st.slider("Si recuperamos el X% de las ausencias:", 0, 100, 50, key="slider_meta")
    dinero_recuperable = total_perdido * (meta_recupero / 100)
    
    c_sim1, c_sim2 = st.columns([1, 3])
    with c_sim1:
        st.metric(f"💰 Recupero ({meta_recupero}%)", f"$ {dinero_recuperable:,.0f}")
    with c_sim2:
        # Barra de progreso visual
        st.progress(meta_recupero / 100)
        st.caption(f"Ingreso Adicional Estimado: **$ {dinero_recuperable:,.0f}**")

    st.markdown("---")

    # C. GRÁFICO DE IMPACTO (BARRAS)
    st.subheader("📊 Fuga de Dinero por Servicio (Top 10)")
    
    grp_perdida = df_perdidas.groupby('SERVICIO')[['DINERO_PERDIDO', 'TURNOS_PERDIDOS']].sum().reset_index()
    grp_perdida = grp_perdida.sort_values('DINERO_PERDIDO', ascending=True).tail(10)
    
    # Etiqueta inteligente
    def formato_texto(row):
        millones = row['DINERO_PERDIDO'] / 1000000
        return f"$ {millones:.1f}M"

    grp_perdida['ETIQUETA'] = grp_perdida.apply(formato_texto, axis=1)
    
    fig = px.bar(grp_perdida, x='DINERO_PERDIDO', y='SERVICIO', orientation='h', 
                 text='ETIQUETA', 
                 hover_data=['TURNOS_PERDIDOS'])
    
    fig.update_traces(marker_color='#FF5252', textposition='inside')
    fig.update_layout(xaxis_title="Pérdida ($)", yaxis_title=None, height=500)
    st.plotly_chart(fig, use_container_width=True)

    # D. DETALLE
    with st.expander("📄 Ver Detalle de Pérdidas"):
        st.dataframe(df_perdidas[['FECHA_INICIO', 'SERVICIO', 'PROFESIONAL', 'TURNOS_PERDIDOS', 'DINERO_PERDIDO']].sort_values('DINERO_PERDIDO', ascending=False).style.format({'DINERO_PERDIDO': '${:,.0f}', 'TURNOS_PERDIDOS': '{:,.0f}'}), use_container_width=True)

except Exception as e:
    st.error(f"Error de cálculo: {e}")
