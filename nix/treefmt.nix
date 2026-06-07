{ inputs, ... }:
{
  imports = [ inputs.treefmt-nix.flakeModule ];

  perSystem =
    { pkgs, lib, ... }:
    {
      treefmt = {
        projectRootFile = "flake.nix";
        programs = {
          nixfmt.enable = true;
          shfmt.enable = true;

          # taplo crashes `nix flake check` on darwin
          taplo.enable = pkgs.stdenv.hostPlatform.isLinux;

          yamlfmt.enable = true;

          prettier.enable = true;
        };

        settings.excludes = [
          "*.md"
          "pyproject.toml"

          "*.png"
          "*.jpg"
          "*.mp4"

          "LICENSE"

          "Dockerfile"
          ".dockerignore"

          ".gitignore"
          "*.lock"
        ]
        ++ lib.optionals pkgs.stdenv.hostPlatform.isDarwin [
          "*.toml"
        ];
      };
    };
}
