bl_info = {
    "name": "Nova Tools",
    "author": "VrcFoss (Yotva)",
    "version": (1, 6),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Nova Tools",
    "description": "Combine clothes, auto weight paint, and clean unused bones. FR/EN/JP languages.",
    "category": "Rigging"
}

# Nova Tools - VrcFoss | Yotva
# ---------------------------------
# Developed by VrcFoss (Yotva)
# https://yotva.shop

import bpy

# ----------- Properties -----------

def get_lang(self):
    return self.get("_language", "EN")

def set_lang(self, value):
    self["_language"] = value
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()

bpy.types.Scene.nova_language = bpy.props.EnumProperty(
    name="Language",
    items=[("EN", "English", ""), ("FR", "Français", ""), ("JP", "日本語", "")],
    get=get_lang,
    set=set_lang
)

bpy.types.Scene.nova_collection_1 = bpy.props.StringProperty(
    name="Collection A",
    description="Clothing meshes collection",
    default="To_combine"
)

bpy.types.Scene.nova_collection_2 = bpy.props.StringProperty(
    name="Collection B",
    description="Body mesh with armature",
    default="Body"
)

bpy.types.Scene.nova_excluded_bones = bpy.props.StringProperty(
    name="Exclude Bones",
    description="Comma-separated list of bones to keep (e.g. Root,Hips,Spine)",
    default=""
)

def list_armatures(self, context):
    return [(obj.name, obj.name, "") for obj in bpy.data.objects if obj.type == 'ARMATURE']

bpy.types.Scene.nova_armature = bpy.props.EnumProperty(
    name="Armature",
    items=list_armatures
)

# ----------- Operators -----------

class NOVA_OT_CreateDefaultCollections(bpy.types.Operator):
    bl_idname = "nova.create_collections"
    bl_label = "Create Default Collections"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if "To_combine" not in bpy.data.collections:
            col1 = bpy.data.collections.new("To_combine")
            bpy.context.scene.collection.children.link(col1)
        if "Body" not in bpy.data.collections:
            col2 = bpy.data.collections.new("Body")
            bpy.context.scene.collection.children.link(col2)
        self.report({'INFO'}, "Default collections created.")
        return {'FINISHED'}

class NOVA_OT_CombineClothes(bpy.types.Operator):
    bl_idname = "nova.combine_clothes"
    bl_label = "Combine Clothes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        lang = context.scene.nova_language
        col1 = bpy.data.collections.get(context.scene.nova_collection_1)
        col2 = bpy.data.collections.get(context.scene.nova_collection_2)

        if not col1 or not col2:
            self.report({'ERROR'}, "Collections not found.")
            return {'CANCELLED'}

        armature = next((o for o in col2.objects if o.type == 'ARMATURE'), None)
        base_mesh = next((o for o in col2.objects if o.type == 'MESH'), None)

        if not armature or not base_mesh:
            self.report({'ERROR'}, "No valid armature or base mesh found.")
            return {'CANCELLED'}

        for obj in col1.objects:
            if obj.type == 'MESH':
                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
                bpy.ops.object.modifier_add(type='ARMATURE')
                obj.modifiers[-1].object = armature
                base_mesh.select_set(True)
                bpy.ops.object.parent_set(type='ARMATURE_NAME')
                bpy.ops.object.join()
                obj.select_set(False)

        col1.hide_viewport = True
        col1.hide_render = True

        msg = {
            "FR": "Vêtements combinés avec succès.",
            "JP": "服が正常に結合されました。",
            "EN": "Clothes combined successfully."
        }
        self.report({'INFO'}, msg.get(lang, "Done."))
        return {'FINISHED'}

