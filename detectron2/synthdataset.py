import os
import glob
import cv2
import numpy as np
import detectron2
import pycocotools
from detectron2.data import MetadataCatalog
import functools

synthdataset_dir = os.path.join("..", "out")

def synthbbox(mask):
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]

    return [cmin, rmin, cmax, rmax]

@functools.lru_cache
def synthdataset_fn(validation=False):

    @functools.lru_cache
    def get_synthdataset():
        filepaths = glob.glob(os.path.join(synthdataset_dir, "*_rgb.png"))
        n_samples = len(filepaths)

        if validation:
            filepaths = filepaths[-n_samples//5:]
        else:
            filepaths = filepaths[:-n_samples//5]

        ds = []
        for filepath in filepaths:
            dic = {}
            filepath_base = filepath[: -len("_rgb.png")]
            rgb = cv2.imread(f"{filepath_base}_rgb.png")
            cla = cv2.imread(f"{filepath_base}_cla.png", cv2.IMREAD_GRAYSCALE)
            ins = cv2.imread(f"{filepath_base}_ins.png", cv2.IMREAD_GRAYSCALE)

            dic['file_name'] = f"{filepath_base}_rgb.png"
            dic['height'], dic['width'] = rgb.shape[0:2]
            dic['id'] = os.path.basename(filepath_base)

            class_ids = np.unique(cla.reshape(-1))
            instance_ids = np.unique(ins.reshape(-1))

            dic['annotations'] = []
            for instance_id in instance_ids:
                
                # ignore background for now
                if instance_id < 1:
                    continue

                mask = ins == instance_id

                if np.sum(mask) < 20 ** 2:
                    # too small of an instance
                    continue


                contours, hierarchy = cv2.findContours((mask).astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                # before opencv 3.2
                # contours, hierarchy = cv2.findContours((mask).astype(np.uint8), cv2.RETR_TREE,
                #                                                    cv2.CHAIN_APPROX_SIMPLE)
                segmentation = []

                for contour in contours:
                    contour = contour.flatten().tolist()
                    # segmentation.append(contour)
                    if len(contour) > 4:
                        segmentation.append(contour)
                if len(segmentation) == 0:
                    continue

                annotation = {}
                annotation['bbox'] = synthbbox(mask)
                annotation['bbox_mode'] = detectron2.structures.BoxMode.XYXY_ABS
                annotation['category_id'] = int(round(np.mean(cla[mask])) - 1)
                # annotation['segmentation'] = pycocotools.mask.encode(np.asfortranarray(mask.astype(np.uint8)).copy())
                annotation['segmentation'] = segmentation
                dic['annotations'].append(annotation)

            dic['sem_seg_file_name'] = f"{filepath_base}_cla.png"

            ds.append(dic)
        return ds
    
    return get_synthdataset

from detectron2.data import DatasetCatalog

DatasetCatalog.register("synthdataset_train", synthdataset_fn(validation=False))
DatasetCatalog.register("synthdataset_validation", synthdataset_fn(validation=True))
MetadataCatalog.get("synthdataset_train").thing_classes = ["deer", 'boar', 'rabbit']
MetadataCatalog.get("synthdataset_train").stuff_classes = []
MetadataCatalog.get("synthdataset_validation").thing_classes = ["deer", 'boar', 'rabbit']
MetadataCatalog.get("synthdataset_validation").stuff_classes = []