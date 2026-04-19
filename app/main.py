from fastapi import FastAPI
from api.routes import translate, rag, source

app = FastAPI(title="JnanaSetu")

app.include_router(translate.router)
app.include_router(rag.router)
app.include_router(source.router)