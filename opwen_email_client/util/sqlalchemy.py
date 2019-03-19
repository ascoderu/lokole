from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.exc import NoResultFound


def create_database(uri: str, base):
    engine = create_engine(uri)

    try:
        base.metadata.create_all(bind=engine)
    except SQLAlchemyError:
        pass

    return engine


def get_or_create(db, model, **model_args):
    try:
        return db.query(model).filter_by(**model_args).one()
    except NoResultFound:
        pass

    created = model(**model_args)
    try:
        db.add(created)
        db.flush()
        return created
    except IntegrityError:
        pass

    db.rollback()
    return db.query(model).filter_by(**model_args).one()


@contextmanager
def session(session_maker, commit: bool = False):
    session_factory = scoped_session(session_maker)
    db = session_factory()

    try:
        yield db
        if commit:
            db.commit()
    except SQLAlchemyError:
        db.rollback()
    finally:
        db.close()
