import util
import re
from collections import OrderedDict

def read(pac_path, read_inner=False):
  f = open(pac_path, 'rb')
  assert f.read(4) == b'KCAP'
  util.log('\nReading PAC', pac_path, level=util.LOG_INFO)

  files = OrderedDict()

  f.seek(0x04, 1)
  file_count = util.readlong(f)
  util.log('{:d} files in archive'.format(file_count), level=util.LOG_INFO)
  
  if read_inner:
    import fmt_omo

  for i in range(0, file_count):
    f.seek(0x10 + i*4)
    f.seek(util.readlong(f))
    file_name = util.readstring(f)

    m = re.match('(.*)([A-Z])([0-9][0-9])(.*)\.([a-z]{3})', file_name)
    if not m:
      util.log('Unmatched file skipped', file_name, level=util.LOG_ERROR)
      continue

    bodygroup = m.group(1)
    motion_name = m.group(4)
    ext = m.group(5)

    f.seek(0x10 + (file_count * 4) + (i * 4))
    file_offset = util.readlong(f)
    f.seek(0x10 + (file_count * 8) + (i * 4))
    file_len = util.readlong(f)

    f.seek(file_offset)
    file_contents = f.read(file_len)
    assert(len(file_contents) == file_len)

    if read_inner and m.group(5) == 'omo':
      util.log('\nReading OMO', file_name, level=util.LOG_INFO)
      files[file_name] = fmt_omo.read(file_contents)
    else:
      files[file_name] = file_contents

  return files