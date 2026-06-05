import socket
import threading
import time

# ==============================================================================
# CONFIGURACIÓN DE LA RED LAN (Modificar según la PC actual)
# ==============================================================================
# Mapeo de IPs de la guía práctica
NODOS = {
    "PC1": "192.168.1.10",
    "PC2": "192.168.1.11",
    "PC3": "192.168.1.12",
    "PC4": "192.168.1.13",
    "PC5": "192.168.1.14"
}

PUERTO = 5000  # Puerto común para el chat

# Identifica esta máquina (CAMBIAR ESTO en cada PC antes de ejecutar)
MI_NOMBRE = "PC1"  # Ej: Cambiar a "PC2", "PC3", etc., en las otras laptops
MI_IP = NODOS[MI_NOMBRE]

# ==============================================================================
# VARIABLES DEL ALGORITMO DE LAMPORT
# ==============================================================================
reloj_logico = 0
lock = threading.Lock()  # Para evitar condiciones de carrera al modificar el reloj

# ==============================================================================
# HILO RECEPTOR (Escucha mensajes de otras PCs)
# ==============================================================================
def recibir_mensajes():
    global reloj_logico
    
    # Crear socket UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((MI_IP, PUERTO))
    
    print(f"[*] Servidor Lamport activo en {MI_IP}:{PUERTO}. Esperando mensajes...\n")
    
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            mensaje_decodificado = data.decode('utf-8')
            
            # El mensaje viene en formato: "RELOJ_RECIBIDO|ORIGEN|TEXTO"
            partes = mensaje_decodificado.split('|', 2)
            if len(partes) < 3:
                continue
                
            reloj_recibido = int(partes[0])
            origen = partes[1]
            texto = partes[2]
            
            with lock:
                reloj_anterior = reloj_logico
                # REGLA DE RECEPCIÓN LAMPORT: max(Mi_Contador, Contador_Recibido) + 1
                reloj_logico = max(reloj_logico, reloj_recibido) + 1
                
                print(f"\n[MENSAJE RECIBIDO desde {origen}]")
                print(f" ├─ Contenido: '{texto}'")
                print(f" ├─ Reloj adjunto en paquete: L = {reloj_recibido}")
                print(f" ├─ Mi reloj antes: {reloj_anterior}")
                print(f" └─ Mi reloj ajustado: L = {reloj_logico}")
                print("Escribe el nombre del destino (ej: PC2) o 'salir': ", end="", flush=True)
                
        except Exception as e:
            print(f"[-] Error al recibir mensaje: {e}")
            break

# ==============================================================================
# HILO EMISOR (Interfaz de usuario para enviar)
# ==============================================================================
def enviar_mensajes():
    global reloj_logico
    
    # Crear socket UDP para envíos
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    time.sleep(1) # Esperar a que el hilo receptor imprima el inicio
    
    while True:
        destino = input("Escribe el nombre del destino (ej: PC2) o 'salir': ").strip().upper()
        
        if destino == "SALIR":
            print("[*] Saliendo del chat...")
            sock.close()
            import os; os._exit(0)
            
        if destino not in NODOS:
            print(f"[-] Destino '{destino}' no válido. Opciones: PC1, PC2, PC3, PC4, PC5.")
            continue
            
        if destino == MI_NOMBRE:
            print("[-] No te puedes enviar un mensaje a ti mismo en esta práctica.")
            continue
            
        texto = input(f"Mensaje para {destino}: ")
        
        with lock:
            # REGLA DE ENVÍO LAMPORT: Incrementar contador en 1 antes de enviar
            reloj_logico += 1
            
            # Formatear el payload para que viaje en la red
            # Formato: "RELOJ|ORIGEN|TEXTO"
            payload = f"{reloj_logico}|{MI_NOMBRE}|{texto}"
            
            ip_destino = NODOS[destino]
            sock.sendto(payload.encode('utf-8'), (ip_destino, PUERTO))
            
            print(f"[+] Mensaje enviado a {destino}. Mi reloj actual: L = {reloj_logico}\n")

# ==============================================================================
# FLUJO PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    print("-" * 50)
    print(f"   CARRERA DE COMPUTACIÓN UNL - RELOJES DE LAMPORT")
    print("-" * 50)
    print(f"Nodo Activo: {MI_NOMBRE} | IP Estática: {MI_IP}")
    print("-" * 50)
    
    # Iniciar el hilo que escucha de forma asíncrona
    hilo_receptor = threading.Thread(target=recibir_mensajes, daemon=True)
    hilo_receptor.start()
    
    # Iniciar la interfaz de envío en el hilo principal
    enviar_mensajes()