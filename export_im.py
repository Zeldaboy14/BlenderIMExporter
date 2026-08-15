import os
import io
import struct
import bmesh
import bpy
import math
import mathutils
from mathutils import Matrix, Vector, Color
from bpy_extras import io_utils
import bmesh

# Trainz PM/IM mesh header names
#ATCH
#INFL
#NINF
#GEOM
#MATL
#CHNK
#IDXM
#BONE
#SKEL
#JIRF

#### make a version number to do some unfortunatly necessary version switches
blender_version = (bpy.app.version[0] * pow(10, 6) +
                   bpy.app.version[1] * pow(10, 3) +
                   bpy.app.version[2])

def name_compat(name):
    if name is None:
        return 'None'
    else:
        return name.replace(' ', '_')

def mesh_triangulate(me):
    #import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()

def veckey2d(v):
    return round(v[0], 4), round(v[1], 4)

def power_of_two(n):
    return (n & (n-1) == 0) and n != 0

#def split_obj(split_objects, obj):
#    print("Too many vertices on object " + obj.name + "! Splitting.")
#    objcount = len(obj.vertices) % 65535
#    for i in range(objcount):
#        baseIndex = i * 65535
#        bm = bmesh.new()
#        bm.from_mesh(me)
#        #new_obj.data = obj.data.copy()
#        bm.vertices = obj.vertices[baseIndex : baseIndex + 65535]
#

    #new_obj = src_obj.copy()
    #new_obj.data = src_obj.data.copy()

def jet_str(f, str):
    #wacky Jet byte alignment
    numTerminators = 4 - len(str) % 4 if len(str) % 4 != 0 else 0
    encoded_name = (str + ('\0' * numTerminators)).encode('utf-8')
    f.write(struct.pack("<I", len(encoded_name)))
    f.write(encoded_name)

def texture_file(type, img_path, target_dir, is_npo2, use_alpha=False):
    basename = os.path.basename(img_path).lower()
    texturepath = target_dir + '\\' + os.path.splitext(basename)[0] + ".texture"
    txtpath = texturepath + ".txt"
    print("write to " + txtpath)
    with open(txtpath, "w") as f:
        f.write("Primary=" + basename + "\n")
        if use_alpha:
            f.write("Alpha=" + basename + "\n")
        f.write("Tile=st" + "\n")
        if is_npo2:
            f.write("nonpoweroftwo=1\n")
        if type == 8:
            f.write("NormalMapHint=normalmap")
    return texturepath

def chunk_ver(f, ver):
    f.write(struct.pack("<I", ver))

def end_chunk(f, chunk):
    f.write(struct.pack("<I", chunk.tell()))
    f.write(chunk.getbuffer())

def recursive_writebone(chnk, srcBone, bones_flat):
    bones_flat.append(srcBone)

    relevant_children = []
    for child in srcBone.children:
        if "b.r." in child.name:
            relevant_children.append(child)

    chnk.write('BONE'.encode('utf-8'))
    with io.BytesIO() as bone:
        chunk_ver(bone, 100)
        #BoneName
        jet_str(bone, srcBone.name)
        #NumChildren
        bone.write(struct.pack("<I", len(relevant_children)))
        #BoneList
        for child in relevant_children:
            recursive_writebone(bone, child, bones_flat)
        end_chunk(chnk, bone)


def write_kin(filepath, bones, armature, EXPORT_GLOBAL_MATRIX):
    print("Writing .kin to " + filepath)

    scene = bpy.context.scene
    #NumFrames = scene.frame_end - scene.frame_start + 1
    NumFrames = scene.frame_end - scene.frame_start

    #preprocess
    root_bone = None
    for key in bones:
        bonegroup = bones[key]
        bone = bonegroup[0]
        if bone.parent is None:
            root_bone = bone
            break

    if root_bone is None:
        print("Could not find a root bone!")
        return
        
    #if root_bone is 1:
    #    self.log("Found more than one Trainz Root Bone", LOG.ERROR)

    with open(filepath, "wb") as f:
        #JIRF, filesize
        f.write('JIRF'.encode('utf-8'))
        with io.BytesIO() as rf: #resource file
            rf.write('ANIM'.encode('utf-8'))

            rf.write('INFO'.encode('utf-8'))
            with io.BytesIO() as info:
                chunk_ver(info, 100)
                #FileName
                jet_str(info, os.path.basename(filepath).lower())
                #NumFrames
                info.write(struct.pack("<I", NumFrames))
                #FrameRate
                info.write(struct.pack("<I", 30))
                #MetricScale
                info.write(struct.pack("<f", 1.0))
                end_chunk(rf, info)

            #Events
            rf.write('EVNT'.encode('utf-8'))
            with io.BytesIO() as evnt:
                chunk_ver(evnt, 100)
                #NumEvents
                evnt.write(struct.pack("<I", 0))
                end_chunk(rf, evnt)

            bones_flat = []

            #Skeleton
            rf.write('SKEL'.encode('utf-8'))
            with io.BytesIO() as skel:
                chunk_ver(skel, 100)
                #SkeletonBlock
                recursive_writebone(skel, root_bone, bones_flat)
                #skel.write(struct.pack("<I", 0))
                end_chunk(rf, skel)

            posebones_flat = []
            if armature != None:
                for bone in bones_flat:
                    print("bone " + bone.name)
                    for posebone in armature.pose.bones:
                        if posebone.name == bone.name:
                            posebones_flat.append(posebone)
                            break

            objbones_flat = []
            for obj in bones_flat:
                if hasattr(obj, 'type') and obj.type == 'EMPTY' or obj.type == 'LATTICE':
                    objbones_flat.append(obj)

                #pose_bone = (b for b in armature.pose.bones if b.bone is bone)
                #posebones_flat.append(pose_bone)
            if armature != None:
                print("Found " + str(len(posebones_flat)) + "/" + str(len(armature.pose.bones)) + " pose bones")

            print("Found " + str(len(objbones_flat)) + " object bones")
            #FrameList
            for i in range(NumFrames):
                scene.frame_set(i)
                rf.write('FRAM'.encode('utf-8'))
                with io.BytesIO() as fram:
                    chunk_ver(fram, 100)
                    #FrameNum
                    fram.write(struct.pack("<I", i))
                    #BoneDataList
                    for pose_bone in posebones_flat:
                        #mat = pose_bone.matrix_basis
                        mat = EXPORT_GLOBAL_MATRIX * armature.matrix_world * pose_bone.matrix
                        position, rotation, scale = mat.decompose()
                        rotation = rotation.inverted()
                        #Position
                        fram.write(struct.pack("<fff", *position))
                        #Orientation
                        fram.write(struct.pack("<ffff", rotation.x, rotation.y, rotation.z, rotation.w))
                        #Scale
                        #fram.write(struct.pack("<fff", scale.x, scale.y, scale.z))

                    for obj_bone in objbones_flat:
                        #objMat = obj_bone.matrix_world
                        #if obj_bone.parent != None:
                            #objMat = obj_bone.parent.matrix_world.inverted() * objMat
                        #objMat = EXPORT_GLOBAL_MATRIX * objMat

                        objMat = obj_bone.matrix_world
                        #if obj_bone.parent is None:
                            #objMat = obj_bone.matrix_world
                        #else:
                            #pbMat = obj_bone.matrix_local.copy() * obj_bone.matrix_basis
                            #objMat = obj_bone.parent.matrix_world.copy() * pbMat

                        objMat = EXPORT_GLOBAL_MATRIX * objMat
                        position, rotation, scale = objMat.decompose()
                        rotation = rotation.inverted()
                        #Position
                        fram.write(struct.pack("<fff", *position))
                        #Orientation
                        fram.write(struct.pack("<ffff", rotation.x, rotation.y, rotation.z, rotation.w))
                        #Scale
                        #fram.write(struct.pack("<fff", scale.x, scale.y, scale.z))

                    end_chunk(rf, fram)

            end_chunk(f, rf)



