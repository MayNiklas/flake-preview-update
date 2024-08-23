{

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "aarch64-darwin" "aarch64-linux" "x86_64-darwin" "x86_64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      nixpkgsFor = forAllSystems (system:
        import nixpkgs {
          inherit system;
          overlays = [ ];
        });
    in
    {

      formatter = forAllSystems (system: nixpkgsFor.${system}.nixpkgs-fmt);

      devShells = forAllSystems (system: {
        default = let flake_preview_update = self.packages.${system}.flake_preview_update; in
          nixpkgsFor.${system}.callPackage
            ({ mkShell, python3, ... }:
              mkShell {
                buildInputs =
                  flake_preview_update.buildInputs ++ [
                    (python3.withPackages (p: with p; [ ] ++
                    flake_preview_update.nativeBuildInputs))
                  ];
              })
            { };
      });

      packages = forAllSystems (system:
        let pkgs = nixpkgsFor.${system}; in {
          default = self.packages.${system}.flake_preview_update;
          flake_preview_update = pkgs.callPackage
            ({ lib, python3 }:
              python3.pkgs.buildPythonApplication {
                pname = "flake_preview_update";
                version = "1.0.0";
                pyproject = true;
                src = self;
                nativeBuildInputs = with python3.pkgs; [ setuptools ];
                buildInputs = with pkgs; [ git nix ];
                pythonImportsCheck = [ "flake_preview_update" ];
                meta = with lib; {
                  description = "Get infos before updating a flake";
                  homepage = "https://github.com/MayNiklas/flake-preview-update";
                  maintainers = with maintainers; [ MayNiklas ];
                  mainProgram = "flake_preview_update";
                };
              })
            { };
        });

    };
}
