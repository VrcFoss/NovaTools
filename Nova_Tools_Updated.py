# =====================================================================
#  Nova Tools — Blender 5.1+ Addon
#  Author  : VrcFoss (Yotva)
#  Version : 5.1
#  GitHub  : https://github.com/VrcFoss/NovaTools
# =====================================================================


bl_info = {
    "name": "Nova Tools",
    "author": "VrcFoss (Yotva)",
    "version": (5, 1),
    "blender": (5, 1, 0),
    "location": "View3D > Sidebar > Nova Tools",
    "description": "All-in-one VRChat/MMD rigging, mesh, material and export toolkit. EN/FR/JP/RU. Blender 5.1+",
    "category": "Rigging",
    "doc_url": "https://github.com/VrcFoss/NovaTools",
    "tracker_url": "https://github.com/VrcFoss/NovaTools/issues",
}

import ssl
import bpy
import bmesh
import os
import re
import json
import math
import time
import shutil
import urllib.request
from mathutils import Vector
from mathutils.kdtree import KDTree
from bpy.app.handlers import persistent
from bpy.props import (
    StringProperty, BoolProperty, IntProperty, FloatProperty,
    EnumProperty, CollectionProperty,
)
from bpy.types import PropertyGroup, Panel, Operator, UIList, AddonPreferences

ADDON_ID   = __name__
ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(ADDON_PATH, ".nova_update_cache.json")
GITHUB_API = "https://api.github.com/repos/VrcFoss/NovaTools/releases/latest"
GITHUB_DL  = "https://github.com/VrcFoss/NovaTools/releases/latest/download/NovaTools.py"

VRCHAT_LIMITS = {
    "triangles_poor":    70000,
    "triangles_medium":  32000,
    "triangles_good":    10000,
    "materials":         4,
    "bones":             400,
    "texture_size":      2048,
    "skinned_meshes":    16,
    "mesh_renderers":    24,
}

# =====================================================================
#  TRANSLATION SYSTEM
# =====================================================================
_TRANSLATIONS: dict = {}

def _build_translations() -> dict:
    return {
        "section.collections":    {"EN": "1. Setup Collections",     "FR": "1. Collections",           "JP": "1. コレクション",         "RU": "1. Коллекции"},
        "section.combine":        {"EN": "2. Combine Clothes",        "FR": "2. Combiner Vêtements",    "JP": "2. 衣服結合",              "RU": "2. Объединить одежду"},
        "section.weights":        {"EN": "3. Weight Tools",           "FR": "3. Poids",                 "JP": "3. ウェイト",              "RU": "3. Веса"},
        "section.bones":          {"EN": "4. Bone Tools",             "FR": "4. Outils Os",             "JP": "4. ボーン",                "RU": "4. Кости"},
        "section.mesh":           {"EN": "5. Mesh Tools",             "FR": "5. Outils Mesh",           "JP": "5. メッシュ",              "RU": "5. Меш"},
        "section.materials":      {"EN": "6. Material Tools",         "FR": "6. Matériaux",             "JP": "6. マテリアル",            "RU": "6. Материалы"},
        "section.shapekeys":      {"EN": "7. Shape Keys",             "FR": "7. Shape Keys",            "JP": "7. シェイプキー",          "RU": "7. Шейп-кеи"},
        "section.scene":          {"EN": "8. Scene Tools",            "FR": "8. Scène",                 "JP": "8. シーン",                "RU": "8. Сцена"},
        "section.export":         {"EN": "9. Export & Validate",      "FR": "9. Export & Validation",   "JP": "9. エクスポート",          "RU": "9. Экспорт"},
        "section.update":         {"EN": "Update",                    "FR": "Mise à jour",              "JP": "アップデート",             "RU": "Обновление"},
        "btn.create_collections": {"EN": "Create Collections",        "FR": "Créer collections",        "JP": "コレクション作成",         "RU": "Создать коллекции"},
        "btn.combine":            {"EN": "Combine Clothes",           "FR": "Combiner",                 "JP": "結合",                    "RU": "Объединить"},
        "btn.transfer_weights":   {"EN": "Transfer Weight Paints",    "FR": "Transférer poids",         "JP": "ウェイト転送",             "RU": "Перенос весов"},
        "btn.auto_weight":        {"EN": "Auto Weight Paint",         "FR": "Poids auto",               "JP": "自動ウェイト",             "RU": "Авто-веса"},
        "btn.normalize_weights":  {"EN": "Normalize Weights",         "FR": "Normaliser poids",         "JP": "ウェイト正規化",           "RU": "Нормализовать веса"},
        "btn.mirror_vgroups":     {"EN": "Mirror Vertex Groups",      "FR": "Miroir groupes",           "JP": "グループミラー",           "RU": "Зеркало групп"},
        "btn.clean_vgroups":      {"EN": "Clean Vertex Groups",       "FR": "Nettoyer groupes",         "JP": "グループ整理",             "RU": "Очистить группы"},
        "btn.remove_unused_bones":{"EN": "Remove Bones",              "FR": "Suppr. os",                "JP": "ボーン削除",               "RU": "Удалить кости"},
        "btn.add_root_bone":      {"EN": "Add Root Bone",             "FR": "Ajouter Root",             "JP": "Rootボーン追加",           "RU": "Добавить Root"},
        "btn.fix_bone_axes":      {"EN": "Fix Bone Roll Axes",        "FR": "Corriger axes",            "JP": "ボーン軸修正",             "RU": "Исправить оси"},
        "btn.bone_colors":        {"EN": "Assign Bone Colors",        "FR": "Couleurs os",              "JP": "ボーン色設定",             "RU": "Цвета костей"},
        "btn.symmetry_check":     {"EN": "Check Symmetry",            "FR": "Vérif. symétrie",          "JP": "対称チェック",             "RU": "Проверить симм."},
        "btn.symmetrize":         {"EN": "Symmetrize Mesh+Groups",    "FR": "Symmétriser",              "JP": "対称化",                  "RU": "Симметризовать"},
        "btn.center_origins":     {"EN": "Center All Origins",        "FR": "Centrer origines",         "JP": "原点を中心へ",             "RU": "Центровать origins"},
        "btn.mesh_validate":      {"EN": "Validate Mesh",             "FR": "Valider mesh",             "JP": "メッシュ検証",             "RU": "Проверить меш"},
        "btn.apply_mods_safe":    {"EN": "Apply Modifiers (Safe)",    "FR": "Appliquer modif. (sûr)",  "JP": "モディファイア適用",       "RU": "Применить модиф."},
        "btn.decimate":           {"EN": "Smart Decimate",            "FR": "Décimation",               "JP": "デシメート",               "RU": "Децимация"},
        "btn.detect_ngons":       {"EN": "Detect Ngons",              "FR": "Détecter Ngons",           "JP": "Ngon検出",                 "RU": "Найти Ngons"},
        "btn.uv_check":           {"EN": "UV Overlap Detect",         "FR": "Détecter UV overlap",      "JP": "UVオーバーラップ",         "RU": "Overlap UV"},
        "btn.auto_smooth":        {"EN": "Auto Smooth Groups",        "FR": "Smooth auto",              "JP": "自動スムース",             "RU": "Авто-смус"},
        "btn.cleanup_mats":       {"EN": "Cleanup Materials",         "FR": "Nettoyer matériaux",       "JP": "マテリアル整理",           "RU": "Очистка матер."},
        "btn.alpha_fix":          {"EN": "Fix Alpha Blend Modes",     "FR": "Corriger alpha",           "JP": "アルファ修正",             "RU": "Исправить альфа"},
        "btn.remove_mat_slots":   {"EN": "Remove Empty Mat Slots",    "FR": "Suppr. slots vides",       "JP": "空スロット削除",           "RU": "Удалить пустые"},
        "btn.add_mmd":            {"EN": "Add MMD Expressions | don't work",       "FR": "Expressions MMD | don't work",          "JP": "MMD表情追加 | don't work",              "RU": "MMD выражения | don't work"},
        "btn.manage_shapekeys":   {"EN": "Shape Key Manager",         "FR": "Gérer shape keys",         "JP": "シェイプキー管理",         "RU": "Менеджер ключей"},
        "btn.scene_stats":        {"EN": "Scene Statistics",          "FR": "Statistiques",             "JP": "統計情報",                 "RU": "Статистика"},
        "btn.scene_clean":        {"EN": "Scene Cleaner",             "FR": "Nettoyer scène",           "JP": "シーン掃除",               "RU": "Очистить сцену"},
        "btn.collection_colors":  {"EN": "Color-Code Collections",    "FR": "Coloriser collections",    "JP": "コレクション色分け",       "RU": "Цвет коллекций"},
        "btn.batch_rename":       {"EN": "Batch Rename",              "FR": "Renommer en masse",        "JP": "一括リネーム",             "RU": "Пакетный rename"},
        "btn.vrchat_validate":    {"EN": "VRChat Validator",          "FR": "Validation VRChat",        "JP": "VRChat検証",               "RU": "Валидация VRChat"},
        "btn.check_update":       {"EN": "Check for Update",          "FR": "Vérifier mises à jour",   "JP": "更新を確認",               "RU": "Проверить обновл."},
        "btn.download_update":    {"EN": "Download & Install",        "FR": "Télécharger & Installer", "JP": "DL & インストール",        "RU": "Скачать & уст."},
        "btn.add_bone":           {"EN": "Add Bone",                  "FR": "Ajouter Os",               "JP": "ボーン追加",               "RU": "Добавить кость"},
        "btn.remove_bone":        {"EN": "Remove Selected Bone",      "FR": "Supprimer os",             "JP": "ボーン削除",               "RU": "Удалить кость"},
        "lbl.armature":           {"EN": "Armature",                  "FR": "Armature",                 "JP": "アーマチュア",             "RU": "Арматура"},
        "lbl.collection_body":    {"EN": "Body Collection",           "FR": "Collection corps",         "JP": "ボディコレクション",       "RU": "Коллекция тела"},
        "lbl.collection_clothes": {"EN": "Clothes Collection",        "FR": "Collection vêtements",     "JP": "服コレクション",           "RU": "Коллекция одежды"},
        "lbl.extra_collections":  {"EN": "Extra Collections",         "FR": "Collections sup.",         "JP": "追加コレクション",         "RU": "Доп. коллекции"},
        "lbl.current_version":    {"EN": "Current",                   "FR": "Actuelle",                 "JP": "現在",                    "RU": "Текущая"},
        "lbl.new_version":        {"EN": "New version available",     "FR": "Nouvelle version dispo",   "JP": "新バージョンあり",         "RU": "Новая версия"},
        "lbl.language":           {"EN": "Language",                  "FR": "Langue",                   "JP": "言語",                    "RU": "Язык"},
        "lbl.prefix":             {"EN": "Prefix",                    "FR": "Préfixe",                  "JP": "プレフィックス",           "RU": "Префикс"},
        "lbl.suffix":             {"EN": "Suffix",                    "FR": "Suffixe",                  "JP": "サフィックス",             "RU": "Суффикс"},
        "lbl.find":               {"EN": "Find",                      "FR": "Chercher",                 "JP": "検索",                    "RU": "Найти"},
        "lbl.replace":            {"EN": "Replace",                   "FR": "Remplacer",                "JP": "置換",                    "RU": "Заменить"},
        "lbl.angle":              {"EN": "Angle",                     "FR": "Angle",                    "JP": "角度",                    "RU": "Угол"},
        "lbl.threshold":          {"EN": "Threshold",                 "FR": "Seuil",                    "JP": "しきい値",                "RU": "Порог"},
        "lbl.ratio":              {"EN": "Ratio",                     "FR": "Ratio",                    "JP": "比率",                    "RU": "Соотношение"},
        "lbl.bone_filters":       {"EN": "Removal Filters",           "FR": "Filtres de suppression",   "JP": "削除フィルター",           "RU": "Фильтры удаления"},
        "lbl.merge_sk":           {"EN": "Merge Identical Shape Keys","FR": "Fusionner Shape Keys",     "JP": "同名SK統合",               "RU": "Объединить Shape Keys"},
        "msg.done":               {"EN": "Done.",                     "FR": "Terminé.",                 "JP": "完了。",                  "RU": "Готово."},
        "msg.cancelled":          {"EN": "Cancelled.",                "FR": "Annulé.",                  "JP": "キャンセル。",            "RU": "Отменено."},
        "msg.no_armature":        {"EN": "Select an armature.",       "FR": "Sélect. une armature.",    "JP": "アーマチュアを選択。",    "RU": "Выберите арматуру."},
        "msg.no_mesh":            {"EN": "Select a mesh.",            "FR": "Sélect. un mesh.",         "JP": "メッシュを選択。",        "RU": "Выберите меш."},
        "msg.no_selection":       {"EN": "Nothing selected.",         "FR": "Rien de sélectionné.",     "JP": "未選択。",                "RU": "Нет выбора."},
        "msg.no_shapekeys":       {"EN": "No shape keys found.",      "FR": "Aucun shape key.",         "JP": "シェイプキーなし。",      "RU": "Нет шейп-кеев."},
        "msg.no_collections":     {"EN": "Collections not found.",    "FR": "Collections introuvables.","JP": "コレクション不明。",      "RU": "Коллекции не найдены."},
        "msg.collections_ok":     {"EN": "Collections created.",      "FR": "Collections créées.",      "JP": "コレクション作成完了。", "RU": "Коллекции созданы."},
        "msg.up_to_date":         {"EN": "You're up to date.",        "FR": "À jour.",                  "JP": "最新版です。",            "RU": "Всё актуально."},
        "msg.update_available":   {"EN": "Update available!",         "FR": "Mise à jour dispo !",      "JP": "アップデートあり！",      "RU": "Обновление доступно!"},
        "msg.update_failed":      {"EN": "Could not check updates.",  "FR": "Vérif. impossible.",       "JP": "確認失敗。",              "RU": "Не удалось проверить."},
        "msg.bones_removed":      {"EN": "bones removed.",            "FR": "os supprimés.",            "JP": "ボーン削除。",            "RU": "костей удалено."},
        "msg.weights_done":       {"EN": "Weights applied.",          "FR": "Poids appliqués.",         "JP": "ウェイト適用済。",        "RU": "Веса применены."},
        "msg.select_two":         {"EN": "Select source then target.","FR": "Src puis cible.",          "JP": "ソース、次にターゲット。","RU": "Источник затем цель."},
        "msg.missing_elements":   {"EN": "Missing required elements.","FR": "Éléments manquants.",      "JP": "必要な要素なし。",        "RU": "Не хватает элементов."},
        "msg.no_vertex_groups":   {"EN": "No vertex groups found.",   "FR": "Aucun groupe vertex.",     "JP": "頂点グループなし。",      "RU": "Нет групп вершин."},
        "msg.root_exists":        {"EN": "Root bone already exists.", "FR": "Root déjà présent.",       "JP": "Rootボーン既存。",        "RU": "Root уже существует."},
        "msg.root_added":         {"EN": "Root bone added.",          "FR": "Root ajouté.",             "JP": "Rootボーン追加完了。",    "RU": "Root добавлен."},
        "msg.download_ok":        {"EN": "Update installed. Restart Blender.","FR": "Màj installée. Redémarrez.","JP": "更新完了。再起動してください。","RU": "Обновление установлено. Перезапустите."},
        "msg.download_fail":      {"EN": "Download failed.",          "FR": "Téléchargement échoué.",   "JP": "DL失敗。",               "RU": "Загрузка не удалась."},
    }

