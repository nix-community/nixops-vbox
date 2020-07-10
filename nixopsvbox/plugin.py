import os.path
import nixops.plugins
from nixops.plugins import Plugin


class NixopsVboxPlugin(Plugin):
    @staticmethod
    def nixexprs():
        expr_path = os.path.realpath(
            os.path.dirname(__file__) + "/../../../../share/nix/nixops-vbox"
        )
        if not os.path.exists(expr_path):
            expr_path = os.path.realpath(
                os.path.dirname(__file__) + "/../../../../../share/nix/nixops-vbox"
            )
        if not os.path.exists(expr_path):
            expr_path = os.path.dirname(__file__) + "/../nix"

        return [expr_path]

    @staticmethod
    def load():
        return [
            "nixopsvbox.backends.virtualbox",
        ]


@nixops.plugins.hookimpl
def plugin():
    return NixopsVboxPlugin()
