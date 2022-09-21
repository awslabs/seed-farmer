# Building docs

To rebuild the documentation:

```bash
cd docs/
make clean
make html
```

these python libraries need to be installed in the virtual env:
```bash
pip install sphinx myst_parser sphinx-autoapi sphinx_rtd_theme docutils==0.15 seed-farmer
```