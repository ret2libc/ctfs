#!/usr/bin/env python2

import sys
import re

t = open(sys.argv[1]).read()
o = open('debug.fs', 'wb')
for l in t.split('\n'):
	o.write(l + '\n')
	for fmt in l.split('%'):
 		if 'hhn' in fmt:
 			m = re.match('(\d+)\$hhn', fmt)
 			# o.write('flag: "%56$s"\n')

for i in range(1, 65):
	s = 'flag: "%' + str(i) + '$x"\n'
	print s
	o.write(s)

o.close()
