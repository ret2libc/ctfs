#!/usr/bin/env python2

import sys
import re
import itertools
import string
import subprocess
import argparse
import logging

def do(exec_file, check_output, max_length = 20, choices = string.lowercase + string.uppercase + string.punctuation + string.digits):
	n_try = 0
	password = '=FX'
	lenp= len(password)
	for i in range(0xf):
		min_v = 1000
		min_ch = {}
		for ch in choices:
			flag = password + ch + '\n'
			# print 'trying ' + flag
			p = subprocess.Popen([exec_file, 'debug.fs'], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
			p.stdin.write(flag)
			(out, err) = p.communicate()
			#print out,err
			val = check_output(err, i)
			if val is not None and val <= min_v:
				min_v = val
				if min_v not in min_ch:
					min_ch[min_v] = []
				min_ch[min_v].append(ch)

		min_key = min(min_ch.keys())
		password = password + min_ch[min_key][-1]
		print 'min_v = ' + str(min_key) + ', min_ch = ' + str(min_ch[min_key]) + ', psw = ' + password

	if len(password) < 16:
		return None

	#n_try += 1
	#if n_try % 153 == 0:
	#	logging.debug('Try #%d. Last password = %s' % (n_try, password))
	return password


def check_output(out, i):
	for l in out.split('\n'):
		if 'DBG' in l:
			lendbg = len('DBG CHAR: "')
			
			l = l[lendbg:]
			l = l[:l.index('"')]
			ch = int(l, 16)
			return ch

	return None

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Bruteforce stdin')
	parser.add_argument('input_bin', help='Program to bruteforce')
	parser.add_argument('--length', help='Max length of the string to try')
	parser.add_argument('--debug', action='store_true', help='Enable debugging printing')
	args = parser.parse_args()

	if args.debug:
		logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

	if args.length:
		result = do(args.input_bin, check_output, max_length = args.length)
	else:
		result = do(args.input_bin, check_output)

	if result is None:
		print "I'm sorry, I wasn't able to find the correct value"
	else:
		print "The good value is: %s" % result