def t(key: str) -> str:
    global _TRANSLATIONS
    if not _TRANSLATIONS:
        _TRANSLATIONS = _build_translations()
    lang = "EN"
    try:
        lang = bpy.context.scene.nova_language
    except Exception:
        pass
    entry = _TRANSLATIONS.get(key)
    if entry is None:
        return key
    return entry.get(lang, entry.get("EN", key))

# =====================================================================
#  VERSION / UPDATE HELPERS
# =====================================================================
def _parse_version(s: str) -> tuple:
    try:
        clean = re.sub(r"[^\d.]", "", s)
        return tuple(int(x) for x in clean.split(".") if x)
    except Exception:
        return (0,)

def _fetch_latest_version() -> str | None:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # Méthode 1 : API GitHub
    try:
        req = urllib.request.Request(
            GITHUB_API,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Mozilla/5.0 NovaTools-Blender-Addon",
            },
        )
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            tag = data.get("tag_name", "").strip().lstrip("v")
            if tag:
                print(f"[NovaTools] Version trouvée via API: {tag}")
                return tag
    except Exception as e:
        print(f"[NovaTools] API method failed: {e}")

    # Méthode 2 : redirect URL
    try:
        req2 = urllib.request.Request(
            "https://github.com/VrcFoss/NovaTools/releases/latest",
            headers={"User-Agent": "Mozilla/5.0 NovaTools-Blender-Addon"},
        )
        with urllib.request.urlopen(req2, timeout=10, context=ctx) as resp2:
            final_url = resp2.geturl()
            tag = final_url.rstrip("/").split("/")[-1].lstrip("v")
            if tag and tag != "latest":
                print(f"[NovaTools] Version trouvée via redirect: {tag}")
                return tag
    except Exception as e:
        print(f"[NovaTools] Redirect method failed: {e}")

    return None

def _read_cache() -> str | None:
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("latest_version")
    except Exception:
        pass
    return None

def _write_cache(version: str) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"latest_version": version, "checked": time.time()}, f)
    except Exception:
        pass

@persistent
def _auto_check_update(dummy=None):
    try:
        cached = _read_cache()
        latest = cached or _fetch_latest_version()
        if latest and not cached:
            _write_cache(latest)
        current = _parse_version(".".join(str(x) for x in bl_info["version"]))
        bpy.types.Scene.nova_update_available = latest and _parse_version(latest) > current
        bpy.types.Scene.nova_update_version   = latest or ""
    except Exception:
        pass

# =====================================================================
#  PROPERTY GROUPS
# =====================================================================
class NOVA_ExcludeBoneItem(PropertyGroup):
    name: StringProperty(name="Bone Name")

class NOVA_ShapeKeyItem(PropertyGroup):
    name:    StringProperty(name="Shape Key Name")
    enabled: BoolProperty(name="Enabled", default=True)

# =====================================================================
#  UI LIST CLASSES
# =====================================================================
class NOVA_UL_ExcludeBoneList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.label(text=item.name, icon="BONE_DATA")

class NOVA_UL_ShapeKeyList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        row = layout.row(align=True)
        row.prop(item, "enabled", text="")
        row.label(text=item.name, icon="SHAPEKEY_DATA")

