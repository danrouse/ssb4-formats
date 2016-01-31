import os, re, json
import numpy as np
import util, fmt_nud, fmt_vbn, fmt_pac, fmt_omo

def get_fighters(base):
  fighters = []
  for f in os.listdir(os.path.join(base, 'fighter')):
    if f != 'common' and f != 'mii': fighters.append(f)
  return fighters

def get_fighter_paths(base, name):
  return {
    'nud': os.path.join(base, 'fighter', name, 'model', 'body', 'c00', 'model.nud'),
    'vbn': os.path.join(base, 'fighter', name, 'model', 'body', 'c00', 'model.vbn'),
    'pac': os.path.join(base, 'fighter', name, 'motion', 'body', 'main.pac')
  }

if __name__ == '__main__':
  util.log_level = util.LOG_INFO
  paths = get_fighter_paths('S:\\SSB4\\extracted_content', 'cloud')
  bones, bone_uids = fmt_vbn.read(paths['vbn'])
  archive = fmt_pac.read(paths['pac'])

  # convert OMOs into JSON animation format
  animations = []
  for f, f_data in archive.items():
    m = re.match('.+([A-Z])\d{2}(.+)\.([a-z]{3})', f)
    if m.group(3) == 'omo' and (m.group(1) == 'A'):
      motion = fmt_omo.read(f_data)
      animation = {
        'name': m.group(2),
        'fps': 30,
        'length': motion['frame_count'] / 30,
        'hierarchy': [{ 'parent': b['parent'], 'keys': []} for b in bones]
      }
      if motion['unknown']:
        animation['name'] += '_INCOMPLETE'

      for channel in motion['channels']:
        bone_index = bone_uids[channel['bone']]
        for i, frame in enumerate(channel['frames']):
          frame['time'] = i / 30
          if 'pos' in frame:
            frame['pos'] = list(np.add(bones[bone_index]['pos'], frame['pos']))
          animation['hierarchy'][bone_index]['keys'].append(frame)

      # clean up empty frames
      for bone, _ in enumerate(animation['hierarchy']):
        if len(animation['hierarchy'][bone]['keys']) == 0:
          del animation['hierarchy'][bone]
      animations.append(animation)

  model = fmt_nud.read(paths['nud'])
  model['metadata']['bones'] = len(bones)
  model['bones'] = bones
  model['animations'] = animations

  json.encoder.FLOAT_REPR = lambda o: format(o, '.4f')
  with open('model_test/model.json', 'w') as fh:
    fh.write(json.dumps(model, indent=2))