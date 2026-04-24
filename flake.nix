{
  description = "Development shell for apm-registry";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f system);
    in
    {
      devShells = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
          toonCli = pkgs.writeShellApplication {
            name = "toon";
            runtimeInputs = [ pkgs.nodejs_22 ];
            text = ''
              exec npx --yes @toon-format/cli@2.0.1 "$@"
            '';
          };
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              bash
              coreutils
              findutils
              gawk
              git
              gnused
              jq
              nodejs_22
              python3
              ripgrep
              toonCli
            ];

            shellHook = ''
              echo "apm-registry dev shell"
              echo "- JSON tooling: jq"
              echo "- TOON tooling: toon (via pinned @toon-format/cli)"
              echo "- Corpus validation: scripts/validate-security-corpus"
            '';
          };
        }
      );
    };
}
