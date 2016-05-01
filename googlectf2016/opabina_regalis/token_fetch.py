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

HOST = 'ssl-added-and-removed-here.ctfcompetition.com' # The remote host
PORT = 1876 # The same port as used by the server

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s = ssl.wrap_socket(s)
s.connect((HOST, PORT))

r1 = myrec()
r1.request.uri='/token'
print r1
mysend(r1.SerializeToString())
r = myrec()
print 'server: ' + str(r)

s.close()
