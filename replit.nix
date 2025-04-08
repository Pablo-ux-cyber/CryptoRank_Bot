{pkgs}: {
  deps = [
    pkgs.chromium
    pkgs.geckodriver
    pkgs.postgresql
    pkgs.openssl
  ];
}
