
from sqlalchemy import text

from app.db.database import engine


def check_database_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("MYSQL CONNECTION: SUCCESS")
            print("DATABASE:", connection.execute(
                text("SELECT DATABASE()")
            ).scalar())
            print("TEST RESULT:", result.scalar())

    except Exception as error:
        print("MYSQL CONNECTION: FAILED")
        print("ERROR:", error)

    finally:
        engine.dispose()


if __name__ == "__main__":
    check_database_connection()
