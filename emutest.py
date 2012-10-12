
from base128 import base128

#from bitarray import bitarray
bitarray = base128('bitstring').getEmuUsingBitString()
#bitarray = base128('BitVector').getEmuUsingBitVector()

def getb(a):
	return ''.join(['0' if a[i] else '1' for i in range(0,len(a))])

ba = bitarray()
ba.frombytes(b"\x55\x00\xff")
print(getb(ba), len(ba))
ba.insert(0,1)
print(getb(ba))
ba.pop(0)
print(getb(ba))
print(len(ba))
print(list(map(bin,ba.tobytes())))
