# 📡 Práctica: Algoritmos Distribuidos en Python 3
## Sistemas Distribuidos — Universidad

---

## 📁 Estructura del Proyecto

```
distributed_algorithms/
│
├── cristian/
│   ├── servidor_cristian.py     ← Servidor de tiempo (UDP)
│   └── cliente_cristian.py      ← Cliente que sincroniza su reloj
│
├── berkeley/
│   ├── coordinador_berkeley.py  ← Maestro: calcula promedio y offsets
│   └── nodo_berkeley.py         ← Esclavo: responde y aplica offset
│
├── lamport/
│   ├── servidor_lamport.py      ← Proceso A (TCP)
│   └── cliente_lamport.py       ← Proceso B (TCP)
│
└── vector_clock/
    ├── servidor_vector.py       ← Proceso 0 (TCP)
    └── cliente_vector.py        ← Proceso 1..4 (TCP)
```

---

## ✅ Requisitos

```bash
# Python 3 y módulos estándar (no requiere pip install)
python3 --version   # Debe ser >= 3.6
```

---

## 1️⃣ ALGORITMO DE CRISTIAN (UDP)

### Teoría
El cliente solicita el tiempo al servidor. Mide el RTT y ajusta
su reloj sumando `T_servidor + (RTT / 2)`.

```
Cliente         Servidor
  |---REQUEST_TIME--->|   (T1 = time.time())
  |<--[timestamp]-----|   (T4 = time.time())
  RTT = T4 - T1
  Delay = RTT / 2
  T_ajustado = T_servidor + Delay
```

### Cómo ejecutar (misma PC)

**Terminal 1 — Servidor:**
```bash
cd cristian/
python3 servidor_cristian.py
```

**Terminal 2 — Cliente:**
```bash
cd cristian/
python3 cliente_cristian.py
```

### Cómo ejecutar en LAN (2 PCs)

En PC1 (servidor):
```bash
python3 servidor_cristian.py
# Anota la IP: ip addr show  →  p. ej. 192.168.1.10
```

En PC2 (cliente), edita `cliente_cristian.py`:
```python
SERVER_HOST = '192.168.1.10'  # IP de PC1
```
```bash
python3 cliente_cristian.py
```

### Salida esperada (Servidor)
```
============================================================
  SERVIDOR DE TIEMPO - ALGORITMO DE CRISTIAN
============================================================
  Escuchando en 0.0.0.0:5000 (UDP)
  Hora actual del servidor: 14:32:10
  Esperando clientes... (Ctrl+C para detener)
============================================================

[RECIBIDO]  Cliente: ('127.0.0.1', 52341) | Mensaje: 'REQUEST_TIME' | T_recv: 1748612330.123456
[ENVIADO]   → ('127.0.0.1', 52341) | T_respuesta: 1748612330.123489
            Hora legible: 14:32:10
```

### Salida esperada (Cliente)
```
============================================================
  CLIENTE DE TIEMPO - ALGORITMO DE CRISTIAN
============================================================
  Servidor objetivo: 127.0.0.1:5000
  Hora LOCAL antes de sync: 14:32:09
============================================================

── Sincronización #1 ────────────────────────────────────
  [ENVIADO]   REQUEST_TIME → 127.0.0.1:5000
  [T1]        Tiempo de envío:     1748612330.115000 s  (14:32:10.115000)
  [RECIBIDO]  Timestamp del servidor: 1748612330.123489 s
  [T4]        Tiempo de recepción:    1748612330.125000 s

  ┌─ RESULTADOS ─────────────────────────────────────┐
  │  RTT (ida+vuelta):    10.000 ms
  │  Delay (estimado):    5.000 ms
  │  Hora SERVIDOR:       14:32:10
  │  Hora AJUSTADA:       1748612330.128489 s (Unix)
  │  Diferencia con local:3.489 ms
  └──────────────────────────────────────────────────┘

ESTADÍSTICAS FINALES
  RTT mínimo:   8.123 ms
  RTT máximo:   12.456 ms
  RTT promedio: 9.876 ms
  Delay prom.:  4.938 ms
```

---

## 2️⃣ ALGORITMO DE BERKELEY (TCP)

