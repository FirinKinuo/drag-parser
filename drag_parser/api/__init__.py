from fastapi import FastAPI
from fastapi.routing import APIRouter
from starlette.middleware.cors import CORSMiddleware

import project
from drag_parser.settings import config
from drag_parser.api.parser import endpoints as parser_endpoints


api_router = APIRouter(prefix='/api/v1')
api_router.include_router(router=parser_endpoints.router)


def create_application() -> FastAPI:
    application = FastAPI(
        title="DragParser",
        description=project.DESCRIPTION,
        version=project.VERSION,
        contact={
            'mail': project.EMAIL,
            'telegram': project.TELEGRAM
        },
        debug=config.DEBUG,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(router=api_router)

    return application


app = create_application()
