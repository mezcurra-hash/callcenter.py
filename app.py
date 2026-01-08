import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Llamados/Turnos - Call Center", layout="wide", page_icon="🎧")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stMetricDelta"] svg { display: inline; }
    /* Estilo Tarjeta Oscura */
    div[data-testid="stMetric"] {
        background-color: #262730;
        border: 1px solid #464b5f;
        padding: 10px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Cabecera
col1, col2 = st.columns([1, 6])
with col1:
    # st.image("logo.png", width=90)
    st.write("🎧") 
with col2:
    st.title("Call Center - CEMIC")
st.markdown("---")

# --- 1. CARGA Y LIMPIEZA DE DATOS ---
@st.cache_data
def cargar_datos():
    url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTOxpr7RRNTLGO96pUK8HJ0iy2ZHeqNpiR7OelleljCVoWPuJCO26q5z66VisWB76khl7Tmsqh5CqNC/pub?gid=0&single=true&output=csv" 
    
    df = pd.read_csv(url_csv, dtype=str)
    
    # LIMPIEZA DE NÚMEROS
    cols_numericas = [
        'RECIBIDAS_FIN', 'ATENDIDAS_FIN', 'PERDIDAS_FIN', 
        'RECIBIDAS_PREPAGO', 'ATENDIDAS_PREPAGO', 'PERDIDAS_PREPAGO',
        'TURNOS_PRACT_TEL', 'TURNOS_CONS_TEL', 'TURNOS_TOTAL_TEL'
    ]
    
    for col in cols_numericas:
        if col in df.columns:
            df[col] = df[col].str.replace('.', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.fillna(0)
    return df

def parsear_fecha_custom(texto_fecha):
    if pd.isna(texto_fecha): return None
    texto = str(texto_fecha).lower().strip().replace(".", "")
    
    meses = {
        'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12,
        'jan': 1, 'apr': 4, 'aug': 8, 'dec': 12 
    }
    
    partes = texto.replace("-", " ").split()
    if len(partes) < 2: return None
    
    mes_txt = partes[0][:3] 
    anio_txt = partes[1]
    
    if len(anio_txt) == 2: anio_txt = "20" + anio_txt
    
    num_mes = meses.get(mes_txt)
    if num_mes:
        return pd.Timestamp(year=int(anio_txt), month=num_mes, day=1)
    return None

try:
    df = cargar_datos()
    
    df['FECHA_REAL'] = df['MES'].apply(parsear_fecha_custom)
    df = df.dropna(subset=['FECHA_REAL']).sort_values('FECHA_REAL')
    
    df['TOTAL_LLAMADAS'] = df['RECIBIDAS_FIN'] + df['RECIBIDAS_PREPAGO']
    df['TOTAL_ATENDIDAS'] = df['ATENDIDAS_FIN'] + df['ATENDIDAS_PREPAGO']
    df['TOTAL_PERDIDAS'] = df['PERDIDAS_FIN'] + df['PERDIDAS_PREPAGO']
    
    df['SLA_GLOBAL'] = (df['TOTAL_ATENDIDAS'] / df['TOTAL_LLAMADAS']) * 100

    # --- BARRA LATERAL ---
    with st.sidebar:
        st.header("📞 Panel de Control")
        modo = st.radio("Modo de Análisis:", ["📅 Evolución Mensual", "🔄 Comparativa Interanual"])
        st.divider()
        segmento = st.selectbox("Filtrar por Tipo:", ["Todo Unificado", "Solo Financiadores", "Solo Prepago"])
        st.divider()
        st.info("💡 Tip: La 'Comparativa Interanual' busca automáticamente el mismo mes en años anteriores.")

    # --- VISUALIZACIÓN ---

    if modo == "📅 Evolución Mensual":
        fechas_dispo = sorted(df['FECHA_REAL'].unique(), reverse=True)
        fecha_sel = st.selectbox("Seleccionar Mes:", fechas_dispo, format_func=lambda x: x.strftime("%B-%Y").capitalize())
        
        datos_mes = df[df['FECHA_REAL'] == fecha_sel].iloc[0]
        
        if segmento == "Solo Financiadores":
            rec, aten, perd = datos_mes['RECIBIDAS_FIN'], datos_mes['ATENDIDAS_FIN'], datos_mes['PERDIDAS_FIN']
        elif segmento == "Solo Prepago":
            rec, aten, perd = datos_mes['RECIBIDAS_PREPAGO'], datos_mes['ATENDIDAS_PREPAGO'], datos_mes['PERDIDAS_PREPAGO']
        else:
            rec, aten, perd = datos_mes['TOTAL_LLAMADAS'], datos_mes['TOTAL_ATENDIDAS'], datos_mes['TOTAL_PERDIDAS']
        
        sla_mes = (aten / rec * 100) if rec > 0 else 0
        pct_perdidas = (perd / rec * 100) if rec > 0 else 0

        # --- LÓGICA DE COLORES DINÁMICA ---
        
        # 1. Lógica para Perdidas:
        # Si perdidas > 10% -> ES MALO (Rojo). Usamos "normal" porque el string es negativo (-15%), y en "normal" negativo es rojo.
        # Si perdidas <= 10% -> ES BUENO (Verde). Usamos "inverse" porque en "inverse" negativo es verde.
        color_delta_perdidas = "normal" if pct_perdidas > 10 else "inverse"

        # 2. Lógica para Nivel de Servicio (SLA):
        # Objetivo: 90%. Si es > 90 es "normal" (verde), si es menor es "inverse" (rojo/gris).
        # Nota: delta_color="off" pone gris, "inverse" pone rojo si el delta fuera positivo.
        # Aquí usaremos un truco visual simple.
        color_delta_sla = "normal" if sla_mes >= 90 else "inverse"

        # KPIs
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📞 Llamadas Recibidas", f"{rec:,.0f}")
        c2.metric("✅ Atendidas", f"{aten:,.0f}", delta=f"{(aten/rec*100):.1f}%")
        
        # Métrica Perdidas con Lógica de Alerta
        c3.metric("❌ Perdidas (Abandono)", f"{perd:,.0f}", 
                  delta=f"-{pct_perdidas:.1f}%", 
                  delta_color=color_delta_perdidas) # <--- Aquí aplicamos el color dinámico
        
        # Métrica SLA con Meta 90%
        c4.metric("📊 Nivel de Servicio", f"{sla_mes:.1f}%", 
                  delta="Meta: >90%", 
                  delta_color="normal" if sla_mes >= 90 else "inverse")

        st.markdown("---")

        col_graf1, col_graf2 = st.columns([1, 1])
        
        with col_graf1:
            st.subheader("Nivel de Atención")
            
            # DataFrame auxiliar para controlar colores estrictos
            df_pie = pd.DataFrame({
                'Estado': ['Atendidas', 'Perdidas'],
                'Cantidad': [aten, perd]
            })
            
            # Mapeo estricto de colores
            colores_fijos = {'Atendidas': '#4CAF50', 'Perdidas': '#FF5252'} # Verde y Rojo
            
            fig_pie = px.pie(
                df_pie, 
                values='Cantidad', 
                names='Estado',
                color='Estado', # <--- Importante: Usar la columna Estado para mapear color
                color_discrete_map=colores_fijos, # <--- Forzamos el mapa de colores
                hole=0.4
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_graf2:
            st.subheader("Cantidad de turnos (Ts y AS")
            datos_canales = {
                'Plataforma': ['Ts (Tel)', 'AS (Tel)', 'Total (Tel)'],
                'Turnos': [datos_mes['TURNOS_CONS_TEL'], datos_mes['TURNOS_PRACT_TEL'], datos_mes['TURNOS_TOTAL_TEL']]
            }
            fig_bar = px.bar(datos_canales, x='Canal', y='Turnos', color='Canal')
            st.plotly_chart(fig_bar, use_container_width=True)

    # === MODO 2: COMPARATIVA INTERANUAL ===
    else:
        st.subheader("🔄 Análisis Interanual (Mismo mes, distintos años)")
        meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        mes_target_nombre = st.selectbox("¿Qué mes quieres comparar?", meses_nombres)
        mes_target_num = meses_nombres.index(mes_target_nombre) + 1
        
        df_interanual = df[df['FECHA_REAL'].dt.month == mes_target_num].copy()
        
        if df_interanual.empty:
            st.warning(f"No encontré datos para {mes_target_nombre}.")
            st.stop()
            
        df_interanual['AÑO'] = df_interanual['FECHA_REAL'].dt.year.astype(str)
        
        tab1, tab2 = st.tabs(["📈 Evolución Visual", "📄 Datos"])
        
        with tab1:
            fig_inter = go.Figure()
            fig_inter.add_trace(go.Bar(x=df_interanual['AÑO'], y=df_interanual['TOTAL_ATENDIDAS'], name='Atendidas', marker_color='#4CAF50'))
            fig_inter.add_trace(go.Bar(x=df_interanual['AÑO'], y=df_interanual['TOTAL_PERDIDAS'], name='Perdidas', marker_color='#FF5252'))
            fig_inter.update_layout(barmode='group', title=f"Desempeño en {mes_target_nombre}")
            st.plotly_chart(fig_inter, use_container_width=True)
            st.caption("Evolución de Turnos Telefónicos Totales:")
            st.line_chart(data=df_interanual, x='AÑO', y='TURNOS_TOTAL_TEL')

        with tab2:
            st.dataframe(df_interanual[['AÑO', 'TOTAL_LLAMADAS', 'TOTAL_ATENDIDAS', 'TOTAL_PERDIDAS', 'SLA_GLOBAL']].style.format({
                'TOTAL_LLAMADAS': '{:,.0f}', 'TOTAL_ATENDIDAS': '{:,.0f}', 'TOTAL_PERDIDAS': '{:,.0f}', 'SLA_GLOBAL': '{:.1f}%'
            }))

except Exception as e:
    st.error("Hubo un error cargando los datos.")
    st.expander("Ver error técnico").write(e)