class NOVA_OT_RemoveUnusedBones(bpy.types.Operator):
    bl_idname = "nova.remove_unused_bones"
    bl_label = "Remove Unused Bones"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        lang = context.scene.nova_language
        body_collection_name = context.scene.nova_collection_2
        exclude_input = context.scene.nova_excluded_bones.strip()
        exclude_bones = [name.strip() for name in exclude_input.split(",") if name.strip()]

        collection = bpy.data.collections.get(body_collection_name)
        if not collection:
            self.report({'ERROR'}, "Collection not found.")
            return {'CANCELLED'}

        armature_obj = next((obj for obj in collection.objects if obj.type == "ARMATURE"), None)
        mesh_objects = [obj for obj in collection.objects if obj.type == "MESH"]

        if not armature_obj:
            self.report({'ERROR'}, "No armature found in the collection.")
            return {'CANCELLED'}

        armature = armature_obj.data
        used_bone_names = set()
        for mesh in mesh_objects:
            for group in mesh.vertex_groups:
                used_bone_names.add(group.name)

        bpy.context.view_layer.objects.active = armature_obj
        bpy.ops.object.mode_set(mode='EDIT')

        bones_to_remove = [
            bone.name for bone in armature.edit_bones
            if bone.name not in used_bone_names and bone.name not in exclude_bones
        ]

        for bone_name in bones_to_remove:
            armature.edit_bones.remove(armature.edit_bones[bone_name])

        bpy.ops.object.mode_set(mode='OBJECT')

        msg = {
            "FR": f"{len(bones_to_remove)} os supprimés.",
            "JP": f"{len(bones_to_remove)} 個のボーンが削除されました。",
            "EN": f"{len(bones_to_remove)} bones removed."
        }
        self.report({'INFO'}, msg.get(lang, "Done."))
        return {'FINISHED'}

class NOVA_OT_AutoWeightPaint(bpy.types.Operator):
    bl_idname = "nova.auto_weight_paint"
    bl_label = "Auto Weight Paint (Bêta)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        armature_name = context.scene.nova_armature
        armature = bpy.data.objects.get(armature_name)

        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object.")
            return {'CANCELLED'}

        if not armature:
            self.report({'ERROR'}, "No armature selected.")
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')
        armature.select_set(True)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')

        lang = context.scene.nova_language
        msg = {
            "FR": "Poids automatiquement générés.",
            "JP": "自動的にウェイトペイントが生成されました。",
            "EN": "Auto weights applied."
        }
        self.report({'INFO'}, msg.get(lang, "Done."))
        return {'FINISHED'}

class NOVA_OT_Info(bpy.types.Operator):
    bl_idname = "nova.info"
    bl_label = "Show Info"

    def execute(self, context):
        lang = context.scene.nova_language
        info = {
            "EN": "Combine clothes with the body and clean unused bones.",
            "FR": "Combine les vêtements avec le corps et supprime les os inutilisés.",
            "JP": "服を体に結合し、未使用のボーンを削除します。"
        }
        self.report({'INFO'}, info.get(lang, "Nova Tools info"))
        return {'FINISHED'}

# ----------- UI Panel -----------

class NOVA_PT_Tools(bpy.types.Panel):
    bl_label = "Nova Tools"
    bl_idname = "NOVA_PT_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Nova Tools"

    def draw(self, context):
        layout = self.layout
        scn = context.scene

        layout.prop(scn, "nova_language")
        layout.operator("nova.create_collections")
        layout.separator()
        layout.prop(scn, "nova_collection_1")
        layout.prop(scn, "nova_collection_2")
        layout.operator("nova.combine_clothes")
        layout.separator()
        layout.prop(scn, "nova_armature")
        layout.operator("nova.auto_weight_paint")
        layout.prop(scn, "nova_excluded_bones")
        layout.operator("nova.remove_unused_bones")
        layout.separator()
        layout.operator("nova.info")
        layout.separator()
        layout.label(text="Developed by VrcFoss (Yotva)", icon='INFO')
        layout.label(text="https://yotva.shop", icon='URL')

# ----------- Register -----------

classes = [
    NOVA_OT_CreateDefaultCollections,
    NOVA_OT_CombineClothes,
    NOVA_OT_RemoveUnusedBones,
    NOVA_OT_AutoWeightPaint,
    NOVA_OT_Info,
    NOVA_PT_Tools
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