### Teoría
El coordinador recopila tiempos de todos los nodos, calcula el
promedio y envía a cada nodo el offset que debe aplicar.

```
Coordinador        Nodo1      Nodo2      Nodo3
    |--GET_TIME-->|
    |<--T_nodo1--|
    |--GET_TIME------------>|
    |<----------T_nodo2-----|
    |--GET_TIME------------------------->|
    |<--------------------------T_nodo3--|
    | (calcula promedio)
    |--offset1-->|
    |--offset2------------>|
    |--offset3-------------------------->|
```

### Cómo ejecutar (misma PC — 4 terminales)

**Terminal 1 — Nodo 1:**
```bash
cd berkeley/
python3 nodo_berkeley.py --puerto 6001
```

**Terminal 2 — Nodo 2:**
```bash
python3 nodo_berkeley.py --puerto 6002
```

**Terminal 3 — Nodo 3:**
```bash
python3 nodo_berkeley.py --puerto 6003
```

**Terminal 4 — Coordinador (después de iniciar los nodos):**
```bash
python3 coordinador_berkeley.py
```

### Cómo ejecutar en LAN (4 PCs)

En cada PC esclava, ejecuta:
```bash
python3 nodo_berkeley.py --puerto 6001  # PC2
python3 nodo_berkeley.py --puerto 6001  # PC3
python3 nodo_berkeley.py --puerto 6001  # PC4
```

En `coordinador_berkeley.py`, edita la lista NODOS:
```python
NODOS = [
    ('192.168.1.11', 6001),   # PC2
    ('192.168.1.12', 6001),   # PC3
    ('192.168.1.13', 6001),   # PC4
]
```

### Salida esperada (Coordinador)
```
────────────────────────────────────────────────────────────
  INICIANDO RONDA DE SINCRONIZACIÓN
  Tiempo coordinador: 14:35:00
────────────────────────────────────────────────────────────

[PASO 1] Solicitando tiempo a todos los nodos...
  [CONECTADO]  Nodo 127.0.0.1:6001
  [CONECTADO]  Nodo 127.0.0.1:6002
  [CONECTADO]  Nodo 127.0.0.1:6003
  [RECIBIDO]   Nodo 127.0.0.1:6001 → T = 1748612100.010000 s  (14:35:00)
  [RECIBIDO]   Nodo 127.0.0.1:6002 → T = 1748612100.250000 s  (14:35:00)
  [RECIBIDO]   Nodo 127.0.0.1:6003 → T = 1748612099.800000 s  (14:35:00)

[PASO 2] Calculando promedio de tiempos...
  T_coordinador = 1748612100.000000 s
  T_nodo 127.0.0.1:6001 = 1748612100.010000 s  (diferencia: +10.0 ms)
  T_nodo 127.0.0.1:6002 = 1748612100.250000 s  (diferencia: +250.0 ms)
  T_nodo 127.0.0.1:6003 = 1748612099.800000 s  (diferencia: -200.0 ms)

  Tiempos recopilados: 4
  T_promedio = 1748612100.015000 s  (14:35:00)

[PASO 3] Calculando y enviando offsets a cada nodo...
  Coordinador debe ajustar: +15.000 ms
  → Nodo 127.0.0.1:6001 | offset = +5.000 ms  | adelantar
  → Nodo 127.0.0.1:6002 | offset = -235.000 ms | atrasar
  → Nodo 127.0.0.1:6003 | offset = +215.000 ms | adelantar

[OK] Ronda completada. 3/3 nodos sincronizados.
```

---

## 3️⃣ RELOJES LÓGICOS DE LAMPORT (TCP)

### Teoría
Sin reloj global, se asignan timestamps lógicos a eventos para
determinar causalidad. Si A envía a B, entonces A → B.

```
Regla 1: Evento LOCAL   → L = L + 1
Regla 2: ENVÍO de msg   → L = L + 1, adjuntar L al mensaje
Regla 3: RECEPCIÓN msg  → L = max(L_local, L_msg) + 1
```

### Cómo ejecutar

**Terminal 1:**
```bash
cd lamport/
python3 servidor_lamport.py
```

**Terminal 2:**
```bash
python3 cliente_lamport.py
```

