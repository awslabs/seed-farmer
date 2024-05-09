# Upgrades

This page give indications related to supporting upgrading `seed-farmer` from previous version where changes must be enacted in order to properly use new feature.

This is not an exhaustive list but merely a guide.


## Upgrading to 3.5.0

`seed-farmer` 3.5.0 introduces the use of `pypiMirrorSecret` to support configuring a pypi mirror with credentials (see [Manifests - Mirrors](./manifests.md#mirroroverride)).

If you are currently using an older version of `seed-farmer`, to upgrade you must install the 3.5.0 version from Pypi and then update your current deployments by updating the seedkit in each target account/region mapping via the CLI using the `--update-seedkit` flag.  This is needed only once
```code
seedfarmer apply <manifest-path> --update-seedkit
```

Please see the [CLI references](./cli_commands.rst) for more details