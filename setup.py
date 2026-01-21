from setuptools import setup, find_packages

setup(
    name="aiesda",
    version="0.1.0",
    description="Artificial Intelligence based Earth System Data Assimilation",
    author="gibies",
    # Define the hierarchy
    packages=["aiesda", "aiesda.pylib", "aiesda.pydic", "aiesda.scripts"],

    # Mapping namespaces to physical directories
    package_dir={
        "aiesda": "pylib",          # This makes aiesda/aidaconf.py accessible
        "aiesda.pylib": "pylib",
        "aiesda.pydic": "pydic",
        "aiesda.scripts": "scripts",
    },

    # Ensuring configs are bundled into the versioned build
    package_data={
        "aiesda": ["nml/*.nml", "yaml/*.yml", "jobs/*.sh", "palette/*"],
    },
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "numpy>=1.22.4",
        "torch>=1.12.0",
        "pyyaml>=6.0",
        "xarray",
        "netCDF4"
        "matplotlib>=3.5.0",
        # Note: JEDI/SABER/NCAR components are usually 
        # provided by the HPC environment modules.
    ],
    python_requires=">=3.9",
)

