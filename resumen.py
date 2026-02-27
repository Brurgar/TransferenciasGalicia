import streamlit as st
import pandas as pd
from datetime import datetime
from fleteros import BASE_FILE

def mostrar_resumen(galicia):
    st.subheader("Resumen de transferencias")

    # Convertir columna Crédito a numérica para evitar errores de tipo
    if "Crédito" in galicia.columns:
        galicia["Crédito"] = pd.to_numeric(galicia["Crédito"], errors="coerce")

    # Totales del resumen (todos los registros con fletero asignado)
    total_transferencias_resumen = len(galicia)
    total_monto_resumen = galicia["Crédito"].sum()

    # Totales del extracto (control cruzado)
    total_transferencias_extracto = len(galicia)
    total_monto_extracto = galicia["Crédito"].sum()

    # Mostrar totales generales con formato
    st.write("Total de transferencias Galicia:", total_transferencias_resumen)
    st.write("Total monto Galicia:", f"{total_monto_resumen:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Control cruzado
    st.subheader("Control cruzado con extracto")
    diferencia = total_monto_resumen - total_monto_extracto
    if (total_transferencias_resumen == total_transferencias_extracto) and (diferencia == 0):
        st.success("✅ Los totales coinciden con el extracto de Galicia")
    else:
        st.error("❌ Los totales NO coinciden con el extracto")
        st.write("Totales en resumen → Transferencias:", total_transferencias_resumen,
                 "Monto:", f"{total_monto_resumen:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.write("Totales en extracto → Transferencias:", total_transferencias_extracto,
                 "Monto:", f"{total_monto_extracto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.write("Diferencia de montos:", f"{diferencia:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Resumen por fletero
    if "Fletero" in galicia.columns:
        resumen_fleteros = galicia.groupby("Fletero").agg({
            "Cliente": "count",
            "Crédito": "sum"
        }).reset_index()
        resumen_fleteros.rename(columns={"Cliente": "Cantidad de transferencias", "Crédito": "Monto total"}, inplace=True)

        # Enumerar desde 1
        resumen_fleteros.index = resumen_fleteros.index + 1

        # Formatear números
        resumen_fleteros["Monto total"] = resumen_fleteros["Monto total"].map(
            lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

        st.write("Resumen por fletero:")
        st.dataframe(resumen_fleteros)

        # Expander por cada fletero con detalle de clientes
        st.subheader("Detalle por fletero")
        for _, row in resumen_fleteros.iterrows():
            fletero = row["Fletero"]
            detalle = galicia[galicia["Fletero"] == fletero][["Cliente", "CUIT", "Crédito"]].reset_index(drop=True)
            detalle.index = detalle.index + 1
            detalle["Crédito"] = detalle["Crédito"].map(
                lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )
            with st.expander(f"Fletero: {fletero}"):
                st.dataframe(detalle)

    # Guardar histórico por fecha con detalle por fletero
    if st.button("Guardar histórico"):
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Totales generales
        historial_general = pd.DataFrame([{
            "Fecha": fecha,
            "Total transferencias": total_transferencias_resumen,
            "Monto total": total_monto_resumen
        }])

        # Detalle por fletero
        resumen_fleteros["Fecha"] = fecha
        historial_fleteros = resumen_fleteros[["Fecha", "Fletero", "Cantidad de transferencias", "Monto total"]]

        try:
            with pd.ExcelWriter(BASE_FILE, mode="a", engine="openpyxl", if_sheet_exists="overlay") as writer:
                historial_general.to_excel(writer, sheet_name="Historial", index=False, header=False, startrow=writer.sheets["Historial"].max_row)
                historial_fleteros.to_excel(writer, sheet_name="HistorialFleteros", index=False, header=False, startrow=writer.sheets["HistorialFleteros"].max_row)
            st.success("Histórico actualizado ✅")
        except Exception:
            with pd.ExcelWriter(BASE_FILE, mode="a", engine="openpyxl", if_sheet_exists="replace") as writer:
                historial_general.to_excel(writer, sheet_name="Historial", index=False)
                historial_fleteros.to_excel(writer, sheet_name="HistorialFleteros", index=False)
            st.success("Histórico creado ✅")

    # Detalle completo
    st.subheader("Detalle completo de transferencias")
    detalle_completo = galicia.reset_index(drop=True)
    detalle_completo.index = detalle_completo.index + 1
    detalle_completo["Crédito"] = detalle_completo["Crédito"].map(
        lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    st.dataframe(detalle_completo)