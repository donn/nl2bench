{
  click,
  libparse,
  black,
  lib,
  nix-gitignore,
  buildPythonPackage,
  poetry-core,
  setuptools,
  frozendict,
  pytest,
  coverage,
  yosys,
  quaigh,
  antlr4_9,
  antlr4_9-runtime,
}:
  buildPythonPackage {
    name = "nl2bench";
    version = (builtins.fromTOML (builtins.readFile ./pyproject.toml)).tool.poetry.version;
    format = "pyproject";

    src = nix-gitignore.gitignoreSourcePure ./.gitignore ./.;

    nativeBuildInputs = [
      poetry-core
      antlr4_9
    ];

    propagatedBuildInputs = [
      antlr4_9-runtime
      click
      libparse
      frozendict
      yosys.pyosys
    ];

    nativeCheckInputs = [
      pytest
      black
      quaigh
    ];

    preBuild = "make parsers";
    checkPhase = "pytest";

    meta = {
      mainProgram = "nl2bench";
    };
  }