# =====================================================================
#  REGISTER / UNREGISTER PROPERTIES
# =====================================================================
def register_properties():
    bpy.types.Scene.nova_excluded_bones_list  = CollectionProperty(type=NOVA_ExcludeBoneItem)
    bpy.types.Scene.nova_excluded_bones_index = IntProperty(default=0)
    bpy.types.Scene.nova_shapekey_list        = CollectionProperty(type=NOVA_ShapeKeyItem)
    bpy.types.Scene.nova_shapekey_index       = IntProperty(default=0)

    def _get_lang(self):  return self.get("_nova_lang", 0)
    def _set_lang(self, v):
        self["_nova_lang"] = v
        for area in (bpy.context.screen.areas if bpy.context.screen else []):
            area.tag_redraw()

    bpy.types.Scene.nova_language = EnumProperty(
        name="Language",
        items=[("EN","English",""),("FR","Français",""),("JP","日本語",""),("RU","Русский","")],
        get=_get_lang, set=_set_lang,
    )

    bpy.types.Scene.nova_collection_body    = StringProperty(name="Body Collection",    default="Body")
    bpy.types.Scene.nova_collection_clothes = StringProperty(name="Clothes Collection", default="To_combine")

    # Extra collection toggles for section 1
    bpy.types.Scene.nova_col_armature = BoolProperty(name="Armature", default=True)
    bpy.types.Scene.nova_col_props    = BoolProperty(name="Props",    default=True)
    bpy.types.Scene.nova_col_fx       = BoolProperty(name="FX",       default=False)

    def _list_armatures(self, context):
        items = [(o.name, o.name, "") for o in bpy.data.objects if o.type == "ARMATURE"]
        return items if items else [("NONE", "No Armature", "")]

    bpy.types.Scene.nova_armature = EnumProperty(name="Armature", items=_list_armatures)

    # Combine Clothes options
    bpy.types.Scene.nova_combine_merge_shapekeys = BoolProperty(
        name="Merge Identical Shape Keys",
        description="Merge shape keys that share the same name between body and clothes meshes",
        default=True,
    )

    bpy.types.Scene.nova_temp_bone_name = StringProperty(name="Bone Name", default="")

    # Bone removal filters
    bpy.types.Scene.nova_remove_unweighted_bones = BoolProperty(
        name="Unweighted Bones",
        description="Remove bones that have no vertex group influence and no children",
        default=True,
    )
    bpy.types.Scene.nova_remove_end_bones = BoolProperty(
        name='Bones Containing "_end"',
        description='Remove bones whose name contains "_end" (case-insensitive)',
        default=False,
    )

    bpy.types.Scene.nova_rename_prefix  = StringProperty(name="Prefix",  default="")
    bpy.types.Scene.nova_rename_suffix  = StringProperty(name="Suffix",  default="")
    bpy.types.Scene.nova_rename_find    = StringProperty(name="Find",    default="")
    bpy.types.Scene.nova_rename_replace = StringProperty(name="Replace", default="")
    bpy.types.Scene.nova_rename_target  = EnumProperty(
        name="Target", default="OBJECTS",
        items=[("OBJECTS","Objects",""),("BONES","Bones",""),("MATERIALS","Materials",""),("VERTEX_GROUPS","Vertex Groups","")],
    )

    bpy.types.Scene.nova_decimate_ratio = FloatProperty(name="Ratio", default=0.5, min=0.01, max=1.0, step=1)

    bpy.types.Scene.nova_smooth_angle = FloatProperty(
        name="Angle", default=math.radians(30), min=0, max=math.pi,
        subtype="ANGLE",
    )

    bpy.types.Scene.nova_vgroup_threshold = FloatProperty(name="Min Weight", default=0.01, min=0.0, max=0.5, step=1)

    bpy.types.Scene.nova_update_available = BoolProperty(default=False)
    bpy.types.Scene.nova_update_version   = StringProperty(default="")

    bpy.types.Scene.nova_stats_cache        = StringProperty(default="")
    bpy.types.Scene.nova_vrchat_cache       = StringProperty(default="")
    bpy.types.Scene.nova_tri_status_cache   = StringProperty(default="")

    for section in ("collections","combine","weights","bones","mesh","materials","shapekeys","scene","export"):
        setattr(bpy.types.Scene, f"nova_show_{section}", BoolProperty(name=section.title(), default=False))

def unregister_properties():
    props = [
        "nova_excluded_bones_list","nova_excluded_bones_index",
        "nova_shapekey_list","nova_shapekey_index",
        "nova_language","nova_collection_body","nova_collection_clothes",
        "nova_col_armature","nova_col_props","nova_col_fx",
        "nova_armature","nova_temp_bone_name",
        "nova_combine_merge_shapekeys",
        "nova_remove_unweighted_bones","nova_remove_end_bones",
        "nova_rename_prefix","nova_rename_suffix","nova_rename_find","nova_rename_replace","nova_rename_target",
        "nova_decimate_ratio","nova_smooth_angle","nova_vgroup_threshold",
        "nova_update_available","nova_update_version",
        "nova_stats_cache","nova_vrchat_cache","nova_tri_status_cache",
    ]
    for section in ("collections","combine","weights","bones","mesh","materials","shapekeys","scene","export"):
        props.append(f"nova_show_{section}")
    for p in props:
        if hasattr(bpy.types.Scene, p):
            try:
                delattr(bpy.types.Scene, p)
            except Exception:
                pass

# =====================================================================
#  HELPERS
# =====================================================================
def _get_armature(context) -> bpy.types.Object | None:
    name = context.scene.nova_armature
    obj  = bpy.data.objects.get(name)
    if obj and obj.type == "ARMATURE":
        return obj
    if context.active_object and context.active_object.type == "ARMATURE":
        return context.active_object
    return None

def _ensure_object_mode(context):
    if context.active_object and context.active_object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

def _select_only(obj, context):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    context.view_layer.objects.active = obj

def _meshes_in_collection(col_name: str):
    col = bpy.data.collections.get(col_name)
    if not col:
        return []
    return [o for o in col.all_objects if o.type == "MESH"]

def _get_all_meshes(context):
    return [o for o in context.scene.objects if o.type == "MESH"]

def _report(op, level: str, msg: str):
    op.report({level}, msg)

# =====================================================================
#  SECTION 1 — COLLECTION SETUP
# =====================================================================
class NOVA_OT_CreateCollections(Operator):
    bl_idname  = "nova.create_collections"
    bl_label   = "Create Collections"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        to_create = [
            scene.nova_collection_body,
            scene.nova_collection_clothes,
        ]
        if scene.nova_col_armature:
            to_create.append("Armature")
        if scene.nova_col_props:
            to_create.append("Props")
        if scene.nova_col_fx:
            to_create.append("FX")

        created = []
        for name in to_create:
            if not name:
                continue
            if name not in bpy.data.collections:
                col = bpy.data.collections.new(name)
                context.scene.collection.children.link(col)
                created.append(name)

        msg = t("msg.collections_ok") + (f" ({', '.join(created)})" if created else " (all already exist)")
        _report(self, "INFO", msg)
        return {"FINISHED"}

# =====================================================================
#  SECTION 2 — COMBINE CLOTHES
# =====================================================================
_DUP_PATTERN = re.compile(r"^(.+)\.\d{3,}$")

class NOVA_OT_CombineClothes(Operator):
    bl_idname  = "nova.combine_clothes"
    bl_label   = "Combine Clothes"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Join all meshes from the Clothes collection onto the Body mesh, "
        "merge the clothes armature into the body armature, "
        "and handle shape keys according to the merge option"
    )

    def execute(self, context):
        scene = context.scene
        arm   = _get_armature(context)
        if arm is None:
            _report(self, "ERROR", t("msg.no_armature"))
            return {"CANCELLED"}

        body_meshes    = _meshes_in_collection(scene.nova_collection_body)
        clothes_meshes = _meshes_in_collection(scene.nova_collection_clothes)

        if not body_meshes:
            _report(self, "ERROR", t("msg.no_mesh"))
            return {"CANCELLED"}
        if not clothes_meshes:
            _report(self, "WARNING", "No meshes found in the clothes collection.")
            return {"CANCELLED"}

        _ensure_object_mode(context)
        body = body_meshes[0]

        # Identify the clothes armature before modifying anything
        clothes_arm_name = self._find_clothes_armature_name(clothes_meshes, arm)

        # Reassign armature modifiers on clothes meshes to point to the body armature
        for obj in clothes_meshes:
            existing_arm_mods = [m for m in obj.modifiers if m.type == "ARMATURE"]
            if not any(m.object == arm for m in existing_arm_mods):
                for m in existing_arm_mods:
                    obj.modifiers.remove(m)
                mod        = obj.modifiers.new("Armature", "ARMATURE")
                mod.object = arm

        # Handle shape keys: if merge is disabled, rename conflicts before joining
        if not scene.nova_combine_merge_shapekeys:
                    body_sk_names_lower: dict[str, str] = {}
                    if body.data.shape_keys:
                        for kb in body.data.shape_keys.key_blocks:
                            body_sk_names_lower[kb.name.lower()] = kb.name
                    for obj in clothes_meshes:
                        if obj.data.shape_keys:
                            for kb in obj.data.shape_keys.key_blocks:
                                if kb.name != "Basis" and kb.name.lower() in body_sk_names_lower:
                                    kb.name = f"{obj.name}_{kb.name}"
        else:
            # Renommer les shape keys des vêtements pour qu'ils correspondent
            # exactement à la casse du body avant le join
            if body.data.shape_keys:
                body_sk_lower: dict[str, str] = {
                    kb.name.lower(): kb.name
                    for kb in body.data.shape_keys.key_blocks
                }
                for obj in clothes_meshes:
                    if obj.data.shape_keys:
                        for kb in obj.data.shape_keys.key_blocks:
                            match = body_sk_lower.get(kb.name.lower())
                            if match and kb.name != match:
                                kb.name = match

        # Join clothes meshes into body
        bpy.ops.object.select_all(action="DESELECT")
        for obj in clothes_meshes:
            obj.select_set(True)
        body.select_set(True)
        context.view_layer.objects.active = body
        bpy.ops.object.join()

        # Merge clothes armature into body armature if a separate one was found
        if clothes_arm_name:
            clothes_arm = bpy.data.objects.get(clothes_arm_name)
            if clothes_arm and clothes_arm != arm:
                self._merge_armatures(context, arm, clothes_arm)

        _report(self, "INFO", t("msg.done"))
        return {"FINISHED"}

    @staticmethod
    def _find_clothes_armature_name(clothes_meshes, body_arm) -> str | None:
        for obj in clothes_meshes:
            for mod in obj.modifiers:
                if mod.type == "ARMATURE" and mod.object and mod.object != body_arm:
                    return mod.object.name
        for obj in clothes_meshes:
            if obj.parent and obj.parent.type == "ARMATURE" and obj.parent != body_arm:
                return obj.parent.name
        return None

    @staticmethod
    def _merge_armatures(context, body_arm, clothes_arm):
        body_bone_names = {bone.name for bone in body_arm.data.bones}

        # Sauvegarder les relations parent des bones supplémentaires (non-dupliqués)
        # avant le join, depuis l'armature des vêtements
        extra_bone_parents = {}
        for bone in clothes_arm.data.bones:
            m = _DUP_PATTERN.match(bone.name)
            base_name = m.group(1) if m else bone.name
            if base_name not in body_bone_names:
                if bone.parent:
                    parent_name = bone.parent.name
                    m2 = _DUP_PATTERN.match(parent_name)
                    extra_bone_parents[bone.name] = m2.group(1) if m2 else parent_name
                    extra_bone_parents[bone.name + "__use_connect"] = bone.use_connect

        bpy.ops.object.select_all(action="DESELECT")
        clothes_arm.select_set(True)
        body_arm.select_set(True)
        context.view_layer.objects.active = body_arm
        bpy.ops.object.join()

        _select_only(body_arm, context)
        bpy.ops.object.mode_set(mode="EDIT")
        try:
            ebs = body_arm.data.edit_bones
            bones_to_remove = []
            for bone in ebs:
                m = _DUP_PATTERN.match(bone.name)
                if m and m.group(1) in body_bone_names:
                    bones_to_remove.append(bone)
            for bone in bones_to_remove:
                ebs.remove(bone)

            # Restaurer les parents des bones supplémentaires
            for bone_name, parent_name in extra_bone_parents.items():
                if bone_name.endswith("__use_connect"):
                    continue
                eb = ebs.get(bone_name)
                parent_eb = ebs.get(parent_name)
                if eb and parent_eb:
                    use_connect = extra_bone_parents.get(bone_name + "__use_connect", False)
                    eb.parent = parent_eb
                    eb.use_connect = use_connect
        finally:
            bpy.ops.object.mode_set(mode="OBJECT")

