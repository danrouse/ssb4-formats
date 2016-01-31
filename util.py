import struct, io, math, binascii
import numpy as np

def readlong(f, LE=False):
  #pos = f.tell()
  raw = f.read(4)
  ulong = struct.unpack('{}I'.format('<' if LE != False else '>'), raw)[0]
  #log('{:08x}: R Uint16, {:s}'.format(pos, str(binascii.hexlify(raw), 'utf-8')), ulong, level=LOG_VERBOSE)
  return ulong

def readshort(f, LE=False):
  #pos = f.tell()
  raw = f.read(2)
  short = struct.unpack('{}H'.format('<' if LE != False else '>'), raw)[0]
  #log('{:08x}: R Uint8, {:s}'.format(pos, str(binascii.hexlify(raw), 'utf-8')), short, level=LOG_VERBOSE)
  return short

def readbyte(f, LE=False):
  #pos = f.tell()
  raw = f.read(1)
  byte = struct.unpack('{}B'.format('<' if LE != False else '>'), raw)[0]
  #log('{:08x}: R Byte, {:s}'.format(pos, str(binascii.hexlify(raw), 'utf-8')), byte, level=LOG_VERBOSE)
  return byte

def readfloat(f, LE=False):
  #pos = f.tell()
  raw = f.read(4)
  float32 = struct.unpack('{}f'.format('<' if LE != False else '>'), raw)[0]
  #log('{:08x}: R Float32, {:s}'.format(pos, str(binascii.hexlify(raw), 'utf-8')), float32, level=LOG_VERBOSE)
  return float32

def readhalffloat(f):
  #pos = f.tell()
  raw = f.read(2)
  float16 = float(np.frombuffer(raw, dtype=np.float16))
  #log('{:08x}: R Float16, {:s}'.format(pos, str(binascii.hexlify(raw), 'utf-8')), float16, level=LOG_VERBOSE)
  return float16

def readstring(f, term=b'\0'):
  #pos = f.tell()
  buf = b''
  while True:
    char = f.read(1)
    if char == term or char == '':
      break
    buf += char
  #log('{:08x}: R String'.format(pos), buf, level=LOG_VERBOSE)
  return str(buf, 'utf-8')

def readvec3(f):
  #pos = f.tell()
  raw = f.read(12)
  floats = struct.unpack('>fff', raw)
  #log('{:08x}: R Vec3, {:s}'.format(pos, str(binascii.hexlify(raw), 'utf-8')), floats, level=LOG_VERBOSE)
  return floats

def readvec4(f):
  #pos = f.tell()
  raw = f.read(16)
  floats = struct.unpack('>ffff', raw)
  #log('{:08x}: R Vec4, {:s}'.format(pos, str(binascii.hexlify(raw), 'utf-8')), floats, level=LOG_VERBOSE)
  return floats

def readmults(f, nmults):
  #pos = f.tell()
  raw = f.read(nmults * 2)
  #log('{:08x}: R {:d} Mults, {:s}'.format(pos, nmults, str(binascii.hexlify(raw), 'utf-8')), level=LOG_VERBOSE)
  mults = [m / 0xFFFF for m in struct.unpack('>{:d}H'.format(nmults), raw)]
  
  return mults

def lerp(start, diff, mults):
  return list(np.add(start, np.multiply(diff, mults)))

def open_mixed(input):
  if isinstance(input, str):
    f = open(input, 'rb')
  else:
    f = io.BytesIO(input)
  return f

def hx(s):
  s = str(binascii.hexlify(s), 'utf-8')
  buf = ''
  for i in range(len(s)):
    buf += s[i]
  return buf


LOG_FATAL = 1
LOG_ERROR = 2
LOG_INFO = 3
LOG_DEBUG = 4
LOG_VERBOSE = 5
log_level = LOG_DEBUG
def log(*args, f=None, level=LOG_INFO):
  if log_level >= level:
    if f:
      print('0x{:08x}:'.format(f.tell()), *args)
    else:
      print(*args)

# map axes strings to/from tuples of inner axis, parity, repetition, frame
_AXES2TUPLE = {
    'sxyz': (0, 0, 0, 0), 'sxyx': (0, 0, 1, 0), 'sxzy': (0, 1, 0, 0),
    'sxzx': (0, 1, 1, 0), 'syzx': (1, 0, 0, 0), 'syzy': (1, 0, 1, 0),
    'syxz': (1, 1, 0, 0), 'syxy': (1, 1, 1, 0), 'szxy': (2, 0, 0, 0),
    'szxz': (2, 0, 1, 0), 'szyx': (2, 1, 0, 0), 'szyz': (2, 1, 1, 0),
    'rzyx': (0, 0, 0, 1), 'rxyx': (0, 0, 1, 1), 'ryzx': (0, 1, 0, 1),
    'rxzx': (0, 1, 1, 1), 'rxzy': (1, 0, 0, 1), 'ryzy': (1, 0, 1, 1),
    'rzxy': (1, 1, 0, 1), 'ryxy': (1, 1, 1, 1), 'ryxz': (2, 0, 0, 1),
    'rzxz': (2, 0, 1, 1), 'rxyz': (2, 1, 0, 1), 'rzyz': (2, 1, 1, 1)}
# axis sequences for Euler angles
_NEXT_AXIS = [1, 2, 0, 1]

def quaternion_from_euler(ai, aj, ak, axes='sxyz'):
    """Return quaternion from Euler angles and axis sequence.

    ai, aj, ak : Euler's roll, pitch and yaw angles
    axes : One of 24 axis sequences as string or encoded tuple

    >>> q = quaternion_from_euler(1, 2, 3, 'ryxz')
    >>> numpy.allclose(q, [0.435953, 0.310622, -0.718287, 0.444435])
    True

    """
    try:
        firstaxis, parity, repetition, frame = _AXES2TUPLE[axes.lower()]
    except (AttributeError, KeyError):
        _TUPLE2AXES[axes]  # validation
        firstaxis, parity, repetition, frame = axes

    i = firstaxis + 1
    j = _NEXT_AXIS[i+parity-1] + 1
    k = _NEXT_AXIS[i-parity] + 1

    if frame:
        ai, ak = ak, ai
    if parity:
        aj = -aj

    ai /= 2.0
    aj /= 2.0
    ak /= 2.0
    ci = math.cos(ai)
    si = math.sin(ai)
    cj = math.cos(aj)
    sj = math.sin(aj)
    ck = math.cos(ak)
    sk = math.sin(ak)
    cc = ci*ck
    cs = ci*sk
    sc = si*ck
    ss = si*sk

    q = np.empty((4, ))
    if repetition:
        q[0] = cj*(cc - ss)
        q[i] = cj*(cs + sc)
        q[j] = sj*(cc + ss)
        q[k] = sj*(cs - sc)
    else:
        q[0] = cj*cc + sj*ss
        q[i] = cj*sc - sj*cs
        q[j] = cj*ss + sj*cc
        q[k] = cj*cs - sj*sc
    if parity:
        q[j] *= -1.0

    q = list(q)
    return [q[1], q[2], q[3], q[0]]
