{
  config_exporters = { optionalAttrs, lib, ... }: [
    (config :
    { virtualbox =
      optionalAttrs (config.deployment.targetEnv == "virtualbox")
        (config.deployment.virtualbox
        //
        { disks = lib.mapAttrs (n: v: v //
          { baseImage =
            if lib.isDerivation v.baseImage then "drv"
            else toString v.baseImage;
          }) config.deployment.virtualbox.disks;
        });
      })
  ];
  options = [
    ./virtualbox.nix
  ];
  resources = { ... }: {};
}