# =====================================================================
#  SECTION 3 — WEIGHT TOOLS
# =====================================================================
class NOVA_OT_TransferWeights(Operator):
    bl_idname  = "nova.transfer_weights"
    bl_label   = "Transfer Weight Paints"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Transfer vertex weights from active object to all other selected meshes"

    def execute(self, context):
        source = context.active_object
        if source is None or source.type != "MESH":
            _report(self, "ERROR", t("msg.no_mesh"))
            return {"CANCELLED"}
        targets = [o for o in context.selected_objects if o != source and o.type == "MESH"]
        if not targets:
            _report(self, "ERROR", t("msg.select_two"))
            return {"CANCELLED"}

        _ensure_object_mode(context)
        for tgt in targets:
            _select_only(tgt, context)
            source.select_set(True)
            context.view_layer.objects.active = tgt
            bpy.ops.object.data_transfer(
                use_create=True,
                data_type="VGROUP_WEIGHTS",
                use_object_transform=True,
                layers_select_src="ALL",
                layers_select_dst="NAME",
                mix_mode="REPLACE",
            )
        _report(self, "INFO", t("msg.weights_done"))
        return {"FINISHED"}

class NOVA_OT_AutoWeightPaint(Operator):
    bl_idname  = "nova.auto_weight_paint"
    bl_label   = "Auto Weight Paint"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Apply automatic weight painting from armature to selected meshes"

    def execute(self, context):
        arm = _get_armature(context)
        if arm is None:
            _report(self, "ERROR", t("msg.no_armature"))
            return {"CANCELLED"}
        meshes = [o for o in context.selected_objects if o.type == "MESH"]
        if not meshes:
            _report(self, "ERROR", t("msg.no_mesh"))
            return {"CANCELLED"}
        _ensure_object_mode(context)
        for mesh in meshes:
            _select_only(mesh, context)
            arm.select_set(True)
            context.view_layer.objects.active = arm
            bpy.ops.object.parent_set(type="ARMATURE_AUTO")
        _report(self, "INFO", t("msg.weights_done"))
        return {"FINISHED"}

class NOVA_OT_NormalizeWeights(Operator):
    bl_idname  = "nova.normalize_weights"
    bl_label   = "Normalize Weights"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Normalize all vertex weights so they sum to 1.0 per vertex"

    def execute(self, context):
        meshes = [o for o in context.selected_objects if o.type == "MESH"]
        if not meshes:
            _report(self, "ERROR", t("msg.no_mesh"))
            return {"CANCELLED"}
        _ensure_object_mode(context)
        for obj in meshes:
            _select_only(obj, context)
            bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
            bpy.ops.object.vertex_group_normalize_all(lock_active=False)
            bpy.ops.object.mode_set(mode="OBJECT")
        _report(self, "INFO", t("msg.done"))
        return {"FINISHED"}

class NOVA_OT_MirrorVertexGroups(Operator):
    bl_idname  = "nova.mirror_vertex_groups"
    bl_label   = "Mirror Vertex Groups"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Mirror vertex groups from left to right side (requires .L/.R naming)"

    def execute(self, context):
        meshes = [o for o in context.selected_objects if o.type == "MESH"]
        if not meshes:
            _report(self, "ERROR", t("msg.no_mesh"))
            return {"CANCELLED"}
        _ensure_object_mode(context)
        count = 0
        for obj in meshes:
            _select_only(obj, context)
            before = len(obj.vertex_groups)
            bpy.ops.object.vertex_group_mirror(mirror_weights=True, flip_group_names=True, all_groups=True)
            count += len(obj.vertex_groups) - before
        _report(self, "INFO", f"{count} groups mirrored. " + t("msg.done"))
        return {"FINISHED"}

class NOVA_OT_CleanVertexGroups(Operator):
    bl_idname  = "nova.clean_vertex_groups"
    bl_label   = "Clean Vertex Groups"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Remove vertex groups with no or very low influence"

    def execute(self, context):
        threshold = context.scene.nova_vgroup_threshold
        meshes    = [o for o in context.selected_objects if o.type == "MESH"]
        if not meshes:
            _report(self, "ERROR", t("msg.no_mesh"))
            return {"CANCELLED"}
        _ensure_object_mode(context)
        total_removed = 0
        for obj in meshes:
            to_remove = []
            for vg in obj.vertex_groups:
                has_influence = False
                for v in obj.data.vertices:
                    try:
                        w = vg.weight(v.index)
                        if w > threshold:
                            has_influence = True
                            break
                    except RuntimeError:
                        pass
                if not has_influence:
                    to_remove.append(vg)
            for vg in to_remove:
                obj.vertex_groups.remove(vg)
                total_removed += 1
        _report(self, "INFO", f"{total_removed} " + t("msg.bones_removed"))
        return {"FINISHED"}

# =====================================================================
#  SECTION 4 — BONE TOOLS
# =====================================================================
class NOVA_OT_RemoveUnusedBones(Operator):
    bl_idname  = "nova.remove_unused_bones"
    bl_label   = "Remove Bones"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Remove bones based on the active removal filters"

    def execute(self, context):
        arm = _get_armature(context)
        if arm is None:
            _report(self, "ERROR", t("msg.no_armature"))
            return {"CANCELLED"}

        scene              = context.scene
        remove_unweighted  = scene.nova_remove_unweighted_bones
        remove_end         = scene.nova_remove_end_bones

        if not remove_unweighted and not remove_end:
            _report(self, "WARNING", "No removal filter is active. Enable at least one filter.")
            return {"CANCELLED"}

        _ensure_object_mode(context)

        # Collect bone names that have vertex group influence
        weighted_bones: set[str] = set()
        for obj in bpy.data.objects:
            if obj.type == "MESH" and obj.parent == arm:
                for vg in obj.vertex_groups:
                    weighted_bones.add(vg.name)

        excluded = {item.name for item in scene.nova_excluded_bones_list}

        _select_only(arm, context)
        bpy.ops.object.mode_set(mode="EDIT")
        removed = 0
        try:
            bones_to_remove = []
            for bone in arm.data.edit_bones:
                if bone.name in excluded:
                    continue
                should_remove = False
                if remove_unweighted and bone.name not in weighted_bones and not bone.children:
                    should_remove = True
                if remove_end and "_end" in bone.name.lower():
                    should_remove = True
                if should_remove:
                    bones_to_remove.append(bone)
            for bone in bones_to_remove:
                arm.data.edit_bones.remove(bone)
                removed += 1
        finally:
            bpy.ops.object.mode_set(mode="OBJECT")

        _report(self, "INFO", f"{removed} " + t("msg.bones_removed"))
        return {"FINISHED"}

class NOVA_OT_AddRootBone(Operator):
    bl_idname  = "nova.add_root_bone"
    bl_label   = "Add Root Bone"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Add a Root bone at the origin and parent all top-level bones to it"

    def execute(self, context):
        arm = _get_armature(context)
        if arm is None:
            _report(self, "ERROR", t("msg.no_armature"))
            return {"CANCELLED"}
        _select_only(arm, context)
        bpy.ops.object.mode_set(mode="EDIT")
        try:
            ebs = arm.data.edit_bones
            if "Root" in ebs:
                _report(self, "WARNING", t("msg.root_exists"))
                return {"CANCELLED"}
            root      = ebs.new("Root")
            root.head = Vector((0, 0, 0))
            root.tail = Vector((0, 0, 0.1))
            for bone in ebs:
                if bone != root and bone.parent is None:
                    bone.parent = root
        finally:
            bpy.ops.object.mode_set(mode="OBJECT")
        _report(self, "INFO", t("msg.root_added"))
        return {"FINISHED"}

class NOVA_OT_FixBoneAxes(Operator):
    bl_idname  = "nova.fix_bone_axes"
    bl_label   = "Fix Bone Roll Axes"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Recalculate bone roll axes so they point upward consistently"

    def execute(self, context):
        arm = _get_armature(context)
        if arm is None:
            _report(self, "ERROR", t("msg.no_armature"))
            return {"CANCELLED"}
        _select_only(arm, context)
        bpy.ops.object.mode_set(mode="EDIT")
        try:
            bpy.ops.armature.select_all(action="SELECT")
            bpy.ops.armature.calculate_roll(type="GLOBAL_POS_Z")
        finally:
            bpy.ops.object.mode_set(mode="OBJECT")
        _report(self, "INFO", t("msg.done"))
        return {"FINISHED"}

