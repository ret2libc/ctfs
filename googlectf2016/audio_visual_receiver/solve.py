#!/usr/bin/env python2

from z3 import *
import sys
import string
import struct

flag = map(lambda x: struct.unpack('<B', x)[0], list('465b6be16f5ea3d3a21c82ed62246771dd6df320838dca3e33c8755a6887'.decode('hex')))

def bb(x): return x & 0xff
def rshift(val, n): return val>>n if val >= 0 else (val+0x100000000)>>n
def get_seq(buf):
    out = ''
    for i in range(1, len(flag) + 1):
        sn = buf[i]
        sp = buf[i-1]
        if sn == bb(3 * sp):
            out += 'u'
        elif sn == bb(bb((rshift(sp, 1)) * 8) - (rshift(sp, 1))):
            out += 'd'
        elif sn == bb(sp * 2):
            out += 'l'
        elif sn == bb((rshift(sp, 3)) | bb((sp * 32))):
            out += 'r'
        elif sn == bb(~sp):
            out += 'b'
        elif sn == bb((sp * 16)) | (rshift(sp, 4)):
            out += 'a'
    return out

s = Solver()

checks = [BitVec('check%d' % i, 8) for i in range(len(flag) + 1)]
state = [BitVec('state%d' % i, 8) for i in range(len(flag) + 1)]
cross_ptr = [Int('cross_ptr%d' % i) for i in range(len(flag) + 1)]

def cross_ptr_check(i):
    return Or(
        And((checks[i-1] ^ state[i-1]) == 0x25, cross_ptr[i-1] == 0),
        And((checks[i-1] ^ state[i-1]) == 0x68, cross_ptr[i-1] == 1),
        And((checks[i-1] ^ state[i-1]) == 0xef, cross_ptr[i-1] == 2),
        And((checks[i-1] ^ state[i-1]) == 0x00, cross_ptr[i-1] >= 3),
    )

# initial state
s.add(checks[0] == 0)
s.add(state[0] == 5)
s.add(cross_ptr[0] == 0)

# printable flag
for i in range(0, len(flag)):
    s.add((state[i] ^ flag[i]) >= 0x20)
    s.add((state[i] ^ flag[i]) <= 0x7e)

for i in range(1, len(flag) + 1):
    xor_check = (checks[i] == checks[i-1] ^ state[i-1])
    a_change_state = (state[i] == (state[i-1] * 16) | LShR(state[i-1], 4))

    s.add(Or(
        And(xor_check, state[i] == (state[i-1] * 3), cross_ptr[i] == cross_ptr[i-1]), # up
        And(xor_check, state[i] == (LShR(state[i-1], 1) * 8) - (LShR(state[i-1], 1)), cross_ptr[i] == cross_ptr[i-1]), # down
        And(xor_check, state[i] == (state[i-1] * 2), cross_ptr[i] == cross_ptr[i-1]), # left
        And(xor_check, state[i] == (LShR(state[i-1], 3)) | (state[i-1]*32), cross_ptr[i] == cross_ptr[i-1]), # right
        And(xor_check, state[i] == ~(state[i-1]), cross_ptr[i] == cross_ptr[i-1]), # b
        Or(
            And(cross_ptr_check(i), checks[i] == 0, cross_ptr[i] == cross_ptr[i-1] + 1, a_change_state), # a 1
            And(Not(cross_ptr_check(i)), xor_check, a_change_state, cross_ptr[i] == cross_ptr[i-1]) # a 2
        )
    ))

s.add(state[0] ^ flag[0] == ord('C'))
s.add(state[1] ^ flag[1] == ord('T'))
s.add(state[2] ^ flag[2] == ord('F'))
s.add(state[3] ^ flag[3] == ord('{'))
s.add(state[len(flag)-1] ^ flag[len(flag)-1] == ord('}'))

# force the last char to be 'a'
s.add(checks[len(flag)] == 0)
s.add(state[len(flag)] == (state[len(flag)-1] * 16) | LShR(state[len(flag)-1], 4))
s.add(cross_ptr_check(len(flag)))

print s.check()
while s.check() == sat:
    buf = [int(str(s.model()[state[i]])) for i in range(len(flag) + 1)]
    seq = get_seq(buf)
    f = [i ^ j for i, j in zip(buf, flag)]
    print ''.join(map(chr, f)), seq

    block = []
    for i in range(len(flag)):
        block.append(state[i] ^ flag[i] != f[i])

    s.add(Or(block))
