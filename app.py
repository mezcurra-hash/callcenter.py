import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Simulador Financiero CEMIC", layout="wide", page_icon="💰")

# Estilos
st.markdown("""
<style>
    div[data-testid="stMetric"] { background-color: #1E1E1E; border: 1px solid #333; border-radius: 10px; padding: 15px; }
</style>
""", unsafe_allow_html=True)

st.title("💰 Simulador de Impacto Económico")
st.markdown("Cálculo de facturación potencial y pérdidas por ausentismo basado en valores parametrizados.")
st.markdown("---")

# ==============================================================================
# 1. CARGA DE DATOS (LAS 3 BASES)
# ==============================================================================
@st.cache_data
def cargar_datos_completo():
    # 1. OFERTA (Volumen Real)
    url_oferta = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQHFwl-Dxn-Rw9KN_evkCMk2Er8lQqgZMzAtN4LuEkWcCeBVUNwgb8xeIFKvpyxMgeGTeJ3oEWKpMZj/pub?gid=1524527213&single=true&output=csv"
    # 2. AUSENCIAS (Volumen Perdido)
    url_ausencias = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQHFwl-Dxn-Rw9KN_evkCMk2Er8lQqgZMzAtN4LuEkWcCeBVUNwgb8xeIFKvpyxMgeGTeJ3oEWKpMZj/pub?gid=2132722842&single=true&output=csv"
    # 3. VALORES (Precios y Rendimiento) -> ¡PEGA TU NUEVO LINK ACÁ ABAJO!
    url_valores = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQHFwl-Dxn-Rw9KN_evkCMk2Er8lQqgZMzAtN4LuEkWcCeBVUNwgb8xeIFKvpyxMgeGTeJ3oEWKpMZj/pub?gid=554651129&single=true&output=csv" 
    
    # Si no hay link, devolvemos error controlado
    if "PEGAR" in url_valores: return None, None, None

    df_of = pd.read_csv(url_oferta)
    df_au = pd.read_csv(url_ausencias)
    df_val = pd.read_csv(url_valores)
    
    # --- LIMPIEZA ---
    # Fechas
    df_of['PERIODO'] = pd.to_datetime(df_of['PERIODO'], dayfirst=True, errors='coerce')
    df_au['FECHA_INICIO'] = pd.to_datetime(df_au['FECHA_INICIO'], dayfirst=True, errors='coerce')
    df_val['PERIODO'] = pd.to_datetime(df_val['PERIODO'], dayfirst=True, errors='coerce')
    
    # Limpieza de columnas clave (Espacios, mayúsculas)
    for df in [df_of, df_au, df_val]:
        df.columns = df.columns.str.strip()
        if 'SERVICIO' in df.columns:
            df['SERVICIO'] = df['SERVICIO'].astype(str).str.strip().str.upper()

    # Limpieza de VALOR_TURNO (Sacar signos $ y puntos)
    if 'VALOR_TURNO' in df_val.columns:
        # Convertimos a string, sacamos $ y puntos, luego a número
        df_val['VALOR_TURNO'] = df_val['VALOR_TURNO'].astype(str).str.replace('$','', regex=False).str.replace('.','', regex=False)
        df_val['VALOR_TURNO'] = pd.to_numeric(df_val['VALOR_TURNO'], errors='coerce').fillna(0)
    
    # Limpieza de RENDIMIENTO
    if 'RENDIMIENTO' in df_val.columns:
        df_val['RENDIMIENTO'] = pd.to_numeric(df_val['RENDIMIENTO'], errors='coerce').fillna(14) # Default 14

    # Asegurar columna en ausencias
    col_target = 'CONSULTORIOS_REALES'
    if col_target not in df_au.columns: df_au[col_target] = df_au['DIAS_CAIDOS']
    df_au[col_target] = pd.to_numeric(df_au[col_target], errors='coerce').fillna(0)

    return df_of, df_au, df_val

