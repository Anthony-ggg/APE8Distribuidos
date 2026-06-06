import socket
import datetime

# --- CONFIGURACIÓN DEL SERVIDOR ---
HOST_SERVIDOR = '192.168.1.10'  # Escucha estrictamente en tu interfaz LAN
PUERTO_SERVIDOR = 7001          # Puerto configurado
# Las IPs exactas de las PCs que deben sincronizarse para que el servidor finalice
IPS_ESPERADAS = {'192.168.1.11', 
                 '192.168.1.12', 
                 #'192.168.1.13'
                 } 

def iniciar_coordinador(host, puerto, ips_esperadas):
    # Crear el socket TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Permitir reusar la dirección si el script se reinicia rápido
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server_socket.bind((host, puerto))
    server_socket.listen(5)
    
    print("="*55)
    print(" 🕒 COORDINADOR DE RELOJES TCP (ALGORITMO DE CRISTIAN) 🕒 ")
    print("="*55)
    print("[*] Inicializando servidor maestro...")
    print(f"[*] Escuchando exclusivamente en la IP: {host}")
    print(f"[*] Puerto configurado: {puerto}")
    print(f"[*] IPs obligatorias a sincronizar: {', '.join(ips_esperadas)}")
    print("[*] Estado: Esperando a que las PCs clientes se conecten...\n")

    # Aquí guardaremos las IPs que ya se han ido conectando
    ips_atendidas = set()

    # El bucle se repite mientras la lista de atendidas no sea igual a la de esperadas
    while ips_atendidas != ips_esperadas:
        client_socket, addr = server_socket.accept()
        ip_cliente = addr[0]
        
        print(f"[+] ¡Nueva petición de sincronización recibida!")
        print(f"    - Desde el cliente con IP: {ip_cliente}:{addr[1]}")
        
        # t2: Hora exacta del servidor
        t2 = datetime.datetime.now()
        
        # Enviar t2 al cliente como cadena de texto
        tiempo_str = t2.strftime('%Y-%m-%d %H:%M:%S.%f')
        client_socket.send(tiempo_str.encode('utf-8'))
        
        print(f"    - [t2] Hora exacta enviada: {tiempo_str}")
        print(f"    - Conexión con {ip_cliente} finalizada correctamente.")
        
        client_socket.close()

        # Verificamos si la IP está en nuestra lista de control
        if ip_cliente in ips_esperadas:
            ips_atendidas.add(ip_cliente) # La tachamos de la lista
            faltan = ips_esperadas - ips_atendidas
            
            if faltan:
                print(f"    - [!] Aún faltan por conectarse: {', '.join(faltan)}")
                print("\n[*] Esperando la siguiente petición...")
        else:
            print(f"    - [?] Aviso: Se atendió a una IP no requerida ({ip_cliente}).")
            print("\n[*] Esperando la siguiente petición...")

    # Una vez que sale del bucle
    print("\n" + "="*55)
    print("✅ Todas las IPs especificadas han sido sincronizadas.")
    print("[*] Finalizando el proceso. Cerrando servidor coordinador...")
    print("="*55)
    server_socket.close()

if __name__ == '__main__':
    # Se pasan los parámetros definidos en la parte superior
    iniciar_coordinador(HOST_SERVIDOR, PUERTO_SERVIDOR, IPS_ESPERADAS)