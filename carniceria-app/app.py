import streamlit as st
import pandas as pd
from datetime import date
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# 1. Configuración de la página (Título de la pestaña e ícono)
st.set_page_config(page_title="El Rincón del Asador", page_icon="🥩", layout="wide", initial_sidebar_state="expanded")

# --- CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def conectar_gsheets():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # Asegúrate de que tu Google Sheet se llame exactamente "Carniceria_BD"
    sheet = client.open("Carniceria_BD").sheet1
    return sheet

sheet = conectar_gsheets()

# --- INTERFAZ PRINCIPAL CON LOGO Y TÍTULO ---
col_logo, col_titulo = st.columns([1, 6]) # Ajusta las proporciones si lo ves necesario

with col_logo:
    try:
        # Intenta cargar el logo subido al repositorio (Asegúrate de que se llame logo.png o cámbiale el nombre aquí)
        st.image("logo.png", width=90)
    except:
        st.write("🥩") # Emoji de respaldo por si el archivo de imagen aún no fue subido

with col_titulo:
    st.title("El Rincón del Asador")
    st.caption("Sistema de Gestión y Contabilidad")

st.markdown("---")

# Pestañas de navegación
tab1, tab2 = st.tabs(["📝 Registrar Movimiento", "📊 Consultar y Auditar"])

with tab1:
    st.header("Nuevo Registro")
    with st.form("form_registro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha_input = st.date_input("Fecha", date.today())
            tipo_input = st.selectbox("Tipo de Movimiento", ["Entrada (Ingreso)", "Salida (Gasto)"])
            monto_input = st.number_input("Monto ($)", min_value=0.0, step=1000.0)
        with col2:
            categoria_input = st.selectbox("Categoría / Etiqueta", 
                                           ["Venta Mostrador", "Pago a Proveedor", "Falta de Pago (Deuda)", "Préstamo Solicitado", "Otros"])
            detalle_input = st.text_input("Detalle (Ej. Media res vaca, o Nombre de quien debe)")
        
        submit = st.form_submit_button("Guardar Registro")
        if submit:
            if monto_input > 0:
                nueva_fila = [fecha_input.strftime("%Y-%m-%d"), tipo_input, categoria_input, monto_input, detalle_input]
                sheet.append_row(nueva_fila)
                st.success("¡Movimiento guardado con éxito en Google Sheets!")
            else:
                st.error("El monto debe ser mayor a 0.")

with tab2:
    st.header("Auditoría de Días y Meses")
    
    datos = sheet.get_all_records()
    df = pd.DataFrame(datos)
    
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        
        col_f1, col_f2 = st.columns(2)
        meses = df['Fecha'].dt.to_period('M').unique().astype(str)
        
        with col_f1:
            mes_seleccionado = st.selectbox("Filtrar por Mes", ["Todos"] + list(meses))
        with col_f2:
            filtro_categoria = st.selectbox("Filtrar por Etiqueta", ["Todas", "Falta de Pago (Deuda)", "Préstamo Solicitado", "Pago a Proveedor", "Venta Mostrador", "Otros"])

        df_filtrado = df.copy()
        if mes_seleccionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Fecha'].dt.to_period('M').astype(str) == mes_seleccionado]
        if filtro_categoria != "Todas":
            df_filtrado = df_filtrado[df_filtrado['Categoría'] == filtro_categoria]

        df_filtrado['Fecha'] = df_filtrado['Fecha'].dt.strftime('%Y-%m-%d')
        st.dataframe(df_filtrado, use_container_width=True)
        
        st.subheader("Resumen del período seleccionado")
        df_filtrado['Monto'] = pd.to_numeric(df_filtrado['Monto'], errors='coerce').fillna(0)
        
        total_entradas = df_filtrado[df_filtrado['Tipo'] == 'Entrada (Ingreso)']['Monto'].sum()
        total_salidas = df_filtrado[df_filtrado['Tipo'] == 'Salida (Gasto)']['Monto'].sum()
        
        col_t1, col_t2, col_t3 = st.columns(3)
        col_t1.metric("Total Entradas", f"${total_entradas:,.2f}")
        col_t2.metric("Total Salidas", f"${total_salidas:,.2f}")
        col_t3.metric("Balance", f"${(total_entradas - total_salidas):,.2f}")
    else:
        st.info("Aún no hay movimientos registrados.")
