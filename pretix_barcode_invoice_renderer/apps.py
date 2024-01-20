from django.utils.translation import gettext_lazy

from . import __version__

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")


class PluginApp(PluginConfig):
    default = True
    name = "pretix_barcode_invoice_renderer"
    verbose_name = "Barcode Invoice Renderer (DPSG Würzburg)"

    class PretixPluginMeta:
        name = gettext_lazy("Barcode Invoice Renderer")
        author = "DPSG Würzburg"
        description = gettext_lazy("Invoices with created barcode")
        visible = True
        version = __version__
        category = "CUSTOMIZATION"
        compatibility = "pretix>=2.7.0"

    def ready(self):
        from . import signals  # NOQA
