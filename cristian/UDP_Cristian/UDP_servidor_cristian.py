import socket
import datetime

# --- CONFIGURACIÓN DEL SERVIDOR UDP ---
HOST_SERVIDOR = '192.168.1.10'      # IP estricta en la red LAN
PUERTO_SERVIDOR = 7001              # Puerto de comunicación
# Las IPs exactas de las PCs que deben sincronizarse para que el servidor finalice
IPS_ESPERADAS = {'192.168.1.11', 
                 '192.168.1.12', 
                 #'192.168.1.13', 
                 #'192.168.1.14'
                 } 

def iniciar_coordinador_udp(host, puerto, ips_esperadas):
    # Crear el socket UDP (SOCK_DGRAM es la clave aquí)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, puerto))
    
    print("="*55)
    print(" 🕒 COORDINADOR UDP (ALGORITMO DE CRISTIAN) 🕒 ")
    print("="*55)
    print("[*] Inicializando servidor maestro...")
    print(f"[*] Escuchando exclusivamente en la IP/Interfaz: {host}")
    print(f"[*] Puerto configurado: {puerto}")
    print(f"[*] IPs obligatorias a sincronizar: {', '.join(ips_esperadas)}")
    print("[*] Estado: Esperando datagramas de las PCs clientes...\n")

    # Aquí guardaremos las IPs que ya enviaron su datagrama
    ips_atendidas = set()

    # El bucle se repite mientras la lista de atendidas no sea igual a la de esperadas
    while ips_atendidas != ips_esperadas:
        # Espera recibir cualquier dato. addr contiene la IP y puerto del cliente
        mensaje, addr = server_socket.recvfrom(1024)
        ip_cliente = addr[0]
        
        print(f"[+] ¡Nuevo datagrama de sincronización recibido!")
        print(f"    - Desde el cliente con IP: {ip_cliente}:{addr[1]}")
        print(f"    - Mensaje recibido: '{mensaje.decode('utf-8')}'")
        
        # t2: Hora exacta del servidor en cuanto recibe el paquete
        t2 = datetime.datetime.now()
        tiempo_str = t2.strftime('%Y-%m-%d %H:%M:%S.%f')
        
        # Envía la hora de vuelta directamente a la dirección del cliente
        server_socket.sendto(tiempo_str.encode('utf-8'), addr)
        
        print(f"    - [t2] Hora exacta enviada: {tiempo_str}")
        print(f"    - Respuesta enviada a {ip_cliente} correctamente.")

        # Verificamos si la IP está en nuestra lista de control
        if ip_cliente in ips_esperadas:
            ips_atendidas.add(ip_cliente) # La tachamos de la lista
            faltan = ips_esperadas - ips_atendidas
            
            if faltan:
                print(f"    - [!] Aún faltan por enviar datagrama: {', '.join(faltan)}")
                print("\n[*] Esperando el siguiente datagrama...")
        else:
            print(f"    - [?] Aviso: Se respondió a una IP no requerida ({ip_cliente}).")
            print("\n[*] Esperando el siguiente datagrama...")

    # Una vez que sale del bucle
    print("\n" + "="*55)
    print("✅ Todas las IPs especificadas han sido sincronizadas por UDP.")
    print("[*] Finalizando el proceso. Cerrando socket del coordinador...")
    print("="*55)
    server_socket.close()

if __name__ == '__main__':
    # Se pasan los parámetros definidos en la parte superior
    iniciar_coordinador_udp(HOST_SERVIDOR, PUERTO_SERVIDOR, IPS_ESPERADAS)