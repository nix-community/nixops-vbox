{
  config_exporters = { optionalAttrs, pkgs, ... }: with pkgs.lib; [
    (config :
    { virtualbox =
      optionalAttrs (config.deployment.targetEnv == "virtualbox")
        (config.deployment.virtualbox
        //
        { disks = mapAttrs (n: v: v //
          { baseImage =
            if isDerivation v.baseImage then "drv"
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
