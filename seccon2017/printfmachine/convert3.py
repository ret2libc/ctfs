#!/usr/bin/env python2

import re
import sys

t = open(sys.argv[1]).read()
tl = t.split('\n')
out = []
i = 0
vals = []

while i < len(tl):
    if 'input = ' in tl[i]:
        l = tl[i]
        n = l[len('input = r[8] = i['):]
        n = int(n[:n.index(']')])

        i += 1
        l = tl[i]
        v = int(l[len('r[2] += '):l.index('x')])
        vals.append(v)
        continue

    if 'r[0] = r[2] + ' in tl[i]:
        l = tl[i]
        opp = int(l[len('r[0] = r[2] + '):])

        final_v = 256 - opp
        print 'res.append((' + str(vals) + ', ' + str(final_v) + '))'

        vals = []
        i += 1
        continue

    i += 1
