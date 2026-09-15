import streamlit as st
import pandas as pd

st.set_page_config(page_title="AI-Recruiter Portal", layout="wide")

st.title("🤖 Portal Inteligente de Reclutamiento")
st.markdown("Plataforma centralizada: Ingesta automática, alertas de SLA, Chat con IA y Dashboard.")
st.divider()

col_izq, col_der = st.columns([1, 1.5]) 

with col_izq:
    st.subheader("⚙️ 1. Carga de Workday y Alertas")
    rpt_file = st.file_uploader("Arrastra aquí el archivo RPT de Workday", type=['xlsx'])
    
    if rpt_file:
        df_rpt = pd.read_excel(rpt_file, sheet_name=0)
        df_rpt['Dias'] = pd.to_numeric(df_rpt['Dias que lleva abierta la JR'], errors='coerce')
        
        rojas = df_rpt[df_rpt['Dias'] > 60]
        amarillas = df_rpt[(df_rpt['Dias'] >= 31) & (df_rpt['Dias'] <= 60)]
        verdes = df_rpt[df_rpt['Dias'] <= 30]
        contratos = df_rpt[df_rpt['Subtipo trabajador'] == 'Contrato Periodo Determinado/Eventual (duración determinada)']
        
        st.success("✅ Datos procesados. Matriz de Control actualizada.")
        
        st.markdown("### 🚦 Semáforo de Vacantes (SLAs)")
        c1, c2, c3 = st.columns(3)
        c1.metric("🔴 Críticas (>60 días)", len(rojas))
        c2.metric("🟡 Riesgo (31-60 días)", len(amarillas))
        c3.metric("🟢 Saludables (0-30)", len(verdes))
        
        if len(contratos) > 0:
            st.warning(f"⏳ Tienes {len(contratos)} vacantes con Contrato Determinado.")

with col_der:
    st.subheader("📊 3. Dashboard Ejecutivo (Looker Studio)")
    st.info("Espacio reservado para incrustar el panel interactivo.")
