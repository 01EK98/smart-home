from sanic import BadRequest, Request, Sanic
from sanic.response import redirect
from sanic.views import HTTPMethodView
from tortoise.transactions import atomic

from ..form_helpers import get_formdata
from ..forms import BulbForm
from ..models import Bulb, Bulb_Py
from . import Page, PageContext


def create_view(app: Sanic) -> None:
    class BulbView(HTTPMethodView):
        decorators = [atomic()]
        template_path = "views/bulbs/:id/get.html"

        @classmethod
        def page(cls, id: str):
            if id == "new":
                return Page(
                    name="bulb",
                    path="/bulbs/new",
                    title="Dodaj Żarówkę",
                    template_path=cls.template_path,
                )
            else:
                id_ = int(id)
                return Page(
                    name="bulb",
                    path=f"/bulbs/${id_}",
                    title=f"Żarówka #${id_}",
                    template_path=cls.template_path,
                )

        @app.ext.template(template_path)
        async def get(self, request: Request, id: str):
            context = PageContext(current_page=self.page(id)).model_dump()
            if id == "new":
                context["new"] = True
            else:
                id_ = int(id)
                bulb_record = await Bulb.get(id=id_)
                bulb = (await Bulb_Py.from_tortoise_orm(bulb_record)).model_dump()
                context["bulb"] = bulb

            return {**context, "form": BulbForm()}

        async def post(self, request: Request, id: str):
            form = BulbForm(get_formdata(request))
            if form.validate():
                await Bulb.create(
                    name=form.name.data,
                    ip=form.ip_address.data,
                )
                return redirect(app.url_for("bulbs"), status=303)
            if form.errors:
                raise BadRequest(str(form.errors.items()))

    app.add_route(BulbView.as_view(), "/bulb/<id:strorempty>", name="bulb")
