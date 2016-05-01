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
PORT = 12001 # The same port as used by the server

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s = ssl.wrap_socket(s)
s.connect((HOST, PORT))

r1 = myrec()
#  r1.request.uri='/token'
print r1
mysend(r1.SerializeToString())
r = myrec()
print 'server: ' + str(r)

# get opaque and nonce from the reply, we'll need them in a moment
opaque = r.reply.headers[1].value
opaque = opaque[opaque.find('opaque') + len('opaque') + 2:-1]
nonce = r.reply.headers[1].value
nonce = nonce[nonce.find('nonce=') + len('nonce=') + 1:]
nonce = str(nonce[:nonce.find('"')])

r.reply.headers[1].value = 'Basic realm="In the realm of hackers"'
mysend(r.SerializeToString())
r = myrec()
print 'server: ' + str(r)

t = r.request.headers[0].value
t = t[len('Basic '):].decode('base64')
username, password = t.split(':')

print username, password

e = proto_pb2.Exchange()
req = e.request
req.ver = 0
req.uri = '/protected/token'
head = req.headers.add()
head.key = r1.request.headers[0].key
head.value = r1.request.headers[0].value

req = e.request
head= req.headers.add()
head.key = "Authorization"
username = 'google.ctf'
cnonce = '12345678'
nc = '00000001'
opts = {
    'username': username,
    'realm': 'In the realm of hackers',
    'uri': str(req.uri),
    'qop': 'auth',
    'cnonce': cnonce,
    'nc': nc,
    'opaque': opaque,
    'nonce': nonce,
    'response': calc_resp(username, 'In the realm of hackers', password, req.uri, nonce, nc, cnonce, 'auth'),
}
head.value = 'Digest username="{username}",realm="{realm}",nonce="{nonce}",uri="{uri}",qop=auth,nc={nc},cnonce="{cnonce}",response="{response}",opaque="{opaque}"'.format(**opts)
print e
mysend(e.SerializeToString())

print myrec()

s.close()
