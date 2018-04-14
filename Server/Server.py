import sys
import traceback
from select import *
from socket import *

import params

switchesVarDefaults = (
    (('-l', '--listenPort'), 'listenPort', 50000),
    (('-d', '--debug'), "debug", False),  # boolean (set if present)
    (('-?', '--usage'), "usage", False)  # boolean (set if present)
)

paramMap = params.parseParams(switchesVarDefaults)
listenPort, usage, debug = paramMap["listenPort"], paramMap["usage"], paramMap["debug"]

if usage:
    params.usage()

try:
    listenPort = int(listenPort)
except:
    print "Can't parse listen port from %s" % listenPort
    sys.exit(1)

sockNames = {}  # from socket to name
nextConnectionNumber = 0  # each connection is assigned a unique id


class Fwd:
    def __init__(self, conn, inSock, outSock, bufCap=1000):
        self.conn, self.inSock, self.outSock, self.bufCap = conn, inSock, outSock, bufCap
        self.inClosed, self.buf = 0," "
        self.file = ""
        # Check if there is something to read
    def checkRead(self):
        if len(self.buf) < self.bufCap and not self.inClosed:
            return self.inSock
        else:
            return None


        # Check if there is something to write
    def checkWrite(self):
        if len(self.buf) > 0:
            return self.outSock
        else:
            return None



        # Actually receive something
    def doRecv(self):
        b = ""
        try:
            if not self.file:
                b = self.inSock.recv(self.bufCap - len(self.buf))
                self.file = b
                print "Self.file is:" + self.file
                with open("file.txt", "r") as file:
                    self.content = file.read()
                    print "my content is:", self.content

        except:
            self.conn.die()

        self.inClosed = 1
        self.checkDone()


# Actually Send something
    def doSend(self):
        try:
            n=self.outSock.send(self.content)
            self.buf = self.buf[n:]
            print "self buf is ",self.buf
        except:
            print "time to die?"
            self.conn.die()
        self.checkDone()
        # Check if it has finished sending

    def checkDone(self):
        if len(self.buf) == 0 and self.inClosed:
            try:
                self.outSock.shutdown(SHUT_WR)
            except:
                pass
            self.conn.fwdDone(self)


connections = set()


class Conn:
    def __init__(self, csock, caddr):
        global nextConnectionNumber
        self.csock = csock  # to client
        self.caddr = caddr
        self.connIndex = connIndex = nextConnectionNumber
        nextConnectionNumber += 1
        self.forwarders = forwarders = set()
        print "New connection #%d from %s" % (connIndex, repr(caddr))
        sockNames[csock] = "C%d:ToClient" % connIndex
        forwarders.add(Fwd(self, csock, csock))
        connections.add(self)

    def fwdDone(self, forwarder):
        forwarders = self.forwarders
        forwarders.remove(forwarder)
        print "forwarder %s ==> %s from connection %d shutting down" % (
        sockNames[forwarder.inSock], sockNames[forwarder.outSock], self.connIndex)
        if len(forwarders) == 0:
            self.die()

    def die(self):
        print "connection %d shutting down" % self.connIndex
        for s in [self.csock]:
            del sockNames[s]
            try:
                s.close()
            except:
                pass
        connections.remove(self)

    def doErr(self):
        print "forwarder from client %s failing due to error" % repr(self.caddr)
        self.die()


class Listener:
    def __init__(self, bindaddr, addrFamily=AF_INET, socktype=SOCK_STREAM):
        self.bindaddr = bindaddr
        self.addrFamily, self.socktype = addrFamily, socktype
        self.lsock = lsock = socket(addrFamily, socktype)
        sockNames[lsock] = "listener"
        lsock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        lsock.bind(bindaddr)
        lsock.setblocking(False)
        lsock.listen(2)

    def doRecv(self):
        try:
            csock, caddr = self.lsock.accept()  # socket connected to client
            conn = Conn(csock, caddr)
        except:
            print "weird.  listener readable but can't accept!"
            traceback.print_exc(file=sys.stdout)

    def doErr(self):
        print "listener socket failed!!!!!"
        sys.exit(2)

    def checkRead(self):
        return self.lsock

    def checkWrite(self):
        return None

    def checkErr(self):
        return self.lsock


l = Listener(("0.0.0.0", listenPort))


def lookupSocknames(socks):
    return [sockNames[s] for s in socks]


while 1:
    rmap, wmap, xmap = {}, {}, {}  # socket:object mappings for select
    xmap[l.checkErr()] = l
    rmap[l.checkRead()] = l
    for conn in connections:
        for sock in [conn.csock]:
            xmap[sock] = conn
            for fwd in conn.forwarders:
                sock = fwd.checkRead()
                if (sock): rmap[sock] = fwd
                sock = fwd.checkWrite()
                if (sock): wmap[sock] = fwd
    rset, wset, xset = select(rmap.keys(), wmap.keys(), xmap.keys(), 60)
    # print "select r=%s, w=%s, x=%s" %
    if debug: print [repr([sockNames[s] for s in sset]) for sset in [rset, wset, xset]]
    for sock in rset:
        rmap[sock].doRecv()
    for sock in wset:
        wmap[sock].doSend()
    for sock in xset:
        xmap[sock].doErr()



