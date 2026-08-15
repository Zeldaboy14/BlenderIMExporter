  # -*- coding: utf-8 -*-
"""

Trainz Mesh Exporter for Blender 2.78b

This script exports a Blender scene to use it in Trainz. It is based on
the BlenderIMExporter by rileyzzzzzzz.

Specific commit this version is based on: https://github.com/rileyzzz/BlenderIMExporter/tree/63844bde0ec677b8f445469a29f3fa03fa6694ae
Additional support from this edit by not1tfm: https://github.com/no1tfm/BlenderIMExporter

Unlike the old exporter, this is a direct-from-blender script, meaning that
we skip the middleman, aka, TrainzMeshImporter. This can provide cleaner
IM files, and allows for bigger files the old exporter couldn't do, in
no part thanks to the usage of a XML file, and conversion from TrainzMeshImporter.

known bugs:
 - currently none

"""

# Contribution 2021/06/05 #1TFM. Added version selector for you minimum trainz build.

bl_info = {
    "name": "Indexed Mesh Format (.im)",
    "author": "Riley Lemmler, not1tfm, Zeldaboy14",
    "version": (1, 00),
    "blender": (2, 78, 0),
    "api": 40968,
    "location": "File > Export",
    "description": "Export Trainz indexed meshes",
    "warning": "",
    "doc_url": "",
    "support": 'COMMUNITY',
    "category": "Import-Export",
}

if "bpy" in locals():
    import importlib
    print("reload im local")
    if "export_im" in locals():
        print("lib reload")
        importlib.reload(export_im)
from . import interface
import bpy
import os

from bpy.props import (
        BoolProperty,
        FloatProperty,
        StringProperty,
        EnumProperty,
        )
from bpy_extras.io_utils import (
        ExportHelper,
        path_reference_mode,
        axis_conversion,
        )
        
#### make a version number to do some unfortunatly necessary version switches
blender_version = (bpy.app.version[0] * pow(10, 6) +
                   bpy.app.version[1] * pow(10, 3) +
                   bpy.app.version[2])

class ExportIM(bpy.types.Operator, ExportHelper):
    """Save an Indexed Mesh File"""

    bl_idname = "export_scene.im"
    bl_label = 'Export IM'
    bl_options = {'PRESET'}

    filename_ext = ".im"
    filter_glob = StringProperty(
            default="*.im",
            options={'HIDDEN'},
            )
            
    #Handle the update to the properties when the dropdown is altered.
    def trainzVer_update (self, context):
        #if self.use_trainzVer != '2006':
        if context.scene.use_trainzVer in ('2009'):
            #self.export_tangents = True
            context.export_tangents = True
            
        #if self.use_trainzVer == '2006':
        if context.scene.use_trainzVer in ('UTC', '2006'):
            #self.export_tangents = False
            context.export_tangents = False
            
        context.region.tag_redraw()

    #Define the lsit of trainz versions
    #This can be simplified depending on whether TS2009 - TS 19 use the same settings
    #TRS04/06 appear to not support the tangents option.
    trainzVersion = [
        ("UTC",  "Ultimate Trainz Collection",'UTC or newer'),
        ("2006", "Trainz Railroad Simulator 2004/2006",'TRS04/06 or newer'),
        ("2009", "Trainz Simulator 2009",'TS09 or newer'),
    ]

    #Create the drop down to allow for selection of our target trainz version
    #Default to Trainz 2009 mode
    #use_trainzVer = EnumProperty(
    # moved to the material window
    bpy.types.Scene.use_trainzVer = EnumProperty(
            items=trainzVersion,
            name="Trainz Verison",
            description="Sets the compatibility level of the IM format.",
            default="2009",
            update=trainzVer_update,
            )
    # specular akin to gmax and 3dsmax on export        
    gmax_specular_hardness = BoolProperty(
            name="Gmax/3ds Max Specular Hardness",
            description="Compatability from the older softwares on specular hardness",
            default=False,
            )
            
    # legacy exporter stuff        
    use_old_ambient_color = BoolProperty(
            name="Set Ambient color from Diffuse color",
            description="Compatability from the old exporter. Set Ambient color as Diffuse color",
            default=True,
            )

    # context group
    use_selection = BoolProperty(
            name="Selection Only",
            description="Export selected objects only",
            default=False,
            )

    # object group
    use_mesh_modifiers = BoolProperty(
            name="Apply Modifiers",
            description="Apply modifiers",
            default=True,
            )

    use_texturetxt = BoolProperty(
            name="Export texture.txt",
            description="Write out a texture.txt for each used texture",
            default=True,
            )

    export_tangents = BoolProperty(
            name="Export Tangents",
            description="Export tangent data. Requires Trainz 2009 or higher",
            default=False,
            )
            
    export_bounds = BoolProperty(
            name="Export Bounding Box",
            description="Export bounding box data",
            default=True,
            )

    use_kin = BoolProperty(
            name="Export Animation",
            description="Write out the kin file",
            default=True,
            )


    global_scale = FloatProperty(
            name="Scale",
            min=0.01, max=1000.0,
            default=1.0,
            )

    path_mode = path_reference_mode

    check_extension = True

    def execute(self, context):
        from . import export_im

        from mathutils import Matrix
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "global_scale",
                                            "check_existing",
                                            "filter_glob",
                                            #"use_trainzVer",
                                            "use_old_ambient_color",
                                            "gmax_specular_hardness",
                                            ))

        global_matrix = (Matrix.Scale(self.global_scale, 4))

        keywords["global_matrix"] = global_matrix
        
        return export_im.save(self, context, **keywords)

    def draw(self, context):
        pass


