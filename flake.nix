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
  nixConfig = {
    extra-substituters = [
      "https://openlane.cachix.org"
    ];
    extra-trusted-public-keys = [
      "openlane.cachix.org-1:qqdwh+QMNGmZAuyeQJTH9ErW57OWSvdtuwfBKdS254E="
    ];
  };

  inputs = {
    nix-eda.url = github:efabless/nix-eda;
    libparse.url = github:efabless/libparse-python;
  };

  inputs.libparse.inputs.nixpkgs.follows = "nix-eda/nixpkgs";

  outputs = {
    self,
    nix-eda,
    libparse,
    ...
  }: {
    # Outputs
    packages =
      nix-eda.forAllSystems {
        current = self;
        withInputs = [libparse];
      } (util:
        with util; let
          self = {
            nl2bench = callPythonPackage ./default.nix {};
            default = self.nl2bench;
          };
        in
          self);
  };
}
