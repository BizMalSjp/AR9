"""Preserve AR9's mesh and transform animation in an Apple-compatible USDZ.

Requires the official usd-core Python package. No source model is modified.
"""
import json, re, struct, tempfile
from pathlib import Path
from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade, UsdUtils, UsdValidation

root = Path(__file__).resolve().parent.parent
raw = (root/'assets/blue-rabbit-animated.glb').read_bytes()
jlength = struct.unpack_from('<I',raw,12)[0]
doc = json.loads(raw[20:20+jlength])
binary = raw[28+jlength:]

def read_accessor(index):
    acc = doc['accessors'][index]
    view = doc['bufferViews'][acc['bufferView']]
    count = {'SCALAR':1,'VEC3':3,'VEC4':4}[acc['type']]
    kind = {5126:'f',5125:'I',5123:'H',5121:'B'}[acc['componentType']]
    row = struct.Struct('<'+kind*count)
    offset = view.get('byteOffset',0)+acc.get('byteOffset',0)
    stride = view.get('byteStride',row.size)
    values = [row.unpack_from(binary,offset+i*stride) for i in range(acc['count'])]
    return [v[0] for v in values] if count == 1 else values

with tempfile.TemporaryDirectory() as temp:
    layer = Path(temp)/'blue-rabbit.usdc'
    stage = Usd.Stage.CreateNew(str(layer))
    UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage,1.)
    stage.SetTimeCodesPerSecond(30)
    stage.SetFramesPerSecond(30)
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(300)
    master = UsdGeom.Xform.Define(stage,'/BlueRabbit')
    stage.SetDefaultPrim(master.GetPrim())
    materials = []
    for i,info in enumerate(doc['materials']):
        material = UsdShade.Material.Define(stage,f'/BlueRabbit/Materials/Material_{i}')
        shader = UsdShade.Shader.Define(stage,material.GetPath().AppendChild('Surface'))
        shader.CreateIdAttr('UsdPreviewSurface')
        pbr = info['pbrMetallicRoughness']
        shader.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*pbr['baseColorFactor'][:3]))
        shader.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(pbr['roughnessFactor'])
        shader.CreateInput('metallic',Sdf.ValueTypeNames.Float).Set(pbr['metallicFactor'])
        shader.CreateInput('opacity',Sdf.ValueTypeNames.Float).Set(1.)
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(),'surface')
        materials.append(material)

    paths,ops = {},{}
    def create_node(index,parent):
        node = doc['nodes'][index]
        label = re.sub(r'[^A-Za-z0-9_]','_',node.get('name','part'))
        path = parent.AppendChild(f'Part_{index}_{label}')
        paths[index] = path
        xf = UsdGeom.Xform.Define(stage,path)
        translate = xf.AddTranslateOp()
        translate.Set(Gf.Vec3d(*node.get('translation',[0,0,0])))
        scale = xf.AddScaleOp()
        scale.Set(Gf.Vec3f(*node.get('scale',[1,1,1])))
        ops[index] = {'translation':translate,'scale':scale}
        if 'mesh' in node:
            primitive = doc['meshes'][node['mesh']]['primitives'][0]
            mesh = UsdGeom.Mesh.Define(stage,path.AppendChild('Geometry'))
            positions = read_accessor(primitive['attributes']['POSITION'])
            normals = read_accessor(primitive['attributes']['NORMAL'])
            indices = read_accessor(primitive['indices'])
            mesh.CreatePointsAttr([Gf.Vec3f(*p) for p in positions])
            mesh.CreateNormalsAttr([Gf.Vec3f(*p) for p in normals])
            mesh.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
            mesh.CreateFaceVertexIndicesAttr(indices)
            mesh.CreateFaceVertexCountsAttr([3]*(len(indices)//3))
            mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
            mesh.CreateOrientationAttr(UsdGeom.Tokens.rightHanded)
            mesh.CreateDoubleSidedAttr(False)
            lo = Gf.Vec3f(*(min(p[k] for p in positions) for k in range(3)))
            hi = Gf.Vec3f(*(max(p[k] for p in positions) for k in range(3)))
            mesh.CreateExtentAttr([lo,hi])
            UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(materials[primitive['material']])
        for child in node.get('children',[]):
            create_node(child,path)

    for index in doc['scenes'][doc.get('scene',0)]['nodes']:
        create_node(index,master.GetPath())
    for channel in doc['animations'][0]['channels']:
        sampler = doc['animations'][0]['samplers'][channel['sampler']]
        times = read_accessor(sampler['input'])
        values = read_accessor(sampler['output'])
        path = channel['target']['path']
        op = ops[channel['target']['node']][path]
        vector = Gf.Vec3d if path == 'translation' else Gf.Vec3f
        for time,value in zip(times,values):
            op.Set(vector(*value),Usd.TimeCode(round(time*30,5)))
    stage.GetRootLayer().Save()
    target = root/'assets/blue-rabbit-animated.usdz'
    assert UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(str(layer)),str(target))
    loaded = Usd.Stage.Open(str(target))
    registry = UsdValidation.ValidationRegistry()
    checker = UsdValidation.ValidationContext(registry.GetOrLoadAllValidators())
    errors = checker.Validate(loaded)
    for error in errors:
        print(error)
    assert not errors, 'USDZ compliance errors'
    # Verify every exported animation channel retains all 301 keyframes.
    for channel in doc['animations'][0]['channels']:
        node = channel['target']['node']
        path = channel['target']['path']
        attr = loaded.GetPrimAtPath(paths[node]).GetAttribute('xformOp:'+('translate' if path=='translation' else 'scale'))
        assert attr.GetNumTimeSamples() == 301
    print(f'Created {target}: {target.stat().st_size:,} bytes; 10 animation channels; OpenUSD validation passed')
