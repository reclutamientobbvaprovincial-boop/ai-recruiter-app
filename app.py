import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="AI-Recruiter Portal", layout="wide")

st.title("🤖 Portal Inteligente de Reclutamiento")
st.markdown("Plataforma centralizada: Ingesta automática, cruce de datos, alertas de SLA y Matriz Interactiva.")
st.divider()

col_izq, col_der = st.columns([1, 1.5]) 

with col_izq:
    st.subheader("⚙️ 1. Ingesta de Datos")
    inv_file = st.file_uploader("📥 1. Sube tu Inventario de Control actual", type=['xlsx'])
    rpt_file = st.file_uploader("📥 2. Sube el nuevo reporte de Workday (RPT)", type=['xlsx'])
    
    if inv_file and rpt_file:
        # Leer los archivos
        df_inv = pd.read_excel(inv_file, sheet_name=0)
        df_rpt = pd.read_excel(rpt_file, sheet_name=0)
        
        # Limpiar columnas y preparar cruce
        df_rpt.columns = df_rpt.columns.str.strip()
        df_inv['JR_clean'] = df_inv['JR'].astype(str).str.strip().str.upper()
        df_rpt['JR_clean'] = df_rpt['JR'].astype(str).str.strip().str.upper()
        
        df_inv = df_inv.dropna(subset=['JR'])
        df_rpt = df_rpt.dropna(subset=['JR'])
        
        # Mapeo de columnas (Workday -> Inventario)
        mapping = {
            'Job Family Group': 'AREA/OFICINA',
            'Título de publicación de puesto': 'JOB PROFILE',
            'Manager': 'MANAGER',
            'Fecha de introducción de solicitud': 'FECHA DE PUBLICACION',
            'JR Owner': 'TAM RESPONSABLE'
        }
        
        # PROCESO DE ACTUALIZACIÓN
        rpt_dict = df_rpt.drop_duplicates('JR_clean').set_index('JR_clean')
        
        # 1. Actualizar las vacantes que ya existen
        for index, row in df_inv.iterrows():
            jr = row['JR_clean']
            if jr in rpt_dict.index:
                for wd_col, inv_col in mapping.items():
                    if wd_col in rpt_dict.columns and inv_col in df_inv.columns:
                        df_inv.at[index, inv_col] = rpt_dict.at[jr, wd_col]
        
        # 2. Agregar las vacantes nuevas de Workday
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
            df_nuevas = pd.DataFrame(nuevas_filas)
            df_inv = pd.concat([df_inv, df_nuevas], ignore_index=True)
            
        df_inv = df_inv.drop(columns=['JR_clean'])
        
        st.success(f"✅ ¡Cruce exitoso! Se detectaron y agregaron {len(nuevas_filas)} vacantes nuevas.")
        
        # CÁLCULO DE SEMÁFOROS (Usando el RPT)
        if 'Dias que lleva abierta la JR' in df_rpt.columns:
            df_rpt['Dias'] = pd.to_numeric(df_rpt['Dias que lleva abierta la JR'], errors='coerce')
            rojas = df_rpt[df_rpt['Dias'] > 60]
            amarillas = df_rpt[(df_rpt['Dias'] >= 31) & (df_rpt['Dias'] <= 60)]
            verdes = df_rpt[df_rpt['Dias'] <= 30]
            
            st.markdown("### 🚦 Alertas de SLAs")
            c1, c2, c3 = st.columns(3)
            c1.metric("🔴 Críticas (>60 días)", len(rojas))
            c2.metric("🟡 Riesgo (31-60 días)", len(amarillas))
            c3.metric("🟢 Saludables (0-30)", len(verdes))

with col_der:
    if inv_file and rpt_file:
        st.subheader("📋 Matriz de Control Interactiva")
        st.markdown("Busca, filtra y revisa tu inventario actualizado en tiempo real.")
        
        # Mostrar la tabla interactiva
        st.dataframe(df_inv, use_container_width=True, height=400)
        
        # Botón para descargar el Excel actualizado
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_inv.to_excel(writer, index=False, sheet_name='Inventario_Actualizado')
        
        st.download_button(
            label="⬇️ Descargar Matriz Actualizada (Excel)",
            data=buffer.getvalue(),
            file_name="Inventario_RRHH_Actualizado.xlsx",
            mime="application/vnd.ms-excel"
        )
    else:
        st.info("Sube ambos archivos (Inventario y Workday) en el panel izquierdo para generar tu Matriz Interactiva.")
