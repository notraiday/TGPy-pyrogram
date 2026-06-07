{
  system ? builtins.currentSystem,
  inputs ? import ./nix/mkInputs.nix { },

  pkgs ? import inputs.nixpkgs { inherit system; },
  lib ? pkgs.lib,
  pyproject-nix ? import inputs.pyproject-nix { inherit lib; },
  project ? pyproject-nix.lib.project.loadPyproject {
    pyproject = lib.pipe ./pyproject.toml [
      lib.readFile
      (lib.replaceStrings [ "cryptg-anyos" ] [ "cryptg" ])
      builtins.fromTOML
    ];
  },
  withPackages ? ps: [ ],
}:
let
  python = pkgs.python314.override {
    packageOverrides = import ./nix/mkPackageOverrides.nix { inherit pkgs; };
  };
  uvPinned =
    let
      version = "0.11.19";
      targets = {
        x86_64-linux = {
          target = "x86_64-unknown-linux-musl";
          hash = "sha256-zPTdvVv8H9XtXpTom0dc/SHVM9018gJAF+Iyw8viySk=";
        };
        aarch64-linux = {
          target = "aarch64-unknown-linux-musl";
          hash = "sha256-OaBw0e12Nwyd0MwkHjKYWOSkwCEyQQEKjAWDmoLQRi8=";
        };
        x86_64-darwin = {
          target = "x86_64-apple-darwin";
          hash = "sha256-qQi8bSy/nOQ7UrOEOPb4dc5ysKXMArksIY+2Oo6I0Ik=";
        };
        aarch64-darwin = {
          target = "aarch64-apple-darwin";
          hash = "sha256-fvstzrY1Nxw+JBLrah4y2/mul4jjhVhhuyFWwmguM/g=";
        };
      };
      target = targets.${system};
    in
    pkgs.stdenvNoCC.mkDerivation {
      pname = "uv";
      inherit version;

      src = pkgs.fetchzip {
        url = "https://github.com/astral-sh/uv/releases/download/${version}/uv-${target.target}.tar.gz";
        inherit (target) hash;
      };

      installPhase = ''
        runHook preInstall
        install -Dm755 uv -t $out/bin
        install -Dm755 uvx -t $out/bin
        runHook postInstall
      '';
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
      uvPinned
      pkgs.gcc
      pkgs.gnumake
      pkgs.cargo
      pkgs.rustc
    ];

    UV_PYTHON = "${python}/bin/python";
    UV_PYTHON_DOWNLOADS = "never";
  };
}
