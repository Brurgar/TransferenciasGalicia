import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.title("Procesar Extracto Galicia")

# Archivo base fijo dentro del repo
BASE_FILE = "Resumen Banco Fleteros.xlsm"

# Usuario sube el extracto diario
archivo = st.file_uploader("Subí el extracto de Galicia (Excel)", type=["xls", "xlsx", "xlsm"])

if archivo is not None:
    if not os.path.exists(BASE_FILE):
        st.error("No se encontró el archivo 'Resumen Banco Fleteros.xlsm' en el repositorio.")
    else:
        # Procesar extracto subido por el usuario
        galicia = pd.read_excel(archivo, header=5)

        galicia["Concepto"] = ""
        galicia["Cliente"] = ""
        galicia["CUIT"] = ""

        def procesar_movimiento(texto):
            if pd.isna(texto):
                return ("", "", "")
            lineas = str(texto).split("\n")
            concepto = lineas[0].strip() if len(lineas) > 0 else ""
            cliente = lineas[1].strip() if len(lineas) > 1 else ""
            cuit = lineas[2].strip() if len(lineas) > 2 else ""
            return (concepto, cliente, cuit)

        galicia[["Concepto","Cliente","CUIT"]] = galicia["Movimiento"].apply(lambda x: pd.Series(procesar_movimiento(x)))
        galicia["CUIT"] = galicia["CUIT"].astype(str).str.strip()

        galicia["Crédito"] = (
            galicia["Crédito"]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        galicia["Crédito"] = pd.to_numeric(galicia["Crédito"], errors="coerce").fillna(0)

        # Filtrar transferencias válidas
        transferencias_validas = galicia[
            (galicia["Crédito"] > 0) &
            (galicia["Concepto"].str.contains("Transferencia", case=False, na=False))
        ]
        total_transferencias_galicia = transferencias_validas.shape[0]
        total_monto_galicia = transferencias_validas["Crédito"].sum()

        # Abrimos el archivo base del repo
        xls = pd.ExcelFile(BASE_FILE)
        if "MaestroClientes" not in xls.sheet_names:
            st.error("El archivo base no tiene la hoja 'MaestroClientes'.")
        else:
            clientes = pd.read_excel(xls, sheet_name="MaestroClientes")
            clientes["CUIT"] = clientes["CUIT"].astype(str).str.strip()
            clientes = clientes.drop_duplicates(subset=["CUIT"], keep="first")

            if "Fleteros" not in xls.sheet_names:
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
            else:
                fleteros_df = pd.read_excel(xls, sheet_name="Fleteros")
                lista_fleteros = fleteros_df["Fletero"].dropna().unique().tolist()

                galicia = galicia.merge(clientes, on="CUIT", how="left", suffixes=("", "_mc"))
                galicia = galicia.drop_duplicates(subset=["CUIT","Crédito","Concepto"], keep="first")

                con_fletero = galicia[galicia["Fletero"].notna()]
                if not con_fletero.empty:
                    resumen_fleteros = con_fletero.groupby("Fletero").agg(
                        CantidadTransferencias=("Crédito", "count"),
                        Total=("Crédito", "sum")
                    ).reset_index()

                    resumen_fleteros["Total"] = pd.to_numeric(resumen_fleteros["Total"], errors="coerce").fillna(0)
                    resumen_fleteros["Total_fmt"] = resumen_fleteros["Total"].map(lambda x: f"${x:,.2f}")

                    st.subheader("Resumen de transferencias por Fletero")
                    st.dataframe(resumen_fleteros[["Fletero","CantidadTransferencias","Total_fmt"]])

                    # Control global
                    total_transferencias_resumen = resumen_fleteros["CantidadTransferencias"].sum()
                    total_monto_resumen = resumen_fleteros["Total"].sum()

                    st.subheader("Control de Totales")
                    if total_transferencias_resumen == total_transferencias_galicia:
                        st.success(f"✔ Cantidad de transferencias coincide: {total_transferencias_resumen}")
                    else:
                        st.error(f"✘ Diferencia en cantidad de transferencias. Galicia: {total_transferencias_galicia}, Resumen: {total_transferencias_resumen}")

                    if abs(total_monto_resumen - total_monto_galicia) < 0.01:
                        st.success(f"✔ Monto total coincide: ${total_monto_resumen:,.2f}")
                    else:
                        st.error(f"✘ Diferencia en monto total. Galicia: ${total_monto_galicia:,.2f}, Resumen: ${total_monto_resumen:,.2f}")

                    # ✅ Guardar historial por fecha
                    fecha_proceso = datetime.today().strftime("%Y-%m-%d")
                    historial = resumen_fleteros.copy()
                    historial["Fecha"] = fecha_proceso

                    if "Historial" not in xls.sheet_names:
                        with pd.ExcelWriter(BASE_FILE, mode="a", engine="openpyxl") as writer:
                            historial.to_excel(writer, sheet_name="Historial", index=False)
                    else:
                        historial_existente = pd.read_excel(xls, sheet_name="Historial")
                        historial_completo = pd.concat([historial_existente, historial], ignore_index=True)
                        with pd.ExcelWriter(BASE_FILE, mode="a", engine="openpyxl", if_sheet_exists="replace") as writer:
                            historial_completo.to_excel(writer, sheet_name="Historial", index=False)

                    st.success(f"Historial guardado para la fecha {fecha_proceso} ✅")

                    # Desglose por fletero
                    st.subheader("Detalle por Fletero")
                    for fletero in resumen_fleteros["Fletero"]:
                        with st.expander(f"Fletero: {fletero}"):
                            detalle = con_fletero[con_fletero["Fletero"] == fletero][["Cliente","CUIT","Crédito"]]
                            detalle["Crédito"] = detalle["Crédito"].map(lambda x: f"${x:,.2f}")
                            st.dataframe(detalle)

                    # ✅ Visualización del historial
                    if "Historial" in xls.sheet_names:
                        historial_df = pd.read_excel(xls, sheet_name="Historial")
                        historial_df["Fecha"] = pd.to_datetime(historial_df["Fecha"], errors="coerce").dt.date

                        st.subheader("Historial de transferencias")
                        fechas_disponibles = historial_df["Fecha"].dropna().unique()
                        fecha_seleccionada = st.selectbox("Seleccioná una fecha", options=sorted(fechas_disponibles))

                        historial_filtrado = historial_df[historial_df["Fecha"] == fecha_seleccionada]
                        st.dataframe(historial_filtrado[["Fecha","Fletero","CantidadTransferencias","Total"]])

                        total_transf = historial_filtrado["CantidadTransferencias"].sum()
                        total_monto = historial_filtrado["Total"].sum()
                        st.info(f"Totales del {fecha_seleccionada}: {total_transf} transferencias, ${total_monto:,.2f}")