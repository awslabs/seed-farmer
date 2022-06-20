import setuptools

with open("README.md") as fp:
    long_description = fp.read()

setuptools.setup(
    version="{{ cookiecutter.version }}",
    description="{{ cookiecutter.project_short_description }}",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="{{ cookiecutter.author }}",
    install_requires=[
        "aws-cdk-lib==2.20.0",
    ],
    python_requires=">={{ cookiecutter.python_requires }}",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: {{ cookiecutter.open_source_license }}",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: {{ cookiecutter.python_requires }}",
        "Typing :: Typed",
    ],
)
