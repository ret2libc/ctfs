#!/usr/bin/env python2

import re
import sys

t = open(sys.argv[1]).read()
tl = t.split('\n')
out = []
i = 0
while i < len(tl):
    l = tl[i]
    m = re.match('r\[3\] = i\[(\d+)\]', l)
    if m is not None:
        i1 = int(m.groups()[0])
        m = re.match('i\[(\d+)\] = i\[(\d+)\]', tl[i+1])
        if m is not None:
            i2, i3 = int(m.groups()[0]), int(m.groups()[1])
            m = re.match('i\[(\d+)\] = r\[3\]', tl[i+2])
            if m is not None:
                i4 = int(m.groups()[0])
                if i1 == i2 and i3 == i4:
                    out.append('swap(&i[%d], &i[%d])' % (i2, i3))
                    i += 3
                    continue

    if tl[i] == 'r[3] = 0':
        out.append(tl[i])
        i += 1
        out.append('input = ' + tl[i])
        i += 1

        vv = 0
        s = 1
        while True:
            while tl[i] == 'r[8] = r[8] + r[8]':
                s *= 2
                i += 1

            #  out.append(str(s))
            if tl[i] == 'r[3] = r[3] + r[8]':
                vv += s
                i += 1
                continue

            break

        out.append('r[2] += %dx' % (vv,))
        i += 1
        continue

    i += 1
    out.append(l)

open(sys.argv[2], 'w').write('\n'.join(out))
