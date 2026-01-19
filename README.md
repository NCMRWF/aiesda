# AIESDA: Artificial Intelligence based Earth System Data Assimilation

AIESDA is a robust framework designed to bridge **AI Foundation Models** (GraphCast, Pangu-Weather, etc.) with **Dynamical Forecast Systems** (Bharat, Mithuna) and **Data Assimilation engines** like JEDI/UFO.


## 🏗 System Architecture
AIESDA follows a decoupled architecture to ensure scalability:

aidadic.py: The "Source of Truth" (Registry and Mappings).

aidaconf.py: The Orchestrator (ModelPassport and workflow logic).

ailib/: Interfaces for AI Foundation Models.

dynlib/: Interfaces for Dynamical/Coupled Models.

dalib/: Bridges for JEDI, CRTM, and RTTOV.

## 🚀 Key Features
* **Model Passport**: A zero-trust multi-factor authentication system for meteorological data.
* **JEDI Model Bridge**: Automated standardization of AI outputs for Observation Operators (CRTM/RTTOV).
* **Unified Registry**: Centralized management of variable mappings and vertical grid fingerprints.


**The Multi-Factor Model Passport**

#### Overview
The **Model Passport** replaces fragile "if-else" logic with a rigorous verification system. Every dataset entering the assimilation cycle must pass a three-tier check to ensure scientific integrity and prevent JEDI solver crashes.



#### The Three Tiers of Verification
1. **Identity Factor**: Scans global metadata attributes for recognized source tags (e.g., `graphcast`, `bharat`).
2. **Biometric Factor**: Compares the vertical pressure levels of the file against known "fingerprints" using `numpy.allclose`. This distinguishes between models sharing similar level counts.
3. **Integrity Factor**:
    * **Horizontal Resolution**: Validates the grid spacing (e.g., ensures a 0.25° model isn't processed as a 0.06° model).
    * **Variable Completeness**: Ensures all required coupled fields (like SST for Bharat) are present.
    * **Strict NaN Check**: Rejects data with null values to protect the DA solver.


## 🛠 Installation
```bash
git clone [https://github.com/NCMRWF/aiesda.git](https://github.com/NCMRWF/aiesda.git)
cd aiesda
pip install -r requirements.txt



## 🚦 ***Quick Start***
Python

import xarray
from aidaconf import ModelPassport

# Load a raw forecast file
ds = xarray.open_dataset("pangu_forecast.nc")

# Identify and Verify via Passport
interface = ModelPassport.identify(ds)

# Standardize for JEDI
standard_ds = interface.prepare_state(ds)

---


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
