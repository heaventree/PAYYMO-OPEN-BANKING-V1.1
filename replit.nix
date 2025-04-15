{pkgs}: {
  deps = [
    pkgs.rustc
    pkgs.pkg-config
    pkgs.libxcrypt
    pkgs.libiconv
    pkgs.cargo
    pkgs.unzip
    pkgs.zip
    pkgs.jq
    pkgs.postgresql
    pkgs.openssl
  ];
}
