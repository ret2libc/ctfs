#!/usr/bin/env python2

import re
import sys

def convert(i):
    if 0 < i <= 16:
        return 'r', 0, i - 1
    elif 16 < i <= 32:
        return 'i', 16, i - 16 - 1
    elif 32 < i <= 48:
        return 'r', 32, i - 32 - 1
    else:
        return 'i', 48, i - 48 - 1

t = open(sys.argv[1]).read()
out = []
for l in t.split('\n'):
    m = re.match('^\%(\d+)\$\*(\d+)\$s\%(\d+)\$hhn$', l)
    if m is not None:
        r, i, o = m.groups()
        r, i, o = int(r), int(i), int(o)
        #  print r, i, o
        assert o <= 32
        assert 32 < i <= 64
        os, obase, oval = convert(o)
        iss, ibase, ival = convert(i)

        out.append('%s[%d] = %s[%d]' % (os, oval, iss, ival))
        continue

    m = re.match('^\%(\d+)\$hhn$', l)
    if m is not None:
        r = int(m.groups()[0])
        os, obase, oval = convert(r)
        out.append('%s[%d] = 0' %(os, oval))
        continue

    m = re.match('^\%(\d+)\$\*(\d+)\$s\%(\d+)\$\*(\d+)\$s\%(\d+)\$hhn$', l)
    if m is not None:
        _, i1, _, i2, o = m.groups()
        i1, i2, o = int(i1), int(i2), int(o)
        i1s, i1sbase, i1val = convert(i1)
        i2s, i2sbase, i2val = convert(i2)
        os, osbase, oval = convert(o)
        out.append('%s[%d] = %s[%d] + %s[%d]' % (os, oval, i1s, i1val, i2s, i2val))
        continue

    m = re.match('^\%(\d+)\$hhn\%(\d+)\$\*(\d+)\$s\%(\d+)\$hhn$', l)
    if m is not None:
        z, _, i, o = m.groups()
        z, i, o = int(z), int(i), int(o)
        zs, _, zval = convert(z)
        iss, _, ival = convert(i)
        os, _, oval = convert(o)
        out.append('%s[%d] = 0' % (zs, zval))
        out.append('%s[%d] = %s[%d]' % (os, oval, iss, ival))
        continue

    m = re.match('^\%(\d+)\$s\%(\d+)\$hhn$', l)
    if m is not None:
        i, o = m.groups()
        i, o = int(i), int(o)
        iss, _, ival = convert(i)
        os, _, oval = convert(o)
        out.append('%s[%d] = len(&%s[%d])' % (os, oval, iss, ival))
        continue

    m = re.match('^\%(\d+)\$\*(\d+)\$s\%(\d+)\$(\d+)s\%(\d+)\$hhn$', l)
    if m is not None:
        _, i, _, c, o = m.groups()
        i, c, o = int(i), int(c), int(o)
        iss, _, ival = convert(i)
        os, _, oval = convert(o)
        out.append('%s[%d] = %s[%d] + %d' % (os, oval, iss, ival, c))
        continue

    out.append(l)

open(sys.argv[2], 'w').write('\n'.join(out))
