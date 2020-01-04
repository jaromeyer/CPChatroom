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

msg = generateMsg("endli gaht de schiaat")
desc = generateDesc(msg)
print("Desc packet: ", ''.join(format(x, '02x') for x in desc))
print("Msg packet: ", ''.join(format(x, '02x') for x in msg))
