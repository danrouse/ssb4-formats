import util
import struct

bones = []
uids = {}

def read(vbn_path):
  f = open(vbn_path, 'rb')
  assert f.read(4) == b' NBV'
  util.log('\nReading VBN', vbn_path, level=util.LOG_INFO)

  f.seek(0x04, 1)
  bone_count = util.readlong(f, True)
  f.seek(0x10, 1)

  for i in range(bone_count):
    bone = read_bone_header(f)
    uids[bone['uid']] = i
    bones.append(bone)

  for i in range(bone_count):
    bones[i].update(read_bone_data(f))
    util.log('Bone UID {:08x} "{:s}"'.format(bones[i]['uid'], bones[i]['name']), level=util.LOG_DEBUG)
    util.log('\tT({:.02f},{:.02f},{:.02f}) R({:.02f},{:.02f},{:.02f},{:.02f}) S({:.02f},{:.02f},{:.02f})' \
      .format(*bones[i]['pos'], *bones[i]['rotq'], *bones[i]['scl']), level=util.LOG_VERBOSE)

  return bones, uids

def read_bone_header(f):
  next_addr = f.tell() + 0x44
  bone_name = util.readstring(f)

  f.seek(next_addr)
  bone_parent = util.readshort(f, True)
  if bone_parent == 0xFFFF: bone_parent = -1

  f.seek(0x02, 1)
  bone_uid = util.readlong(f, True)

  return {
    'name': bone_name,
    'parent': bone_parent,
    'uid': bone_uid
  }
  

def read_bone_data(f):
  tx, ty, tz, \
  rx, ry, rz, \
  sx, sy, sz = struct.unpack('<9f', f.read(9 * 4))

  return {
    'pos': (tx, ty, tz),
    'rotq': util.quaternion_from_euler(rx, ry, rz, 'sxyz'),
    'scl': (sx, sy, sz)
  }

