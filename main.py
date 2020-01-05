import uos
import network
import socket
import select
import time
from machine import UART, Pin

ap_mode = False
recvPollers = []
sockets = []
clients = []

def socketSend(message):
    for socket in sockets:
        try:
            socket.sendall(message)
        except:
            socket.close()
            
def generateDataPkg(text):
    data = bytearray(b'\x3A\x00\x01')
    data.extend(text.encode('utf8'))
    for i in range(4-(len(text)%4)):
        data.append(0)
    data.append((~(sum(data)-58)+1)&0xFF)
    return data

def generateDescPkg(dataPkg):
    desc = bytearray(b'\x3a\x4e\x44\x64\x00\x01\x00\x01\x00\x00\x00\x00\x05\xff\x00')
    desc[9], desc[11] = (len(dataPkg)-2,)*2
    desc[14] = (~(sum(desc)-58)+1)&0xFF
    return desc

def casioSend(descPkg, dataPkg):
    uart.write(b'\x15')
    uart.read(1)
    uart.write(descPkg)
    uart.read(1)
    uart.write(dataPkg)
    uart.read(1)
        
def handler(pin):
    dataPkg = generateDataPkg("rtr")
    descPkg = generateDescPkg(dataPkg)
    casioSend(descPkg, dataPkg)

sta_if = network.WLAN(network.STA_IF)
ap_if = network.WLAN(network.AP_IF)

if not sta_if.isconnected():
    print('connecting to network...')
    sta_if.active(True)
    ap_if.active(False)
    sta_if.connect('gurkenterror', 'saas1234')
    while not sta_if.isconnected():
        if sta_if.status() == 3:
            print('network not available, starting ap')
            sta_if.active(False)
            ap_if.active(True)
            ap_if.config(essid="gurkenterror", password="saas1234")
            ap_mode = True
            break

if ap_mode:
    print('network config:', ap_if.ifconfig())
else:
    print('network config:', sta_if.ifconfig())

if not ap_mode:
    s = socket.socket()
    print("connecting")
    s.connect(('192.168.4.1', 65432))
    print("connected")
    clients = eval(s.recv(500))
    print(clients)
    sockets.append(s) 
    recvPoller = select.poll()
    recvPoller.register(s, select.POLLIN)
    recvPollers.append(recvPoller)
    for client in clients:
        s = socket.socket()
        s.connect((client, 65432))
        sockets.append(s)
        recvPoller = select.poll()
        recvPoller.register(s, select.POLLIN)
        recvPollers.append(recvPoller)

listener = socket.socket()
listener.bind(("", 65432))
listener.listen(10)
print("listener started")
 
connPoller = select.poll()
connPoller.register(listener, select.POLLIN)

uos.dupterm(None, 1) # disable REPL on UART(0)
uart = UART(0, 38400)
uart.init(38400, bits=8, parity=None, stop=1, timeout=1000)

button = Pin(0, Pin.IN, Pin.PULL_UP)
button.irq(trigger=Pin.IRQ_FALLING, handler=handler)

# Main loop
while(True):
    # Handle new connections
    connEvents = connPoller.poll(100)
    for descriptor, Event in connEvents:
        print("Got an incoming connection request")
        conn, addr = listener.accept()
        print(conn, addr)
        conn.sendall(str(clients))
        sockets.append(conn)
        clients.append(addr[0])
        recvPoller = select.poll()
        recvPoller.register(conn, select.POLLIN)
        recvPollers.append(recvPoller)

    # Handle new messsages for every socket
    for recvPoller in recvPollers:
        recvEvents = recvPoller.poll(100)
        for descriptor, Event in recvEvents:
            data = descriptor.recv(500)
            print("Received: ", data)
            descPkg = generateDescPkg(data)
            casioSend(descPkg, data)
            
    # Handle UART com
    if uart.any() and uart.read(1) == b'\x15':
        uart.write(b'\x13')
        desc = uart.read(15)
        uart.write(b'\x06')
        msg = uart.read(desc[9]+2)
        uart.write(b'\x06')
        print("".join("%02x " % i for i in msg))
        socketSend(msg)
        try:
            print("Received: ", msg[3:-2].decode("utf8"))
        except:
            print("not unicode")
