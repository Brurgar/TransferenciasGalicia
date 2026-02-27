import pandas as pd
from openpyxl import load_workbook

archivo = r"D:\Catamarca\Resumen Banco Fleteros.xlsm"

# 1. Leer MaestroClientes
maestro = pd.read_excel(archivo, sheet_name="MaestroClientes").dropna(how="all")
maestro["CUIT"] = maestro["CUIT"].astype(str).str.strip()

# 2. Leer Galicia
galicia = pd.read_excel(archivo, sheet_name="Galicia").dropna(how="all")
galicia["CUIT"] = galicia["CUIT"].astype(str).str.strip()

# 3. Detectar CUIT nuevos
nuevos = galicia[~galicia["CUIT"].isin(maestro["CUIT"])]
if not nuevos.empty:
    print("Se encontraron clientes nuevos:")
    print(nuevos[["CUIT", "Importe"]])
    nuevos_registros = nuevos[["CUIT"]].drop_duplicates()
    nuevos_registros["Cliente"] = "DESCONOCIDO"
    nuevos_registros["Fletero"] = "SIN ASIGNAR"
    maestro = pd.concat([maestro, nuevos_registros], ignore_index=True)

# 4. Actualizar directamente la pestaña MaestroClientes en el mismo archivo
book = load_workbook(archivo)
with pd.ExcelWriter(archivo, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
    writer.book = book
    maestro.to_excel(writer, sheet_name="MaestroClientes", index=False)

print("\nLa pestaña MaestroClientes fue actualizada con los nuevos clientes.")