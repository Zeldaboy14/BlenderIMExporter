import bpy

bpy.types.Material.use_trainz_material_type = bpy.props.BoolProperty(
    name="Use preset material type",
    description="This will allow easy access to setting a Trainz material type from the dropdown below.",
    default=False
)

bpy.types.Material.trainz_material_type = bpy.props.EnumProperty(
    name="Material",
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

class IM_PT_main(bpy.types.Panel):
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
        
        # for now. this will be disabled. hooks into nothing
        #layout.prop(
        #    context.scene,
        #    "use_trainzVer",
        #    text="Trainz Version"
        #)
        
        #if mat.trainz_material_type in ('.m.tbumptex', '.m.tbumpgloss'):
        #    if scene.use_trainzVer in ('UTC'):
        #        row = layout.row()
        #        row.label(
        #            text="Warning: Material requires TRS2004 or newer",
        #            icon='ERROR'
        #        )

        #elif mat.trainz_material_type == '.m.tbumpenv':
        #    if scene.use_trainzVer in ('UTC', '2006'):
        #        row = layout.row()
        #        row.label(
        #            text="Warning: Material requires Trainz 2009 or newer",
        #            icon='ERROR'
        #        )
        
        
        layout = col.row()
        
        layout.prop(context.material, 'use_trainz_material_type')
        
        layout = col.row()
        
        layout.active = context.material.use_trainz_material_type
            
        layout.prop(
            context.material,
            "trainz_material_type",
            text="Material Type"
        )
        
        layout = col.row()
        
        layout.prop(
            context.material,
            "trainz_tile_options",
            text="Tile Options"
        )
        
        layout = col.row()
        
        layout.prop(context.material, 'use_trainz_compression')
        
        layout = col.row()
        
        layout.active = context.material.use_trainz_compression
        layout.prop(
            context.material,
            "trainz_compression_options",
            text="Compression"
        )
        
        layout = col.row()

        layout.prop(context.material, 'use_trainz_alphahint')
        
        layout = col.row()
        
        layout.active = context.material.use_trainz_alphahint
        layout.prop(
            context.material,
            "trainz_alphahint",
            text="Alphahint"
        )


classes = (
    IM_PT_main,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)