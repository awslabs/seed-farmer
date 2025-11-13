---
title: CLI Commands
---

This page provides a reference for all Seed-Farmer CLI commands.  

::: mkdocs-click
    :module: seedfarmer.__main__
    :command: bootstrap
    :depth: 1
    :list_subcommands: True

::: mkdocs-click
    :module: seedfarmer.__main__
    :command: seedkit
    :depth: 1
    :list_subcommands: True

::: mkdocs-click
    :module: seedfarmer.__main__
    :command: init
    :depth: 1
    :list_subcommands: True

::: mkdocs-click
    :module: seedfarmer.__main__
    :command: apply
    :depth: 1
    :list_subcommands: True

::: mkdocs-click
    :module: seedfarmer.__main__
    :command: destroy
    :depth: 1
    :list_subcommands: True

::: mkdocs-click
    :module: seedfarmer.__main__
    :command: list
    :depth: 1
    :list_subcommands: True

::: mkdocs-click
    :module: seedfarmer.__main__
    :command: projectpolicy
    :depth: 1
    :list_subcommands: True

<br/>

!!! warning
    The _metadata command_ work only within a `deployspec.yaml`

::: mkdocs-click
    :module: seedfarmer.__main__
    :command: metadata
    :depth: 1
    :list_subcommands: True

<br/>

!!! info
    The _taint command_ will mark an individual module for redeploy on next `apply`.

::: mkdocs-click
    :module: seedfarmer.__main__
    :command: taint
    :depth: 1
    :list_subcommands: True

<br/>

!!! warning
    The _remove command_ is meant for SeedFarmer but can be used for iterative development.

::: mkdocs-click
    :module: seedfarmer.__main__
    :command: remove
    :depth: 1
    :list_subcommands: True

<br/>
!!! Danger
    The _store command_ is meant for Seed-Farmer use.
    Only the `deployspec` command may be used to support iterative development

::: mkdocs-click
    :module: seedfarmer.__main__
    :command: store
    :depth: 1
    :list_subcommands: True

<br/>
!!! Danger
    The _bundle command_ is meant for Seed-Farmer use.

::: mkdocs-click
    :module: seedfarmer.__main__
    :command: bundle
    :depth: 1
    :list_subcommands: True
