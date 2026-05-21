from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base

Base = declarative_base()
_SessionFactory = None
_engine = None

def init_db(db_url: str = "sqlite:///data/app.db"):
    global _engine, _SessionFactory
    _engine = create_engine(db_url, connect_args={"check_same_thread": False})
    _SessionFactory = scoped_session(sessionmaker(bind=_engine))
    return _engine

def get_session():
    global _SessionFactory
    if _SessionFactory is None:
        init_db()
    return _SessionFactory()

def create_all(BaseClass=Base, db_url: str = "sqlite:///data/app.db"):
    eng = init_db(db_url)
    BaseClass.metadata.create_all(eng)
