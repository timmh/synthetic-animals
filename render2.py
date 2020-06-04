import sys
import os

sys.path.insert(0, os.path.abspath("./modules"))

import cv2
import bpy
import bpycv
import importlib
import random
import math
from bpy.app.handlers import persistent
import progressbar

# make RNG deterministic
random.seed(42)


@persistent
def RandomSeedHandler(scene):
    bpy.context.scene.cycles.seed = random.randint(10, 1000000000)


def register():
    bpy.app.handlers.render_pre.append(RandomSeedHandler)


def unregister():
    bpy.app.handlers.render_pre.remove(RandomSeedHandler)


register()

# get keyframes of object list
def get_keyframes(obj_list):
    keyframes = []
    for obj in obj_list:
        anim = obj.animation_data
        if anim is not None and anim.action is not None:
            for fcu in anim.action.fcurves:
                for keyframe in fcu.keyframe_points:
                    x, y = keyframe.co
                    if x not in keyframes:
                        keyframes.append((math.ceil(x)))
    return keyframes


def get_first_child_with_type(parent, child_type):
    for child in parent.children:
        if child.type == child_type:
            return child


def import_fbx(**kwargs):
    old_objs = set(bpy.context.scene.objects)
    bpy.ops.import_scene.fbx(**kwargs)
    imported_objs = set(bpy.context.scene.objects) - old_objs
    for ob in imported_objs:
        if ob.type == "ARMATURE":
            return ob


def create_material(name, color_path, normal_path,SCENE_VARIATION):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    texImage = mat.node_tree.nodes.new("ShaderNodeTexImage")
    texImage.image = bpy.data.images.load(bpy.path.abspath(color_path))
    
    # norImage = mat.node_tree.nodes.new("ShaderNodeTexImage")
    # norImage.image = bpy.data.images.load(bpy.path.abspath(normal_path))
    # mat.node_tree.links.new(bsdf.inputs["Normal"], norImage.outputs["Color"])
    bsdf.inputs["Specular"].default_value = 0
    
    if SCENE_VARIATION == 'night':
        bright_contrast = mat.node_tree.nodes.new("ShaderNodeBrightContrast")
        bright_contrast.inputs["Bright"].default_value = 0.2
        bright_contrast.inputs["Contrast"].default_value = 0
        mat.node_tree.links.new(bright_contrast.inputs["Color"], texImage.outputs["Color"])
        mat.node_tree.links.new(bsdf.inputs["Base Color"], bright_contrast.outputs["Color"])
    else:
        mat.node_tree.links.new(bsdf.inputs["Base Color"], texImage.outputs["Color"])
    return mat


def apply_animation(target_object, animation_path):
    rig = import_fbx(
        filepath=bpy.path.abspath(animation_path), automatic_bone_orientation=True,
    )
    target_object.animation_data_clear()
    bpy.ops.object.select_all(action="DESELECT")
    target_object.select_set(True)
    rig.select_set(True)
    bpy.ops.object.make_links_data(type="ANIMATION")
    # set_animation_time(rig)
    # bpy.ops.anim.channels_select_all("SELECT")
    # bpy.ops.action.extrapolation_type(type="MAKE_CYCLIC")
    # print(get_keyframes([rig]))


# def set_animation_time(aniamted_object):
#     bpy.ops.object.select_all(action="DESELECT")
#     animation = get_first_child_with_type(aniamted_object, "ANIMATION")
#     animation.select_set(True)
#     bpy.ops.anim.change_frame(frame=15)


def randomize_particles():
    plane = [obj for obj in bpy.context.scene.objects if obj.name.startswith("Ground")][
        0
    ]
    plane.particle_systems["grass"].seed = random.randint(10, 1000000000)
    plane.particle_systems["rocks"].seed = random.randint(10, 1000000000)
    plane.particle_systems["trees"].seed = random.randint(10, 1000000000)


def randomize_sun():
    sun = [obj for obj in bpy.context.scene.objects if obj.name.startswith("Sun")][0]
    sun.location.x += random.randrange(-50, 50)
    sun.location.y += random.randrange(-50, 50)


def import_animal(animal_data, SCENE_VARIATION):
    animal = import_fbx(
        filepath=bpy.path.abspath(animal_data.model_path),
        automatic_bone_orientation=True,
    )
    animal_mesh = get_first_child_with_type(animal, "MESH")


    # TODO: remove hack for proper deer display
    for child in animal.children:
        if child.name == 'deer_horns':
            bpy.ops.object.delete({"selected_objects": [child]})

    mat = create_material(
        animal_data.name,
        animal_data.texture_color_path,
        animal_data.texture_normal_path,
        SCENE_VARIATION
    )
    if animal_mesh.data.materials:
        animal_mesh.data.materials[0] = mat
    else:
        animal_mesh.data.materials.append(mat)
    apply_animation(animal, animal_data.animation_path)
    return animal


