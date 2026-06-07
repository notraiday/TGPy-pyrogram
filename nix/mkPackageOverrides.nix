{ pkgs }:
self: super: {
  tgcrypto = super.buildPythonPackage (finalAttrs: {
    pname = "TgCrypto";
    version = "1.2.5";
    format = "setuptools";

    src = pkgs.fetchPypi {
      inherit (finalAttrs) pname version;
      hash = "sha256-m8LKxvuaEu9bCPPdUAF0/jdNibZgzOmB9X4xOFWctoI=";
    };

    pythonImportsCheck = [ "tgcrypto" ];

    meta = {
      description = "Fast and portable cryptography extension for Telegram clients";
      homepage = "https://github.com/pyrogram/tgcrypto";
      license = pkgs.lib.licenses.lgpl3Only;
    };
  });

  python-socks = super.buildPythonPackage (finalAttrs: {
    pname = "python-socks";
    version = "2.5.3";
    format = "wheel";

    src = pkgs.fetchPypi {
      pname = "python_socks";
      inherit (finalAttrs) version;
      format = "wheel";
      dist = "py3";
      python = "py3";
      hash = "sha256-a8Qo0OGfgEPnuPvIrzNBfmkCOL2MnB6SFYcawYxhNq0=";
    };

    pythonImportsCheck = [ "python_socks" ];

    meta = {
      description = "Core proxy client functionality for Python";
      homepage = "https://github.com/romis2012/python-socks";
      license = pkgs.lib.licenses.asl20;
    };
  });

  kurigram = super.buildPythonPackage (finalAttrs: {
    pname = "kurigram";
    version = "2.2.23";
    format = "wheel";

    src = pkgs.fetchPypi {
      inherit (finalAttrs) pname version;
      format = "wheel";
      dist = "py3";
      python = "py3";
      hash = "sha256-OlgGx2rND4/dnNHi9l+Exh+LJlBonHSBxQNaitJgItk=";
    };

    dependencies = [
      self.pyaes
      self.python-socks
    ];

    pythonImportsCheck = [ "pyrogram" ];

    meta = {
      description = "Telegram MTProto API framework, forked from Pyrogram";
      homepage = "https://github.com/KurimuzonAkuma/pyrogram";
      license = pkgs.lib.licenses.lgpl3Only;
    };
  });

  mkdocs-git-revision-date-localized-plugin =
    super.mkdocs-git-revision-date-localized-plugin.overrideAttrs
      (old: {
        pyproject = true;
        format = null;

        dependencies = old.propagatedBuildInputs ++ [ super.setuptools-scm ];
      });
}