class NOVA_OT_AssignBoneColors(Operator):
    bl_idname  = "nova.assign_bone_colors"
    bl_label   = "Assign Bone Colors"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Color-code bones by group (spine=red, arms=blue, legs=green, face=yellow, fingers=orange)"

    COLOR_MAP = {
        "spine": 1,  "chest": 1,  "hips": 1,   "pelvis": 1,  "root": 1,
        "arm":   4,  "hand":  4,  "shoulder": 4,
        "leg":   3,  "foot":  3,  "knee": 3,    "thigh": 3,
        "head":  6,  "neck":  6,  "face": 6,    "jaw": 6,     "eye": 6,
        "finger":9,  "thumb": 9,  "index": 9,   "middle": 9,  "ring": 9, "pinky": 9,
        "hair":  2,  "tail":  2,  "ear": 2,
    }

    def execute(self, context):
        arm = _get_armature(context)
        if arm is None:
            _report(self, "ERROR", t("msg.no_armature"))
            return {"CANCELLED"}
        _select_only(arm, context)
        bpy.ops.object.mode_set(mode="POSE")
        try:
            for pbone in arm.pose.bones:
                low   = pbone.name.lower()
                theme = 0
                for kw, idx in self.COLOR_MAP.items():
                    if kw in low:
                        theme = idx
                        break
                if theme:
                    pbone.color.palette = f"THEME{theme:02d}"
        finally:
            bpy.ops.object.mode_set(mode="OBJECT")
        _report(self, "INFO", t("msg.done"))
        return {"FINISHED"}

class NOVA_OT_AddExcludedBone(Operator):
    bl_idname = "nova.add_excluded_bone"
    bl_label  = "Add Bone"

    def execute(self, context):
        name = context.scene.nova_temp_bone_name.strip()
        if not name:
            _report(self, "WARNING", "Enter a bone name first.")
            return {"CANCELLED"}
        item      = context.scene.nova_excluded_bones_list.add()
        item.name = name
        context.scene.nova_temp_bone_name = ""
        return {"FINISHED"}

class NOVA_OT_RemoveExcludedBone(Operator):
    bl_idname = "nova.remove_excluded_bone"
    bl_label  = "Remove Bone"

    def execute(self, context):
        lst = context.scene.nova_excluded_bones_list
        idx = context.scene.nova_excluded_bones_index
        if 0 <= idx < len(lst):
            lst.remove(idx)
            context.scene.nova_excluded_bones_index = max(0, idx - 1)
        return {"FINISHED"}

# =====================================================================
#  SECTION 5 — MESH TOOLS
# =====================================================================
class NOVA_OT_CheckSymmetry(Operator):
    bl_idname  = "nova.check_symmetry"
    bl_label   = "Check Symmetry"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Detect vertices that are not symmetric on the X axis"

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            _report(self, "ERROR", t("msg.no_mesh"))
            return {"CANCELLED"}
        _ensure_object_mode(context)
        mesh      = obj.data
        threshold = 0.001
        bm        = bmesh.new()
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()

        kd = KDTree(len(bm.verts))
        for v in bm.verts:
            kd.insert(v.co, v.index)
        kd.balance()

        asymmetric = []
        for v in bm.verts:
            mirror        = Vector((-v.co.x, v.co.y, v.co.z))
            _co, _idx, dist = kd.find(mirror)
            if dist > threshold:
                asymmetric.append(v.index)

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")
        for vi in asymmetric:
            mesh.vertices[vi].select = True
        bpy.ops.object.mode_set(mode="EDIT")

        bm.free()
        _report(self, "INFO", f"{len(asymmetric)} asymmetric vertices found.")
        return {"FINISHED"}

class NOVA_OT_SymmetrizeMesh(Operator):
    bl_idname  = "nova.symmetrize_mesh"
    bl_label   = "Symmetrize Mesh + Groups"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Symmetrize mesh geometry and vertex groups from +X to -X"

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            _report(self, "ERROR", t("msg.no_mesh"))
            return {"CANCELLED"}
        _ensure_object_mode(context)
        _select_only(obj, context)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.symmetrize(direction="NEGATIVE_X")
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.vertex_group_mirror(mirror_weights=True, flip_group_names=True, all_groups=True)
        _report(self, "INFO", t("msg.done"))
        return {"FINISHED"}

class NOVA_OT_CenterOrigins(Operator):
    bl_idname  = "nova.center_origins"
    bl_label   = "Center All Origins"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Set origin to geometry center for all selected objects"

    def execute(self, context):
        objs = [o for o in context.selected_objects if o.type in {"MESH","CURVE","EMPTY"}]
        if not objs:
            _report(self, "ERROR", t("msg.no_selection"))
            return {"CANCELLED"}
        _ensure_object_mode(context)
        for obj in objs:
            _select_only(obj, context)
            bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
        _report(self, "INFO", t("msg.done"))
        return {"FINISHED"}

class NOVA_OT_ValidateMesh(Operator):
    bl_idname  = "nova.validate_mesh"
    bl_label   = "Validate Mesh"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Check for non-manifold edges, flipped normals, loose vertices and degenerate faces"

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            _report(self, "ERROR", t("msg.no_mesh"))
            return {"CANCELLED"}
        _ensure_object_mode(context)
        issues = obj.data.validate(verbose=True)
        if issues:
            _report(self, "WARNING", f"Mesh had {issues} issue(s) — auto-fixed.")
        else:
            _report(self, "INFO", "Mesh is clean. " + t("msg.done"))
        return {"FINISHED"}

