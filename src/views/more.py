from sanic import Request, Sanic
from sanic.views import HTTPMethodView

from ..utils import get_js_file

from . import NAVIGATION, Page, PageContext


def create_view(app: Sanic) -> None:
    class MoreView(HTTPMethodView):
        page = Page(
            name="more",
            path="/more",
            title="Więcej",
            template_path="views/more/get.html",
            js_file=get_js_file("views/more/index.ts"),
        )

        @app.ext.template(page.template_path)
        async def get(self, request: Request):
            return PageContext(current_page=self.page).model_dump()

    app.add_route(MoreView.as_view(), MoreView.page.path, name=MoreView.page.name)
    NAVIGATION["more"] = MoreView.page