try:
    df_oferta, df_ausencia, df_valores = cargar_datos_completo()

    if df_valores is None:
        st.error("⚠️ **Falta el Link de BD_VALORES.**")
        st.info("Por favor, publica tu nueva hoja de Google Sheets como CSV y pega el link en la línea 27 del código.")
        st.stop()

    # ==============================================================================
    # 2. FILTROS
    # ==============================================================================
    with st.sidebar:
        st.header("🎛️ Configuración Financiera")
        
        # Filtro Fecha (Basado en la hoja de Valores)
        fechas_disp = sorted(df_valores['PERIODO'].unique())
        periodo_sel = st.selectbox("Periodo a Analizar:", dates_disp, format_func=lambda x: x.strftime("%B %Y"))
        
        # Filtramos las bases por ese mes
        df_val_f = df_valores[df_valores['PERIODO'] == periodo_sel]
        df_of_f = df_oferta[(df_oferta['PERIODO'].dt.year == periodo_sel.year) & (df_oferta['PERIODO'].dt.month == periodo_sel.month)]
        df_au_f = df_ausencia[(df_ausencia['FECHA_INICIO'].dt.year == periodo_sel.year) & (df_ausencia['FECHA_INICIO'].dt.month == periodo_sel.month)]

        st.divider()
        
        # Opción para jugar con el rendimiento en vivo
        usar_slider = st.checkbox("¿Sobrescribir Rendimiento?", value=False)
        rend_manual = 14
        if usar_slider:
            rend_manual = st.slider("Pacientes por Consultorio (Global):", 1, 30, 14)

    # ==============================================================================
    # 3. EL CÁLCULO (CRUCE DE BASES) 🧠
    # ==============================================================================
    
    # Paso A: Unir precios a la Oferta Real
    # Usamos 'left' join para que si falta precio en algun servicio, no desaparezca el dato (quedará precio 0 o nulo)
    df_ingresos = df_of_f.merge(df_val_f[['SERVICIO', 'VALOR_TURNO']], on='SERVICIO', how='left')
    df_ingresos['VALOR_TURNO'] = df_ingresos['VALOR_TURNO'].fillna(0) # Servicios sin precio valen 0
    df_ingresos['FACTURACION_REAL'] = df_ingresos['TURNOS_MENSUAL'] * df_ingresos['VALOR_TURNO']

    # Paso B: Unir precios y rendimiento a las Ausencias
    df_perdidas = df_au_f.merge(df_val_f[['SERVICIO', 'VALOR_TURNO', 'RENDIMIENTO']], on='SERVICIO', how='left')
    df_perdidas['VALOR_TURNO'] = df_perdidas['VALOR_TURNO'].fillna(0)
    
    # Decidimos qué rendimiento usar (el del Excel o el del Slider)
    if usar_slider:
        df_perdidas['RENDIMIENTO_USADO'] = rend_manual
    else:
        df_perdidas['RENDIMIENTO_USADO'] = df_perdidas['RENDIMIENTO'].fillna(14)
        
    # Cálculo Clave: Consultorios * Pacientes * Precio
    df_perdidas['TURNOS_PERDIDOS'] = df_perdidas['CONSULTORIOS_REALES'] * df_perdidas['RENDIMIENTO_USADO']
    df_perdidas['DINERO_PERDIDO'] = df_perdidas['TURNOS_PERDIDOS'] * df_perdidas['VALOR_TURNO']

    # ==============================================================================
    # 4. DASHBOARD DE RESULTADOS
    # ==============================================================================
    
    # Totales Generales
    total_facturado = df_ingresos['FACTURACION_REAL'].sum()
    total_perdido = df_perdidas['DINERO_PERDIDO'].sum()
    total_potencial = total_facturado + total_perdido
    
    turnos_reales = df_ingresos['TURNOS_MENSUAL'].sum()
    turnos_perdidos = df_perdidas['TURNOS_PERDIDOS'].sum()

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Facturación Base (Oferta)", f"$ {total_facturado:,.0f}", f"{turnos_reales:,.0f} turnos")
    c2.metric("💸 Dinero Perdido (Ausentismo)", f"$ {total_perdido:,.0f}", f"-{turnos_perdidos:,.0f} turnos", delta_color="inverse")
    c3.metric("🚀 Potencial Total", f"$ {total_potencial:,.0f}", help="Facturación teórica si no hubiera habido ausencias")

    st.markdown("---")

    # Gráfico de Impacto por Servicio
    st.subheader("📊 Impacto Económico por Servicio")
    
    # Agrupamos por servicio para el gráfico
    # 1. Agrupar pérdidas
    grp_perdida = df_perdidas.groupby('SERVICIO')['DINERO_PERDIDO'].sum().reset_index()
    grp_perdida = grp_perdida.sort_values('DINERO_PERDIDO', ascending=True).tail(10) # Top 10 que más pierden
    
    fig = px.bar(grp_perdida, x='DINERO_PERDIDO', y='SERVICIO', orientation='h', 
                 title="Top 10 Servicios con Mayor Pérdida Económica", text_auto='.2s')
    fig.update_traces(marker_color='#FF5252') # Rojo alerta
    st.plotly_chart(fig, use_container_width=True)

    # Tabla de Detalle
    with st.expander("📄 Ver Detalle de Cálculo (Auditoría)"):
        st.write("Esta tabla muestra exactamente cómo se calculó la pérdida de cada médico:")
        cols_ver = ['FECHA_INICIO', 'PROFESIONAL', 'SERVICIO', 'CONSULTORIOS_REALES', 'RENDIMIENTO_USADO', 'VALOR_TURNO', 'DINERO_PERDIDO']
        st.dataframe(df_perdidas[cols_ver].sort_values('DINERO_PERDIDO', ascending=False).style.format({'DINERO_PERDIDO': '${:,.0f}', 'VALOR_TURNO': '${:,.0f}'}), use_container_width=True)

except Exception as e:
    st.error(f"Hubo un error de cálculo: {e}")
