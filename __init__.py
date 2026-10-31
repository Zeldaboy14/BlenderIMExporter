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
import bmesh
import mathutils
import os
import traceback

from bpy.props import (
        BoolProperty,
        FloatProperty,
        StringProperty,
        EnumProperty,
        )
from bpy_extras.io_utils import (
        ImportHelper,
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
            
    export_vertex_colors = BoolProperty(
            name="Vertex Colors",
            description="Export vertex color data (disables tangents)",
            default=False,
            )
            
    export_neighbor_info = BoolProperty(
            name="Adjacency Data",
            description="Export triangle adjacency information. Requires triangulated geometry. This can be slow",
            default=False,
            )

    use_kin = BoolProperty(
            name="Export Animation",
            description="Write out the kin file",
            default=True,
            )
            
    use_blender_framerate = BoolProperty(
            name="Use Blender Frame Rate",
            description="Use the configured blender framerate instead of the default (30 fps). May cause issues with bogey exports",
            default=False,
            )
    
    use_skel = BoolProperty(
            name="Use SKEL Hierarchy",
            description="Use a SKEL hierarchy instead of INFL to store bone data. Will break skinning, but can reduce file size",
            default=False,
            )

    export_anim_scale = BoolProperty(
            name="Export Scaling Data",
            description="Export additional scaling data in animations",
            default=False,
            )

    use_relative_positioning = BoolProperty(
            name="Use Relative Positioning",
            description="Use relative positioning in animation data. (Only supported in TANE+)",
            default=False,
            )

    export_all_bones = BoolProperty(
            name="Export All Bones",
            description="Exports all bones/animated nodes, regardless of b.r. prefix",
            default=False,
            )

    use_nla = BoolProperty(
            name="NLA Tracks",
            description="Export each NLA track to its own .kin file",
            default=False,
            )
    
    export_events = BoolProperty(
            name="Animation Events",
            description="Exports timeline markers as animation events. Add the prefix 's.' (removed on export) for sound events, generic events will be created otherwise",
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
        layout.prop(operator, 'use_texturetxt')
        #layout.prop(operator, 'export_tangents')
        layout.prop(operator, 'export_bounds')
        layout.prop(operator, 'export_neighbor_info')
        #layout.prop(operator, 'use_kin')


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
        
        layout.prop(operator, 'export_vertex_colors')
        
        #layout.prop(operator, 'export_curves')
        layout.prop(operator, 'global_scale')
        layout.prop(operator, 'path_mode')
        #layout.prop(operator, 'use_triangles')
        
class IM_PT_export_armature(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Armature"
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

        layout.prop(operator, 'use_skel')
        layout.prop(operator, 'export_all_bones')
        
class IM_PT_export_animation(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Animation"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_im"

    def draw_header(self, context):
        sfile = context.space_data
        operator = sfile.active_operator

        self.layout.prop(operator, 'use_kin', text="")

    def draw(self, context):
        layout = self.layout
        if blender_version > 2080000:
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.enabled = operator.use_kin
        
        layout.prop(operator, 'export_anim_scale')
        layout.prop(operator, 'use_relative_positioning')
        layout.prop(operator, 'use_nla')
        layout.prop(operator, 'export_events')
        layout.prop(operator, 'use_blender_framerate')

def menu_func_export(self, context):
    menu_icon = custom_icons_export["main"]["trainz_icon_export"]
    self.layout.operator(ExportIM.bl_idname, icon_value=menu_icon.icon_id, text="Indexed Mesh (.im)")

classesexport = (
    ExportIM,
    IM_PT_export_include,
    IM_PT_export_geometry,
    IM_PT_export_animation,
    IM_PT_export_armature,
)

# --------------------------------------------------------------------------------
#  Custom Icons
# --------------------------------------------------------------------------------
custom_icons_export = {}
    
def registerCustomIconExport():
    import bpy.utils.previews
    pcoll = bpy.utils.previews.new()
    script_path = os.path.dirname(__file__)
    icons_dir = os.path.join(script_path, "icons")
    pcoll.load("trainz_icon_export", os.path.join(icons_dir, "trainz_icon.png"), 'IMAGE')
    custom_icons_export["main"] = pcoll

def unregisterCustomIconExport():
    for pcoll in custom_icons_export.values():
        bpy.utils.previews.remove(pcoll)
    custom_icons_export.clear()

def register():
    for cls in classesexport:
        bpy.utils.register_class(cls)
    registerCustomIconExport()
    bpy.types.INFO_MT_file_export.append(menu_func_export)
    interface.register()
    


def unregister():
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    interface.unregister()   
        
    for cls in classesexport:
        bpy.utils.unregister_class(cls)

    unregisterCustomIconExport()

if __name__ == "__main__":
    register()