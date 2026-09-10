import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# 1. Configuración y Base de Datos
st.set_page_config(page_title="Gestión Carnicería", layout="wide", initial_sidebar_state="expanded")

conn = sqlite3.connect('contabilidad.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS movimientos
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              fecha TEXT, tipo TEXT, categoria TEXT, monto REAL, detalle TEXT)''')
conn.commit()

def cargar_movimiento(fecha, tipo, categoria, monto, detalle):
    c.execute("INSERT INTO movimientos (fecha, tipo, categoria, monto, detalle) VALUES (?, ?, ?, ?, ?)",
              (fecha, tipo, categoria, monto, detalle))
    conn.commit()

# 2. Interfaz Principal
st.title("🥩 Contabilidad - Carnicería")

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
                cargar_movimiento(fecha_input.strftime("%Y-%m-%d"), tipo_input, categoria_input, monto_input, detalle_input)
                st.success("¡Movimiento guardado con éxito!")
            else:
                st.error("El monto debe ser mayor a 0.")

with tab2:
    st.header("Auditoría de Días y Meses")
    
    # Filtros
    df = pd.read_sql_query("SELECT fecha as Fecha, tipo as Tipo, categoria as Categoría, monto as Monto, detalle as Detalle FROM movimientos", conn)
    
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        
        col_f1, col_f2 = st.columns(2)
        meses = df['Fecha'].dt.to_period('M').unique().astype(str)
        
        with col_f1:
            mes_seleccionado = st.selectbox("Filtrar por Mes", ["Todos"] + list(meses))
        with col_f2:
            filtro_categoria = st.selectbox("Filtrar por Etiqueta", ["Todas", "Falta de Pago (Deuda)", "Préstamo Solicitado", "Pago a Proveedor"])

        # Aplicar filtros
        df_filtrado = df.copy()
        if mes_seleccionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Fecha'].dt.to_period('M').astype(str) == mes_seleccionado]
        if filtro_categoria != "Todas":
            df_filtrado = df_filtrado[df_filtrado['Categoría'] == filtro_categoria]

        # Convertir fecha a texto para mostrar limpio
        df_filtrado['Fecha'] = df_filtrado['Fecha'].dt.strftime('%Y-%m-%d')
        
        # Mostrar tabla
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Totales rápidos
        st.subheader("Resumen del período seleccionado")
        total_entradas = df_filtrado[df_filtrado['Tipo'] == 'Entrada (Ingreso)']['Monto'].sum()
        total_salidas = df_filtrado[df_filtrado['Tipo'] == 'Salida (Gasto)']['Monto'].sum()
        
        col_t1, col_t2, col_t3 = st.columns(3)
        col_t1.metric("Total Entradas", f"${total_entradas:,.2f}")
        col_t2.metric("Total Salidas", f"${total_salidas:,.2f}")
        col_t3.metric("Balance", f"${(total_entradas - total_salidas):,.2f}")
    else:
        st.info("Aún no hay movimientos registrados.")