#!/usr/bin/env python2
import proto_pb2
import socket
import struct
import random
import ssl
import md5

def mysend(msg):
    length = struct.pack("<I",len(msg))
    tot = length + msg
    s.send(tot)

def myrec():
    a = s.recv(4000)
    length = struct.unpack("<I",a[:4])[0]
    neww = proto_pb2.Exchange()
    neww.ParseFromString(a[4:])
    return neww

def calc_resp(u, r, p, uri, nonce, nc, cnonce, qop):
    ha1 = md5.new(u + ':' + r + ':' + p).hexdigest()
    ha2 = md5.new('GET:' + uri).hexdigest()
    return md5.new(ha1 + ':' + nonce + ':' + nc + ':' + cnonce + ':' + qop + ":" + ha2).hexdigest()

HOST = 'ssl-added-and-removed-here.ctfcompetition.com' # The remote host
PORT = 13001 # The same port as used by the server

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s = ssl.wrap_socket(s)
s.connect((HOST, PORT))

r1 = myrec()
r1.request.uri = '/protected/secret'
print r1
mysend(r1.SerializeToString())
r = myrec()
print 'server: ' + str(r)

print r
mysend(r.SerializeToString())
r = myrec()
print 'server: ' + str(r)
print r
mysend(r.SerializeToString())
print myrec()

s.close()