**Probar concurrencia (múltiples clientes simultáneos):**
```bash
python3 cliente_lamport.py &
python3 cliente_lamport.py &
python3 cliente_lamport.py &
wait
```

### Salida esperada (Cliente)
```
  ──────────────────────────────────────────────────
  [14:40:01] EVENTO: LOCAL (preparación)
  Descripción: Preparando mensaje #1
  Reloj ANTES:  L = 1
  Reloj DESPUÉS: L = 2
  ──────────────────────────────────────────────────

  ──────────────────────────────────────────────────
  [14:40:01] EVENTO: ENVÍO
  Descripción: Contenido: 'Mensaje-1-de-PROCESO_B' | TS=3
  Reloj ANTES:  L = 2
  Reloj DESPUÉS: L = 3
  ──────────────────────────────────────────────────

  ──────────────────────────────────────────────────
  [14:40:01] EVENTO: RECEPCIÓN (ACK)
  Descripción: ACK recibido | TS_servidor=5
  Reloj ANTES:  L = 3
  Reloj DESPUÉS: L = 6
  ──────────────────────────────────────────────────
  [CAUSALIDAD] Mi reloj (6) > TS servidor (5)
               → Este proceso tiene eventos más recientes.
```

---

## 4️⃣ VECTORES DE TIEMPO (TCP)

### Teoría
El vector de tiempo tiene una posición por proceso.
Permite detectar eventos **concurrentes** (que Lamport no puede).

```
V = [V0, V1, V2, V3, V4]   ← 5 procesos

Regla 1: Evento local        → V[i] += 1
Regla 2: Envío de msg        → V[i] += 1, adjuntar V completo
Regla 3: Recepción de msg M  → V[j] = max(V[j], M.V[j]) para todo j
                                V[i] += 1

A → B si:  A.V[j] ≤ B.V[j] para todo j  (y alguno estrictamente menor)
A || B si: ¬(A→B) y ¬(B→A)              ← CONCURRENTES
```

### Cómo ejecutar

**Terminal 1 — Servidor (Proceso 0):**
```bash
cd vector_clock/
python3 servidor_vector.py
```

**Terminales 2, 3, 4, 5 — Clientes (Procesos 1..4):**
```bash
python3 cliente_vector.py --id 1
python3 cliente_vector.py --id 2
python3 cliente_vector.py --id 3
python3 cliente_vector.py --id 4
```

### Salida esperada (Cliente --id 1)
```
  ┌─ LOCAL (trabajo #1) ──────────────────────────────
  │  Proceso 1 realiza trabajo interno
  │  Vector ANTES:  [0, 0, 0, 0, 0]
  │  Vector DESPUÉS:[0, 1, 0, 0, 0]
  └──────────────────────────────────────────────────

  ┌─ ENVÍO mensaje #1 ────────────────────────────────
  │  Contenido: 'Evento-1 del Proceso-1'
  │  Vector ANTES:  [0, 1, 0, 0, 0]
  │  Vector DESPUÉS:[0, 2, 0, 0, 0]
  └──────────────────────────────────────────────────

  ┌─ RECEPCIÓN ACK #1 ────────────────────────────────
  │  V_servidor recibido: [1, 2, 0, 0, 0]
  │  Vector ANTES:  [0, 2, 0, 0, 0]
  │  Vector DESPUÉS:[1, 3, 0, 0, 0]
  └──────────────────────────────────────────────────
  [CAUSALIDAD] P1(envío) → P0(ACK)  (P1 causalmente ANTES)

  RESUMEN: ANÁLISIS DE CAUSALIDAD ENTRE EVENTOS PROPIOS
  E1=[0, 2, 0, 0, 0] vs E2=[0, 4, 0, 0, 0]
  → E1 → E2  (E1 causalmente ANTES)
```

---

## 🔬 Pruebas en LAN (Switch físico)

### Topología recomendada
```
          Switch/Router
         /    |    \
       PC1   PC2   PC3
   (servidor) (cliente1) (cliente2)
```

### Pasos
1. Conectar todas las PCs al mismo switch
2. Asignar IPs estáticas o verificar las asignadas por DHCP:
   ```bash
   ip addr show    # Linux
   ```
