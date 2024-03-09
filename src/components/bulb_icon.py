from typing import Optional

from dominate.tags import button, p
from dominate.util import raw
from sanic import Sanic

from src.components.material_icons import Icon
from src.models.bulb import Bulb
from src.views import ROUTES


class BulbIcon(button):
    tagname = "button"
    id = "app-bulb-icon"

    def __init__(self, app: Sanic, bulb: Bulb = None, state: Optional[bool] = None) -> None:
        super().__init__()

        self["class"] = "align-middle select-none font-sans font-bold text-center uppercase " \
                        "transition-all disabled:opacity-50 disabled:shadow-none " \
                        "disabled:pointer-events-none text-xs py-3 px-6 rounded-lg bg-gray-900 " \
                        "text-white shadow-md shadow-gray-900/10 hover:shadow-lg hover:shadow-gray-900/20 " \
                        "focus:opacity-[0.85] focus:shadow-none active:opacity-[0.85] active:shadow-none"
        self["type"] = "button"
        self["data-ripple-light"] = "true"
        self["data-ripple-dark"] = "true"
        self["hx-swap"] = "outerHTML"

        with self:
            if state or bulb.wiz_info["state"]:
                Icon(
                    "lightbulb",
                    class_name="material-symbols-rounded"
                )
                self["hx-get"] = app.url_for(ROUTES["turn_bulb_off"], id=bulb.id)
            else:
                Icon(
                    "light_off",
                    class_name="material-symbols-rounded"
                )
                self["hx-get"] = app.url_for(ROUTES["turn_bulb_on"], id=bulb.id)
            p(bulb.name)
            # TODO: trigger script rerun instead with htmx if possible
            raw("""
                <script src="https://unpkg.com/@material-tailwind/html@latest/scripts/ripple.js"></script>
            """)
