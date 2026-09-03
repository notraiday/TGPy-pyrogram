{
  system ? builtins.currentSystem,
  inputs ? import ./nix/mkInputs.nix { },

  pkgs ? import inputs.nixpkgs { inherit system; },
  lib ? pkgs.lib,
  pyproject-nix ? import inputs.pyproject-nix { inherit lib; },
  project ? pyproject-nix.lib.project.loadPyproject {
    pyproject = builtins.fromTOML (builtins.readFile ./pyproject.toml);
  },
  withPackages ? ps: [ ],
}:
let
  python = pkgs.python314.override {
    packageOverrides = import ./nix/mkPackageOverrides.nix { inherit pkgs; };
  };
  packageAttrsNoPackages = import ./nix/mkPackageAttrs.nix {
    inherit project;
    inherit pkgs python;
  };
  packageAttrs = packageAttrsNoPackages // {
    propagatedBuildInputs =
      (packageAttrsNoPackages.propagatedBuildInputs or [ ]) ++ (withPackages python.pkgs);
  };
in
{
  package = python.pkgs.buildPythonPackage packageAttrs;
  shell = pkgs.mkShell {
    packages = [
      python
      pkgs.uv
      pkgs.cairo
      pkgs.gcc
    ];

    LD_LIBRARY_PATH = lib.makeLibraryPath [ pkgs.cairo ];
    UV_PYTHON = "${python}/bin/python";
    UV_PYTHON_DOWNLOADS = "never";
  };
}
