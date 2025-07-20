# Adapted from nix-eda
#
# Copyright 2023 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
{
  inputs = {
    nix-eda.url = "github:fossi-foundation/nix-eda";
    quaigh = {
      url = "github:coloquinte/quaigh";
      inputs.nixpkgs.follows = "nix-eda/nixpkgs";
    };
    libparse = {
      url = "github:efabless/libparse-python";
      inputs.nixpkgs.follows = "nix-eda/nixpkgs";
    };
  };

  outputs = {
    self,
    nix-eda,
    libparse,
    quaigh,
    ...
  }: let
    nixpkgs = nix-eda.inputs.nixpkgs;
    lib = nixpkgs.lib;
  in {
    overlays = {
      default = lib.composeManyExtensions [
        # Using quaigh as an overlaigh here requires me to propagate the
        # cargo2nix overlay here too and I can think of about 80 better things
        # to do with my time
        (nix-eda.flakesToOverlay [libparse quaigh])
        (nix-eda.composePythonOverlay (pkgs': pkgs: pypkgs': pypkgs: let
          callPythonPackage = lib.callPackageWith (pkgs' // pypkgs');
        in {
          nl2bench = callPythonPackage ./default.nix {
            flake = self;
          };
        }))
      ];
    };

    legacyPackages = nix-eda.forAllSystems (
      system:
        import nixpkgs {
          inherit system;
          overlays = [nix-eda.overlays.default self.overlays.default];
        }
    );

    # Outputs
    packages = nix-eda.forAllSystems (system: {
      inherit (self.legacyPackages.${system}.python3.pkgs) nl2bench;
      default = self.packages.${system}.nl2bench;
    });
  };
}
