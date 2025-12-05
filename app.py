import streamlit as st
import json
import pandas as pd
from logic import process_data
import docx

st.set_page_config(page_title="Lead Classifier", layout="wide")

st.title("📊 Lead Classifier & Analyzer")
st.markdown("""
Sube tu archivo JSON (o .docx con JSON) de logs de chat para procesarlo y clasificar los leads en **SQL** o **MQL** 
basado en las reglas de negocio definidas.
""")

uploaded_file = st.file_uploader("Cargar archivo de Chat Logs (JSON/DOCX)", type=["json", "docx"])
neotel_file = st.file_uploader("Cargar base Neotel (Excel) - Opcional", type=["xls", "xlsx"])

if uploaded_file is not None:
    try:
        data = None
        # Determine file type and load content
        if uploaded_file.name.endswith('.json'):
            data = json.load(uploaded_file)
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            # Join with newlines or spaces, depending on how the JSON is formatted in the doc
            # Assuming the doc contains just the JSON text
            json_text = "\n".join(full_text)
            data = json.loads(json_text)
            
        if data is None:
             st.error("No se pudo leer el archivo.")
        elif "items" not in data:
            st.error("El JSON no tiene el formato correcto (falta la clave 'items').")
        else:
            st.success(f"Archivo de logs cargado correctamente. {len(data['items'])} mensajes encontrados.")
            
            neotel_df = None
            if neotel_file is not None:
                try:
                    neotel_df = pd.read_excel(neotel_file)
                    st.success(f"Base Neotel cargada correctamente. {len(neotel_df)} registros.")
                except Exception as e:
                    st.error(f"Error al leer el archivo Excel de Neotel: {e}")

            if st.button("Procesar Leads"):
                with st.spinner("Procesando conversaciones..."):
                    # Process data
                    results = process_data(data, neotel_df)
                    
                    # Convert to DataFrame for display
                    df = pd.DataFrame(results)
                    
                    # Metrics
                    total_leads = len(df)
                    sql_leads = len(df[df['clasificacion'] == 'SQL'])
                    mql_leads = len(df[df['clasificacion'] == 'MQL'])
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Leads", total_leads)
                    col2.metric("SQL (Qualified)", sql_leads)
                    col3.metric("MQL (Marketing)", mql_leads)
                    
                    # Display Data
                    st.subheader("Resultados Detallados")
                    
                    # Interactive Table with Column Config
                    st.dataframe(
                        df, 
                        use_container_width=True,
                        column_config={
                            "chat_id": "Chat ID",
                            "nombre_detectado": "Nombre",
                            "clasificacion": st.column_config.TextColumn(
                                "Clasificación",
                                help="SQL: Sales Qualified Lead, MQL: Marketing Qualified Lead",
                                width="medium"
                            ),
                            "razon_principal": "Razón",
                            "señales_clave": "Señales",
                            "estado_conversacion": "Estado",
                            "utm_source": "UTM Source",
                            "utm_medium": "UTM Medium",
                            "utm_origen": "UTM Origen"
                        }
                    )
                    
                    # Download Buttons
                    col_d1, col_d2 = st.columns(2)
                    
                    # JSON Download
                    json_output = json.dumps(results, indent=2, ensure_ascii=False)
                    col_d1.download_button(
                        label="📥 Descargar JSON",
                        data=json_output,
                        file_name="leads_clasificados.json",
                        mime="application/json"
                    )
                    
                    # Excel Download
                    # Create Excel in memory
                    import io
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Leads')
                    excel_data = output.getvalue()
                    
                    col_d2.download_button(
                        label="📊 Descargar Excel",
                        data=excel_data,
                        file_name="leads_clasificados.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
    except json.JSONDecodeError:
        st.error("Error al leer el archivo JSON. Asegúrate de que sea un JSON válido.")
    except Exception as e:
        st.error(f"Ocurrió un error inesperado: {e}")
