# Benchmark
# python3 -m timeit -s "import base128, os; i = base128.base128('bitarray')"  "i.iteration(os.urandom(32))"
# python3 -m timeit -s "import base128, os; i = base128.base128('bitstring')" "i.iteration(os.urandom(32))"
# python3 -m timeit -s "import base128, os; i = base128.base128('BitVector')" "i.iteration(os.urandom(32))"

import operator
import functools
import itertools
import os
import json
import struct
import math
import sys
import io

class base128:
  def getEmuUsingBitVector(self):
    outer = self
    class bitarrayemu:
        def __getitem__(self, pos):
                return self.bv[pos] == 1
        def __init__(self):
                pass
        def frombytes(self, bs):
                if len(bs) == 0:
                        self.bv = outer.BitVector(size = 0)
                else:
                        self.bv = outer.BitVector(intVal = int.from_bytes(bs, 'big'))
                padlen = len(bs)*8-len(self.bv)
                self.bv.pad_from_left(padlen)
        def __len__(self):
                return len(self.bv)
        def insert(self, pos, val):
                self.bv = outer.BitVector( bitlist = list(self.bv[0:pos]) + list([val]) + list(self.bv[pos:]) )
        def tobytes(self):
                #bio = io.BytesIO()
                #self.bv.write_to_file(bio)
                #return bio.getvalue()

                return int(self.bv).to_bytes(math.ceil(len(self.bv) / 8), byteorder='big')
        def pop(self, pos):
                self.bv = outer.BitVector( bitlist = list(self.bv[0:pos]) + list(self.bv[pos+1:]) )
        def __str__(self):
                return str(self.bv)
        def __repr__(self):
                return repr(self.bv)
    return bitarrayemu
  def getEmuUsingBitString(self):
    outer = self
    class bitarrayemu:
        def __getitem__(self, pos):
          return self.bs[pos]
        def __init__(self):
          pass
        def frombytes(self, bites):
          self.bs = outer.BitArray(bytes=bites)
        def __len__(self):
          return len(self.bs)
        def insert(self, pos, val):
          self.bs.insert("0b" + str(int(val)), pos)
        def tobytes(self):
          return self.bs.bytes
        def pop(self, pos):
          del self.bs[pos]
        def __str__(self):
                return str(self.bs)
        def __repr__(self):
                return repr(self.bs)
    return bitarrayemu
                


  def encode(self,minbytes):
    chosenbitarray = self.chosenbitarray

    mbinarr = chosenbitarray()
    mbinarr.frombytes(minbytes)

    orglength = len(mbinarr)
    for i in itertools.count(0,8):
      pos = orglength - 7*(i//8) - 7
      if pos < 0: break
      mbinarr.insert(pos,0)

    padlen = (8 - (len(mbinarr) % 8)) % 8
    #padlen2 = math.ceil(len(mbinarr) / 8) * 8 - len(mbinarr)
    #if padlen != padlen2: raise Exception("uoverenstemmelse!" + str((len(mbinarr), padlen, padlen2, mbinarr)))

    for i in range(padlen): mbinarr.insert(0,0)

    mstring = mbinarr.tobytes().decode("utf-8")

    return (orglength, mstring)

#tochars1 = lambda mbinarr: '' if len(mbinarr) == 0 else bin(int.from_bytes(mbinarr.tobytes(), 'big'))[2:].zfill(len(mbinarr))
#tochars2 = lambda mbinarr: ''.join(list(map(lambda x: '1' if x else '0', mbinarr.tolist()))) # .zfill(mbinarr.length())
#tochars3 = lambda mbinarr: mbinarr.to01()

  def decode(self,pair):
    chosenbitarray = self.chosenbitarray

    (rawlen, mstring) = pair

    mbinarr = chosenbitarray()
    mbinarr.frombytes(mstring.encode())

    orglength = len(mbinarr)

    for i in itertools.count(0,8):
      pos = orglength - i - 8
      if pos < 0: break
      mbinarr.pop(pos)

    for i in range(len(mbinarr)-rawlen):
      mbinarr.pop(0)

    return mbinarr.tobytes()
    
#data = (0x12345678abcdef).to_bytes(7,'big')
#data = (0xffffffffffffff).to_bytes(7,'big')
#data = functools.reduce(operator.add, (map(lambda x: x.to_bytes(4,'big'), [0xaaaaaaaa, 0xbbbbbbbb, 0xcccccccc, 0xdddddddd, 0xeeeeeeee, 0xffffffff])))

  def iteration(self,data):
    data2 = self.decode(self.encode(data))

    if data2 != data:
      raise Exception("error!\n{}\n{}".format(data, data2))

  def test(self):
    self.iteration(b"")

    n = 100
    for i in range(1,n+1):
      l = int.from_bytes(os.urandom(2),'big') >> 7
      l = 32
      data = os.urandom(l)
      self.iteration(data)
      if (i) % (n // 10) == 0: print(i // (n // 10) * 10 , '% complete')

  def simpletest(self):
    iteration(b"\x00\xff")
  
  def choosebitarray(self,t):
    if t == 'BitVector':
      sys.path.append("BitVector-3.1.1")
      from BitVector import BitVector
      self.BitVector = BitVector
      self.chosenbitarray = self.getEmuUsingBitVector()
    elif t == 'bitstring':
      sys.path.append("bitstring-3.0.2")
      from bitstring import BitArray
      self.BitArray = BitArray
      self.chosenbitarray = self.getEmuUsingBitString()
    elif t == 'bitarray':
      from bitarray import bitarray
      self.chosenbitarray = bitarray
    else:
      raise Exception("unsupported bit wrapper")
  def __init__(self, t):
    self.choosebitarray(t)

if __name__ == "__main__":
        i = base128('bitstring')
        i.test()
        i = base128('bitarray')
        i.test()
        i = base128('BitVector')
        i.test()
