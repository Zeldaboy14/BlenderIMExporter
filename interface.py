import bpy

bpy.types.Material.use_trainz_material_type = bpy.props.BoolProperty(
    name="Use preset material type",
    description="This will allow easy access to setting a Trainz material type from the dropdown below.",
    default=False
)

bpy.types.Material.lock_diffuse_to_specular = bpy.props.BoolProperty(
    name="Lock ambient to diffuse",
    description="Feature from Gmax/3dsmax. Takes the diffuse color, and uses that on export instead of the specular color.",
    default=True
)

bpy.types.Material.trainz_phong_version = bpy.props.EnumProperty(
    name="Phong Versioning",
    items=[
        ('gmax',  "gmax",  "gmax handles this as glossiness, and handles 0 to 100 as 0.000 to 1.000 in the Mesh File."),
        ('3dsmax',  "3dsmax",  "3dsmax handles this as glossiness, and handles 0 to 100 as 0.000 to 100.000 in the Mesh File."),
        ('Blender',  "Blender",  "Blender handles this as specular hardness, and handles 0 to 511 as 0.000 to 100.000 in the Mesh File."),
    ],
    default='Blender'
)

bpy.types.Material.trainz_material_type = bpy.props.EnumProperty(
    name="Material Type",
    items=[
        ('.m.onetex',  "m.onetex",  "Native to Trainz on launch. Diffuse texture mapped material."),
        ('.m.gloss',   "m.gloss",   "Native to Trainz on launch. Reflection is died to the alpha of the diffuse map."),
        ('.m.notex',   "m.notex",   "Native to Trainz on launch. Non-textured material"),
        ('.m.reflect', "m.reflect", "Native to Trainz on launch. Reflection map blended onto a diffuse map"),
        ('.m.tbumptex', "m.tbumptex", "Introduced in TRS2004. Bump mapped material"),
        ('.m.tbumpgloss', "m.tbumpgloss", "Introduced in TRS2004. Reflection map blended onto a bump map"),
        ('.m.tbumpenv', "m.tbumpenv", "Introduced in Trainz 2009. Enviromental reflection bump map. In TRS2019, the alpha channel of the diffuse is the metallic, and normal map alpha is roughness"),
    ],
    default='.m.onetex'
)

bpy.types.Material.trainz_tile_options = bpy.props.EnumProperty(
    name="Tile Options",
    items=[
        ('st',  "st",  "Tile both horizontally and vertically."),
        ('s', "s",   "Tile horizontally."),
        ('t', "t",   "Tile vertically."),
        ('none',   "none",   "Don't tile the image."),
    ],
    default='st'
)

bpy.types.Material.use_trainz_compression = bpy.props.BoolProperty(
    name="Use Compression",
    description="This tag hints the usage of a particular texture compression scheme. If you don't have a specific effect in mind, don't enable this.",
    default=False
)

bpy.types.Material.trainz_compression_options = bpy.props.EnumProperty(
    name="Compression",
    items=[
        ('none',   "none",   "Don't compress the image."),
        ('dxt1',   "dxt1",   "DXT1 does not store alpha data enabling higher compression ratio of 8:1. DXT1 can be used for masked alpha textures."),
        ('dxt3',   "dxt3",   "DTX3 is well suited to images with sharp alpha transitions, between translucent and opaque areas. Compression ratio is 4:1."),
        ('dxt5',   "dxt5",   "DXT5 is considered to be the most flexible general purpose compression codec. Compression ratio is 4:1."),
    ],
    default='none'
)

bpy.types.Material.use_trainz_alphahint = bpy.props.BoolProperty(
    name="Use Alphahint",
    description="The 'AlphaHint' tag allows you to force a particular alpha mode on the texture.",
    default=False
)

bpy.types.Material.trainz_alphahint = bpy.props.EnumProperty(
    name="Alphahint",
    items=[
        ('opaque',   "opaque",   "Alpha channel is pure white."),
        ('semitransparent',   "semitransparent",   "Alpha channel is a grayscale blend."),
        ('masked',   "masked",   "Alpha channel is clamped to a pure black&white bitmap based on a 50% threshold."),
    ],
    default='opaque'
)

