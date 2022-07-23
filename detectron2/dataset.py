import os
import glob
import functools
import cv2
import numpy as np
import detectron2
from detectron2.data import DatasetCatalog
from detectron2.data import MetadataCatalog


def mask_to_bbox(mask):
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]

    return [cmin, rmin, cmax, rmax]


@functools.lru_cache
def synthetic_animals_dataset_fn(validation=False, dataset_dir=os.getenv("OUT_DIR", "./out")):

    @functools.lru_cache
    def get_synthetic_animals_dataset():

        filepaths = glob.glob(os.path.join(dataset_dir, "*_rgb.png"))
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

                contours_ret = cv2.findContours((mask).astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                if len(contours_ret) == 2:
                    contours, _ = contours_ret
                else:
                    _, contours, _ = contours_ret

                segmentation = []

                for contour in contours:
                    contour = contour.flatten().tolist()
                    if len(contour) > 4:
                        segmentation.append(contour)
                if len(segmentation) == 0:
                    continue

                annotation = {}
                annotation['bbox'] = mask_to_bbox(mask)
                annotation['bbox_mode'] = detectron2.structures.BoxMode.XYXY_ABS
                annotation['category_id'] = int(round(np.mean(cla[mask])) - 1)
                annotation['segmentation'] = segmentation
                dic['annotations'].append(annotation)

            dic['sem_seg_file_name'] = f"{filepath_base}_cla.png"

            ds.append(dic)
        return ds
    
    return get_synthetic_animals_dataset


DatasetCatalog.register("synthetic_animals_train", synthetic_animals_dataset_fn(validation=False))
DatasetCatalog.register("synthetic_animals_validation", synthetic_animals_dataset_fn(validation=True))
MetadataCatalog.get("synthetic_animals_train").thing_classes = ["deer", "boar", "rabbit"]
MetadataCatalog.get("synthetic_animals_train").stuff_classes = []
MetadataCatalog.get("synthetic_animals_validation").thing_classes = ["deer", "boar", "rabbit"]
MetadataCatalog.get("synthetic_animals_validation").stuff_classes = []