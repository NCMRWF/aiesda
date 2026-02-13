
# Artificial Intelligence based Earth System Data Assimilation (AIESDA)

Welcome to the AIESDA Wiki

AIESDA (Artificial Intelligence based Earth System Data Assimilation) is a next-generation framework designed to integrate AI Foundation Models into traditional Numerical Weather Prediction (NWP) and Data Assimilation (DA) workflows. The goal of this project is to provide **Data Assimilation engine** based on JEDI and to bridge it seamlessly with **Dynamical Forecast Systems** (Bharat, Mithuna) as well as cutting-edge **AI Foundation Models** (GraphCast, Pangu-Weather, etc.).


![unnamed](https://github.com/user-attachments/assets/7028f2ae-f08e-4c39-bdf9-46bdbe2d9937)


## 🚀 ***Key Features***

**Modular and Object Oriented Design**

**Seperation of concern**

**Entry Level Data Identity Verification**



## 🛠 Installation
```bash
git clone https://github.com/NCMRWF/aiesda.git
cd aiesda
make install

```
# Package directory structure after installation

```
aiesda_build_2026.1/
├── lib/
│   ├── aiesda/
│   │   ├── __init__.py    (from setup.py build)
│   │   ├── VERSION        (copied manually)
│   │   ├── nml/           (synced assets)
│   │   ├── yaml/          (synced assets)
│   │   ├── pylib/         (synced assets)
│   │   ├── pydic/
│   │   ├── scripts/
│   │   ├── jobs/
│   │   ├── pallets/
│   │   ├── docs/ 
│   │   └── ...
│   └── [site-packages]    (compiled python code)
└───bin/
    ├─── ...
    └─── ...
    
jedi_build_2026.1/
├── lib/
│   ├──
│   └─── ...
└───bin/
    ├─── ...  
    └─── ...
    
```

## 🛠 Management & Automation (Makefile)

The project utilizes a centralized `Makefile` to handle the development lifecycle. This ensures that the source area remains clean and that builds are site-aware (HPC vs. Local).

### ⚙️ Configuration Variables
Set these variables at runtime to override defaults:
* **`SITE`**: Target environment (`docker` [default] or `arunika`).
* **`MSG`**: Custom commit message for releases.

---

## 🚀 Available Commands

<table width="100%">
  <thead>
    <tr>
      <th align="left">Command</th>
      <th align="left">Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>make help</code></td>
      <td>Displays the interactive help menu.</td>
    </tr>
    <tr>
      <td><code>make sync</code></td>
      <td>Pulls latest source. Handles SSH tunnel on <b>elogin</b> nodes.</td>
    </tr>
    <tr>
      <td><code>make install</code></td>
      <td>Builds and installs the package to the "Away" directory.</td>
    </tr>
    <tr>
      <td><code>make clean</code></td>
      <td>Surgically removes the current version and build artifacts.</td>
    </tr>
    <tr>
      <td><code>make update</code></td>
      <td><b>Sync → Clean → Install</b>. The standard daily refresh.</td>
    </tr>
    <tr>
      <td><code>make release</code></td>
      <td><b>Test → Bump Version → Archive</b>. Production push to Git.</td>
    </tr>
    <tr>
      <td><code>make test</code></td>
      <td>Runs the <code>aiesda-dev-cycle-test.sh</code> suite.</td>
    </tr>
  </tbody>
</table>



---

## 📖 Usage Examples

### 1. Daily Development Sync
To synchronize your local environment with the latest remote changes:
```bash
make update SITE=arunika
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

