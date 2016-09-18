#!/usr/bin/env python2

from pwn import *

p = remote('pwn.chal.csaw.io', 8001)
p.recvline()
table = p.recvlines(8)
p.sendline('help')

p.recvline()
t = p.recvuntil(table)
t = '\x1b' + t[:t.rfind('Didn\'t understand')]
t = t.replace('\x0d\x0a', '\x0a')
open('file.bin', 'wb').write(t)