def activate_cuda():
    bpy.context.scene.cycles.device = "GPU"
    prefs = bpy.context.preferences
    cprefs = prefs.addons["cycles"].preferences
    bpy.context.scene.render.use_overwrite = False
    bpy.context.scene.render.use_placeholder = True
    cprefs.compute_device_type = "CUDA"
    print("getting devices:", cprefs.get_devices())
    for device in cprefs.devices:
        device.use = True
    print("using devices:", cprefs.devices)
    

# class Bear:
#     name = "Bear"
#     model_path = "//assets/animal_pack_deluxe/Models/Bear_Rig.fbx"
#     texture_color_path = (
#         "//assets/animal_pack_deluxe/Textures/brown_bear_col4_unity.tga"
#     )
#     texture_normal_path = "//assets/animal_pack_deluxe/Textures/brown_bear_nrml7.tga"
#     animation_path = "//assets/animal_pack_deluxe/Animations/Bear_Run.fbx"


class Deer:
    name = "Deer"
    model_path = "//assets/animal_pack_deluxe/Models/Deer_Rig.fbx"
    texture_color_path = "//assets/animal_pack_deluxe/Textures/deer_col6_unity.tga"
    texture_normal_path = "//assets/animal_pack_deluxe/Textures/deer_nrml4.tga"
    animation_path = "//assets/animal_pack_deluxe/Animations/Deer_Walk.fbx"


class Boar:
    name = "Boar"
    model_path = "//assets/animal_pack_deluxe/Models/WildBoar_Rig.fbx"
    texture_color_path = "//assets/animal_pack_deluxe/Textures/wild_boar_col9_unity.tga"
    texture_normal_path = "//assets/animal_pack_deluxe/Textures/wild_boar_nrml10.tga"
    animation_path = "//assets/animal_pack_deluxe/Animations/WildBoar_Walk.fbx"

class Rabbit:
    name = "Rabbit"
    model_path = "//assets/animal_pack_deluxe/Models/WildRabbit_Rig.fbx"
    texture_color_path = "//assets/animal_pack_deluxe/Textures/wild_rabbit_col_v3_unity.tga"
    texture_normal_path = "//assets/animal_pack_deluxe/Textures/wild_rabbit_nrml_v3.tga"
    animation_path = "//assets/animal_pack_deluxe/Animations/WildRabbit_Walk.fbx"


def main():
    OUT_DIR = os.getenv("OUT_DIR", "./out")
    os.makedirs(OUT_DIR, exist_ok=True)
    N_SAMPLES = 1250
    ANIMALS = [Deer(), Boar(), Rabbit()]
    MIN_N_ANIMALS = 0
    MAX_N_ANIMALS = 10
    SCENE_VARIATION = 'night'

    for i in progressbar.progressbar(range(1, N_SAMPLES + 1)):
        bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath)
        # activate_cuda()

        animals = []
        for j in range(random.randint(MIN_N_ANIMALS, MAX_N_ANIMALS)):
            animal_data = random.sample(ANIMALS, 1)[0]
            class_id = ANIMALS.index(animal_data) + 1
            animal = import_animal(animal_data, SCENE_VARIATION)
            animals.append(animal)

            animal.rotation_euler.z += random.random() * math.pi
            animal.location.x = random.randrange(0, 40)
            animal.location.y = random.randrange(-15, 15)

            get_first_child_with_type(animal, "MESH")["class_id"] = class_id
            get_first_child_with_type(animal, "MESH")["inst_id"] = j + 1

        bpy.context.scene.frame_set(random.randint(0, 15))
        bpy.context.scene.cycles.seed = random.randint(10, 1000000000)
        randomize_particles()

        if SCENE_VARIATION != 'night':
            randomize_sun()

        result = bpycv.render_data()

        rgb = result["image"]
        cv2.imwrite(
            os.path.join(OUT_DIR, f"{i:06d}_rgb.png"),
            cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR) if SCENE_VARIATION != 'night' else cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY),
        )
        cv2.imwrite(os.path.join(OUT_DIR, f"{i:06d}_ins.png"), result["inst"])
        cv2.imwrite(os.path.join(OUT_DIR, f"{i:06d}_cla.png"), result["class"])
        cv2.imwrite(
            os.path.join(OUT_DIR, f"{i:06d}_dep.png"),
            result["depth"] / result["depth"].max() * 255,
        )
        cv2.imwrite(
            os.path.join(OUT_DIR, f"{i:06d}_vis.png"),
            cv2.cvtColor(result.vis(), cv2.COLOR_RGB2BGR),
        )


main()
