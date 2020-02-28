{ config, lib, pkgs, uuid, name, ... }:

with lib;
with import <nixops/lib.nix> lib;

let
    toMachineName = m: if builtins.isString m then m else m._name;
in
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
            example = ''
              # As an attrset
              {
                "192.168.56.10" = "node1";
                "192.168.56.11" = "node2";
                ...
              }
              # Or as a list
              [
                { address = "192.168.56.10"; machine = "node1"; }
                { address = "192.168.56.11"; machine = "node2"; }
                ...
              ]
            '';
            default = [];
            description = "The list of machine to IPv4 address bindings for fixing IP address of the machine in the network";
            apply = a: if builtins.isAttrs a then mapAttrs (k: toMachineName) a else a;
            type = with types; either attrs (listOf (submodule {
                options = {
                    address = mkOption {
                        example = "192.168.56.3";
                        type = str;
                        description = ''
                          The IPv4 address assigned to the machine as static IP.
                          The static IP must be a non-reserved IP address.
                        '';
                    };
                    machine = mkOption {
                        type = either str (resource "machine");
                        apply = toMachineName;
                        description = "The name of the machine in the network";
                    };
                };
            }));
        };
    };

    config = {
        _type = "virtualbox-network";
    };
}
