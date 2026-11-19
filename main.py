import csv
import os
import time
import xml.etree.ElementTree as ET
import xmlrpc.client

# 1. CONEXIÓN Y AUTENTICACIÓN XML-RPC
# Obtenemos la dirección del servidor XML-RPC y leemos las credenciales locales (~/.one/one_auth)
XMLRPC_ENDPOINT = os.environ.get("ONE_XMLRPC", "http://localhost:2633/RPC2")
with open(os.path.expanduser("~/.one/one_auth"), "r", encoding="utf-8") as f:
    AUTH = f.read().strip()

server = xmlrpc.client.ServerProxy(XMLRPC_ENDPOINT)

# 2. TRADUCIR NOMBRES DE PLANTILLA A ID (Por si el CSV trae el nombre en vez del número)
# one.templatepool.info(sesion, filtro_usuario=-2 [todas], inicio=-1, fin=-1)
exito, xml_plantillas, *_ = server.one.templatepool.info(AUTH, -2, -1, -1)
plantillas_por_nombre = {}
if exito:
    raiz = ET.fromstring(xml_plantillas)
    for tpl in raiz.findall("VMTEMPLATE"):
        plantillas_por_nombre[tpl.find("NAME").text] = int(tpl.find("ID").text)

# 3. LEER CSV DE ENTRADA Y CREAR MÁQUINAS
resultados = []

with open("maquinas.csv", mode="r", encoding="utf-8") as f_entrada:
    lector = csv.DictReader(f_entrada)

    for fila in lector:
        plantilla = fila["plantilla"].strip()
        nombre_vm = fila["vm_name"].strip()

        # Si es un número usamos el ID directo; si es texto buscamos su ID en el diccionario
        template_id = int(plantilla) if plantilla.isdigit() else plantillas_por_nombre[plantilla]

        # Llamada XML-RPC para crear la VM a partir de la plantilla
        # Parámetros: (sesion, id_plantilla, nombre_vm, hold=False, extra_template="", persistente=False)
        exito, respuesta, *_ = server.one.template.instantiate(
            AUTH, template_id, nombre_vm, False, "", False
        )

        if exito:
            vm_id = int(respuesta)
            ip_asignada = "Sin IP"

            # Consultamos la información de la VM hasta que OpenNebula le asigne IP (máx. 30 seg)
            for _ in range(10):
                ok_info, xml_vm, *_ = server.one.vm.info(AUTH, vm_id)
                if ok_info:
                    nodo_ip = ET.fromstring(xml_vm).find(".//TEMPLATE/NIC/IP")
                    if nodo_ip is not None and nodo_ip.text:
                        ip_asignada = nodo_ip.text
                        break
                time.sleep(3)

            resultados.append({"id": vm_id, "ip": ip_asignada})
            print(f"Creada VM -> ID: {vm_id} | IP: {ip_asignada}")
        else:
            print(f"Error creando {nombre_vm}: {respuesta}")

# 4. GUARDAR CSV DE SALIDA (Solo ID e IP)
with open("resultado_vms.csv", mode="w", newline="", encoding="utf-8") as f_salida:
    escritor = csv.DictWriter(f_salida, fieldnames=["id", "ip"])
    escritor.writeheader()
    escritor.writerows(resultados)