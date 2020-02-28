let
    config = {

    };
in
{
    resources.virtualboxNetworks.net1 = { resources, ... }: {
        type = "natnetwork";
        cidrBlock = "192.168.100.0/24";
        staticIPs = {
            "192.168.100.11" = resources.machines.node1;
            "192.168.100.12" = "node2";
        };
    };

    resources.virtualboxNetworks.net2 = { resources, ... }: {
        type = "hostonly";
        cidrBlock = "192.168.101.0/24";
        staticIPs = [
            {
                machine = resources.machines.node1;
                address = "192.168.101.10";
            }
        ];
    };

    node1 = { resources, lib, pkgs, ... }: {
        deployment.targetEnv = "virtualbox";
        deployment.virtualbox.headless = true;
        deployment.virtualbox.networks = [
            { "type" = "nat"; }
            resources.virtualboxNetworks.net1
            resources.virtualboxNetworks.net2
        ];
    };

    node2 = { resources, lib, pkgs, ... }: {
        deployment.targetEnv = "virtualbox";
        deployment.virtualbox.headless = true;
        deployment.virtualbox.networks = [
            resources.virtualboxNetworks.net2
            resources.virtualboxNetworks.net1
        ];
    };

    node3 = { resources, lib, pkgs, ... }: {
        deployment.targetEnv = "virtualbox";
        deployment.virtualbox.headless = true;
    };
}
