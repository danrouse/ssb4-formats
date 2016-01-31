import util
import binascii

def read(nud_path):
  polys = []

  verts = []
  normals = []
  uvs = [[], [], [], []]
  colors = []
  alphas = []
  bones = []
  weights = []
  skin_indices = []
  skin_weights = []
  faces = []

  f = open(nud_path, 'rb')
  assert f.read(4) == b'NDP3'
  util.log('\nReading NUD', nud_path, level=util.LOG_INFO)

  file_size = util.readlong(f)
  f.seek(0x02, 1) # H
  polyset_count = util.readshort(f)
  f.seek(0x04, 1) # HH

  # clump offsets and sizes
  face_clump_start = util.readlong(f) + 0x30
  face_clump_size = util.readlong(f)
  vert_clump_start = (face_clump_start + face_clump_size)
  vert_clump_size = util.readlong(f)
  vert_add_clump_start = (vert_clump_start + vert_clump_size)
  vert_add_clump_size = util.readlong(f)
  name_clump_start = (vert_add_clump_start + vert_add_clump_size)
  f.seek(0x10, 1) # IIII

  bodygroups = {}

  for i in range(polyset_count):
    buf = b''
    for j in range(8):
      buf += f.read(4)
    # f.seek(0x20, 1) # ffffffff
    
    name_start = util.readlong(f)
    identifiera = util.readlong(f)
    singlebind = util.readshort(f)
    if singlebind == 0xFFFF:
      singlebind = 1
    else:
      singlebind += 1
    poly_count = util.readshort(f)
    positionb = util.readlong(f)
    for j in range(poly_count):
      polys.append({
        'name': name_start,
        'identifiera': identifiera,
        'positionb': positionb,
        'singlebind': singlebind,
        'pgroup': i,
        'garbage': buf
      })

  util.log('{:d} objects found in {:d} polysets'.format(len(polys), polyset_count), level=util.LOG_INFO)

  for i, poly in enumerate(polys):
    next_poly_addr = f.tell() + 0x30
    face_start = util.readlong(f) + face_clump_start
    vert_start = util.readlong(f) + vert_clump_start
    vert_add_start = util.readlong(f) + vert_add_clump_start
    vert_count = util.readshort(f)
    vert_size = util.readbyte(f)
    uv_size = util.readbyte(f)
    tex1_props = util.readlong(f)
    tex2_props = util.readlong(f)
    tex3_props = util.readlong(f)
    tex4_props = util.readlong(f)
    face_count = util.readshort(f)
    face_size = util.readbyte(f)
    face_flags = util.readbyte(f)
    vert_len = int(len(verts) / 3)

    # get mystery clump
    f.seek(poly['positionb'])
    mystery = f.read(0x60)
    mystery = binascii.hexlify(mystery)
    mbuf = ''
    for mi in range(len(mystery)):
      mbuf += chr(mystery[mi])
      if mi > 0 and not ((mi + 1) % 8):
        mbuf += ' '

    f.seek(poly['positionb'] + 0x3c)
    bodygroup_id = util.readlong(f)
    # if bodygroup_id in bodygroups and bodygroups[bodygroup_id] != poly['pgroup']:
    #   f.seek(next_poly_addr)
    #   print('ignore')
    #   continue
    bodygroups[bodygroup_id] = poly['pgroup']

    # get name
    f.seek(name_clump_start + poly['name'])
    poly_name = util.readstring(f)

    util.log('obj {:03d} "{:s}": {:d} verts, {:d} faces. Bodygroup? {:08x}, IdentifierA {:08x}' \
      .format(i, poly_name, int(vert_count / 3), int(face_count / 3), bodygroup_id, poly['identifiera']), level=util.LOG_DEBUG)
    util.log('debug: ', mbuf, level=util.LOG_DEBUG)
    util.log('debug: ', binascii.hexlify(poly['garbage']), level=util.LOG_DEBUG)

    # read texture properties
    # f.seek(tex1_props)
    # f.seek(0x0a, 1) # bbbbIH
    # layer_write = [0, 0, 0, 0] # UNUSED
    # tex_prop_count = util.readshort(f)
    # f.seek(0x14, 1) # bbbbIIII
    # for j in range(tex_prop_count):
    #   f.seek(0x02, 1) # bb
    #   tex_num = util.readshort(f)
    #   f.seek(0x14, 1) # IIbbbbbbbbI
    #   layer_write[j] = 1
    #   # polys[i]['tex_{:d}_num'.format(j)] = tex_num

    # read vertices
    f.seek(vert_start)
    if vert_size < 0x40:
      for j in range(vert_count):
        if vert_size == 0x08:
          vx = 0
          vy = 0
          vz = 0
        else:
          vx = util.readfloat(f)
          vy = util.readfloat(f)
          vz = util.readfloat(f)
        verts.extend((vx, vy, vz))
        bones.extend((poly['singlebind'], 0, 0, 0))
        weights.extend((1, 0, 0, 0))
        #print('read vert', hex(f.tell() - 0xC), verts[-3:])

        if vert_size == 0x00:
          f.seek(0x04, 1) # f
        elif vert_size == 0x06:
          nx = util.readhalffloat(f)
          ny = util.readhalffloat(f)
          nz = util.readhalffloat(f)
          nq = util.readhalffloat(f)
          normals.extend((nx, ny, nz, nq))
        elif vert_size == 0x07:
          nx = util.readhalffloat(f)
          ny = util.readhalffloat(f)
          nz = util.readhalffloat(f)
          nq = util.readhalffloat(f)
          nx2 = util.readhalffloat(f)
          ny2 = util.readhalffloat(f)
          nz2 = util.readhalffloat(f)
          nq2 = util.readhalffloat(f)
          nx3 = util.readhalffloat(f)
          ny3 = util.readhalffloat(f)
          nz3 = util.readhalffloat(f)
          nq3 = util.readhalffloat(f)
          normals.extend((nx, ny, nz, nq))
        elif vert_size == 0x08:
          nx = util.readhalffloat(f)
          ny = util.readhalffloat(f)
          nz = util.readhalffloat(f)
          nq = util.readhalffloat(f)
          nx2 = util.readhalffloat(f)
          ny2 = util.readhalffloat(f)
          nz2 = util.readhalffloat(f)
          nq2 = util.readhalffloat(f)
          nx3 = util.readhalffloat(f)
          normals.extend((nx, ny, nz, nq))

        crgb = (255, 255, 255)
        ca = 255
        if vert_size == 0x00 or \
          (uv_size == 0x12 or uv_size == 0x22 or uv_size == 0x42):
          crgb = (util.readbyte(f), util.readbyte(f), util.readbyte(f))
          ca = util.readbyte(f) / 127.0
          if ca >= 254: ca = 255
        colors.extend(crgb)
        alphas.append(ca)

        if uv_size >= 0x12:
          v_uvs = []
          tu = util.readhalffloat(f) * 2
          tv = (util.readhalffloat(f) * -2) + 1
          v_uvs.append((tu, tv, 0))
          if uv_size >= 0x22:
            tu2 = util.readhalffloat(f) * 2
            tv2 = (util.readhalffloat(f) * -2) + 1
            v_uvs.append((tu2, tv2, 0))
          if uv_size >= 0x32:
            tu3 = util.readhalffloat(f) * 2
            tv3 = (util.readhalffloat(f) * -2) + 1
            v_uvs.append((tu3, tv3, 0))
          if uv_size >= 0x42:
            tu4 = util.readhalffloat(f) * 2
            tv4 = (util.readhalffloat(f) * -2) + 1
            v_uvs.append((tu4, tv4, 0))
          uvs.extend(v_uvs)
    else:
      if uv_size >= 0x10:
        for j in range(vert_count):
          crgb = (127, 127, 127)
          ca = 1.0
          if uv_size >= 0x12:
            crgb = (util.readbyte(f), util.readbyte(f), util.readbyte(f))
            ca = util.readbyte(f) / 127.0
            if ca >= 254: ca = 255
          colors.extend(crgb)
          alphas.append(ca)

          v_uvs = []

          tu = util.readhalffloat(f) * 2
          tv = (util.readhalffloat(f) * -2) + 1
          v_uvs.append((tu, tv, 0))

          if uv_size >= 0x22:
            tu2 = util.readhalffloat(f) * 2
            tv2 = (util.readhalffloat(f) * -2) + 1
            v_uvs.append((tu2, tv2, 0))
          if uv_size >= 0x32:
            tu3 = util.readhalffloat(f) * 2
            tv3 = (util.readhalffloat(f) * -2) + 1
            v_uvs.append((tu3, tv3, 0))
          if uv_size >= 0x42:
            tu4 = util.readhalffloat(f) * 2
            tv4 = (util.readhalffloat(f) * -2) + 1
            v_uvs.append((tu4, tv4, 0))
          uvs.extend(v_uvs)
      else:
        for j in range(vert_count):
          crgb = (127, 127, 127)
          ca = 1.0
          colors.extend(crgb)
          alphas.append(ca)

      f.seek(vert_add_start)
      for j in range(vert_count):
        vx = util.readfloat(f)
        vy = util.readfloat(f)
        vz = util.readfloat(f)
        
        #print('read vert', hex(f.tell() - 0xC), verts[-3:])

        if vert_size == 0x40:
          f.seek(0x04, 1) # f
        elif vert_size == 0x46:
          nx = util.readhalffloat(f)
          ny = util.readhalffloat(f)
          nz = util.readhalffloat(f)
          nq = util.readhalffloat(f)
          normals.extend((nx, ny, nz, nq))
        elif vert_size == 0x47:
          nx = util.readhalffloat(f)
          ny = util.readhalffloat(f)
          nz = util.readhalffloat(f)
          nq = util.readhalffloat(f)
          nx2 = util.readhalffloat(f)
          ny2 = util.readhalffloat(f)
          nz2 = util.readhalffloat(f)
          nq2 = util.readhalffloat(f)
          nx3 = util.readhalffloat(f)
          ny3 = util.readhalffloat(f)
          nz3 = util.readhalffloat(f)
          nq3 = util.readhalffloat(f)
          normals.extend((nx, ny, nz, nq))
        
        verts.extend((vx, vy, vz))
        bones.extend((util.readbyte(f), util.readbyte(f), util.readbyte(f), util.readbyte(f)))
        weights.extend((util.readbyte(f) / 255.0, util.readbyte(f) / 255.0, util.readbyte(f) / 255.0, util.readbyte(f) / 255.0))


    # read faces      
    f.seek(face_start)
    if face_size == 0x00:
      face_start = f.tell()
      vert_start = (face_count * 2) + face_start
      #print('face 0x00 start', hex(face_start), hex(vert_start))

      start_direction = 1
      f1 = util.readshort(f) + vert_len
      f2 = util.readshort(f) + vert_len
      face_direction = start_direction
      while True:
        f3 = util.readshort(f)
        if f3 == 0xFFFF:
          f1 = util.readshort(f) + vert_len
          f2 = util.readshort(f) + vert_len
          face_direction = start_direction
        else:
          f3 += vert_len
          face_direction *= -1
          if f1 != f2 and f1 != f3 and f2 != f3:
            if face_direction > 0:
              #print('add face', f3, f2, f1, colors[f3], colors[f2], colors[f1])
              faces.extend((128, f3, f2, f1, f3, f2, f1))
            else:
              #print('add face', f1, f2, f3, colors[f1], colors[f2], colors[f3])
              faces.extend((128, f2, f3, f1, f2, f3, f1))
          f1 = f2
          f2 = f3
        if f.tell() == vert_start:
          break
    elif face_size == 0x40:
      #print('face 0x40 start', hex( f.tell() ), face_count, int(face_count / 3))
      for j in range(int(face_count / 3)):
        fa = util.readshort(f) + vert_len
        fb = util.readshort(f) + vert_len
        fc = util.readshort(f) + vert_len
        #print('add face', fa, fb, fc, colors[fa], colors[fb], colors[fc])
        faces.extend((128, fa, fb, fc, fa, fb, fc))
      # w = ([], [])
      # max_weight = 0
      # if weights[0] != 0: max_weight += weights[0]
      # if weights[1] != 0: max_weight += weights[1]
      # if weights[2] != 0: max_weight += weights[2]
      # if weights[3] != 0: max_weight += weights[3]
      # if max_weight != 0:
      #   if weights[0] != 0:
      #     w[0].append(self.bones[0][0])
      #     w[1].append(weights[0])
      #   elif weights[1] != 0:
      #     w[0].append(self.bones[0][1])
      #     w[1].append(weights[1])
      #   elif weights[2] != 0:
      #     w[0].append(self.bones[0][2])
      #     w[1].append(weights[2])
      #   elif weights[3] != 0:
      #     w[0].append(self.bones[0][3])
      #     w[1].append(weights[3])

    f.seek(next_poly_addr)

  util.log('{:d} verts, {:d} uvs, {:d} faces, {:d} skin indices, {:d} skin weights'.format(
    int(len(verts) / 3), len(uvs), int(len(faces) / 4), int(len(bones) / 4), int(len(weights) / 4)), level=util.LOG_INFO)

  return {
    'scale': 1.0,
    'metadata': {
      'vertices': len(verts),
      'faces': len(faces) / 4
    },
    'influencesPerVertex': 4,
    'vertices': verts,
    'skinIndices': bones,
    'skinWeights': weights,
    'faces': faces,
    'colors': colors
  }
