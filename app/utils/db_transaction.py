import contextlib

from flask import current_app
from pymongo.errors import OperationFailure


@contextlib.contextmanager
def transaction():
    session = current_app.mongodb_client.start_session()
    try:
        with session.start_transaction():
            yield session
    except OperationFailure as e:
        print(f"Transaction operation failed: {e}")
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        raise
    finally:
        session.end_session()
