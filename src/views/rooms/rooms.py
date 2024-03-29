from dataclasses import dataclass
from typing import Callable, Coroutine, Any

from dominate.tags import div, section, p, html_tag, small, h3
from sanic import Request, Sanic, HTTPResponse
from sanic.response import html
from sanic.views import HTTPMethodView
from sanic_ext import serializer
from tortoise.transactions import atomic

from src.components.base_page import BasePage
from src.components.breadcrumbs import Breadcrumbs
from src.components.bulb_icon import BulbIcon
from src.components.new_item_button import NewItemButton
from src.components.nothing_here import NothingHere
from src.components.room_brightness_slider import RoomBrightnessSlider
from src.components.room_light_switch import RoomLightSwitch
from src.models.bulb import Bulb
from src.models.room import Room
from src.views import NAVIGATION, Page, BaseContext, ROUTES


@dataclass
class Routes:
    TURN_BULB_ON: str = "turn_bulb_on"
    TURN_BULB_OFF: str = "turn_bulb_off"


def create_view(app: Sanic) -> None:
    class RoomsView(HTTPMethodView):
        decorators = [atomic(), serializer(html)]
        page = Page(
            name="RoomsView",
            title="Pokoje",
        )

        async def get(self, request: Request):
            rooms = await Room.filter(
                # name="Gabinet",
            ).prefetch_related("bulbs")

            base_ctx = BaseContext(app=app, current_page=self.page)
            navbar = base_ctx.app_navbar

            page_content = BasePage(
                navbar,
                div(
                    Breadcrumbs(app, base_ctx.navigation["home"], self.page),
                    class_name="w-full max-w-screen-xl mx-auto p-2",
                ),
                section(
                    div(
                        NewItemButton(href=app.url_for("RoomView", id="new")),
                        class_name="block mx-auto w-full max-w-screen-xl py-6 px-2",
                    ),
                    room_card_grid(rooms, app),
                    class_name="w-full h-full max-w-screen-xl py-6 px-4 mx-auto mx-4",
                ),
                title=self.page.title,
            )

            return page_content.render()

    @serializer(html)
    async def get_bulb_with_state(request: Request, id: int):
        bulb = await Bulb.get(id=id)
        await bulb.assign_wiz_info()
        return BulbIcon(app, bulb).render()

    def change_bulb_state_handler(
        state: bool,
    ) -> Callable[[Request, int], Coroutine[Any, Any, HTTPResponse]]:
        hx_trigger = "change-bulb-state"

        async def handler(request: Request, id: int):
            bulb = await Bulb.get(id=id)
            await bulb.toggle_state(state)
            content = BulbIcon(app, bulb)

            res = html(content.render())
            res.headers.add("HX-Trigger", hx_trigger)

            return res

        return handler

    app.add_route(RoomsView.as_view(), "/rooms")
    app.add_route(
        get_bulb_with_state,
        "bulbs/<id:int>/state",
        name=BulbIcon.route,
    )
    app.add_route(
        change_bulb_state_handler(True), "bulbs/<id:int>/on", name=Routes.TURN_BULB_ON
    )
    app.add_route(
        change_bulb_state_handler(False),
        "bulbs/<id:int>/off",
        name=Routes.TURN_BULB_OFF,
    )

    NAVIGATION["rooms"] = RoomsView.page
    ROUTES[BulbIcon.route] = BulbIcon.route
    ROUTES[Routes.TURN_BULB_ON] = Routes.TURN_BULB_ON
    ROUTES[Routes.TURN_BULB_OFF] = Routes.TURN_BULB_OFF


def room_card_grid(rooms: list[Room], app: Sanic) -> html_tag:
    with div(
        class_name="grid grid-flow-row gap-8 sm:grid-cols-2 md:grid-cols-3 "
        "lg:grid-cols-4"
    ) as div_:
        if len(rooms) == 0:
            NothingHere()
        else:
            for room in rooms:
                room_card(room, app)
    return div_


def room_card(room: Room, app: Sanic) -> html_tag:
    with div(
        id=f"room-{room.id}",
        event_container=True,
        class_name="w-full flex flex-col rounded-xl bg-white border-2 border-gray-100 text-gray-700 shadow-lg",
    ) as div_:
        # Name and description
        with div(class_name="p-4 self-start"):
            p(room.name, class_name="text-lg font-semibold leading-relaxed")
            if room.description:
                small(room.description, class_name="leading-5 text-gray-500 mt-2")
        # Bulbs
        with div(class_name="flex flex-col items-end gap-1 px-6 h-min"):
            for bulb in room.bulbs:
                BulbIcon.lazy_load(app, bulb)

        # Group controls
        with div(
            class_name=f"w-full flex flex-col my-8 px-8 {'border-t pt-4' if room.bulbs else ''} border-gray-500"
        ):
            if room.bulbs:
                with div(class_name="flex flex-col justify-center items-start mb-2"):
                    h3("Steruj wszystkimi", class_name="font-bold")
                with div(
                    class_name="w-full flex flex-col justify-center items-end gap-y-4"
                ):
                    RoomLightSwitch.lazy_load(app, room)
                    RoomBrightnessSlider.lazy_load(app, room)
            # Edit room link
            # with a(
            #         href=app.url_for("RoomView", id=room.id),
            #         class_name="cursor-pointer self-end py-1 px-2 bg-gray-200 rounded-md flex flex-col items-center",
            #         data_ripple_light="true",
            #         data_ripple_dark="true",
            # ):
            #     Icon("mode_edit")
            #     p("Edytuj pokój", class_name="text-xs")
    return div_
