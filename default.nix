{
  lib,
  flake,
  click,
  libparse,
  black,
  nix-gitignore,
  buildPythonPackage,
  poetry-core,
  setuptools,
  frozendict,
  pytest,
  coverage,
  pyosys,
  quaigh,
  antlr4_9,
  antlr4_9-runtime,
  pytestCheckHook,
}:
buildPythonPackage {
  name = "nl2bench";
  version = (builtins.fromTOML (builtins.readFile ./pyproject.toml)).project.version;
  format = "pyproject";

  src = flake;

  nativeBuildInputs = [
    poetry-core
    antlr4_9
  ];

  nativeCheckInputs = [
    pytest
    black
    quaigh
    pytestCheckHook
  ];

  dependencies = [
    antlr4_9-runtime
    click
    libparse
    frozendict
    pyosys
  ];

  doCheck = true; # OoMs in CI

  preBuild = ''
    make parsers
  '';

  meta = {
    description = "converts a subset of the Verilog language commonly used for Netlists to the Bench format";
    mainProgram = "nl2bench";
    license = lib.licenses.asl20;
    platforms = lib.platforms.all;
  };
}