#def write_file(self, filepath, objects, depsgraph, scene,
def write_file(self, filepath, objects, scene,
               EXPORT_APPLY_MODIFIERS=True,
               EXPORT_TEXTURETXT=True,
               EXPORT_TANGENTS=False,
               EXPORT_BOUNDS=True,
               EXPORT_KIN=True,
               EXPORT_SEL_ONLY=False,
               EXPORT_GLOBAL_MATRIX=None,
               EXPORT_PATH_MODE='AUTO',
               #progress=ProgressReport(),
               ):
    if EXPORT_GLOBAL_MATRIX is None:
    #if EXPORT_GLOBAL_MATRIX is None or not isinstance(EXPORT_GLOBAL_MATRIX, Matrix):
        #EXPORT_GLOBAL_MATRIX = Matrix()
        EXPORT_GLOBAL_MATRIX = mathutils.Matrix()

    #split objects
    meshes = []
    hold_meshes = [] #prevent garbage collection of bmeshes
    
    #set to defaults
    bounds_set = False
    bounds_min = mathutils.Vector((0.0, 0.0, 0.0))
    bounds_max = mathutils.Vector((0.0, 0.0, 0.0))
    
    for obj in objects:

        print("OBJ:", obj.name, obj.type)

        if obj.type != 'MESH':
            continue

        try:
            me = obj.to_mesh(
                scene,
                EXPORT_APPLY_MODIFIERS,
                'PREVIEW'
            )
            self.report({'INFO'}, "Export finished successfully.")

        except Exception as e:
            print("FAILED:", obj.name, e)
            continue
            self.report({'ERROR'}, "Export failed. Please check Blender console window.")

        if me is None:
            print("NO MESH:", obj.name)
            self.report({'ERROR'}, "Export has no mesh. Please check the console.")
            continue

        print("SUCCESS:", obj.name)

        if me is None:
            continue
        if len(me.uv_layers) == 0:
            print("Object " + obj.name + " is missing UV coodinates!") # Skipping.
            #continue

        #uv_layer = me.uv_layers.active.data
        mesh_triangulate(me)
        #me.transform(EXPORT_GLOBAL_MATRIX @ obj.matrix_world)
        me.transform(EXPORT_GLOBAL_MATRIX * obj.matrix_world)

        if len(me.uv_layers) == 0:
            uv_layer = None
        else:
            uv_layer = me.uv_layers.active.data[:]
        me_verts = me.vertices[:]
        me_edges = me.edges[:]
        me.calc_normals_split() #unsure
        if EXPORT_TANGENTS:
            me.calc_tangents()

        #bm = bmesh.new()
        #hold_meshes.append(bm)
        #bm.from_mesh(me)
        #bmesh.ops.triangulate(bm, faces=bm.faces)


        objectParent = None #empty and lattice parents
        if obj.parent != None:
            if "b.r." in obj.parent.name:
                objectParent = obj.parent


        #split_faces = []
        #idx2idxmap = {}
        print("Processing mesh...")

        #vertgroups = obj.vertex_groups.keys()
        vertgroups = obj.vertex_groups

        #split into materials
        materials = me.materials[:]
        print("object contains " + str(len(materials)) + " materials")
        #mat_count = len(materials) if len(materials) > 0 else 1
        if len(materials) == 0:
            materials.append(None)

        #split_matblocks = [None] * len(materials)
        split_matblocks = [[] for i in range(len(materials))]
        for face in me.polygons:
            mat_index = face.material_index
            if mat_index is None:
                mat_index = 0
            split_matblocks[mat_index].append(face)


        for i, srcobject in enumerate(split_matblocks):
            #wasCopied = [None] * len(me_verts)
            uv_dict = {}
            uv = uv_key = uv_val = None
            unique_verts = []
            indices = []
            normals = []
            face_normals = [] #[]
            tangents = []

            area = 0.0
            for face in srcobject:
                area += face.area

                #split_faces.append(face)
                face_normals.append(face.normal.normalized())
                #face_normals.append([0.0, 0.0, 1.0])

                for uv_index, l_index in enumerate(face.loop_indices):
                    loop = me.loops[l_index]
                    vert = me_verts[loop.vertex_index]

                    uv = uv_layer[l_index].uv if uv_layer != None else [0, 0]
                    uv_key = loop.vertex_index, veckey2d(uv)
                    #uv_key = veckey2d(uv)
                    uv_val = uv_dict.get(uv_key)

                    #vert = loop.vert
                    if uv_val is None: #wasCopied[loop.vertex_index] is None or
                        #wasCopied[loop.vertex_index] = len(unique_verts)
                        uv_dict[uv_key] = len(unique_verts)

                        influences = []
                        for group in vertgroups:
                            try:
                                weight = group.weight(loop.vertex_index)
                            except RuntimeError:
                                weight = 0.0
                            if weight != 0.0:
                                influences.append([group.name, weight])

                        #for infl in influences:
                            #print("vert infl obj " + obj.name + " " + infl[0] + ": " + str(infl[1]))
                        unique_verts.append([vert.co[:], uv[:], influences])
                        #normals.append(vert.normal.normalized())
                        normals.append(loop.normal.normalized())
                        if EXPORT_TANGENTS:
                            tangents.append(loop.tangent.normalized())
                            
                            
                        if EXPORT_BOUNDS:
                            if bounds_set:
                                bounds_min.x = min(bounds_min.x, vert.co.x)
                                bounds_min.y = min(bounds_min.y, vert.co.y)
                                bounds_min.z = min(bounds_min.z, vert.co.z)
                                bounds_max.x = max(bounds_max.x, vert.co.x)
                                bounds_max.y = max(bounds_max.y, vert.co.y)
                                bounds_max.z = max(bounds_max.z, vert.co.z)
                            else:
                                bounds_set = True
                                bounds_min = mathutils.Vector(vert.co)
                                bounds_max = mathutils.Vector(vert.co)

                    #indices.append(wasCopied[loop.vertex_index])
                    indices.append(uv_dict[uv_key])

                if len(unique_verts) > 65532 or len(indices) // 3 > 65535:
                    #apply and update
                    #ret = bmesh.ops.split(bm, geom=split_faces)
                    #split_blocks.append(ret["geom"])
                    meshes.append([obj, materials[i],
                                   unique_verts.copy(),
                                   indices.copy(),
                                   normals.copy(),
                                   face_normals.copy(),
                                   tangents.copy(),
                                   area,
                                   uv_layer,
                                   objectParent])

                    unique_verts.clear()
                    indices.clear()
                    normals.clear()
                    face_normals.clear()
                    tangents.clear()
                    area = 0.0
                    #split_faces.clear()
                    #idx2idxmap.clear()
                    #wasCopied = [None] * len(me_verts)
                    uv_dict.clear()
                    uv = uv_key = uv_val = None
                    print("Block split.")

            #Add remaining verts
            if len(unique_verts) > 0:
                meshes.append([obj, materials[i],
                               unique_verts.copy(),
                               indices.copy(),
                               normals.copy(),
                               face_normals.copy(),
                               tangents.copy(),
                               area,
                               uv_layer,
                               objectParent])
        print("Complete.")

        #bm.free()

    active_armature = None
    bones = {}
    root_bone = None
    for ob in objects:
        if ob.type != 'ARMATURE':
            continue
        active_armature = ob
        break

    if active_armature is None:
        print("No armature in scene.")
        #EXPORT_KIN = False
    else:
        for bone in active_armature.data.bones:
            if "b.r." in bone.name:
                #bone, chunk influences
                bones[bone.name] = [bone, [[] for _ in range(len(meshes))]]
                if bone.parent == None:
                    root_bone = bone

    #legacy empty, lattice support
    for ob in objects:
        if "b.r." in ob.name:
            print("Found bone object " + ob.name)
            #ob.scale = [1.0, 1.0, 1.0]
            #bpy.context.view_layer.update()
            bones[ob.name] = [ob, [[] for _ in range(len(meshes))]]
            if ob.parent == None:
                root_bone = ob

    if EXPORT_KIN:
        write_kin(os.path.splitext(filepath)[0] + ".kin", bones, active_armature, EXPORT_GLOBAL_MATRIX)
        #write_kin(os.path.dirname(filepath) + "\\anim.kin", bones, active_armature, EXPORT_GLOBAL_MATRIX)
        #reset frame after writing kin, for object transforms
        scene.frame_set(0)
        scene.update()

    #Attachment setup
    attachments = []
    for ob in objects:
        if ob.type == 'EMPTY' and 'a.' in ob.name:
            print("Attachment " + ob.name)
            attachments.append(ob)
            
            obj_loc = ob.matrix_world.translation
            #extend bounds for attachments too
            if EXPORT_BOUNDS:
                if bounds_set:
                    bounds_min.x = min(bounds_min.x, obj_loc.x)
                    bounds_min.y = min(bounds_min.y, obj_loc.y)
                    bounds_min.z = min(bounds_min.z, obj_loc.z)
                    bounds_max.x = max(bounds_max.x, obj_loc.x)
                    bounds_max.y = max(bounds_max.y, obj_loc.y)
                    bounds_max.z = max(bounds_max.z, obj_loc.z)
                else:
                    bounds_set = True
                    bounds_min = mathutils.Vector(obj_loc)
                    bounds_max = mathutils.Vector(obj_loc)


    copy_set = set()
    with open(filepath, "wb") as f:
        #fw = f.write
        source_dir = os.path.dirname(bpy.data.filepath)
        dest_dir = os.path.dirname(filepath)

        #JIRF, filesize
        f.write('JIRF'.encode('utf-8'))
        with io.BytesIO() as rf: #resource file
            rf.write('IDXM'.encode('utf-8'))

            rf.write('INFO'.encode('utf-8'))
            with io.BytesIO() as info:
                if EXPORT_BOUNDS:
                    chunk_ver(info, 104)
                else:
                    chunk_ver(info, 102)
                    
                objLocation, objRotation, objScale = EXPORT_GLOBAL_MATRIX.decompose();
                #Position
                info.write(struct.pack("<fff", objLocation.x, objLocation.y, objLocation.z))
                #Rotation
                #info.write(struct.pack("<ffff", objRotation.x, objRotation.y, objRotation.z, objRotation.w))
                info.write(struct.pack("<ffff", objRotation.w, objRotation.x, objRotation.y, objRotation.z))
                #NumAttributes
                info.write(struct.pack("<I", len(meshes)))
                #MaxInfluencePerVertex
                info.write(struct.pack("<I", 0))
                #MaxInfluencePerChunk
                info.write(struct.pack("<I", 0))

                #Bounding Box
                if EXPORT_BOUNDS:
                    info.write(struct.pack("<fff", bounds_min.x, bounds_min.y, bounds_min.z))
                    info.write(struct.pack("<fff", bounds_max.x, bounds_max.y, bounds_max.z))

                end_chunk(rf, info)


            for i, entry in enumerate(meshes):

                obj = entry[0]
                #mesh = entry[1]
                #uv_layer = entry[2]
