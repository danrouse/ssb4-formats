import util
import struct, sys
import numpy as np

OMO_entry_flags = [
  (0b100000000000000000000000000, 'has_scale'),
  (0b010000000000000000000000000, 'has_rotation'),
  (0b001000000000000000000000000, 'has_translation'),
  (0b000001000000000000000000000, 'is_translation_fixed'),
  (0b000000010000000000000000000, 'is_translation_inter'),
  (0b000000001000000000000000000, 'is_translation_frame'),
  (0b000000000000111000000000000, 'is_rotation_fixed'),
  (0b000000000000110000000000000, 'is_rotation_quat'),
  (0b000000000000101000000000000, 'is_rotation_euler'),
  (0b000000000001010000000000000, 'is_rotation_frame'),
  (0b000000000000000001000000000, 'is_scale_fixed'),
  (0b000000000000000000010000000, 'is_scale_inter')
]

def read(omo_input, debug_bones=[], debug_bone_ids={}):
  f = util.open_mixed(omo_input)
  assert f.read(4) == b'OMO '

  has_unk = False

  _,_,_,_, \
  channel_count, frame_count, frame_entry_size, \
  channel_data_offset, fixed_data_offset, frame_data_offset = struct.unpack('>HHIHHHHIII', f.read(28))

  util.log('{:d} channels, {:d} frames ({:04x}), offsets: channels {:08x}, fixed {:08x}, frames {:08x}' \
    .format(channel_count, frame_count, frame_entry_size, channel_data_offset, fixed_data_offset, frame_data_offset), level=util.LOG_VERBOSE)

  # channel table. each channel is an animation for a single bone
  channels = []
  
  f.seek(channel_data_offset)
  for i in range(channel_count):
    data = f.read(16)
    flags, bone_id, fixed_offset, frame_offset = struct.unpack('>IIII', data)

    # read flags into booleans
    attribs = {}
    for flag, flag_name in OMO_entry_flags:
      attribs[flag_name] = flags & flag == flag

    util.log('Channel {:d} - flags: {:08x}, bone UID: {:08x}, fixed {:08x}, frame {:08x}' \
      .format(i, flags, bone_id, fixed_offset, frame_offset), level=util.LOG_VERBOSE)
    util.log(attribs, level=util.LOG_VERBOSE)

    if bone_id not in debug_bone_ids:
      print('Ignoring channel', i, bone_id)
      continue

    channel_pos = f.tell() # return here later to read next channel(s)
    channel_frames = [{}]

    # init lerp values in this scope
    inter_scale_start = inter_scale_diff = \
    inter_rotation_start = inter_rotation_diff = \
    inter_translation_start = inter_translation_diff = False

    # read fixed data into frame 0 and calculate lerp values
    f.seek(fixed_data_offset + fixed_offset)

    if attribs['has_scale']:
      if attribs['is_scale_fixed']:
        channel_frames[0]['scl'] = util.readvec3(f)
        print(debug_bones[debug_bone_ids[bone_id]]['name'], 'Scale fixed', [format(f, '.2f') for f in channel_frames[0]['scl']])

      elif attribs['is_scale_inter']:
        inter_scale_start = util.readvec3(f)
        inter_scale_end = util.readvec3(f)
        inter_scale_diff = np.subtract(inter_scale_end, inter_scale_start)
        print(debug_bones[debug_bone_ids[bone_id]]['name'], 'Scale lerp start', [format(f, '.2f') for f in inter_scale_start])
        print(debug_bones[debug_bone_ids[bone_id]]['name'], 'Scale lerp end  ', [format(f, '.2f') for f in inter_scale_end])

    if attribs['has_rotation']:
      if attribs['is_rotation_fixed']:
        rotation = util.readvec3(f)
        channel_frames[0]['rot'] = util.quaternion_from_euler(*rotation, 'sxyz')
        print(debug_bones[debug_bone_ids[bone_id]]['name'], 'Rotation fixed', [format(f, '.2f') for f in rotation])
      elif attribs['is_rotation_quat']:
        channel_frames[0]['rot'] = util.readvec4(f)
        print(debug_bones[debug_bone_ids[bone_id]]['name'], 'Rotation quat', [format(f, '.2f') for f in channel_frames[0]['rot']])
      elif attribs['is_rotation_euler']:
        inter_rotation_start = util.readvec3(f)
        inter_rotation_end = util.readvec3(f)
        print(debug_bones[debug_bone_ids[bone_id]]['name'], 'Rotation lerp start', [format(f, '.2f') for f in inter_rotation_start])
        print(debug_bones[debug_bone_ids[bone_id]]['name'], 'Rotation lerp end  ', [format(f, '.2f') for f in inter_rotation_end])
        inter_rotation_diff = np.subtract(inter_rotation_end, inter_rotation_start)

    if attribs['has_translation']:
      if attribs['is_translation_fixed']:
        channel_frames[0]['pos'] = util.readvec3(f)
        print(debug_bones[debug_bone_ids[bone_id]]['name'], 'Translation fixed', [format(f, '.2f') for f in channel_frames[0]['pos']])
      elif attribs['is_translation_inter']:
        inter_translation_start = util.readvec3(f)
        inter_translation_end = util.readvec3(f)
        inter_translation_diff = np.subtract(inter_translation_end, inter_translation_start)
        print(debug_bones[debug_bone_ids[bone_id]]['name'], 'Translation lerp start', [format(f, '.2f') for f in inter_translation_start])
        print(debug_bones[debug_bone_ids[bone_id]]['name'], 'Translation lerp end  ', [format(f, '.2f') for f in inter_translation_end])

    # read frame data
    for j in range(0, frame_count):
      f.seek(frame_data_offset + (j * frame_entry_size) + frame_offset)
      frame = {}

      if attribs['has_scale'] and attribs['is_scale_inter'] and not attribs['is_scale_fixed']:
        mults = util.readmults(f, 3)
        frame['scl'] = util.lerp(inter_scale_start, inter_scale_diff, mults)
        print(debug_bones[debug_bone_ids[bone_id]]['name'], 'F', j, 'Scale lerp', [format(m, '.2f') for m in mults])
      
      if attribs['has_rotation'] and not attribs['is_rotation_fixed']:
        if attribs['is_rotation_quat']:
          mult = util.readmults(f, 1)
          print(debug_bones[debug_bone_ids[bone_id]]['name'], 'F', j, 'Rotation quat', [format(m, '.2f') for m in mult])
          has_unk = True

        elif attribs['is_rotation_euler']:
          mults = util.readmults(f, 3)
          rotation = util.lerp(inter_rotation_start, inter_rotation_diff, mults)
          quat = util.quaternion_from_euler(*reversed(rotation), 'sxyz')
          frame['rot'] = quat
          print(debug_bones[debug_bone_ids[bone_id]]['name'], 'F', j, 'Rotation lerp', [format(m, '.2f') for m in mults])

        elif attribs['is_rotation_frame']:
          mults = util.readmults(f, 4)
          print(debug_bones[debug_bone_ids[bone_id]]['name'], 'F', j, 'Rotation frame', [format(m, '.2f') for m in mults])
          has_unk = True

      if attribs['has_translation'] and not attribs['is_translation_fixed']:
        if attribs['is_translation_inter']:
          mults = util.readmults(f, 3)
          frame['pos'] = util.lerp(inter_translation_start, inter_translation_diff, mults)
          print(debug_bones[debug_bone_ids[bone_id]]['name'], 'F', j, 'Translation lerp', [format(m, '.2f') for m in mults])

        elif attribs['is_translation_frame']:
          frame['pos'] = util.readvec3(f)
          print(debug_bones[debug_bone_ids[bone_id]]['name'], 'F', j, 'Translation frame', frame['pos'])

      if len(frame.keys()) > 0:
        util.log('Channel {:d} Frame {:d}:'.format(i, j), frame, level=util.LOG_DEBUG)
        channel_frames.append(frame)

    channels.append({
      'flags': flags,
      'bone': bone_id,
      'frames': channel_frames
    })
    # return to channel index
    f.seek(channel_pos)

  return {
    'frame_count': frame_count,
    'channels': channels,
    'unknown': has_unk
  }
