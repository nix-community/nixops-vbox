{ config, lib, pkgs, uuid, name, ... }:

with lib;
with import <nixops/lib.nix> lib;

rec {
    options = {
        type = mkOption {
            default = "hostonly";
            description = ''
              The type of the VirtualBox network.
              Either NAT network or Host-only network can be specified. Defaults to Host-only Network.
            '';
            type = types.enum [ "natnetwork" "hostonly" ];
        };

        cidrBlock = mkOption {
            example = "192.168.56.0/24";
            description = ''
              The IPv4 CIDR block for the VirtualBox network. The following IP addresses are reserved for the network:
              Network     - The first  address in the IP range, e.g. 192.168.56.0   in 192.168.56.0/24
              Gateway     - The second address in the IP range, e.g. 192.168.56.1   in 192.168.56.0/24
              DHCP Server - The third  address in the IP range, e.g. 192.168.56.2   in 192.168.56.0/24
              Broadcast   - The last   address in the IP range, e.g. 192.168.56.255 in 192.168.56.0/24
            '';
            type = types.str;
        };

        staticIPs = mkOption {
            default = [];
            description = "The list of machine to IPv4 address bindings for fixing IP address of the machine in the network";
            type = with types; listOf (submodule {
                options = {
                    machine = mkOption {
                        type = either str (resource "machine");
                        apply = x: if builtins.isString x then x else x._name;
                        description = "The name of the machine in the network";
                    };
                    address = mkOption {
                        example = "192.168.56.3";
                        type = str;
                        description = ''
                          The IPv4 address assigned to the machine as static IP.
                          The static IP must be a non-reserved IP address.
                        '';
                    };
                };
            });
        };
    };

    config = {
        _type = "vbox-network";
    };
}
