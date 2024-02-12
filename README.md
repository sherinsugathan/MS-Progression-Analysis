# MS Progression Analysis
This is a generic tool for analysing MS lesions. The tool supports comparative visualization and filtering of lesions based on activity.
![Screenshot](/screens/ms-progression-screenshot.gif)
## Input File Structure
The input lesion data should follow the following file structure.
```
my_dataset/
├── 1001BC/   # Subject 1 folder
│   ├── 1001BC_m00_m12_snacai/  # baseline folder
│   ├── 1001BC_m12_m24_snacai/  # followup 1 folder
│   ├── 1001BC_m12_m36_snacai/  # followup 2 folder
│   └── 1001BC_m36_m48_snacai/  # followup 3 folder
└── 1002MG/  # Subject 2 folder
    ├── 1001BC_m00_m12_snacai/  # baseline folder
    │   ├── Lesion_1_baseline.nii.gz  # baseline binary mask of lesion 1
    │   ├── Lesion_1_followup.nii.gz  # followup binary mask of lesion 1
    │   ├── Lesion_2_baseline.nii.gz  # baseline binary mask of lesion 2
    │   ├── Lesion_2_followup.nii.gz  # followup binary mask of lesion 2
    │   ├── ...
    │   ├── ...
    │   ├── Lesion_n_baseline.nii.gz  # baseline binary mask of lesion n
    │   ├── Lesion_n_followup.nii.gz  # baseline binary mask of lesion n
    ├── 1001BC_m12_m24_snacai/  # followup 1 folder
    ├── 1001BC_m12_m36_snacai/  # followup 2 folder
    └── 1001BC_m36_m48_snacai/  # followup 3 folder
```

## Setup and Running
1. Clone the repository - `git clone https://github.com/sherinsugathan/MS-Progression-Analysis.git`
2. Install dependencies.
   `pip install -r requirements.txt`
3. Run `main.py` by providing your subject folder as an argument.`python main.py <input folder>`.

```shell
Example:
    python main.py /filesystem/folder/1001BC
```
## Citation
```bibtex
@article{Sugathan2022Longitudinal,
title = {Longitudinal visualization for exploratory analysis of multiple sclerosis lesions},
author = {Sugathan, Sherin and Bartsch, Hauke and Riemer, Frank and Gr{\"u}ner, Renate and Lawonn, Kai and Smit, Noeska},
year = 2022,
journal = {Computers & Graphics},
volume = 107,
pages = {208--219},
doi = {10.1016/j.cag.2022.07.023},
issn = {0097-8493},
url = {https://www.sciencedirect.com/science/article/pii/S0097849322001479},
images = "images/Sugathan-2022-Longitudinal.PNG",
thumbnails = "images/Sugathan-2022-Longitudinal.PNG",
project = {ttmedvis},
youtube = "https://youtu.be/uwcqSf1W-dc"
}
```

