{
  pkgs,
  project,
  python,
  rev ? null,
}:
let
  postPatch = pkgs.lib.optionalString (rev != null) ''
    substituteInPlace tgpy/version.py \
      --replace-fail "COMMIT_HASH = None" "COMMIT_HASH = \"${rev}\""
  '';
  newAttrs = {
    src = ./..;
    inherit postPatch;
    nativeCheckInputs = [ python.pkgs.pytestCheckHook ];
    pytestFlags = [ "tests" ];
    meta = {
      license = pkgs.lib.licenses.mit;
      homepage = "https://tgpy.dev/";
      pythonImportsCheck = [ "tgpy" ];
      mainProgram = "tgpy";
    };
  };
in
(project.renderers.buildPythonPackage { inherit python; }) // newAttrs
