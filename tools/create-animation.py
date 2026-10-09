"""Create a standalone animated GLB from AR8, without changing the source."""
import json, math, struct
from pathlib import Path

root = Path(__file__).resolve().parent.parent
source = root / 'assets/blue-rabbit.glb'
raw = source.read_bytes()
jlength = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20+jlength])
blength = struct.unpack_from('<I', raw, 20+jlength)[0]
binary = bytearray(raw[28+jlength:28+jlength+blength])
nodes = doc['nodes']
by_name = {n['name']: i for i, n in enumerate(nodes)}

def recenter(name):
    index = by_name[name]
    node = nodes[index]
    mesh = doc['meshes'][node['mesh']]
    acc = doc['accessors'][mesh['primitives'][0]['attributes']['POSITION']]
    view = doc['bufferViews'][acc['bufferView']]
    offset = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    center = [(a+b)/2 for a,b in zip(acc['min'], acc['max'])]
    for i in range(acc['count']):
        pos = struct.unpack_from('<3f', binary, offset+12*i)
        struct.pack_into('<3f', binary, offset+12*i, *(v-c for v,c in zip(pos,center)))
    acc['min'] = [a-c for a,c in zip(acc['min'],center)]
    acc['max'] = [a-c for a,c in zip(acc['max'],center)]
    node['translation'] = center
    return index, center

def accessor(values, kind):
    components = {'SCALAR':1, 'VEC3':3}[kind]
    binary.extend(b'\0' * (-len(binary) % 4))
    offset = len(binary)
    flat = values if components == 1 else [v for row in values for v in row]
    binary.extend(struct.pack('<' + str(len(flat)) + 'f', *flat))
    view = len(doc['bufferViews'])
    doc['bufferViews'].append({'buffer':0, 'byteOffset':offset, 'byteLength':len(flat)*4})
    acc = {'bufferView':view, 'componentType':5126, 'count':len(values), 'type':kind}
    if kind == 'SCALAR':
        acc.update(min=[min(values)], max=[max(values)])
    else:
        acc.update(min=[min(row[i] for row in values) for i in range(3)],
                   max=[max(row[i] for row in values) for i in range(3)])
    doc['accessors'].append(acc)
    return len(doc['accessors'])-1

duration = 10.0
times = [i/30 for i in range(301)]
time_acc = accessor(times, 'SCALAR')
animation = {'name':'Hat magic — orbiting balls and curious eyes', 'samplers':[], 'channels':[]}

def channel(index, path, values):
    sampler = len(animation['samplers'])
    animation['samplers'].append({'input':time_acc, 'output':accessor(values,'VEC3'), 'interpolation':'LINEAR'})
    animation['channels'].append({'sampler':sampler, 'target':{'node':index, 'path':path}})

def ball_pose(t, ball):
    u = ((t/duration) + ball/4) % 1
    flight = math.sin(math.pi*u)
    # Starts inside the mouth of the hat, spirals upward and returns to it.
    radius = .20 * flight
    angle = math.tau * 2*u + ball*.34
    # Move away from the character before expanding the orbit. Even the
    # largest sphere stays outside the head AND the floppy ear's bounds.
    away = min(1., flight/.30)
    away = away*away*(3-2*away)
    pos = [-.50 - .52*away + radius*math.sin(angle),
           .965 + (1.14 + .06*ball)*flight,
           .11 + radius*.62*math.cos(angle)]
    scale = max(.001, min(1., flight*5))
    return pos, [scale]*3

# Conservatively check the entire loop against the bounds of each facial
# feature and both ears, accounting for each sphere's full animated radius.
head_bounds = []
for mesh in doc['meshes']:
    if any(word in mesh['name'].lower() for word in ['head','eye','pupil','cheek','nose','tooth','teeth','smile','ear']):
        acc = doc['accessors'][mesh['primitives'][0]['attributes']['POSITION']]
        head_bounds.append((mesh['name'],acc['min'],acc['max']))
clearance = float('inf')
for i in range(2401):
    for ball,radius in enumerate([.17,.10,.08,.11]):
        pos,scale = ball_pose(i/240,ball)
        for name,lo,hi in head_bounds:
            distance = math.sqrt(sum(max(lo[k]-pos[k],0,pos[k]-hi[k])**2 for k in range(3)))
            clearance = min(clearance,distance-radius*scale[0])
assert clearance > .025, f'Ball/head clearance too small: {clearance:.4f}'
print(f'Minimum conservative head/ear clearance: {clearance*.61:.3f}m')

for ball in range(4):
    index, _ = recenter('Floating polka sphere '+str(ball))
    poses = [ball_pose(t,ball) for t in times]
    poses[-1] = poses[0]  # Exact loop seam, including scale.
    nodes[index]['translation'],nodes[index]['scale'] = poses[0]
    channel(index,'translation',[p[0] for p in poses])
    channel(index,'scale',[p[1] for p in poses])

for name, eye_center, white_radius in [
    ('Left pupil',[-.079,1.375,.165],[.070,.139,.035]),
    ('Right pupil',[.067,1.398,.164],[.067,.135,.036])]:
    index, _ = recenter(name)
    gaze = []
    for t in times:
        target,_ = ball_pose(t,0)
        dx = .030*math.tanh((target[0]-eye_center[0])/.28)
        dy = .065*math.tanh((target[1]-eye_center[1])/.42)
        front = white_radius[2]*math.sqrt(max(.1,1-(dx/white_radius[0])**2-(dy/white_radius[1])**2))
        gaze.append([eye_center[0]+dx,eye_center[1]+dy,eye_center[2]+front+.008])
    gaze[-1] = gaze[0]
    nodes[index]['translation'] = gaze[0]
    channel(index,'translation',gaze)

doc['animations'] = [animation]
doc['extras'] = {'description':'AR9 animation preview: four balls spiral out of the hat, while both pupils follow the pink ball. Original AR8 meshes retained; background is transparent.', 'durationSeconds':duration}
doc['buffers'][0]['byteLength'] = len(binary)
doc['asset']['generator'] = 'AR9 character animation'
encoded = json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode()
encoded += b' ' * (-len(encoded)%4)
binary += b'\0' * (-len(binary)%4)
output = struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(binary)) + struct.pack('<I4s',len(encoded),b'JSON') + encoded + struct.pack('<I4s',len(binary),b'BIN\0') + binary
target = root / 'assets/blue-rabbit-animated.glb'
target.write_bytes(output)
print(f'Created {target}: {len(output):,} bytes, {len(animation["channels"])} animation channels, {duration}s loop')
