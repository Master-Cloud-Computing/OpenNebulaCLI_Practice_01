import csv
import os
import xmlrpc.client

# 1. CONEXIÓN Y AUTENTICACIÓN XML-RPC
XMLRPC_ENDPOINT = os.environ.get("ONE_XMLRPC", "http://localhost:2633/RPC2")
with open(os.path.expanduser("~/.one/one_auth"), "r", encoding="utf-8") as f:
    AUTH = f.read().strip()

server = xmlrpc.client.ServerProxy(XMLRPC_ENDPOINT)
ARCHIVO_RESULTADOS = "resultado_vms.csv"

# 2. LEER LOS IDs Y ELIMINAR LAS MÁQUINAS
if os.path.exists(ARCHIVO_RESULTADOS):
    with open(ARCHIVO_RESULTADOS, mode="r", encoding="utf-8") as f_entrada:
        lector = csv.DictReader(f_entrada)

        for fila in lector:
            vm_id_texto = fila["id"].strip()

            if vm_id_texto.isdigit():
                vm_id = int(vm_id_texto)
                exito, respuesta, *_ = server.one.vm.action(AUTH, "terminate-hard", vm_id)

                if exito:
                    print(f"Máquina con ID {vm_id} eliminada correctamente.")
                else:
                    print(f"Error al eliminar la VM {vm_id}: {respuesta}")

    # 3. ELIMINAR EL ARCHIVO CSV DE SALIDA
    os.remove(ARCHIVO_RESULTADOS)
    print(f"Archivo '{ARCHIVO_RESULTADOS}' eliminado.")
else:
    print(f"No se encontró el archivo '{ARCHIVO_RESULTADOS}'.")