##                [obj, materials[i]
#                               unique_verts.copy(),
#                               indices.copy(),
#                               normals.copy(),
#                               face_normals.copy(),
#                               area,
#                               uv_layer]
                mat = entry[1]
                verts = entry[2]
                indices = entry[3]
                normals = entry[4]
                face_normals = entry[5]
                tangents = entry[6]
                area = entry[7]
                uv_layer = entry[8]
                objParent = entry[9]
                #uv_layer = mesh.uv_layers.active.data
                #mesh_triangulate(mesh)
                #mat = obj.active_material

                defaultMaterial = bpy.data.materials.new(obj.name)
                if mat is None:
                    mat = defaultMaterial

                rf.write('CHNK'.encode('utf-8'))
                with io.BytesIO() as attr:
                    chunk_ver(attr, 100)
                    #Chunk ID
                    attr.write(struct.pack("<I", i))
                    attr.write('MATL'.encode('utf-8'))
                    with io.BytesIO() as matl:
                        chunk_ver(matl, 103)
                        #Name
                        jet_str(matl, mat.name + mat.trainz_material_type) #append a trainz texture type onto this
                            
                        #NumProperties
                        matl.write(struct.pack("<I", 0))

                        #BULLSHIT IMPORTER  
                        if blender_version > 2080000:
                            #nodes
                            mat_wrap = node_shader_utils.PrincipledBSDFWrapper(mat)

                            #TwoSided
                            matl.write(struct.pack("<I", int(not mat.use_backface_culling)))
                            #matl.write(struct.pack("<I", 0))
                            #Opacity
                            matl.write(struct.pack("<f", mat_wrap.alpha))
                            #Ambient
                            matl.write(struct.pack("<fff", mat_wrap.base_color[0],
                                                           mat_wrap.base_color[1],
                                                           mat_wrap.base_color[2]))
                            #Diffuse
                            matl.write(struct.pack("<fff", mat_wrap.base_color[0],
                                                           mat_wrap.base_color[1],
                                                           mat_wrap.base_color[2]))
                            #Specular
                            matl.write(struct.pack("<fff", mat_wrap.specular,
                                                           mat_wrap.specular,
                                                           mat_wrap.specular))
                            #Emissive
                            if hasattr(mat_wrap, 'emission_strength'):
                                emission_strength = mat_wrap.emission_strength
                            else:
                                emission_strength = 1.0

                            emission = [emission_strength * c for c in mat_wrap.emission_color[:3]]
                            matl.write(struct.pack("<fff", emission[0],
                                                           emission[1],
                                                           emission[2]))
                            #Shininess
                            matl.write(struct.pack("<f", (1.0 - mat_wrap.roughness) * 128.0))
                            #Texture setup
                            #texCount = 0
                            textures = []

                            image_source = [
                                None, #TEX_Ambient
                                "base_color_texture", #TEX_Diffuse
                                "specular_texture", #TEX_Specular
                                "roughness_texture", #TEX_Shine
                                "normalmap_texture" if mat.name.endswith(".m.tbumptex") else None, #TEX_Shinestrength, tbumptex uses the normal map alpha to determine shine strength?
                                "emission_color_texture" if emission_strength != 0.0 else None, #TEX_Selfillum
                                "alpha_texture", #TEX_Opacity
                                None, #TEX_Filtercolor
                                "normalmap_texture", #TEX_Bump,
                                "metallic_texture", #TEX_Reflect,
                                "ior_texture", #TEX_Refract,
                                None, #TEX_Displacement
                                ]
                            for type, entry in enumerate(image_source):
                                if entry is None:
                                    continue
                                tex_wrap = getattr(mat_wrap, entry, None)
                                if tex_wrap is None:
                                    continue
                                image = tex_wrap.image
                                if image is None:
                                    continue
                                is_npo2 = not power_of_two(image.size[0]) or not power_of_two(image.size[1])
                                if is_npo2:
                                    self.report({'WARNING'}, 'Texture ' + image.filepath + ' is not a power of two. Consider resizing it.')
                                filepath = io_utils.path_reference(image.filepath, source_dir, dest_dir,
                                                           EXPORT_PATH_MODE, "", copy_set, image.library)
                                strength = 1.0
                                if entry == "normalmap_texture":
                                    strength = 0.2 * mat_wrap.normalmap_strength
                                if EXPORT_TEXTURETXT:
                                    texturepath = texture_file(type, filepath, dest_dir, is_npo2)
                                else:
                                    basename = os.path.basename(filepath).lower()
                                    texturepath = dest_dir + '\\' + os.path.splitext(basename)[0] + ".texture"

                                textures.append([type, texturepath, strength])

                            #NumTextures
                            matl.write(struct.pack("<I", len(textures)))
                            for tex in textures:
                                #Type
                                matl.write(struct.pack("<I", tex[0]))
                                #FileName
                                jet_str(matl, tex[1])
                                #Amount
                                matl.write(struct.pack("<f", tex[2]))

                            end_chunk(attr, matl)
                        else:
                            # blender 2.7x
                            
                            # Material Types per Trainz Versions for PM/IM Meshs
                            # Introduced in Trainz     # Introduced in Ultimate Trainz Collection  # Introduced in Trainz 2004 # Introduced in Trainz 2006 # Introduced in Trainz Classics 1 & 2 / 3    # Introduced in Trainz 2009    # Introduced in Trainz 2010/2012    # Introduced in Trainz: A New Era
                            # m.tribillboard (unused)  # -> carried over                           # -> carried over           # -> carried over           # -> carried over                            # -> carried over              # -> carried over                   # Removed
                            # m.billboard (unused)     # -> carried over                           # -> carried over           # -> carried over           # -> carried over                            # -> carried over              # -> carried over                   # Removed
                            # m.reflect                # -> carried over                           # -> carried over           # -> carried over           # -> carried over                            # -> carried over              # -> carried over                   # -> carried over 
                            # m.gloss                  # -> carried over                           # -> carried over           # -> carried over           # -> carried over                            # -> carried over              # -> carried over                   # -> carried over 
                            # m.onetex                 # -> carried over                           # -> carried over           # -> carried over           # -> carried over                            # -> carried over              # -> carried over                   # -> carried over 
                            # m.notex                  # -> carried over                           # -> carried over           # -> carried over           # -> carried over                            # -> carried over              # -> carried over                   # -> carried over 
                            # None                     # None                                      # m.tbumptex                # -> carried over           # -> carried over                            # -> carried over              # -> carried over                   # -> carried over 
                            # None                     # None                                      # m.tbumpgloss              # -> carried over           # -> carried over                            # -> carried over              # -> carried over                   # -> carried over 
                            # None                     # None                                      # m.tglossrust (unused)     # -> carried over           # -> carried over                            # -> carried over              # -> carried over                   # Removed
                            # None                     # None                                      # None                      # None                      # None                                       # m.tbumpenv                   # -> carried over                   # -> carried over 
                            # None                     # None                                      # None                      # None                      # None                                       # m.tbumpglosscol (unused)     # -> carried over                   # -> carried over 
                            # None                     # None                                      # None                      # None                      # None                                       # m.tbumpcoltex (unused)       # -> carried over                   # -> carried over 
                            # None                     # None                                      # None                      # None                      # None                                       # m.nofogtex (unused)          # -> carried over                   # Removed
                            # None                     # None                                      # None                      # None                      # None                                       # m.tonetexnoalpha (unused)    # -> carried over                   # Removed
                            # None                     # None                                      # None                      # None                      # None                                       # m.tgroundonetex (unused)     # -> carried over                   # -> carried over
                            # None                     # None                                      # None                      # None                      # None                                       # m.groundbase (unused)        # -> carried over                   # Removed
                            
                            diffuse = (
                                float(mat.diffuse_color[0]),
                                float(mat.diffuse_color[1]),
                                float(mat.diffuse_color[2])
                            )
                            
                            specular = [
                                c * mat.specular_intensity
                                for c in mat.specular_color[:3]
                            ]

                            #TwoSided
                            if (obj.data.show_double_sided == True):
                                matl.write(struct.pack("<I", int(1)))
                            else:
                                matl.write(struct.pack("<I", int(0)))
                                
                            #Opacity
                            if (mat.use_transparency == True):
                                matl.write(struct.pack("<f", mat.alpha))
                            else:
                                matl.write(struct.pack("<f", 1.0))
                            
                            #Ambient
                            #Old trainz exporter writes diffuse here as well.
                            if self.use_old_ambient_color == True:
                                matl.write(struct.pack( "<fff", diffuse[0], diffuse[1], diffuse[2] ))  
                            else:
                                matl.write(struct.pack( "<fff", mat.ambient, mat.ambient, mat.ambient ))
                            
                            #Diffuse
                            matl.write(struct.pack( "<fff", diffuse[0], diffuse[1], diffuse[2] ))          
                            
                            #Specular
                            matl.write(struct.pack( "<fff", specular[0], specular[1], specular[2] ))
                                               
                            #Emissive
                            if hasattr(mat, 'emit_factor'):
                                emission_strength = mat.emit
                            else:
                                emission_strength = 1.0

                            emission = emission_strength * mat.emit

                            matl.write(struct.pack("<fff", emission, emission, emission))
                            #Shininess
                            #Gmax and 3DSMax wrote different values here.
                            if self.gmax_specular_hardness == True:
                                matl.write(struct.pack("<f", (1.0 - mat.specular_hardness + 0.0025) * 128.0))
                            else:
                                matl.write(struct.pack("<f", (1.0 - mat.specular_hardness) * 128.0))

                            textures = []
                            
                            ## documentation regarding AMBIENT, SHINE, FILTERCOLOR, and DISPLACEMENT comes from here -  https://trainz.shaneturner.co.uk/3rdparty/PM2IM%20Tutorial.pdf
                            ## textures
                            #
                            #  Jet name                    meaning               Blender name         Blender Name (2.8+)
                            #
                            #jTEX_AMBIENT       =  0 # -> ambient color         <- Amb(value)        <- None ( Deprecated in Trainz 2009 )
                            #jTEX_DIFFUSE       =  1 # -> diffuse color         <- Col               <- base_color_texture
                            #jTEX_SPECULAR      =  2 # -> specular color        <- Csp               <- specular_texture
                            #jTEX_SHINE         =  3 # -> specular level        <- Spec(value)       <- None ( Deprecated in Trainz 2009 )
                            #jTEX_SHINESTRENGTH =  4 # -> glossiness            <- Hard(value)       <- normalmap_texture
                            #jTEX_SELFILLUM     =  5 # -> self-illumination     <- Emit(value)       <- emission_color_texture
                            #jTEX_OPACITY       =  6 # -> opacity               <- Alpha(value)      <- alpha_texture
                            #jTEX_FILTERCOLOR   =  7 # -> filter color          <- TransLu???        <- None ( Deprecated in Trainz 2009 )
                            #jTEX_BUMP          =  8 # -> normal                <- Nor(normal)       <- normalmap_texture
                            #jTEX_REFLECT       =  9 # -> reflection            <- Ref(value)        <- metallic_texture
                            #jTEX_REFRACT       = 10 # -> refraction            <- RayMir???         <- ior_texture
                            #jTEX_DISPLACEMENT  = 11 # -> displacement          <- Disp              <- None ( Deprecated in Trainz 2009 )
                            #
                            image_source = [
                                None,                                                               #TEX_Ambient ( Deprecated in Trainz 2009 )
                                "base_color_texture",                                               #TEX_Diffuse
                                "specular_texture",                                                 #TEX_Specular
                                None,                                                               #TEX_Shine ( Deprecated in Trainz 2009 )
                                "normalmap_texture" if mat.name.endswith(".m.tbumptex") else None,  #TEX_Shinestrength, tbumptex uses the normal map alpha to determine shine strength?
                                "emission_color_texture" if emission_strength != 0.0 else None,     #TEX_Selfillum
                                "alpha_texture",                                                    #TEX_Opacity
                                None,                                                               #TEX_Filtercolor ( Deprecated in Trainz 2009 )
                                "normalmap_texture",                                                #TEX_Bump,
                                "metallic_texture",                                                 #TEX_Reflect,
                                "ior_texture",                                                      #TEX_Refract,
                                None,                                                               #TEX_Displacement ( Deprecated in Trainz 2009 )
                                ]
                            for type, entry in enumerate(image_source):
                                
                                tex_wrap = None
                                
                                for i, ts in enumerate(mat.texture_slots):
                                    if ts is None:
                                        continue
                                        
                                    if not mat.use_textures[i]:
                                        continue

                                    if ts.texture is None:
                                        continue

                                    if ts.texture.type != 'IMAGE':
                                        continue

                                    #compatability layer. check if we are passing a diffuse or something, and remap to rileyzzz struct from 2.8
                                    if entry == "base_color_texture":
                                        if (ts.use_map_color_diffuse and
                                                ts.texture_coords == 'UV'):
                                            tex_wrap = ts.texture
                                            break
                                    
                                    elif entry == "metallic_texture":
                                        if (ts.use_map_color_diffuse and
                                                ts.texture_coords == 'REFLECTION'):
                                            tex_wrap = ts.texture
                                            break
                                            
                                    elif entry == "normalmap_texture":                                                    
                                        if (ts.use_map_normal):
                                            tex_wrap = ts.texture
                                            break

                               
                                if tex_wrap is None:
                                    continue
                                image = tex_wrap.image
                                if image is None:
                                    continue
                                is_npo2 = not power_of_two(image.size[0]) or not power_of_two(image.size[1])
                                if is_npo2:
                                    self.report({'WARNING'}, 'Texture ' + image.filepath + ' is not a power of two. Consider resizing it.')
                                filepath = io_utils.path_reference(image.filepath, source_dir, dest_dir,
                                                        EXPORT_PATH_MODE, "", copy_set, image.library)
                                strength = 1.0
                                if entry == "base_color_texture":
                                    strength = ts.diffuse_color_factor
                                if entry == "normalmap_texture":
                                    strength = 0.2 * ts.normal_factor
                                if entry == "metallic_texture":
                                    strength = ts.diffuse_color_factor
                                if EXPORT_TEXTURETXT:
                                    texturepath = texture_file(type, filepath, dest_dir, is_npo2)
                                else:
                                    basename = os.path.basename(filepath).lower()
                                    texturepath = dest_dir + '\\' + os.path.splitext(basename)[0] + ".texture"
                                
                                textures.append([type, texturepath, strength])

                            #NumTextures
                            matl.write(struct.pack("<I", len(textures)))
                            for tex in textures:
                                #Type
                                matl.write(struct.pack("<I", tex[0]))
                                #FileName
                                jet_str(matl, tex[1])
                                #Amount
                                matl.write(struct.pack("<f", tex[2]))

                            end_chunk(attr, matl)

                    attr.write('GEOM'.encode('utf-8'))
                    with io.BytesIO() as geom:
                        chunk_ver(geom, 201)
                        #bm = bmesh.new()
                        #bm.from_mesh(mesh)
                        #bm = mesh


