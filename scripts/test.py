import aiesda

# If you added the import to __init__.py, you can access aidaconf directly:
config = aiesda.AIESDAConfig() 
print(f"Loaded version: {aiesda.__version__}")
print(f"Namelists found at: {os.environ['AIESDA_NML']}")