class IM_PT_Material(bpy.types.Panel):
    bl_label = 'Trainz Material Settings'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"
    
    @classmethod
    def poll(self, context):
        material = context.material
        return material is not None

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        mat = context.material   
        
        row = col.row(align=True)
        row.label(text='Trainz Mesh Properties:')
        layout = col.row()  
        col = layout.column()
        
        layout = col.row()
        
        layout.prop(context.material, 'lock_diffuse_to_specular', text="Use Diffuse as Specular")
        
        layout = col.row()
        
        layout.prop(context.material, 'trainz_phong_version')
        
        layout = col.row()
        
        layout.prop(context.material, 'use_trainz_material_type')
        
        layout = col.row()
        
        layout.active = context.material.use_trainz_material_type
        layout.prop(context.material, "trainz_material_type", text="Material Type")
        
        layout = col.row()
        
        row = col.row(align=True)
        row.label(text='texture.txt Properties:')
        layout = col.row()
        col = layout.column()
        
        layout = col.row()
        
        layout.prop( context.material, "trainz_tile_options", text="Tile Options" )
        
        layout = col.row()
        
        layout.prop(context.material, 'use_trainz_compression')
        
        layout = col.row()
        
        layout.active = context.material.use_trainz_compression
        layout.prop( context.material, "trainz_compression_options", text="Compression" )
        
        layout = col.row()

        layout.prop(context.material, 'use_trainz_alphahint')
        
        layout = col.row()
        
        layout.active = context.material.use_trainz_alphahint
        layout.prop( context.material, "trainz_alphahint", text="Alphahint" )
        
bpy.types.Scene.trainz_info_version = bpy.props.EnumProperty(
    name="INFO",
    items=[
        ('100', '100 (Shadowlands, Harn)', ''),
        ('101', '101 (JET SDK)', ''),
        ('102', '102 (JET SDK)', 'Added max influence per vert and chunk'),
        ('104', '104 (Trainz)', 'Added bounding box'),
    ],
    default='104'
)

bpy.types.Scene.trainz_matl_version = bpy.props.EnumProperty(
    name="MATL",
    items=[
        ('101', '101 (JET SDK)', ''),
        ('102', '102 (JET SDK, Trainz 1.1)', 'Added name, custom properties, opacity'),
        ('103', '103 (Trainz)', ''),
    ],
    default='103'
)

bpy.types.Scene.trainz_geom_version = bpy.props.EnumProperty(
    name="GEOM",
    items=[
        ('100', '100 (JET SDK samples, D20)', ''),
        ('101', '101 (JET SDK)', 'Added flags, primitive types, face normals'),
        ('102', '102 (JET SDK)', 'Added max influence'),
        ('103', '103 (Bridge It)', 'Support for multiple texturesets'),
        ('104', '104 (Bridge It)', 'Support for vertex colors'),
        ('200', '200 (Trainz)', '102 with parent bones'),
        ('201', '201 (Trainz)', '200 with tangents data'),
    ],
    default='201'
)

bpy.types.Scene.export_curves = bpy.props.BoolProperty(
    name="Export Curves",
    description="Export curves as line primitives (broken in TANE+)",
    default=False,
)

bpy.types.Scene.export_split = bpy.props.BoolProperty(
    name="Split Face Normals",
    description="Split the face data, as if its edge split. If a model is already pre-split, don't enable this.",
    default=False,
)
        
class IM_PT_Scene(bpy.types.Panel):
    bl_label = 'Trainz Mesh Settings'
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        
        row = col.row(align=True)
        row.label(text='IM Versioning:')
        layout = col.row()  
        col = layout.column()

        layout = col.row()
        
        layout.prop( context.scene, "trainz_info_version", text="INFO Version" )
        
        layout = col.row()

        layout.prop( context.scene, "trainz_matl_version", text="MATL Version" )
        
        layout = col.row()

        layout.prop( context.scene, "trainz_geom_version", text="GEOM Version" )
        
        layout = col.row()
        
        row = col.row(align=True)
        row.label(text='IM Mesh Export Settings:')
        layout = col.row()
        
        layout.prop( context.scene, "export_curves" )
        
        layout.prop( context.scene, "export_split" )

classes = (
    IM_PT_Material,
    IM_PT_Scene,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)