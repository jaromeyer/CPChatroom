import network
import socket
from machine import Pin
import select
import time

def send(message):
    for socket in sockets:
        try:
            socket.sendall(message)
        except:
            socket.close()
            
def handler(pin):
    send(b'feef')

ap_mode = False
recvPollers = []
sockets = []
clients = []

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
            try:
                data = descriptor.recv(500)
                print("Received: ", str(data, 'utf8'))
                if str(data, 'utf8') == "feef":
                    send(b'ACK received: %s' % (str(data, 'utf8')))
            except:
                print("raap")
                descriptor.close()
    # Handle UART com
