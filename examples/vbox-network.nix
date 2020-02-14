let
    config = {

    };
in
{
    resources.vboxNetworks.net1 = {
        type = "natnet";
        cidrBlock = "192.168.100.0/24";
    };

    resources.vboxNetworks.net2 = { resources, ... }: {
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
            resources.vboxNetworks.net1
            resources.vboxNetworks.net2
        ];
    };

    node2 = { resources, lib, pkgs, ... }: {
        deployment.targetEnv = "virtualbox";
        deployment.virtualbox.headless = true;
        deployment.virtualbox.networks = [
            resources.vboxNetworks.net2
            resources.vboxNetworks.net1
        ];
    };

    node3 = { resources, lib, pkgs, ... }: {
        deployment.targetEnv = "virtualbox";
        deployment.virtualbox.headless = true;
    };
}