class IM_PT_export_include(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Include"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_im"

    def draw(self, context):
        layout = self.layout
        if blender_version > 2080000:
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator
        
        #Add our version dropdown to the interface.
        # moved to the material window
        #layout.prop(operator, 'use_trainzVer')
        layout.separator()

        if blender_version > 2080000:
            col = layout.column(heading="Limit to")
        else:
            col = layout.column()
            col.label(text="Limit to")
            
        col.prop(operator, 'use_selection')

        layout.separator()
        layout.prop(operator, 'gmax_specular_hardness')
        layout.prop(operator, 'use_old_ambient_color')
        layout.prop(operator, 'use_texturetxt')
        layout.prop(operator, 'export_tangents')
        layout.prop(operator, 'export_bounds')
        layout.prop(operator, 'use_kin')


class IM_PT_export_geometry(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Geometry"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_im"

    def draw(self, context):
        layout = self.layout
        if blender_version > 2080000:
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, 'use_mesh_modifiers')
        layout.prop(operator, 'global_scale')
        layout.prop(operator, 'path_mode')
        #layout.prop(operator, 'use_triangles')

def menu_func_export(self, context):
    menu_icon = custom_icons["main"]["trainz_icon"]
    self.layout.operator(ExportIM.bl_idname, icon_value=menu_icon.icon_id, text="Indexed Mesh (.im)")


classes = (
    ExportIM,
    IM_PT_export_include,
    IM_PT_export_geometry,
)

# --------------------------------------------------------------------------------
#  Custom Icons
# --------------------------------------------------------------------------------
custom_icons = {}

def registerCustomIcon():
    import bpy.utils.previews
    pcoll = bpy.utils.previews.new()
    script_path = os.path.dirname(__file__)
    icons_dir = os.path.join(script_path, "icons")
    pcoll.load("trainz_icon", os.path.join(icons_dir, "trainz_icon.png"), 'IMAGE')
    custom_icons["main"] = pcoll


def unregisterCustomIcon():
    for pcoll in custom_icons.values():
        bpy.utils.previews.remove(pcoll)
    custom_icons.clear()

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.INFO_MT_file_export.append(menu_func_export)
    interface.register()
    
    registerCustomIcon()


def unregister():
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    interface.unregister()
    
    for cls in classes:
        bpy.utils.unregister_class(cls)
        
    unregisterCustomIcon()

if __name__ == "__main__":
    register()