import bpy

bpy.types.Material.trainz_material_type = bpy.props.EnumProperty(
    name="Trainz Material Type",
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

class IM_PT_main(bpy.types.Panel):
    bl_label = 'Trainz IM Mesh Exporter'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    def draw(self, context):
        layout = self.layout
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
            
        layout.prop(
            context.material,
            "trainz_material_type",
            text="Trainz Material Type"
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