class NOVA_OT_ApplyModifiersSafe(Operator):
    bl_idname  = "nova.apply_modifiers_safe"
    bl_label   = "Apply Modifiers (Safe)"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Apply all modifiers while preserving shape keys via bmesh copy workaround"

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            _report(self, "ERROR", t("msg.no_mesh"))
            return {"CANCELLED"}
        _ensure_object_mode(context)

        has_shape_keys = obj.data.shape_keys and len(obj.data.shape_keys.key_blocks) > 1
        shape_data = {}
        if has_shape_keys:
            for kb in obj.data.shape_keys.key_blocks:
                shape_data[kb.name] = [v.co.copy() for v in kb.data]

        for mod in list(obj.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception as e:
                _report(self, "WARNING", f"Could not apply '{mod.name}': {e}")

        if has_shape_keys and shape_data:
            if obj.data.shape_keys is None:
                obj.shape_key_add(name="Basis", from_mix=False)
            for name, coords in shape_data.items():
                if name == "Basis":
                    continue
                if name not in obj.data.shape_keys.key_blocks:
                    obj.shape_key_add(name=name, from_mix=False)
                kb = obj.data.shape_keys.key_blocks.get(name)
                if kb:
                    for i, co in enumerate(coords):
                        if i < len(kb.data):
                            kb.data[i].co = co

        _report(self, "INFO", t("msg.done"))
        return {"FINISHED"}

class NOVA_OT_SmartDecimate(Operator):
    bl_idname  = "nova.smart_decimate"
    bl_label   = "Smart Decimate"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Apply decimate modifier to selected meshes with chosen ratio"

    def execute(self, context):
        meshes = [o for o in context.selected_objects if o.type == "MESH"]
        if not meshes:
            _report(self, "ERROR", t("msg.no_mesh"))
            return {"CANCELLED"}
        ratio = context.scene.nova_decimate_ratio
        _ensure_object_mode(context)
        for obj in meshes:
            existing = [m for m in obj.modifiers if m.type == "DECIMATE"]
            mod      = existing[0] if existing else obj.modifiers.new("NovaDecimate", "DECIMATE")
            mod.ratio = ratio
            try:
                _select_only(obj, context)
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception as e:
                _report(self, "WARNING", f"Decimate failed on '{obj.name}': {e}")
        _report(self, "INFO", t("msg.done"))
        return {"FINISHED"}

class NOVA_OT_DetectNgons(Operator):
    bl_idname  = "nova.detect_ngons"
    bl_label   = "Detect Ngons"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Select all faces with more than 4 vertices (Ngons)"

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            _report(self, "ERROR", t("msg.no_mesh"))
            return {"CANCELLED"}
        _ensure_object_mode(context)
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        ngon_count = sum(1 for f in bm.faces if len(f.verts) > 4)
        bm.free()
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.mesh.select_face_by_sides(number=4, type="GREATER")
        _report(self, "INFO", f"{ngon_count} Ngons found and selected.")
        return {"FINISHED"}

class NOVA_OT_UVOverlapDetect(Operator):
    bl_idname  = "nova.uv_overlap_detect"
    bl_label   = "UV Overlap Detect"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Select UV faces that overlap other UV islands"

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            _report(self, "ERROR", t("msg.no_mesh"))
            return {"CANCELLED"}
        _ensure_object_mode(context)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        try:
            bpy.ops.uv.select_overlap()
            _report(self, "INFO", "Overlapping UVs selected.")
        except Exception as e:
            _report(self, "WARNING", f"UV overlap check failed: {e}")
        return {"FINISHED"}

class NOVA_OT_AutoSmoothGroups(Operator):
    bl_idname  = "nova.auto_smooth_groups"
    bl_label   = "Auto Smooth Groups"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Set smooth shading with auto-smooth based on angle threshold"

    def execute(self, context):
        meshes = [o for o in context.selected_objects if o.type == "MESH"]
        if not meshes:
            _report(self, "ERROR", t("msg.no_mesh"))
            return {"CANCELLED"}
        angle = context.scene.nova_smooth_angle
        _ensure_object_mode(context)
        for obj in meshes:
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            context.view_layer.objects.active = obj
            try:
                bpy.ops.object.shade_smooth_by_angle(angle=angle)
            except Exception:
                bpy.ops.object.shade_smooth()
        _report(self, "INFO", t("msg.done"))
        return {"FINISHED"}

class NOVA_OT_OptimizeMeshes(Operator):
    bl_idname  = "nova.optimize_meshes"
    bl_label   = "Optimize (Remove Doubles)"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Merge overlapping vertices on selected meshes"

    def execute(self, context):
        meshes = [o for o in context.selected_objects if o.type == "MESH"]
        if not meshes:
            _report(self, "ERROR", t("msg.no_mesh"))
            return {"CANCELLED"}
        _ensure_object_mode(context)
        total = 0
        for obj in meshes:
            before = len(obj.data.vertices)
            _select_only(obj, context)
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.remove_doubles(threshold=0.0001)
            bpy.ops.object.mode_set(mode="OBJECT")
            total += before - len(obj.data.vertices)
        _report(self, "INFO", f"{total} vertices merged. " + t("msg.done"))
        return {"FINISHED"}

# =====================================================================
#  SECTION 6 — MATERIAL TOOLS
# =====================================================================
class NOVA_OT_CleanupMaterials(Operator):
    bl_idname  = "nova.cleanup_materials"
    bl_label   = "Cleanup Materials"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Remove duplicate materials and purge unused ones"

    def execute(self, context):
        merged  = 0
        pattern = re.compile(r"^(.+)\.\d{3}$")
        mat_map = {}
        for mat in bpy.data.materials:
            m = pattern.match(mat.name)
            if m:
                base = m.group(1)
                if base in bpy.data.materials:
                    mat_map[mat.name] = bpy.data.materials[base]

        for obj in bpy.data.objects:
            if obj.type != "MESH":
                continue
            for slot in obj.material_slots:
                if slot.material and slot.material.name in mat_map:
                    slot.material = mat_map[slot.material.name]
                    merged += 1

        bpy.ops.outliner.orphans_purge(do_recursive=True)
        _report(self, "INFO", f"{merged} slots merged, orphans purged. " + t("msg.done"))
        return {"FINISHED"}

class NOVA_OT_FixAlphaModes(Operator):
    bl_idname  = "nova.fix_alpha_modes"
    bl_label   = "Fix Alpha Blend Modes"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Detect materials using alpha and set correct blend mode (CLIP or BLEND)"

    def execute(self, context):
        fixed = 0
        for mat in bpy.data.materials:
            if not mat.use_nodes:
                continue
            uses_alpha = False
            for node in mat.node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    alpha_in = node.inputs.get("Alpha")
                    if alpha_in and (alpha_in.default_value < 1.0 or alpha_in.is_linked):
                        uses_alpha = True
                        break
                if node.type == "TEX_IMAGE" and node.image:
                    if node.image.channels == 4:
                        uses_alpha = True
                        break
            if uses_alpha and mat.blend_method == "OPAQUE":
                mat.blend_method    = "CLIP"
                mat.alpha_threshold = 0.5
                fixed += 1
        _report(self, "INFO", f"{fixed} materials updated. " + t("msg.done"))
        return {"FINISHED"}

class NOVA_OT_RemoveEmptyMatSlots(Operator):
    bl_idname  = "nova.remove_empty_mat_slots"
    bl_label   = "Remove Empty Mat Slots"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Remove material slots that have no material assigned"

    def execute(self, context):
        meshes  = [o for o in context.selected_objects if o.type == "MESH"]
        removed = 0
        _ensure_object_mode(context)
        for obj in meshes:
            _select_only(obj, context)
            for i in range(len(obj.material_slots) - 1, -1, -1):
                if obj.material_slots[i].material is None:
                    context.object.active_material_index = i
                    bpy.ops.object.material_slot_remove()
                    removed += 1
        _report(self, "INFO", f"{removed} empty slots removed. " + t("msg.done"))
        return {"FINISHED"}

class NOVA_OT_ToonShaderSetup(Operator):
    bl_idname  = "nova.toon_shader_setup"
    bl_label   = "Toon Shader Setup"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Create a basic toon shader node tree on the active material"

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            _report(self, "ERROR", t("msg.no_mesh"))
            return {"CANCELLED"}
        if not obj.material_slots:
            mat = bpy.data.materials.new("ToonMaterial")
            obj.data.materials.append(mat)
        mat = obj.active_material
        if mat is None:
            _report(self, "ERROR", "No active material.")
            return {"CANCELLED"}
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        out    = nodes.new("ShaderNodeOutputMaterial"); out.location    = (600, 0)
        diff   = nodes.new("ShaderNodeBsdfDiffuse");   diff.location   = (200, 0)
        shader = nodes.new("ShaderNodeShaderToRGB");   shader.location = (380, 0)
        curve  = nodes.new("ShaderNodeRGBCurve");      curve.location  = (400, 120)
        mix    = nodes.new("ShaderNodeMixRGB");        mix.location    = (500, 50)
        mix.blend_type = "MULTIPLY"
        mix.inputs[0].default_value = 1.0

        links.new(diff.outputs["BSDF"],    shader.inputs["Shader"])
        links.new(shader.outputs["Color"], curve.inputs["Color"])
        links.new(curve.outputs["Color"],  mix.inputs[1])
        links.new(mix.outputs["Color"],    out.inputs["Surface"])

        _report(self, "INFO", "Toon shader created. " + t("msg.done"))
        return {"FINISHED"}

# =====================================================================
#  SECTION 7 — SHAPE KEY TOOLS
# =====================================================================
VISEME_SHAPE_KEYS = [
    "vrc.v_sil", "vrc.v_pp", "vrc.v_ff", "vrc.v_th", "vrc.v_dd",
    "vrc.v_kk",  "vrc.v_ch", "vrc.v_ss", "vrc.v_nn", "vrc.v_rr",
    "vrc.v_aa",  "vrc.v_e",  "vrc.v_ih", "vrc.v_oh", "vrc.v_ou",
]
MMD_SHAPE_KEYS = [
    "あ", "い", "う", "え", "お",
    "まばたき", "笑い", "ウィンク", "ウィンク２",
    "怒り", "困る", "にこり", "真剣", "じと目",
    "口角上げ", "口角下げ", "口横広げ",
]

class NOVA_OT_AddMMDShapeKeys(Operator):
    bl_idname  = "nova.add_mmd_shape_keys"
    bl_label   = "Add MMD Expressions | don't work"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Add standard MMD expression shape keys to the active mesh"

    # def execute(self, context):
    #     obj = context.active_object
    #     if obj is None or obj.type != "MESH":
    #         _report(self, "ERROR", t("msg.no_mesh"))
    #         return {"CANCELLED"}
    #     if obj.data.shape_keys is None:
    #         obj.shape_key_add(name="Basis", from_mix=False)
    #     existing = {kb.name for kb in obj.data.shape_keys.key_blocks}
    #     added = 0
    #     for name in MMD_SHAPE_KEYS:
    #         if name not in existing:
    #             obj.shape_key_add(name=name, from_mix=False)
    #             added += 1
    #     _report(self, "INFO", f"{added} MMD shape keys added. " + t("msg.done"))
    #     return {"FINISHED"}

class NOVA_OT_RefreshShapeKeyList(Operator):
    bl_idname = "nova.refresh_shapekey_list"
    bl_label  = "Refresh Shape Key List"

    def execute(self, context):
        obj = context.active_object
        lst = context.scene.nova_shapekey_list
        lst.clear()
        if obj and obj.type == "MESH" and obj.data.shape_keys:
            for kb in obj.data.shape_keys.key_blocks:
                item      = lst.add()
                item.name = kb.name
        return {"FINISHED"}

class NOVA_OT_DeleteSelectedShapeKey(Operator):
    bl_idname  = "nova.delete_selected_shapekey"
    bl_label   = "Delete Shape Key"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH" or not obj.data.shape_keys:
            _report(self, "ERROR", t("msg.no_shapekeys"))
            return {"CANCELLED"}
        idx = context.scene.nova_shapekey_index
        kbs = obj.data.shape_keys.key_blocks
        if 0 <= idx < len(kbs):
            obj.active_shape_key_index = idx
            bpy.ops.object.shape_key_remove(all=False)
        return {"FINISHED"}

# =====================================================================
#  SECTION 8 — SCENE TOOLS
# =====================================================================
class NOVA_OT_SceneStatistics(Operator):
    bl_idname = "nova.scene_statistics"
    bl_label  = "Print Scene Statistics"

    def execute(self, context):
        total_tris = sum(
            sum(1 for p in o.data.polygons if len(p.vertices) == 3) +
            sum(len(p.vertices) - 2 for p in o.data.polygons if len(p.vertices) > 3)
            for o in bpy.data.objects if o.type == "MESH"
        )
        total_bones = sum(len(o.data.bones) for o in bpy.data.objects if o.type == "ARMATURE")
        total_mats  = len(bpy.data.materials)
        total_texs  = len(bpy.data.images)
        total_objs  = len(list(bpy.data.objects))
        msg = (
            f"Triangles: {total_tris} | "
            f"Bones: {total_bones} | "
            f"Materials: {total_mats} | "
            f"Textures: {total_texs} | "
            f"Objects: {total_objs}"
        )
        _report(self, "INFO", msg)
        context.scene.nova_stats_cache = msg
        return {"FINISHED"}

class NOVA_OT_SceneCleaner(Operator):
    bl_idname  = "nova.scene_cleaner"
    bl_label   = "Scene Cleaner"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Purge all orphaned data-blocks (meshes, materials, textures, actions)"

    def execute(self, context):
        bpy.ops.outliner.orphans_purge(do_recursive=True)
        _report(self, "INFO", "Orphaned data purged. " + t("msg.done"))
        return {"FINISHED"}

class NOVA_OT_ColorCodeCollections(Operator):
    bl_idname  = "nova.color_code_collections"
    bl_label   = "Color-Code Collections"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Assign distinct colors to collections for visual organization"

    COLORS = ["COLOR_01","COLOR_02","COLOR_03","COLOR_04","COLOR_05","COLOR_06","COLOR_07","COLOR_08"]

    def execute(self, context):
        cols = list(bpy.data.collections)
        for i, col in enumerate(cols):
            col.color_tag = self.COLORS[i % len(self.COLORS)]
        _report(self, "INFO", f"{len(cols)} collections colored. " + t("msg.done"))
        return {"FINISHED"}

class NOVA_OT_BatchRename(Operator):
    bl_idname  = "nova.batch_rename"
    bl_label   = "Batch Rename"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Rename objects, bones, materials or vertex groups with prefix/suffix/find-replace"

    def execute(self, context):
        scene   = context.scene
        prefix  = scene.nova_rename_prefix
        suffix  = scene.nova_rename_suffix
        find    = scene.nova_rename_find
        replace = scene.nova_rename_replace
        target  = scene.nova_rename_target
        renamed = 0

        def do_rename(items):
            nonlocal renamed
            for item in items:
                name = item.name
                if find:
                    name = name.replace(find, replace)
                name      = prefix + name + suffix
                item.name = name
                renamed  += 1

        if target == "OBJECTS":
            do_rename(context.selected_objects)
        elif target == "BONES":
            arm = _get_armature(context)
            if arm:
                do_rename(arm.data.bones)
        elif target == "MATERIALS":
            do_rename(bpy.data.materials)
        elif target == "VERTEX_GROUPS":
            for obj in context.selected_objects:
                if obj.type == "MESH":
                    do_rename(obj.vertex_groups)

        _report(self, "INFO", f"{renamed} items renamed. " + t("msg.done"))
        return {"FINISHED"}

# =====================================================================
#  SECTION 9 — EXPORT & VALIDATE
# =====================================================================
class NOVA_OT_VRChatValidator(Operator):
    bl_idname = "nova.vrchat_validator"
    bl_label  = "VRChat Validator"
    bl_description = "Check VRChat performance limits (triangles, materials, bones, textures)"

    def execute(self, context):
        total_tris = 0
        for o in bpy.data.objects:
            if o.type != "MESH":
                continue
            for p in o.data.polygons:
                vcount = len(p.vertices)
                if vcount == 3:
                    total_tris += 1
                elif vcount > 3:
                    total_tris += vcount - 2

        mats_used: set[str] = set()
        for o in bpy.data.objects:
            if o.type == "MESH":
                for slot in o.material_slots:
                    if slot.material:
                        mats_used.add(slot.material.name)

        total_bones = sum(len(o.data.bones) for o in bpy.data.objects if o.type == "ARMATURE")
        skinned     = sum(1 for o in bpy.data.objects if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers))

        def status(val, good, medium, poor):
            if val <= good:   return "EXCELLENT"
            if val <= medium: return "GOOD"
            if val <= poor:   return "MEDIUM"
            return "POOR"

        tri_status  = status(total_tris, 10000, 32000, 70000)
        mat_status  = "OK" if len(mats_used) <= VRCHAT_LIMITS["materials"]      else "EXCEEDED"
        bone_status = "OK" if total_bones   <= VRCHAT_LIMITS["bones"]           else "EXCEEDED"
        sk_status   = "OK" if skinned       <= VRCHAT_LIMITS["skinned_meshes"]  else "EXCEEDED"

        report = (
            f"TRIS: {total_tris} ({tri_status}) | "
            f"MATS: {len(mats_used)} ({mat_status}) | "
            f"BONES: {total_bones} ({bone_status}) | "
            f"SKINNED: {skinned} ({sk_status})"
        )
        context.scene.nova_vrchat_cache     = report
        context.scene.nova_tri_status_cache = tri_status
        level = "INFO" if all(s in {"OK","EXCELLENT","GOOD"} for s in [mat_status, bone_status, sk_status]) else "WARNING"
        _report(self, level, report)
        return {"FINISHED"}

