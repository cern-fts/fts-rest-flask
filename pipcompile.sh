# this assumes the venv is created with --system-site-packages
# so the gfal2-python3 rpm can be used
# here we use --ignore-installed to ensure all other packages are installed in the venv
pip-compile --generate-hashes requirements.in --pip-args '--ignore-installed'
pip-compile --generate-hashes dev-requirements.in --pip-args '--ignore-installed'

