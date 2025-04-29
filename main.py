
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime, timedelta

# Configuración de conexión
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credenciales.json', scope)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key('19Rd4PzPrrzSZ8CXb98VDwdhys9r-owybmdtfbdfOx2U')

# Configuraciones
configuraciones = {
    "Peluches": {
        "hoja": spreadsheet.worksheet("Inventario"),
        "producto": "peluches"
    },
    "Llaveros": {
        "hoja": spreadsheet.worksheet("Inverteros"),
        "producto": "llaveros"
    }
}

# Fecha
fecha_actual = datetime.now().strftime("%Y-%m-%d")

# Funciones
def registrar_pedido(tipo, cantidad, costo_total):
    hoja = configuraciones[tipo]["hoja"]
    costo_promedio = costo_total / cantidad if cantidad > 0 else 0
    fecha_llegada = (datetime.now() + timedelta(weeks=2)).strftime("%Y-%m-%d")
    hoja.append_row([fecha_actual, cantidad, costo_total, round(costo_promedio, 2), "En Camino", fecha_llegada, cantidad, 0])
    st.success(f"✅ Pedido de {cantidad} {configuraciones[tipo]['producto']} registrado.")

def registrar_llegada(tipo, llegados):
    hoja = configuraciones[tipo]["hoja"]
    datos = hoja.get_all_records()
    df = pd.DataFrame(datos)
    df["En camino"] = pd.to_numeric(df["En camino"], errors='coerce').fillna(0)
    df["Llegaron"] = pd.to_numeric(df["Llegaron"], errors='coerce').fillna(0)

    for index, row in df.iterrows():
        faltan = row["En camino"] - row["Llegaron"]
        if faltan > 0:
            fila = index + 2
            cantidad_a_registrar = min(faltan, llegados)
            hoja.update_cell(fila, 8, row["Llegaron"] + cantidad_a_registrar)
            llegados -= cantidad_a_registrar
            st.info(f"📦 Registrados {cantidad_a_registrar} {configuraciones[tipo]['producto']} en fila {fila}.")
            if llegados == 0:
                break

    if llegados > 0:
        st.warning(f"⚠️ Quedaron {llegados} sin asignar. Revisa futuros pedidos.")
    else:
        st.success("✅ Todos los productos registrados correctamente.")

def registrar_ventas_llaveros(maquina, vendidos, monedas):
    hoja = spreadsheet.worksheet("Llaveros")
    ganancias = monedas * 5
    fila = [fecha_actual, vendidos, ganancias, 0, 0, 0] if maquina == "Pri" else [fecha_actual, 0, 0, 0, vendidos, ganancias]
    hoja.append_row(fila)
    st.success(f"✅ Llaveros registrados: {vendidos} vendidos, {ganancias} pesos.")

def registrar_ventas_pelucheras(maquina, vendidos, ganancias):
    hoja = spreadsheet.worksheet("Máquinas")
    fila = [fecha_actual, vendidos, ganancias, 0, 0, 0] if maquina == "Pri" else [fecha_actual, 0, 0, 0, vendidos, ganancias]
    hoja.append_row(fila)
    st.success(f"✅ Peluches registrados: {vendidos} vendidos, {ganancias} pesos.")

def registrar_mas_maquinas(maquina, ganancias):
    hoja = spreadsheet.worksheet("Más máquinas")
    precios = {"Pelotas pequeñas (Pajaro)": 5, "Pelotas grandes (Pri)": 10, "Pelotas pequeñas (Oasis)": 5,
               "Carrito (Oasis)", "Carrusel (Oasis)", "Pelotitas mix (Victor)"]}
    costos = {"Pelotas pequeñas (Pajaro)": 1.127, "Pelotas grandes (Pri)": 5.29,
              "Pelotas pequeñas (Oasis)": 1.127, "Pelotitas mix (Victor)": 1.5}
    vendidos = ganancias / precios[maquina]
    if maquina in ["Carrito (Oasis)", "Carrusel (Oasis)"]:
        fila = [fecha_actual, maquina, ganancias, vendidos, 0, ganancias, 0]
    else:
        costo_total = vendidos * costos.get(maquina, 0)
        ganancia_neta = ganancias - costo_total
        comision = ganancias * 0.20 if maquina == "Pelotitas mix (Victor)" else 0
        fila = [fecha_actual, maquina, ganancias, vendidos, costo_total, ganancia_neta, comision]
    hoja.append_row(fila)
    st.success(f"✅ Más máquinas registrado: {ganancias} pesos, {vendidos} unidades.")

# App
st.title("📊 Gestión de Ventas e Inventario")

tab1, tab2 = st.tabs(["Ventas y Ganancias", "Inventario"])

with tab1:
    st.header("Llaveros")
    maquina_llaveros = st.selectbox("Máquina:", ["Pri", "Oa"])
    vendidos = st.number_input("Llaveros vendidos:", min_value=0)
    monedas = st.number_input("Monedas de 5:", min_value=0)
    if st.button("Registrar Llaveros"):
        registrar_ventas_llaveros(maquina_llaveros, vendidos, monedas)

    st.header("Pelucheras")
    maquina_pelucheras = st.selectbox("Máquina:", ["Pri", "Pa"])
    vendidos_peluches = st.number_input("Peluches vendidos:", min_value=0)
    ganancias_peluches = st.number_input("Ganancias Pelucheras:", min_value=0.0)
    if st.button("Registrar Pelucheras"):
        registrar_ventas_pelucheras(maquina_pelucheras, vendidos_peluches, ganancias_peluches)

    st.header("Más Máquinas")
    maquina_mas = st.selectbox("Máquina Más:", [
        "Pelotas pequeñas (Pajaro)", "Pelotas grandes (Pri)", "Pelotas pequeñas (Oasis)",
        "Carrito (Oasis)", "Carrusel (Oasis)", "Pelotitas mix (Victor)"
    ])
    ganancias_mas = st.number_input("Ganancias brutas Más Máquinas:", min_value=0.0)
    if st.button("Registrar Más Máquinas"):
        registrar_mas_maquinas(maquina_mas, ganancias_mas)

with tab2:
    st.header("Inventario")
    tipo = st.selectbox("Tipo de producto:", list(configuraciones.keys()))
    cantidad = st.number_input("Cantidad pedida:", min_value=0)
    costo_total = st.number_input("Costo Total:", min_value=0.0)
    if st.button("Registrar Pedido"):
        registrar_pedido(tipo, cantidad, costo_total)

    llegados = st.number_input("Cantidad llegada:", min_value=0)
    if st.button("Registrar Llegada"):
        registrar_llegada(tipo, llegados)
