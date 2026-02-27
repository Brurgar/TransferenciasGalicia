import streamlit as st
import pandas as pd
from fleteros import BASE_FILE

def asignar_fleteros(galicia, lista_fleteros):
    st.subheader("Asignar fleteros a clientes")

    # Crear columna Fletero si no existe
    if "Fletero" not in galicia.columns:
        galicia["Fletero"] = pd.NA

    # Normalizar CUIT
    galicia["CUIT"] = galicia["CUIT"].astype(str).str.strip()

    # Intentar leer asignaciones previas desde el Excel maestro
    try:
        asignaciones_previas = pd.read_excel(BASE_FILE, sheet_name="AsignacionesClientes")
        asignaciones_previas["CUIT"] = asignaciones_previas["CUIT"].astype(str).str.strip()
        galicia = galicia.merge(asignaciones_previas, on="CUIT", how="left")
        if "Fletero_y" in galicia.columns:
            galicia["Fletero"] = galicia["Fletero_y"].fillna(galicia["Fletero_x"])
            galicia.drop(columns=["Fletero_x","Fletero_y"], inplace=True)
    except Exception:
        pass

    # Clientes únicos
    clientes_unicos = galicia[["Cliente", "CUIT", "Fletero"]].drop_duplicates()

    asignaciones = {}

    # 🔎 Mostrar selectbox SOLO para clientes sin fletero
    clientes_sin_fletero = clientes_unicos[clientes_unicos["Fletero"].isna() | (clientes_unicos["Fletero"] == "")]

    if not clientes_sin_fletero.empty:
        for idx, row in clientes_sin_fletero.iterrows():
            cliente = row["Cliente"]
            cuit = row["CUIT"]
            fletero_asignado = st.selectbox(
                f"Cliente: {cliente} (CUIT {cuit})",
                options=[""] + lista_fleteros,
                index=0,
                key=f"fletero_{cuit}_{idx}"
            )
            if fletero_asignado:
                asignaciones[cuit] = fletero_asignado

        if st.button("Guardar asignaciones"):
            galicia["Fletero"] = galicia["CUIT"].map(asignaciones).fillna(galicia["Fletero"])
            st.success("Asignaciones guardadas ✅")

            # Guardar/actualizar asignaciones en Excel maestro
            asignaciones_df = galicia[["CUIT", "Fletero"]].drop_duplicates()

            try:
                asignaciones_previas = pd.read_excel(BASE_FILE, sheet_name="AsignacionesClientes")
                asignaciones_previas["CUIT"] = asignaciones_previas["CUIT"].astype(str).str.strip()
                asignaciones_actualizadas = pd.concat([asignaciones_previas, asignaciones_df]).drop_duplicates(subset=["CUIT"], keep="last")
            except Exception:
                asignaciones_actualizadas = asignaciones_df

            with pd.ExcelWriter(BASE_FILE, mode="a", engine="openpyxl", if_sheet_exists="replace") as writer:
                asignaciones_actualizadas.to_excel(writer, sheet_name="AsignacionesClientes", index=False)

    else:
        st.info("✅ Todos los clientes ya tienen fletero asignado.")

    # Verificar si quedan clientes sin fletero
    if galicia["Fletero"].isna().any() or (galicia["Fletero"] == "").any():
        st.warning("⚠️ Todavía hay clientes sin fletero asignado. Asignalos antes de continuar.")
        return None
    else:
        return galicia