class NOVA_OT_BatchExportFBX(Operator):
    bl_idname  = "nova.batch_export_fbx"
    bl_label   = "Batch Export FBX"
    bl_options = {"REGISTER"}
    bl_description = "Export each selected object as a separate FBX file to the chosen directory"

    directory: StringProperty(subtype="DIR_PATH")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        objs = context.selected_objects
        if not objs:
            _report(self, "ERROR", t("msg.no_selection"))
            return {"CANCELLED"}
        exported = 0
        _ensure_object_mode(context)
        for obj in objs:
            _select_only(obj, context)
            path = os.path.join(self.directory, f"{obj.name}.fbx")
            try:
                bpy.ops.export_scene.fbx(
                    filepath=path,
                    use_selection=True,
                    apply_scale_options="FBX_SCALE_ALL",
                    bake_anim=False,
                    path_mode="COPY",
                    embed_textures=False,
                    add_leaf_bones=False,
                )
                exported += 1
            except Exception as e:
                _report(self, "WARNING", f"Failed to export '{obj.name}': {e}")
        _report(self, "INFO", f"{exported} FBX files exported. " + t("msg.done"))
        return {"FINISHED"}

class NOVA_OT_BatchExportGLB(Operator):
    bl_idname  = "nova.batch_export_glb"
    bl_label   = "Batch Export GLB"
    bl_options = {"REGISTER"}
    bl_description = "Export all selected objects as a single optimized GLB file"

    filepath: StringProperty(subtype="FILE_PATH")

    def invoke(self, context, event):
        self.filepath = "export.glb"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if not context.selected_objects:
            _report(self, "ERROR", t("msg.no_selection"))
            return {"CANCELLED"}
        try:
            bpy.ops.export_scene.gltf(
                filepath=self.filepath,
                use_selection=True,
                export_format="GLB",
                export_apply=False,
            )
            _report(self, "INFO", f"GLB exported to: {self.filepath}")
        except Exception as e:
            _report(self, "ERROR", f"GLB export failed: {e}")
            return {"CANCELLED"}
        return {"FINISHED"}

# =====================================================================
#  UPDATE OPERATORS
# =====================================================================
class NOVA_OT_CheckUpdate(Operator):
    bl_idname  = "nova.check_update"
    bl_label   = "Check for Update"
    bl_description = "Check GitHub for a newer version of Nova Tools"

    def execute(self, context):
        try:
            if os.path.exists(CACHE_FILE):
                os.remove(CACHE_FILE)
        except Exception:
            pass

        latest = _fetch_latest_version()

        if latest is None:
            _report(self, "WARNING", t("msg.update_failed"))
            return {"CANCELLED"}

        _write_cache(latest)

        current_tuple = bl_info["version"]
        latest_tuple  = _parse_version(latest)
        current_str   = ".".join(str(x) for x in current_tuple)

        print(f"[NovaTools] Version actuelle: {current_str} | Version GitHub: {latest}")

        if latest_tuple > current_tuple:
            bpy.types.Scene.nova_update_available = True
            bpy.types.Scene.nova_update_version   = latest
            _report(self, "INFO", t("msg.update_available") + f" {current_str} → {latest}")
        else:
            bpy.types.Scene.nova_update_available = False
            _report(self, "INFO", t("msg.up_to_date"))

        return {"FINISHED"}

class NOVA_OT_DownloadUpdate(Operator):
    bl_idname  = "nova.download_update"
    bl_label   = "Download & Install Update"
    bl_description = "Download the latest version and replace the current addon file"

    def execute(self, context):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            current_file = os.path.abspath(__file__)
            tmp_path     = current_file + ".tmp"
            req = urllib.request.Request(
                GITHUB_DL,
                headers={"User-Agent": "Mozilla/5.0 NovaTools-Blender-Addon"},
            )
            with urllib.request.urlopen(req, timeout=30, context=ctx) as resp, \
                 open(tmp_path, "wb") as f:
                f.write(resp.read())
            shutil.move(tmp_path, current_file)
            bpy.types.Scene.nova_update_available = False
            _report(self, "INFO", t("msg.download_ok"))
        except Exception as e:
            _report(self, "ERROR", f"{t('msg.download_fail')} {e}")
            return {"CANCELLED"}
        return {"FINISHED"}

# =====================================================================
#  PREFERENCES
# =====================================================================
class NOVA_Preferences(AddonPreferences):
    bl_idname = ADDON_ID

    def draw(self, context):
        layout = self.layout
        layout.label(text="Nova Tools Preferences", icon="TOOL_SETTINGS")
        layout.label(text=f"Version: {'.'.join(str(v) for v in bl_info['version'])}")
        layout.operator("wm.url_open", text="GitHub",       icon="URL").url   = "https://github.com/VrcFoss/NovaTools"
        layout.operator("wm.url_open", text="Report Issue", icon="ERROR").url = "https://github.com/VrcFoss/NovaTools/issues"

