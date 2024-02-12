from sanic import BadRequest, Request, Sanic, json
from sanic.response import redirect
from sanic.views import HTTPMethodView
from sanic_ext import render
from tortoise.transactions import atomic

from ... import Page, BaseContext
from ....forms.helpers import get_formdata
from ....forms.room import RoomForm
from ....models.room import Room


def create_view(app: Sanic) -> None:
    class RoomView(HTTPMethodView):
        decorators = [atomic()]
        template_path = "views/rooms/:id/get.html"

        @classmethod
        def page(cls, id: str):
            if id == "new":
                return Page(
                    name="RoomView",
                    title="Dodaj Pokój",
                    template_path=cls.template_path,
                )
            else:
                id_ = int(id)
                return Page(
                    name="RoomView",
                    title=f"Pokój #{id_}",
                    template_path=cls.template_path,
                )

        async def get(self, request: Request, id: str):
            context = BaseContext(app=app, current_page=self.page(id)).model_dump()
            form = RoomForm()
            if id == "new":
                context["new"] = True
            else:
                id_ = int(id)
                room = await Room.get(id=id_)
                form.name.default = room.name
                form.description.default = room.description
                form.process()
                context["room"] = room

            return render(self.template_path, context=dict(form=form, **context))

        @staticmethod
        async def post(request: Request, id: str):
            form = RoomForm(get_formdata(request))
            if form.validate():
                await Room.create(
                    name=form.name.data,
                    description=form.description.data,
                )
                return redirect(app.url_for("RoomsView"), status=303)
            if form.errors:
                raise BadRequest(str(form.errors.items()))

        @staticmethod
        async def patch(request: Request, id: str):
            form = RoomForm(get_formdata(request))
            if form.validate():
                await Room.filter(id=id).update(
                    name=form.name.data,
                    description=form.description.data,
                )
                return redirect(app.url_for("RoomsView"), status=303)
            if form.errors:
                raise BadRequest(str(form.errors.items()))

    async def toggle_room_state(request: Request, id: int):
        # TODO: this is outdated now, make consistent with other forms
        previous_state = request.form.get("room_state_value")
        updated_state = request.form.get("room_state", default=None)
        bulb_state = None

        if previous_state is not None and updated_state is None:
            bulb_state = not previous_state
        if previous_state == "False" and updated_state is not None:
            bulb_state = True

        room = await Room.get(id=id).prefetch_related("bulbs")
        await room.toggle_state(bulb_state)

        return await render(
            "views/rooms/room-state-toggle-form.html",
            context=dict(room=room),
        )

    async def change_room_brightness(request: Request, id: int):
        room = await Room.get(id=id).prefetch_related("bulbs")
        await room.change_brightness(int(request.form.get("group_brightness")))

        return await render(
            "views/rooms/room-brightness-form.html",
            context=dict(room=room),
        )

    async def room_bulbs_state(request: Request, id: int):
        room = await Room.get(id=id).prefetch_related("bulbs")
        await room.assign_room_state()

        return await render(
            "views/rooms/room-state-toggle-form.html",
            context=dict(room=room),
        )

    async def room_bulbs_brightness(request: Request, id: int):
        room = await Room.get(id=id).prefetch_related("bulbs")
        await room.assign_room_brightness()

        return await render(
            "views/rooms/room-brightness-form.html",
            context=dict(room=room),
        )

    async def room_bulbs_temp_name(request: Request, id: int):
        room = await Room.get(id=id).prefetch_related("bulbs")
        temp_name = request.args.get("temp_name")
        await room.set_room_temp_by_name(temp_name)

        return json(
            {
                "temp_name": temp_name,
            },
            headers={"HX-Trigger": f"reloadRoom{room.id}BulbsBrightness"},
        )

    app.add_route(RoomView.as_view(), "/rooms/<id:strorempty>")

    app.add_route(
        toggle_room_state,
        "rooms/<id:int>/toggle-state",
        methods=["POST"],
    )
    app.add_route(
        change_room_brightness,
        "rooms/<id:int>/change-brightness",
        methods=["POST"],
    )
    app.add_route(
        room_bulbs_temp_name,
        "rooms/<id:int>/bulbs-temp-name",
        methods=["POST"],
    )

    app.add_route(
        room_bulbs_state,
        "rooms/<id:int>/bulbs-state",
        methods=["GET"],
    )
    app.add_route(
        room_bulbs_brightness,
        "rooms/<id:int>/bulbs-brightness",
        methods=["GET"],
    )
