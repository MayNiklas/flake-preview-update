# flake-preview-update

This tool is meant to preview the changes that would be made by running `nix flake update` on a flake.

Systems are build before and after the update and the resulting generations are compared.

The diff is then getting reduced.

## Usage

```sh
nix run 'github:MayNiklas/flake-preview-update' -- --help

usage: flake_preview_update [-h] [--flake_repo FLAKE_REPO] hosts [hosts ...]

Build a host in a flake repository.

positional arguments:
  hosts                 Hosts to build.

options:
  -h, --help            show this help message and exit
  --flake_repo FLAKE_REPO
                        Path to flake repository.
```

## Example

```sh
nix run 'github:MayNiklas/flake-preview-update' -- aida kora

nix run 'github:MayNiklas/flake-preview-update' -- --flake_repo ~/code/github.com/MayNiklas/nixos aida aida kora
```