# =====================================================================
#  MAIN PANEL
# =====================================================================
class NOVA_PT_MainPanel(Panel):
    bl_label       = "Nova Tools"
    bl_idname      = "NOVA_PT_MainPanel"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "Nova Tools"

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        row = layout.row(align=True)
        row.prop(scene, "nova_language", expand=True)

        layout.separator()

        if getattr(scene, "nova_update_available", False):
            banner       = layout.box()
            banner.alert = True
            banner.label(text=t("lbl.new_version") + f" v{scene.nova_update_version}", icon="INFO")
            banner.operator("nova.download_update", icon="IMPORT")

        layout.separator()

        box = layout.box()
        box.label(text=t("lbl.armature"), icon="ARMATURE_DATA")
        box.prop(scene, "nova_armature", text="")

        layout.separator()

        _draw_section(layout, scene, "collections", t("section.collections"), "OUTLINER_COLLECTION",
            lambda box: self._draw_collections(box, context))

        _draw_section(layout, scene, "combine", t("section.combine"), "MESH_DATA",
            lambda box: self._draw_combine(box, context))

        _draw_section(layout, scene, "weights", t("section.weights"), "MOD_VERTEX_WEIGHT",
            lambda box: self._draw_weights(box, context))

        _draw_section(layout, scene, "bones", t("section.bones"), "BONE_DATA",
            lambda box: self._draw_bones(box, context))

        _draw_section(layout, scene, "mesh", t("section.mesh"), "MESH_ICOSPHERE",
            lambda box: self._draw_mesh(box, context))

        _draw_section(layout, scene, "materials", t("section.materials"), "MATERIAL",
            lambda box: self._draw_materials(box, context))

        _draw_section(layout, scene, "shapekeys", t("section.shapekeys"), "SHAPEKEY_DATA",
            lambda box: self._draw_shapekeys(box, context))

        _draw_section(layout, scene, "scene", t("section.scene"), "SCENE_DATA",
            lambda box: self._draw_scene(box, context))

        _draw_section(layout, scene, "export", t("section.export"), "EXPORT",
            lambda box: self._draw_export(box, context))

        layout.separator()
        footer = layout.box()
        row    = footer.row(align=True)
        ver    = ".".join(str(v) for v in bl_info["version"])
        row.label(text=f"Nova Tools v{ver}", icon="SOLO_ON")
        row.operator("nova.check_update", text=t("btn.check_update"), icon="FILE_REFRESH")

    def _draw_collections(self, box, context):
        scene = context.scene
        box.prop(scene, "nova_collection_body",    text=t("lbl.collection_body"))
        box.prop(scene, "nova_collection_clothes", text=t("lbl.collection_clothes"))
        box.label(text=t("lbl.extra_collections") + ":")
        row = box.row(align=True)
        row.prop(scene, "nova_col_armature", toggle=True)
        row.prop(scene, "nova_col_props",    toggle=True)
        row.prop(scene, "nova_col_fx",       toggle=True)
        box.operator("nova.create_collections", icon="OUTLINER_COLLECTION")

    def _draw_combine(self, box, context):
        box.prop(context.scene, "nova_combine_merge_shapekeys")
        box.operator("nova.combine_clothes", icon="MESH_DATA")

    def _draw_weights(self, box, context):
        box.operator("nova.transfer_weights",     icon="MOD_DATA_TRANSFER")
        box.operator("nova.auto_weight_paint",    icon="WPAINT_HLT")
        box.operator("nova.normalize_weights",    icon="NORMALIZE_FCURVES")
        box.operator("nova.mirror_vertex_groups", icon="MOD_MIRROR")
        box.separator()
        box.label(text=t("lbl.threshold"))
        box.prop(context.scene, "nova_vgroup_threshold", text="")
        box.operator("nova.clean_vertex_groups",  icon="TRASH")

    def _draw_bones(self, box, context):
        scene = context.scene
        box.operator("nova.add_root_bone",      icon="BONE_DATA")
        box.operator("nova.fix_bone_axes",      icon="ORIENTATION_GLOBAL")
        box.operator("nova.assign_bone_colors", icon="COLOR")
        box.separator()
        box.label(text=t("lbl.bone_filters") + ":", icon="FILTER")
        box.prop(scene, "nova_remove_unweighted_bones")
        box.prop(scene, "nova_remove_end_bones")
        box.separator()
        box.label(text="Protected Bones (exclusion list):")
        row = box.row()
        row.template_list("NOVA_UL_ExcludeBoneList", "", scene, "nova_excluded_bones_list",
                          scene, "nova_excluded_bones_index", rows=3)
        col = row.column(align=True)
        col.operator("nova.add_excluded_bone",    icon="ADD",    text="")
        col.operator("nova.remove_excluded_bone", icon="REMOVE", text="")
        box.prop(scene, "nova_temp_bone_name", text="")
        box.operator("nova.remove_unused_bones", icon="TRASH")

    def _draw_mesh(self, box, context):
        scene = context.scene
        box.operator("nova.check_symmetry",       icon="MOD_MIRROR")
        box.operator("nova.symmetrize_mesh",      icon="MOD_MIRROR")
        box.operator("nova.center_origins",       icon="OBJECT_ORIGIN")
        box.operator("nova.validate_mesh",        icon="CHECKMARK")
        box.operator("nova.optimize_meshes",      icon="AUTOMERGE_ON")
        box.operator("nova.apply_modifiers_safe", icon="MODIFIER")
        box.operator("nova.detect_ngons",         icon="FACE_MAPS")
        box.operator("nova.uv_overlap_detect",    icon="UV")
        box.separator()
        box.label(text=t("lbl.angle"))
        box.prop(scene, "nova_smooth_angle", text="")
        box.operator("nova.auto_smooth_groups",   icon="SMOOTHCURVE")
        box.separator()
        box.label(text=t("lbl.ratio"))
        box.prop(scene, "nova_decimate_ratio",    text="")
        box.operator("nova.smart_decimate",       icon="MOD_DECIM")

    def _draw_materials(self, box, context):
        box.operator("nova.cleanup_materials",     icon="MATERIAL")
        box.operator("nova.fix_alpha_modes",       icon="NODE_MATERIAL")
        box.operator("nova.remove_empty_mat_slots",icon="TRASH")
        box.operator("nova.toon_shader_setup",     icon="SHADING_RENDERED")

    def _draw_shapekeys(self, box, context):
        scene = context.scene
        box.operator("nova.add_mmd_shape_keys",    icon="SHAPEKEY_DATA")
        box.separator()
        box.label(text=t("btn.manage_shapekeys"),  icon="SHAPEKEY_DATA")
        box.operator("nova.refresh_shapekey_list", icon="FILE_REFRESH", text="Refresh List")
        if scene.nova_shapekey_list:
            row = box.row()
            row.template_list("NOVA_UL_ShapeKeyList", "", scene, "nova_shapekey_list",
                              scene, "nova_shapekey_index", rows=4)
            box.operator("nova.delete_selected_shapekey", icon="TRASH")
        else:
            box.label(text=t("msg.no_shapekeys"), icon="INFO")

    def _draw_scene(self, box, context):
        scene = context.scene
        box.operator("nova.scene_statistics", icon="INFO")
        if scene.nova_stats_cache:
            stats_box = box.box()
            for part in scene.nova_stats_cache.split(" | "):
                stats_box.label(text=part)
        box.separator()
        box.operator("nova.scene_cleaner",            icon="TRASH")
        box.operator("nova.color_code_collections",   icon="OUTLINER_COLLECTION")
        box.separator()
        box.label(text=t("btn.batch_rename"), icon="SORTALPHA")
        box.prop(scene, "nova_rename_target",  text="")
        box.prop(scene, "nova_rename_prefix",  text=t("lbl.prefix"))
        box.prop(scene, "nova_rename_suffix",  text=t("lbl.suffix"))
        row = box.row(align=True)
        row.prop(scene, "nova_rename_find",    text=t("lbl.find"))
        row.prop(scene, "nova_rename_replace", text=t("lbl.replace"))
        box.operator("nova.batch_rename",      icon="SORTALPHA")

    def _draw_export(self, box, context):
        scene = context.scene
        box.operator("nova.vrchat_validator", icon="CHECKMARK")
        if scene.nova_vrchat_cache:
            status_box       = box.box()
            status_box.alert = scene.nova_tri_status_cache in {"MEDIUM", "POOR"}
            for part in scene.nova_vrchat_cache.split(" | "):
                status_box.label(text=part)
        box.separator()
        box.operator("nova.batch_export_fbx", icon="EXPORT")
        box.operator("nova.batch_export_glb", icon="EXPORT")


def _draw_section(layout, scene, key, label, icon, draw_fn):
    prop_name = f"nova_show_{key}"
    expanded  = getattr(scene, prop_name, False)
    box       = layout.box()
    row       = box.row()
    row.prop(scene, prop_name,
             icon="TRIA_DOWN" if expanded else "TRIA_RIGHT",
             icon_only=True, emboss=False)
    row.label(text=label, icon=icon)
    if expanded:
        draw_fn(box)

# =====================================================================
#  REGISTER / UNREGISTER
# =====================================================================
_CLASSES = [
    NOVA_ExcludeBoneItem,
    NOVA_ShapeKeyItem,
    NOVA_UL_ExcludeBoneList,
    NOVA_UL_ShapeKeyList,
    NOVA_OT_CreateCollections,
    NOVA_OT_CombineClothes,
    NOVA_OT_TransferWeights,
    NOVA_OT_AutoWeightPaint,
    NOVA_OT_NormalizeWeights,
    NOVA_OT_MirrorVertexGroups,
    NOVA_OT_CleanVertexGroups,
    NOVA_OT_RemoveUnusedBones,
    NOVA_OT_AddRootBone,
    NOVA_OT_FixBoneAxes,
    NOVA_OT_AssignBoneColors,
    NOVA_OT_AddExcludedBone,
    NOVA_OT_RemoveExcludedBone,
    NOVA_OT_CheckSymmetry,
    NOVA_OT_SymmetrizeMesh,
    NOVA_OT_CenterOrigins,
    NOVA_OT_ValidateMesh,
    NOVA_OT_ApplyModifiersSafe,
    NOVA_OT_SmartDecimate,
    NOVA_OT_DetectNgons,
    NOVA_OT_UVOverlapDetect,
    NOVA_OT_AutoSmoothGroups,
    NOVA_OT_OptimizeMeshes,
    NOVA_OT_CleanupMaterials,
    NOVA_OT_FixAlphaModes,
    NOVA_OT_RemoveEmptyMatSlots,
    NOVA_OT_ToonShaderSetup,
    NOVA_OT_AddMMDShapeKeys,
    NOVA_OT_RefreshShapeKeyList,
    NOVA_OT_DeleteSelectedShapeKey,
    NOVA_OT_SceneStatistics,
    NOVA_OT_SceneCleaner,
    NOVA_OT_ColorCodeCollections,
    NOVA_OT_BatchRename,
    NOVA_OT_VRChatValidator,
    NOVA_OT_BatchExportFBX,
    NOVA_OT_BatchExportGLB,
    NOVA_OT_CheckUpdate,
    NOVA_OT_DownloadUpdate,
    NOVA_Preferences,
    NOVA_PT_MainPanel,
]


def register():
    for cls in _CLASSES:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"[NovaTools] Could not register {cls.__name__}: {e}")
    register_properties()
    if _auto_check_update not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_auto_check_update)


def unregister():
    if _auto_check_update in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_auto_check_update)
    unregister_properties()
    for cls in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print(f"[NovaTools] Could not unregister {cls.__name__}: {e}")


if __name__ == "__main__":
    register()
