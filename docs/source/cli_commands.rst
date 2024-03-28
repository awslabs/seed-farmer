
####################################
CLI (Command Line Interface)
####################################

The seedfarmer CLI provides the primary way to interface with the orchestration framework that manages a deploymement with AWS CodeSeeder. 
It is used by CICD pipelines and individual users to:
 - deploy code (modules) via a deployment and manifest
 - fetch metadata related to currently deployed modules
 - destroy deployments
 - apply changes to deployments (via a GitOps model)

-------------------
HTTP Proxy Support
-------------------

SeedFarmer does support the use of an HTTP-Proxy.  It is invoked via setting an environment variable in the context of where the CLI is being invoked.  SeedFarmer always leverages HTTPS for its boto3 invocations, so be sure to set the proper parameter.

The parameter we recognize is `HTTPS_PROXY` .  To set it for your runtime, you can do the folllowing (prior to invoking the CLI):

``export HTTPS_PROXY=https://<server>:<port>``

For example, my server DNS is `mygreatserver.com` and is listening on port `8899` 

``export HTTPS_PROXY=http://mygreatserver.com:8899``

In the above example, you will notice that my proxy is NOT over HTTPS....but the `HTTPS_PROXY` variable is being set.  This is correct, as SeedFarmer is leverging HTTPS for is invocation, regardless of your proxy configuration (it is up to you to determine the proper endpoint).

NOTE: if you run the SeedFarmer CLI with the `--debug` flag, you can see what the proxy is being configured for:

``[2023-05-11 12:54:48,392 | DEBUG | _service_utils.py: 32 | MainThread ] Proxies Configured: {'http': None, 'https': 'http://mygreatserver:8899'}``

-------------------
Summary of Commands
-------------------

..
  main commands

.. click:: seedfarmer.__main__:apply
   :prog: seedfarmer apply
   :nested: full

.. click:: seedfarmer.__main__:destroy
   :prog: seedfarmer destroy
   :nested: full

..
  list commands
.. click:: seedfarmer.cli_groups._list_group:list_dependencies
   :prog: seedfarmer list dependencies
   :nested: full

.. click:: seedfarmer.cli_groups._list_group:list_deployspec    
    :prog: seedfarmer list deployspec
    :nested: full
.. click:: seedfarmer.cli_groups._list_group:list_module_metadata
    :prog: seedfarmer list moduledata
    :nested: full
.. click:: seedfarmer.cli_groups._list_group:list_all_module_metadata 
    :prog: seedfarmer list allmoduledata
    :nested: full
.. click:: seedfarmer.cli_groups._list_group:list_modules 
    :prog: seedfarmer list modules
    :nested: full
.. click:: seedfarmer.cli_groups._list_group:list_deployments 
    :prog: seedfarmer list deployments
    :nested: full
.. click:: seedfarmer.cli_groups._list_group:list_build_env_params 
    :prog: seedfarmer list buildparams 
    :nested: full  

..
  bootstrap commands
  
  
.. click:: seedfarmer.cli_groups._bootstrap_group:bootstrap_toolchain 
    :prog: seedfarmer bootstrap toolchain
    :nested: full  

.. click:: seedfarmer.cli_groups._bootstrap_group:bootstrap_target 
    :prog: seedfarmer bootstrap target
    :nested: full  

..
  init commands

.. click:: seedfarmer.cli_groups._init_group:init_module
    :prog: seedfarmer init module
    :nested: full

.. click:: seedfarmer.cli_groups._init_group:init_project
    :prog: seedfarmer init project
    :nested: full  

..
  project commands
  
.. click:: seedfarmer.cli_groups._project_group:policy_synth
    :prog: seedfarmer projectpolicy synth
    :nested: full  
  
..
  metadata commands
.. click:: seedfarmer.cli_groups._manage_metadata_group:convert_cdkexports
    :prog: seedfarmer metadata convert
    :nested: full  
   

.. click:: seedfarmer.cli_groups._manage_metadata_group:add
    :prog: seedfarmer metadata add
    :nested: full  

.. click:: seedfarmer.cli_groups._manage_metadata_group:depmod
    :prog: seedfarmer metadata depmod
    :nested: full  

.. click:: seedfarmer.cli_groups._manage_metadata_group:param_value
    :prog: seedfarmer metadata paramvalue
    :nested: full  


.. 
  remove commands
.. click:: seedfarmer.cli_groups._remove_group:remove_module_data
    :prog: seedfarmer remove moduledata
    :nested: full  


.. 
  store commands
.. click:: seedfarmer.cli_groups._store_group:store_deployspec
    :prog: seedfarmer store deployspec
    :nested: full

.. click:: seedfarmer.cli_groups._store_group:store_module_metadata
    :prog: seedfarmer store moduledata
    :nested: full  

.. click:: seedfarmer.cli_groups._store_group:store_module_md5
    :prog: seedfarmer store md5
    :nested: full  