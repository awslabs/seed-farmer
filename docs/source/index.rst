An `AWS Professional Service <https://aws.amazon.com/professional-services>`_ open source initiative | aws-proserve-opensource@amazon.com


Seed-Farmer
==============
**Seed-Farmer** is an opensource orchestration tool that works with `AWS CodeSeeder <https://github.com/awslabs/aws-codeseeder>`_ and is modeled after `GitOps deployments <https://www.gitops.tech/>`_ .  
It has a CommandLine Interface (CLI) based in Python. 

**Seed-Farmer** leverages modular code deployments (`see modules <module_development.html>`_) leveraging `manifests <manifests.html>`_ and `deployspecs <deployspec.html>`_, keeping track of changes and applying changes as needed / detected.


Architecture
==============
**Seed-Farmer** does not create its own deployments, rather it helps to deploy YOUR modules by acting as the broker between your 
module code and the AWS Cloud via AWS CodeSeeder.


.. image:: _static/SeedFarmer.png
   :alt: Seed-Farmer
=======================================

.. toctree::
   :maxdepth: 3
   :caption: Contents:
   
   reference


   usage

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
