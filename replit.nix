{pkgs}: {
  deps = [
    pkgs.jq
    pkgs.zip
    pkgs.geckodriver
    pkgs.postgresql
    pkgs.openssl
  ];
}
