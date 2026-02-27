import streamlit as st
import pandas as pd
from fleteros import gestionar_fleteros, BASE_FILE
from clientes import asignar_fleteros
from resumen import mostrar_resumen

st.title("Procesar Extracto Galicia")

archivo = st.file_uploader("Subí el extracto de Galicia (Excel)", type=["xls","xlsx","xlsm"])

if archivo is not None:
    galicia = pd.read_excel(archivo, header=5)

    # Normalizar CUIT
    if "CUIT" in galicia.columns:
        galicia["CUIT"] = galicia["CUIT"].astype(str).str.strip()

    # Limpiar y convertir columna Crédito a numérica
    if "Crédito" in galicia.columns:
        galicia["Crédito"] = (
            galicia["Crédito"]
            .astype(str)
            .str.replace(".", "", regex=False)   # quitar separador de miles
            .str.replace(",", ".", regex=False)  # convertir coma decimal a punto
        )
        galicia["Crédito"] = pd.to_numeric(galicia["Crédito"], errors="coerce")

    # Crear columnas básicas si faltan
    if "Cliente" not in galicia.columns:
        galicia["Cliente"] = galicia["Movimiento"].apply(
            lambda x: str(x).split("\n")[1] if pd.notna(x) and len(str(x).split("\n")) > 1 else ""
        )
    if "CUIT" not in galicia.columns:
        galicia["CUIT"] = galicia["Movimiento"].apply(
            lambda x: str(x).split("\n")[2] if pd.notna(x) and len(str(x).split("\n")) > 2 else ""
        )
    galicia["CUIT"] = galicia["CUIT"].astype(str).str.strip()

    # Leer asignaciones previas desde Excel maestro
    try:
        asignaciones_previas = pd.read_excel(BASE_FILE, sheet_name="AsignacionesClientes")
        asignaciones_previas["CUIT"] = asignaciones_previas["CUIT"].astype(str).str.strip()
        galicia = galicia.merge(asignaciones_previas, on="CUIT", how="left")
        if "Fletero_y" in galicia.columns:
            galicia["Fletero"] = galicia["Fletero_y"].fillna(galicia.get("Fletero_x"))
            galicia.drop(columns=["Fletero_x","Fletero_y"], errors="ignore", inplace=True)
    except Exception:
        galicia["Fletero"] = pd.NA

    # Etapa 1: Fleteros
    lista_fleteros = gestionar_fleteros()

    if lista_fleteros:
        # Etapa 2: Asignar fleteros
        galicia_asignado = asignar_fleteros(galicia, lista_fleteros)

        # Etapa 3: Mostrar resumen solo si todos tienen fletero
        if galicia_asignado is not None:
            mostrar_resumen(galicia_asignado)