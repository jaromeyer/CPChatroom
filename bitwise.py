import serial

def generateMsg(text):
    msg = bytearray.fromhex("3A 00 01")
    msg.extend(text.encode('utf8'))
    for i in range(4-(len(text)%4)):
        msg.append(0)
    msg.append((~(sum(msg)-58)+1).to_bytes(8, byteorder='big', signed=True)[-1])
    return msg
    
def generateDesc(msg):
    desc = bytearray.fromhex("3A 4E 44 64 00 01 00 01 00 00 00 00 05 FF 00")
    desc[9], desc[11] = (len(msg)-2,)*2
    desc[14] = (~(sum(desc)-58)+1).to_bytes(8, byteorder='big', signed=True)[-1]
    return desc

def generateSend():
    msg = generateMsg("oiblin idi nahui asdf")
    desc = generateDesc(msg)
    
def printHex(barray):
    print("Bytearray: ", ''.join(format(x, '02x') for x in barray))

with serial.Serial('/dev/ttyUSB0', 38400, timeout=1) as ser:
    while True:
        if ser.read() == b'\x15':
            ser.write(b'\x13')
            desc = ser.read(15)
            ser.write(b'\x06')
            msg = ser.read(desc[9]+2)
            ser.write(b'\x06')
            printHex(msg)
            print("Received: ", msg[3:-2].decode("utf-8"))
            text = input("Input message: ")
            if (text == "asdf"):
                msg = generateMsg(text)
                desc = generateDesc(msg)    
                ser.write(b'\x15')
                ser.write(desc)
                ser.write(msg)
                text = input("Input message: ")
            msg = generateMsg(text)
            desc = generateDesc(msg)    
            ser.write(b'\x15')
            ser.write(desc)
            ser.write(msg)
