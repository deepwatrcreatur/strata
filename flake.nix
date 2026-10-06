{
  description = "A fast, keyboard-first file manager for Linux, packaged for NixOS";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachSystem [ "x86_64-linux" "aarch64-linux" ] (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        strata = pkgs.callPackage ./package.nix { };
      in
      {
        packages = {
          default = strata;
          strata = strata;
        };

        apps.default = {
          type = "app";
          program = "${strata}/bin/strata";
        };
      }
    )
    // {
      nixosModules = {
        default = self.nixosModules.strata;
        strata =
          { config, pkgs, lib, ... }:
          let
            cfg = config.programs.strata;
          in
          {
            options.programs.strata = {
              enable = lib.mkEnableOption "Strata file manager";
              package = lib.mkOption {
                type = lib.types.package;
                default = self.packages.${pkgs.stdenv.hostPlatform.system}.strata;
                description = "The Strata package to install.";
              };
              defaultFileManager = lib.mkOption {
                type = lib.types.bool;
                default = false;
                description = "Whether to configure Strata as default file manager.";
              };
            };

            config = lib.mkIf cfg.enable {
              environment.systemPackages = [ cfg.package ];
              xdg.mime.defaultApplications = lib.mkIf cfg.defaultFileManager {
                "inode/directory" = "io.github.lgse.Strata.desktop";
              };
            };
          };
      };

      overlays.default = final: prev: {
        strata = self.packages.${prev.system}.strata;
      };
    };
}