3. Verificar conectividad:
   ```bash
   ping 192.168.1.11   # Desde PC1 a PC2
   ```
4. Abrir los puertos en el firewall (si UFW está activo):
   ```bash
   sudo ufw allow 5000/udp   # Cristian
   sudo ufw allow 6000/tcp   # Berkeley coordinador
   sudo ufw allow 6001/tcp   # Berkeley nodo 1
   sudo ufw allow 7000/tcp   # Lamport
   sudo ufw allow 8000/tcp   # Vector Clock
   ```
5. Editar las IPs en los archivos de cliente/coordinador y ejecutar.

---

## 📡 Captura en Wireshark

### Instalar Wireshark
```bash
sudo apt install wireshark
sudo usermod -aG wireshark $USER
# (Cerrar sesión y volver a entrar)
```

### Filtros por algoritmo
| Algoritmo    | Protocolo | Filtro Wireshark         |
|-------------|-----------|--------------------------|
| Cristian     | UDP       | `udp.port == 5000`       |
| Berkeley     | TCP       | `tcp.port == 6000 or tcp.port == 6001` |
| Lamport      | TCP       | `tcp.port == 7000`       |
| Vector Clock | TCP       | `tcp.port == 8000`       |

### Cálculo de RTT en Wireshark
1. Selecciona el paquete de solicitud (REQUEST_TIME)
2. Selecciona el paquete de respuesta (timestamp)
3. En la barra inferior verás el `delta time` entre paquetes
4. O usa: **Statistics → TCP Stream Graphs → Round Trip Time**

---

## 🧵 Pruebas de Concurrencia

### Lamport — múltiples clientes simultáneos
```bash
cd lamport/
# Lanzar 5 clientes en paralelo
for i in $(seq 1 5); do
    python3 cliente_lamport.py &
done
wait
echo "Todos los clientes terminaron"
```

### Vector Clock — todos los procesos simultáneos
```bash
cd vector_clock/
python3 servidor_vector.py &
sleep 1
python3 cliente_vector.py --id 1 &
python3 cliente_vector.py --id 2 &
python3 cliente_vector.py --id 3 &
python3 cliente_vector.py --id 4 &
wait
```

---

## 🔧 Cómo Modificar IPs

En cada archivo de **cliente o coordinador**, busca la sección:
```python
# ─────────────────────────────────────────────
#  CONFIGURACIÓN — cambia SERVER_HOST a la IP
# ─────────────────────────────────────────────
SERVER_HOST = '127.0.0.1'   # ← Cambia esto
```

Reemplaza `'127.0.0.1'` por la IP del servidor en tu red:
```python
SERVER_HOST = '192.168.1.10'   # Ejemplo LAN
```

Los **servidores** ya usan `'0.0.0.0'` (escuchan en todas las interfaces).

---

## 📊 Cómo Calcular RTT Manualmente

```
RTT = T_recepcion_cliente - T_envio_cliente
    = T4 - T1

Ejemplo:
  T1 = 1748612330.115000  (antes de enviar)
  T4 = 1748612330.125000  (después de recibir)
  RTT = 0.010000 s = 10.000 ms
  Delay = RTT / 2 = 5.000 ms
```

En el código de Cristian, estos valores se imprimen en cada
sincronización bajo `[T1]` y `[T4]`.

---

## ❓ Preguntas Frecuentes

**¿Por qué UDP para Cristian y TCP para los demás?**
> Cristian solo necesita un paquete de ida y uno de vuelta.
> UDP es más rápido y el RTT más preciso sin overhead de conexión.
> Los demás algoritmos necesitan fiabilidad (no perder mensajes).

**¿Qué pasa si un nodo de Berkeley no responde?**
> El coordinador lo registra como `[TIMEOUT]` y calcula el promedio
> solo con los nodos que respondieron.

**¿Cómo sé si dos eventos son concurrentes en Vector Clock?**
> Si `A.V[i] > B.V[i]` para algún i Y `A.V[j] < B.V[j]` para otro j,
> entonces A y B son CONCURRENTES (ninguno causó al otro).
> El código lo detecta automáticamente e imprime `|| (CONCURRENTES)`.
