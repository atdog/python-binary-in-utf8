from fractions import Fraction
import pprint, difflib, warnings, timeit, operator, functools, itertools, os, json, struct, math, sys, io, shlex, tempfile


def assert_eq(data, data2):
  assert isinstance(data, bytes)
  assert isinstance(data2, bytes)
  if data2 == data: return
  d = difflib.Differ()
  maxlen = max(len(data), len(data2))
  chunksize = 1
  s1 = bin(int.from_bytes(data, 'big'))[2:].zfill(maxlen)
  s2 = bin(int.from_bytes(data2,'big'))[2:].zfill(maxlen)
  l1 = "\n".join(map(lambda x: "".join(x), chunks(s1,chunksize)))
  l2 = "\n".join(map(lambda x: "".join(x), chunks(s2,chunksize)))
  with tempfile.NamedTemporaryFile() as f1:
    f1.write(l1.encode())
    f1.flush()
    with tempfile.NamedTemporaryFile() as f2:
      f2.write(l2.encode())
      f2.flush()
      cmd = "diff -y " + shlex.quote(f1.name) + " " + shlex.quote(f2.name) + ""# | less -r
      print(cmd)
      os.system(cmd)
  #result = list(d.compare(l1,l2))
  #pprint.pprint(result)
  raise Exception("error!")

def chunks(iterable, size):
    """ http://stackoverflow.com/a/434314/309483 """
    it = iter(iterable)
    chunk = tuple(itertools.islice(it, size))
    while chunk:
        yield chunk
        chunk = tuple(itertools.islice(it, size))

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
          siz = len(self.bs)
          del self.bs[pos]
          assert len(self.bs) == siz-1
        def __str__(self):
                return str(self.bs)
        def __repr__(self):
                return repr(self.bs)
    return bitarrayemu

  def encode_chunk(self, minbytes):
    chosenbitarray = self.chosenbitarray

    mbinarr = chosenbitarray()
    mbinarr.frombytes(minbytes)

    orglength = len(mbinarr)
    for pos in itertools.count(0,8):
      if pos >= orglength+1: break
      mbinarr.insert(pos,0)

    padlen = (8 - (len(mbinarr) % 8)) % 8
    #assert int.from_bytes(mbinarr[0::8].tobytes(),'big') == 0, mbinarr[0::8] # doesn't work for BitVector
    #padlen2 = math.ceil(len(mbinarr) / 8) * 8 - len(mbinarr)
    #if padlen != padlen2: raise Exception("uoverenstemmelse!" + str((len(mbinarr), padlen, padlen2, mbinarr)))

    #INSERT ZEROS
    inspos = len(mbinarr)-(len(mbinarr)%8)
    for i in range(padlen): mbinarr.insert(inspos,0)

    mstring = mbinarr.tobytes()

    return ({"pos": inspos, "count": padlen} if padlen else None, mstring)

#tochars1 = lambda mbinarr: '' if len(mbinarr) == 0 else bin(int.from_bytes(mbinarr.tobytes(), 'big'))[2:].zfill(len(mbinarr))
#tochars2 = lambda mbinarr: ''.join(list(map(lambda x: '1' if x else '0', mbinarr.tolist()))) # .zfill(mbinarr.length())
#tochars3 = lambda mbinarr: mbinarr.to01()

  def encode(self, pair):
    l1 = chunks(pair, self.chunksize)
    l2 = map(lambda x: self.encode_chunk(x), l1)
    for idx,j in enumerate(l2):
      zeros, st = j[0], j[1]
      yield zeros, st.decode("utf-8")

  def decode(self, pair):
    l1 = pair
    for idx,item in enumerate(l1):
      insertedzeros = item[0]
      assert insertedzeros is None or not isinstance(l1, list) or idx == len(l1)-1
      yield self.decode_chunk(item[1], insertedzeros)

  def decode_chunk(self, mstring, zeros=None):
    chosenbitarray = self.chosenbitarray

    mbinarr = chosenbitarray()
    mbinarr.frombytes(mstring.encode())

    if zeros:
      for i in range(zeros["count"]):
        mbinarr.pop(zeros["pos"]+1)


    orglength = len(mbinarr)
    for i in itertools.count(0,8):
      pos = i - i//8
      if i > orglength-1: break
      mbinarr.pop(pos)

    return mbinarr.tobytes()

  def iteration(self,data):
    data2 = b"".join(self.decode(self.encode(data)))
    assert_eq(data, data2)

  def test(self):
    self.iteration(b"")

    n = 25
    for i in range(1,n+1):
      l = int.from_bytes(os.urandom(2),'big') >> 7
      l = 32
      data = os.urandom(l)
      self.iteration(data)
      if Fraction(i) % Fraction(n, 10) == 0: print(Fraction(i, Fraction(n, 10)) * 10 , '% complete')

  def simpletest(self):
    self.iteration(b"\x00\xff")

  def choosebitarray(self,t):
    if t == 'BitVector':
      from BitVector import BitVector
      self.BitVector = BitVector
      self.chosenbitarray = self.getEmuUsingBitVector()
    elif t == 'bitstring':
      from bitstring import BitArray
      self.BitArray = BitArray
      self.chosenbitarray = self.getEmuUsingBitString()
    elif t == 'bitarray':
      from bitarray import bitarray
      self.chosenbitarray = bitarray
    else:
      raise Exception("unsupported bit wrapper")

  def __init__(self, t, chunksize=7):
    self.choosebitarray(t)
    self.chunksize = chunksize

if __name__ == "__main__":
	if len(sys.argv) > 1:
		k = base128("bitstring")
		with open(sys.argv[1], "rb") as f:
			for piece in iter(lambda: f.read(1024), ''):
				for i,j in k.encode(piece):
					assert isinstance(j, str), j.__class__
					sys.stdout.write(j)
		sys.exit(0)
	for t in ["bitstring", "bitarray", "BitVector"]:
			chunksize = 7
			print(chunksize)
			if t == 'BitVector':
				sys.path.append("BitVector-3.3.2")
			elif t == "bitstring":
				sys.path.append("bitstring-3.0.2")
			try:
				# Benchmark
				# python3 -m timeit -s "import base128, os; i = base128.base128('bitarray')"  "i.iteration(os.urandom(32))"
				# python3 -m timeit -s "import base128, os; i = base128.base128('bitstring')" "i.iteration(os.urandom(32))"
				# python3 -m timeit -s "import base128, os; i = base128.base128('BitVector')" "i.iteration(os.urandom(32))"
				i = base128(t, chunksize)
				i.test()
				#for j in range(9,128):
				#	data = os.urandom(j)
				#	encoded = i.encode(data)
				#	decoded = i.decode(encoded)
				#	assert_eq(data, b"".join(decoded))
				print(timeit.timeit(setup="import base128, os; i = base128.base128('" + t + "')", stmt="i.iteration(os.urandom(512))", number=10))
				#print(timeit.timeit(setup="import base128, os; i = base128.base128('" + t + "')", stmt="i.iteration(os.urandom(1024))", number=1))
			except ImportError:
				warnings.warn("Can't import " + t)
