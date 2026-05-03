from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import engine
from .models import Base
from .routers import contracts, clauses, clause_types
from .seed import seed_clause_types


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup
    Base.metadata.create_all(bind=engine)

    # Seed default clause types if the table is empty
    seed_clause_types()

    yield


app = FastAPI(
    title="Contract Clause Tracker",
    description="Upload contracts, label clause types, search and filter.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contracts.router, prefix="/api")
app.include_router(clauses.router,   prefix="/api")
app.include_router(clause_types.router, prefix="/api")