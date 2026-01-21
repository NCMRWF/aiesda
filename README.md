# AIESDA: Artificial Intelligence based Earth System Data Assimilation

AIESDA (Artificial Intelligence based Earth System Data Assimilation) is a next-generation framework designed to integrate AI Foundation Models into traditional Numerical Weather Prediction (NWP) and Data Assimilation (DA) workflows. The goal of this project is to provide Data Assimilation engine based on JEDI and to bridge it seamlessly with Dynamical Forecast Systems (Bharat, Mithuna) as well as cutting-edge AI Foundation Models (GraphCast, Pangu-Weather, etc.).

![unnamed](https://github.com/user-attachments/assets/7028f2ae-f08e-4c39-bdf9-46bdbe2d9937)



## 🚀 Key Features

**Modular and Object Oriented Design**

**Seperation of concern**

**Model Passport Verification at the entry level of data**

## 🛠 Installation
```bash
git clone https://github.com/NCMRWF/aiesda.git
cd aiesda
# Initialize the module system (if not already in your .bashrc)
source /etc/profile.d/modules.sh
./install.sh

module use ~/modulefiles; 
module load aiesda/0.1.0
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

### 🗺 **Documentation Navigation**

[🏠 Home](https://github.com/NCMRWF/aiesda/wiki/Home)

[🏗️ Architecture](https://github.com/NCMRWF/aiesda/wiki/Architecture)

[🪜 Development Roadmap](https://github.com/NCMRWF/aiesda/wiki/Development-Roadmap)

[🛠 Contribution Guide](https://github.com/NCMRWF/aiesda/wiki/Contribution-Guide)

