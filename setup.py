from setuptools import setup, find_packages
import os

def parse_requirements(filename):
    """
    Parses requirements.txt for native Python dependencies.
    Skips JEDI/DA components that are handled by Docker/HPC modules.
    """
    requirements = []
    if os.path.exists(filename):
        with open(filename, "r") as f:
            for line in f:
                # Remove inline comments and whitespace
                line = line.split('#')[0].strip()
                
                # Skip empty lines, block headers, or complex JEDI modules
                if not line or "BLOCK" in line:
                    continue
                
                # Exclude packages provided by JEDI stack (HPC/Docker)
                # This prevents pip from trying to build C++ bindings from scratch
                jedi_libs = ["ufo", "saber", "ioda", "oops", "vader"]
                if any(lib in line.lower() for lib in jedi_libs):
                    continue
                    
                requirements.append(line)
    return requirements

with open("VERSION", "r") as f:
    version = f.read().strip()

setup(
    name="aiesda",
    version=version,
    description="Artificial Intelligence based Earth System Data Assimilation",
    author="gibies",

    # We manually define the core 'aiesda' package and use find_packages 
    # to grab everything inside pylib and pydic.
    packages=["aiesda"] + [f"aiesda.{p}" for p in find_packages(where="pylib")] + \
                          [f"aiesda.{p}" for p in find_packages(where="pydic")] + \
                          ["aiesda.pylib", "aiesda.pydic", "aiesda.scripts"],


    # Mapping namespaces to physical directories
    # Note: "." maps the base 'aiesda' to the current directory for package_data
    package_dir={
        "aiesda": ".", 
        "aiesda.pylib": "pylib",
        "aiesda.pydic": "pydic",
        "aiesda.scripts": "scripts",
    },

    # Ensuring configs are bundled into the versioned build
    package_data={
        "aiesda": ["nml/*.nml", "yaml/*.yml", "yaml/*.yaml", "jobs/*.sh", "palette/*"],
    },
    
    include_package_data=True,
    zip_safe=False,
    install_requires=parse_requirements("requirements.txt"),
    python_requires=">=3.9",

    entry_points={
        "console_scripts": [
            "aiesda-run=aiesda.scripts.main:run",  
            "aiesda-init=aiesda.scripts.setup_env:init",
        ],
    },
)


