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
}
