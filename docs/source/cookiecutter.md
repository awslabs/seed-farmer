# Cookiecutter & Project Templating

The `SeedFarmer CLI` used [CookieCutter](https://cookiecutter.readthedocs.io/en/stable/) to simplify the initialization of new project and modules in existing projects.  


* [Create a New Project](cookiecutter_new_project)
* [Create a New Module](cookiecutter_new_module)

## What is Cookiecutter
Cookiecutter is a command-line utility that creates projects from project templates(known as cookiecutters). The project templates are housed in a git repository where the files, directories, and the content of both, can be templated. All templating is done with Jinja2. The repository contains a `cookiecutter.json` that containes keys:values that will be used by the templating engine when intialized. The initialization can be interactive if you want to override the `cookiecutter.json` values. In non-interactive mode, the values in cookiecutter.json are default.

For example, the `cookiecutter.json` in a repository may look like this:

```
{
  ...
  "project_short_description": "A short description of the module or project.",
  "version": "0.1.0",
  "open_source_license": ["MIT License", "GNU General Public License v3", "Apache Software License 2.0"],
  "python_requires": "3.6",
  "author": "usern",
  ...
}

```
The `setup.py` in the repository may looks like this:
```
...
setuptools.setup(
    version="{{ cookiecutter.version }}",
    description="{{ cookiecutter.project_short_description }}",
    long_description_content_type="text/markdown",
    author="{{ cookiecutter.author }}",
    install_requires=[],
    python_requires="{{ cookiecutter.python_requires }}",
    classifiers=[
        "License :: OSI Approved :: {{ cookiecutter.open_source_license }}",
        "Programming Language :: Python :: {{ cookiecutter.python_requires }}",
    ],
)
```
And when initialized, `setup.py` will look like this:
```
...
setuptools.setup(
    version="0.1.0",
    description="A short description of the module or project.",
    long_description_content_type="text/markdown",
    author="usern",
    install_requires=[],
    python_requires="3.6",
    classifiers=[
        "License :: OSI Approved :: Apache Software License 2.0",
        "Programming Language :: Python :: 3.6",
    ],
)

```

Please take a look at the [Cookiecuter Github](https://github.com/cookiecutter/cookiecutter) for more information, including how to create your own project template.


## SeedFarmer and Cookiecutter
`seedfarmer` integrates the Cookiecutter library right out of the box to create projects and modules. The template repo structure differs for a project and module, and are housed in separate branches in this repo: `init-project` and `init-module`. Those branches are defaults for `seedfarmer init` when using our repo for templating. If you'd like to use another cookiecutter repo for initialization, you can override the template url. Keep in mind, if you do override the template url, make sure you follow the seedfarmer deployment guide; The default template creates some of the structure specific for seedfarmer that won't be in other custom templates.

(cookiecutter_new_project)=
## How to Create a New Project
Verify that you have `seedfarmer` installed from PyPi. 
```
pip list | grep seed-farmer
```
If not installed, please install:
```
pip install seed-farmer
```
On your local compute resource, pick a directory and add a file named `seedfarmer.yaml` that has the name of your new project.  For example, a new project named `mynewproject` can be seeded via the following:
```bash
echo project: mynewproject > seedfarmer.yaml
```


Now you are ready to create the new project.  

```bash
seedfarmer init project --help
Usage: seedfarmer init project [OPTIONS]

  Initialize a project. Make sure seedfarmer.yaml is present in the same
  location you execute this command!!

Options:
  -t, --template-url TEXT  The template URL. If not specified, the default
                           template repo is `https://github.com/awslabs/seed-
                           farmer`
  --help                   Show this message and exit.
```
This example will create a new directory in your current working directory that contains some bare structure to support development with seedfarmer:

```bash
seedfarmer init project
```
Your project is created and configured to use the `seedfarmer` CLI.

If you want to use a different project template, you can override the default template url. For example:
```
seedfarmer init project -t https://github.com/briggySmalls/cookiecutter-pypackage
```
NOTE: your project template for a new `seedfarmer` project  must contain at least the required project sturcture.


(cookiecutter_new_module)=
## How to Create a New Module
Within a `seedfarmer` project, you can create new modules. Below are the module initialization commands.
```
# seedfarmer init module --help
Usage: seedfarmer init module [OPTIONS]

  Initialize a new module

Options:
  -g, --group-name TEXT    The group the module belongs to. The `group` is
                           created if it doesn't exist
  -m, --module-name TEXT   The module name  [required]
  -t, --template-url TEXT  The template URL. If not specified, the default
                           template repo is `https://github.com/awslabs/seed-
                           farmer`
  --debug / --no-debug     Enable detail logging  [default: no-debug]
  --help                   Show this message and exit.
```

If we look at the root directory structure of this project, you will see a directory called `modules`. All modules created will appear there.

This is the command to create a module named `my-module-name` from the default project template linked above:
```
seedfarmer init module --m my-module-name
```
In the `modules/` directory, there will be a new folder called `my-module-name`. 

Grouping of modules is also supported and stongly recommended. You can have `group`, which is just a parent directory under `modules/` that can contain multiple modules. 

Here is an example that would create the directory structure `../modules/analytics/athena/`:

```
seedfarmer init module -g analytics -m athena
```

Nested grouping is also supported. An example that would create the directory structure `../modules/analytics/streaming/kinesis`:

```
seedfarmer init module -g "analytics/streaming" -m kinesis
```

If you want to use a different module template, you can override the default template url. For example:
```
seedfarmer init module -m my-module-name -t https://github.com/briggySmalls/cookiecutter-pypackage
```
NOTE: your project template for modules must contain at least the required files for a `seedfarmer` module.

