import streamlit as st
import pandas as pd
import os

BASE_FILE = "Resumen Banco Fleteros.xlsm"

def gestionar_fleteros():
    if not os.path.exists(BASE_FILE):
        st.error("No se encontró el archivo base.")
        return []

    xls = pd.ExcelFile(BASE_FILE)

    # Si ya existe la hoja Fleteros, la leemos y devolvemos la lista
    if "Fleteros" in xls.sheet_names:
        fleteros_df = pd.read_excel(xls, sheet_name="Fleteros")
        lista_fleteros = fleteros_df["Fletero"].dropna().unique().tolist()
        st.success("Fleteros cargados desde el archivo maestro ✅")
        return lista_fleteros

    # Si no existe, pedimos la carga inicial
    st.subheader("Configuración inicial de fleteros")
    num_fleteros = st.number_input("¿Cuántos fleteros querés cargar?", min_value=1, step=1)
    fleteros_list = []
    for i in range(1, num_fleteros+1):
        nombre = st.text_input(f"{i}. Nombre del fletero", key=f"fletero_{i}")
        if nombre:
            fleteros_list.append(nombre)

    if st.button("Guardar fleteros iniciales"):
        fleteros_df = pd.DataFrame({"Fletero": fleteros_list})
        with pd.ExcelWriter(BASE_FILE, mode="a", engine="openpyxl") as writer:
            fleteros_df.to_excel(writer, sheet_name="Fleteros", index=False)
        st.success("Fleteros iniciales guardados ✅")
        return fleteros_list

    return []