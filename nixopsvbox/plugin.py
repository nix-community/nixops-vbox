import os.path
import nixops.plugins
from nixops.plugins import Plugin


class NixopsVboxPlugin(Plugin):
    @staticmethod
    def nixexprs():
        return [os.path.dirname(os.path.abspath(__file__)) + "/nix"]

    @staticmethod
    def load():
        return [
            "nixopsvbox.backends.virtualbox",
        ]


@nixops.plugins.hookimpl
def plugin():
    return NixopsVboxPlugin()
