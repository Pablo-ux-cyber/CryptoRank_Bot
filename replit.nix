{pkgs}: {
  deps = [
    pkgs.chromedriver
    pkgs.chromium
    pkgs.zip
    pkgs.geckodriver
    pkgs.postgresql
    pkgs.openssl
  ];
}
