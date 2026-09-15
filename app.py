with col_der:
    if os.path.exists(ARCHIVO_BASE):
        st.subheader("📋 Matriz de Control Editable")
        st.info("💡 Edita como en Excel (Usa Ctrl+Z si te equivocas). Cuando termines, presiona 'Guardar Cambios'.")
        
        df_mostrar = pd.read_excel(ARCHIVO_BASE)
        
        # Tabla interactiva
        df_editado = st.data_editor(
            df_mostrar, 
            use_container_width=True, 
            height=500,
            num_rows="dynamic" 
        )
        
        # BOTÓN DE SEGURIDAD PARA GUARDAR (Evita guardar errores automáticos)
        if st.button("💾 Guardar Cambios en la Base de Datos"):
            df_editado.to_excel(ARCHIVO_BASE, index=False)
            st.success("¡Tus ediciones manuales se han guardado con éxito!")
        
        st.divider()
        
        # Botón para descargar
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_editado.to_excel(writer, index=False, sheet_name='Inventario_Actualizado')
        
        st.download_button(
            label="⬇️ Descargar Copia en Excel",
            data=buffer.getvalue(),
            file_name="Inventario_Actualizado.xlsx",
            mime="application/vnd.ms-excel"
        )
