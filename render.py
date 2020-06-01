import cv2
import bpy
import bpycv
import random

n_rotations = 10
for i_rotations in range(n_rotations):
    deer = bpy.data.objects["deer"]
    deer.rotation_euler = (0, 0, (i_rotations / n_rotations) * 2 * 3.14)

    # set each instance a unique inst_id, which is used to generate instance annotation.
    deer["inst_id"] = 1

    # render image, instance annoatation and depth in one line code
    # result["ycb_meta"] is 6d pose GT
    result = bpycv.render_data()

    # save result
    # cv2.imwrite(
    #     "demo-rgb.jpg",
    #     cv2.cvtColor(result["image"], cv2.COLOR_RGB2BGR),  # cover RGB to BGR
    # )
    # cv2.imwrite("demo-inst.png", result["inst"])
    # # normalizing depth
    # cv2.imwrite("demo-depth.png", result["depth"] / result["depth"].max() * 255)

    # visualization inst|rgb|depth for human
    cv2.imwrite(
        f"./out/test_{(i_rotations+1):04d}.png",
        cv2.cvtColor(result.vis(), cv2.COLOR_RGB2BGR),
    )
