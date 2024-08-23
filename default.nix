{
  antlr4_9,
  click,
  libparse,
  black,
  lib,
  nix-gitignore,
  buildPythonPackage,
  poetry-core,
  setuptools,
  pytest,
  coverage,
}: let
  antlr4_9-python3-runtime = buildPythonPackage rec {
    pname = "antlr4-python3-runtime";
    inherit (antlr4_9.runtime.cpp) version src;

    sourceRoot = "source/runtime/Python3";

    doCheck = false;

    meta = with lib; {
      description = "Runtime for ANTLR";
      homepage = "https://www.antlr.org/";
      license = licenses.bsd3;
    };
  };
in
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
      antlr4_9-python3-runtime
      click
      libparse
    ];

    nativeCheckInputs = [
      pytest
      black
    ];

    preBuild = "make parsers";
    checkPhase = "pytest";

    meta = {
      mainProgram = "nl2bench";
    };
  }