#                        verts = []
#                        indices = block_indices #[]
#                        normals = []
#                        facenormals = [] #[]
##                        for i, vert in enumerate(bm.verts):
##                            verts.append([vert.co, uv_layer[i].uv]) #vert.index
##                            normals.append(vert.normal)
##
##                        for face in bm.faces:
##                            for vert in face.verts:
##                                indices.append(vert.index)
##                            facenormals.append(face.normal)
#                        for vert in block_verts:
#                            verts.append([vert.co, uv_layer[vert.index].uv])
#                            normals.append(vert.normal)
#                        for face in block_faces:
#                            facenormals.append(face.normal)

                        #Flags
                        geom.write(struct.pack("<I", 4)) #GC_TRIANGLES
                        #UseTangents (201)
                        if EXPORT_TANGENTS:
                            geom.write(struct.pack("<I", 1))
                        else:
                            geom.write(struct.pack("<I", 0))

                        #Area
                        #area = sum(face.calc_area() for face in bm.faces)
                        geom.write(struct.pack("<f", area))
                        #NumVerticies
                        geom.write(struct.pack("<I", len(verts)))
                        #NumPrimitives
                        geom.write(struct.pack("<I", len(indices) // 3))
                        #NumIndices
                        geom.write(struct.pack("<I", len(indices)))
                        #NumFaceNormals
                        geom.write(struct.pack("<I", len(face_normals)))
                        #MaxInfluence
                        geom.write(struct.pack("<I", 0)) #FIX FOR ANIMATION

                        #Parent (201)
                        if objParent != None:
                            jet_str(geom, objParent.name)
                        else:
                            geom.write(struct.pack("<I", 0))

                        #Vertices
                        for idx, vert in enumerate(verts):
                            co = vert[0]
                            texcoord = vert[1]
                            influences = vert[2]

                            #geom.write(struct.pack("<fff", co[0], co[1], co[2]))
                            #geom.write(struct.pack("<ff", texcoord[0], 1.0 - texcoord[1]))

                            co_vector = mathutils.Vector((co[0], co[1], co[2], 1.0))
                            if objParent != None:
                                #OLD METHOD
                                #parentMat = EXPORT_GLOBAL_MATRIX * objParent.matrix_world
                                #co_vector = parentMat.inverted() * co_vector

                                parentLoc, parentRot, parentScale = objParent.matrix_world.decompose()

                                locMat = mathutils.Matrix.Translation(parentLoc)
                                rotMat = parentRot.to_matrix().to_4x4()
                                parentMat = locMat * rotMat
                                co_vector = EXPORT_GLOBAL_MATRIX * parentMat.inverted() * co_vector

                            #co_vector = EXPORT_GLOBAL_MATRIX * obj.matrix_parent_inverse * co_vector

                            geom.write(struct.pack("<fff", co_vector[0], co_vector[1], co_vector[2]))
                            geom.write(struct.pack("<ff", texcoord[0], 1.0 - texcoord[1]))

                            #BoneTransform = None #identity?
                            for influence in influences:
                                name = influence[0]
                                weight = influence[1]
                                if name in bones:
                                    bonegroup = bones[name]
                                    bone = bonegroup[0]
                                    chunkinfl = bonegroup[1][i]

#                                    if BoneTransform == None:
#                                        BoneTransform = bone.matrix_local * weight
#                                    else:
#                                        BoneTransform += bone.matrix_local * weight

                                    boneMat = bone.matrix_local.inverted()
                                    chunkinfl.append([idx, weight, boneMat * co_vector]) #boneMat * co_vector

                            #if BoneTransform == None:
                                #BoneTransform = mathutils.Matrix.Identity()

                            #BoneTransform = EXPORT_GLOBAL_MATRIX * obj.matrix_world * BoneTransform

                            #inverse_vector = BoneTransform.inverted() * co_vector
                            #inverse_vector = co_vector * BoneTransform.inverted()

                            #geom.write(struct.pack("<fff", inverse_vector[0], inverse_vector[1], inverse_vector[2]))
                            #geom.write(struct.pack("<ff", texcoord[0], 1.0 - texcoord[1]))

                        #Indices
                        for idx in indices:
                            geom.write(struct.pack("<H", idx))
                        #VertexNormals
                        for normal in normals:
                            geom.write(struct.pack("<fff", normal[0], normal[1], normal[2]))
                        #FaceNormals
                        for normal in face_normals:
                            geom.write(struct.pack("<fff", normal[0], normal[1], normal[2]))
                        #Tangents
                        if EXPORT_TANGENTS:
                            for tangent in tangents:
                                geom.write(struct.pack("<fff", tangent[0], tangent[1], tangent[2]))

                        #bm.free()

                        end_chunk(attr, geom)
                    end_chunk(rf, attr)
                bpy.data.materials.remove(defaultMaterial)


            rf.write('INFL'.encode('utf-8'))
            with io.BytesIO() as infl:
                chunk_ver(infl, 100)

                #NumBones
                infl.write(struct.pack("<I", len(bones)))
                #Bones
                for key in bones:
                    bonegroup = bones[key]
                    bone = bonegroup[0]
                    chunkinfl = bonegroup[1] # per chunk influences

                    #Name
                    jet_str(infl, bone.name)
                    #Parent
                    if bone.parent != None:
                        jet_str(infl, bone.parent.name)
                    else:
                        infl.write(struct.pack("<I", 0))

                    if not hasattr(bone, 'type'): #bone.type != 'EMPTY'
                        print("BONE TYPE")
                        if bone.parent == None:
                            boneMat = bone.matrix_local
                        else:
                            boneMat = bone.parent.matrix_local.inverted() * bone.matrix_local
                        boneMat = EXPORT_GLOBAL_MATRIX * active_armature.matrix_world * boneMat
                    else:
                        print("NOT BONE TYPE")
                        #boneMat = bone.matrix_local
                        #boneMat = mathutils.Matrix.Identity(4)
                        if bone.parent == None:
                            print("no parent")
                            boneMat = bone.matrix_world
                        else:
                            print("bone " + bone.name + " parent " + bone.parent.name)
                            boneMat = bone.matrix_parent_inverse * bone.matrix_world
                            #boneMat = bone.matrix_local
                            #boneMat = bone.parent.matrix_world.copy() * bone.matrix_local
                        boneMat = EXPORT_GLOBAL_MATRIX * boneMat

                    #boneMat = bone.matrix_local
                    loc, rot, scale = boneMat.decompose()

                    #rot = mathutils.Quaternion()

                    #LocalPosition
                    #infl.write(struct.pack("<fff", bone.head[0], bone.head[1], bone.head[2]))
                    infl.write(struct.pack("<fff", loc[0], loc[1], loc[2]))
                    print("bone " + bone.name + " location: " + str(loc[0]) + " " + str(loc[1]) + " " + str(loc[2]))
                    #infl.write(struct.pack("<fff", 0.0, 0.0, 5.0))
                    #LocalOrientation
                    print("bone " + bone.name + " rotation: " + str(rot.x) + " " + str(rot.y) + " " + str(rot.z) + " " + str(rot.w))

                    rotationMat = rot.to_matrix().transposed()
                    #rotationMat = rot.to_matrix()
                    infl.write(struct.pack("<fffffffff", *rotationMat[0], *rotationMat[1], *rotationMat[2]))

                    necessary_infl = []
                    for influencelist in chunkinfl:
                        #if len(influencelist) > 0:
                        necessary_infl.append(influencelist)

                    #NumInfluences
                    infl.write(struct.pack("<I", len(necessary_infl)))
                    #Influences
                    for i, influencelist in enumerate(necessary_infl):
                        #ChunkIndex
                        infl.write(struct.pack("<I", i))
                        #NumVertices
                        infl.write(struct.pack("<I", len(influencelist)))
                        for influence in influencelist:
                            #Index
                            infl.write(struct.pack("<I", influence[0]))
                            #Weight
                            infl.write(struct.pack("<f", influence[1]))
                            #Position
                            vertpos = influence[2]
                            infl.write(struct.pack("<fff", vertpos[0], vertpos[1], vertpos[2]))
                end_chunk(rf, infl)

            #AttachmentInfo
            if len(attachments) > 0:
                rf.write('ATCH'.encode('utf-8'))
                with io.BytesIO() as atch:
                    chunk_ver(atch, 100)
                    #NumAttachments
                    atch.write(struct.pack("<I", len(attachments)))
                    #Attachments
                    for att in attachments:
                        #Name
                        jet_str(atch, att.name)

                        attMat = EXPORT_GLOBAL_MATRIX * att.matrix_world
                        loc, rot, scale = attMat.decompose()
                        rotationMat = rot.to_matrix().transposed()
                        #Orientation
                        atch.write(struct.pack("<fffffffff", *rotationMat[0], *rotationMat[1], *rotationMat[2]))
                        #Position
                        atch.write(struct.pack("<fff", loc[0], loc[1], loc[2]))

                    end_chunk(rf, atch)


                #me.transform(EXPORT_GLOBAL_MATRIX * ob_mat)

            #with io.BytesIO() as attr:

            #for i, ob_main in enumerate(objects):
            end_chunk(f, rf)

        #fw('IDXM'.encode('utf-8'))
    #copy images?
    io_utils.path_reference_copy(copy_set)
    print("done")




def _write(self, context, filepath,
           EXPORT_APPLY_MODIFIERS,
           EXPORT_TEXTURETXT,
           EXPORT_TANGENTS,
           EXPORT_BOUNDS,
           EXPORT_KIN,
           EXPORT_SEL_ONLY,
           EXPORT_GLOBAL_MATRIX,
           EXPORT_PATH_MODE,
           ):
    print(bpy.context.mode)
    base_name, ext = os.path.splitext(filepath)
    context_name = [base_name, '', '', ext]  # Base name, scene name, frame number, extension

    scene = context.scene
    scene.frame_set(0)
    #scene.update()
    #scene.layers = [True] * 20

    # redo and check blender ver
    # depsgraph = context.evaluated_depsgraph_get()

    # Exit edit mode
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    if EXPORT_SEL_ONLY:
        objects = context.selected_objects
    else:
        #objects = scene.objects
        #objects = [obj for obj in scene.objects]
        # instead of writing every fucking layer, do only what we see. we may have other layers
        # with bogey's or tender stuff
        objects = []

        for obj in scene.objects:
            for i in range(20):
                if obj.layers[i] and scene.layers[i]:
                    objects.append(obj)
                    break
        
    #objects = scene.objects

    #orig_frame = scene.frame_current

    full_path = ''.join(context_name)
    
        # EXPORT THE FILE.
    #write_file(self, full_path, objects, depsgraph, scene,
    write_file(self, full_path, objects, scene,
               EXPORT_APPLY_MODIFIERS,
               EXPORT_TEXTURETXT,
               EXPORT_TANGENTS,
               EXPORT_BOUNDS,
               EXPORT_KIN,
               EXPORT_SEL_ONLY,
               EXPORT_GLOBAL_MATRIX,
               EXPORT_PATH_MODE,
               #progress,
               )



def save(self, context,
         filepath,
         *,
         use_selection=False,
         use_mesh_modifiers=True,
         use_texturetxt=True,
         export_tangents=False,
         export_bounds=True,
         use_kin=True,
         global_matrix=None,
         path_mode='AUTO'
         ):

    _write(self, context, filepath,
           EXPORT_APPLY_MODIFIERS=use_mesh_modifiers,
           EXPORT_TEXTURETXT=use_texturetxt,
           EXPORT_TANGENTS=export_tangents,
           EXPORT_BOUNDS=export_bounds,
           EXPORT_KIN=use_kin,
           EXPORT_SEL_ONLY=use_selection,
           EXPORT_GLOBAL_MATRIX=global_matrix,
           EXPORT_PATH_MODE=path_mode,
           )

    return {'FINISHED'}
    
## Start Interface Code
