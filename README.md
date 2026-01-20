# AIESDA: Artificial Intelligence based Earth System Data Assimilation

AIESDA (Artificial Intelligence based Earth System Data Assimilation) is a next-generation framework designed to integrate AI Foundation Models into traditional Numerical Weather Prediction (NWP) and Data Assimilation (DA) workflows. The goal of this project is to provide Data Assimilation engine based on JEDI and to bridge it seamlessly with Dynamical Forecast Systems (Bharat, Mithuna) as well as cutting-edge AI Foundation Models (GraphCast, Pangu-Weather, etc.).

## 🏗 System Architecture
***AIESDA*** follows a decoupled architecture to ensure scalability:

**aidadic.py:** The "Source of Truth" (Registry and Mappings).

**aidaconf.py:** The Orchestrator (ModelPassport and workflow logic).

**ailib.py:** Interfaces for AI Foundation Models.

**dynlib.py:** Interfaces for Dynamical/Coupled Models.

**dalib.py:** Bridges for JEDI (IODA, UFO, SABER, OOPS), CRTM, and RTTOV.

**scilib.py:** Scientific toolbox for validation, verification and evaluation

## 🚀 Key Features

**Modular Design**

**Object Oriented**

**Seperation of concern**

**Model Passport Verification at the entry level of data**

## 🛠 Installation
```bash
git clone [https://github.com/NCMRWF/aiesda.git](https://github.com/NCMRWF/aiesda.git)
cd aiesda
pip install -r requirements.txt
```



## 🚦 ***Quick Start***
```Python

import xarray
from aidaconf import ModelPassport

# Load a raw forecast file
ds = xarray.open_dataset("pangu_forecast.nc")

# Identify and Verify via Passport
interface = ModelPassport.identify(ds)

# Standardize for JEDI
standard_ds = interface.prepare_state(ds)

---
```

## 🛠 Adding a New Model to the Registry
To register a new model, update the `MODEL_REGISTRY` in `aidadic.py`:
```python
"new_model_name": {
    "interface_class": "ailib.NewModelInterface",
    "required_vars": ["t", "q", "u", "v"],
    "horizontal_res": 0.1,
    "vertical_levels": "standard_grid_key",
    "allow_nans": False,
    "mapping": {"air_temperature": "t", ...}
}
```
