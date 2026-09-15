import streamlit as st
import pandas as pd
import os
import io

# 1. ESTILOS CORPORATIVOS
st.set_page_config(page_title="Portal de Talento", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #f4f6f9; }
    h1, h2, h3 { color: #072146; font-family: 'Arial', sans-serif; }
    .stButton>button { background-color: #1973B8; color: white; border-radius: 5px; border: none; }
    .stButton>button:hover { background-color: #072146; color: white; }
    div[data-testid="stMetricValue"] { color: #072146; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🏦 Portal de Inteligencia de Reclutamiento")
st.markdown("Gestión automatizada de Matriz de Control y SLAs.")
st.divider()

ARCHIVO_BASE = "inventario_maestro.xlsx"
col_izq, col_der = st.columns([1, 1.8]) 

with col_izq:
    st.subheader("⚙️ Ingesta de Datos")
    
    if not os.path.exists(ARCHIVO_BASE):
        st.info("👋 Configuración Inicial: Sube tu Inventario Base por única vez.")
        inv_file = st.file_uploader("📥 1. Sube tu Inventario de Control", type=['xlsx'])
        if inv_file:
            df_inicial = pd.read_excel(inv_file, sheet_name=0)
            df_inicial.to_excel(ARCHIVO_BASE, index=False)
            st.success("✅ Base guardada. Por favor recarga la página (F5).")
    else:
        st.success("✅ Base de datos central conectada.")
        df_inv = pd.read_excel(ARCHIVO_BASE)
        
        rpt_file = st.file_uploader("📥 Sube el nuevo reporte de Workday (RPT)", type=['xlsx'])
        
        if rpt_file:
            df_rpt = pd.read_excel(rpt_file, sheet_name=0)
            df_rpt.columns = df_rpt.columns.str.strip()
            
            df_inv['JR_clean'] = df_inv['JR'].astype(str).str.strip().str.upper()
            df_rpt['JR_clean'] = df_rpt['JR'].astype(str).str.strip().str.upper()
            df_inv = df_inv.dropna(subset=['JR'])
            df_rpt = df_rpt.dropna(subset=['JR'])
            
            mapping = {
                'Job Family Group': 'AREA/OFICINA',
                'Título de publicación de puesto': 'JOB PROFILE',
                'Manager': 'MANAGER',
                'Fecha de introducción de solicitud': 'FECHA DE PUBLICACION',
                'JR Owner': 'TAM RESPONSABLE'
            }
            
            rpt_dict = df_rpt.drop_duplicates('JR_clean').set_index('JR_clean')
            
            for index, row in df_inv.iterrows():
                jr = row['JR_clean']
                if jr in rpt_dict.index:
                    for wd_col, inv_col in mapping.items():
                        if wd_col in rpt_dict.columns and inv_col in df_inv.columns:
                            df_inv.at[index, inv_col] = rpt_dict.at[jr, wd_col]
            
            existing_jrs = df_inv['JR_clean'].tolist()
            nuevas_filas = []
            for jr, row_wd in rpt_dict.iterrows():
                if jr not in existing_jrs:
                    nueva_fila = {col: None for col in df_inv.columns}
                    nueva_fila['JR'] = jr
                    for wd_col, inv_col in mapping.items():
                        if wd_col in row_wd:
                            nueva_fila[inv_col] = row_wd[wd_col]
                    max_nro = pd.to_numeric(df_inv['NRO'], errors='coerce').max()
                    nueva_fila['NRO'] = max_nro + 1 if pd.notna(max_nro) else 1
                    nuevas_filas.append(nueva_fila)
                    
            if nuevas_filas:
                df_inv = pd.concat([df_inv, pd.DataFrame(nuevas_filas)], ignore_index=True)
                
            df_inv = df_inv.drop(columns=['JR_clean'])
            df_inv.to_excel(ARCHIVO_BASE, index=False)
            st.success(f"✅ Cruce exitoso. {len(nuevas_filas)} vacantes nuevas agregadas.")
            
            if 'Dias que lleva abierta la JR' in df_rpt.columns:
                df_rpt['Dias'] = pd.to_numeric(df_rpt['Dias que lleva abierta la JR'], errors='coerce')
                st.markdown("### 🚦 Alertas de SLAs")
                c1, c2, c3 = st.columns(3)
                c1.metric("🔴 Críticas (>60 días)", len(df_rpt[df_rpt['Dias'] > 60]))
                c2.metric("🟡 Riesgo (31-60 días)", len(df_rpt[(df_rpt['Dias'] >= 31) & (df_rpt['Dias'] <= 60)]))
                c3.metric("🟢 Saludables (0-30)", len(df_rpt[df_rpt['Dias'] <= 30]))

with col_der:
    if os.path.exists(ARCHIVO_BASE):
        st.subheader("📋 Matriz de Control Editable")
        st.info("💡 Haz doble clic en cualquier celda para editar (como en Excel). Los cambios se guardan solos.")
        
        df_mostrar = pd.read_excel(ARCHIVO_BASE)
        
        # LA MAGIA: Convertimos el dataframe estático en un editor dinámico
        df_editado = st.data_editor(
            df_mostrar, 
            use_container_width=True, 
            height=500,
            num_rows="dynamic" # Permite agregar filas nuevas manualmente
        )
        
        # Guarda automáticamente cualquier edición que haga el equipo
        df_editado.to_excel(ARCHIVO_BASE, index=False)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_editado.to_excel(writer, index=False, sheet_name='Inventario_Actualizado')
        
        st.download_button(
            label="⬇️ Descargar Copia Manual (Excel)",
            data=buffer.getvalue(),
            file_name="Inventario_Actualizado.xlsx",
            mime="application/vnd.ms-excel"
        )
