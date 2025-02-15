{pkgs}: {
  deps = [
    pkgs.rustc
    pkgs.libiconv
    pkgs.cargo
    pkgs.libxcrypt
    pkgs.cairo
    pkgs.postgresql
    pkgs.glibcLocales
  ];
}
