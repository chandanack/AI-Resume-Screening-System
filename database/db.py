import pymysql


def get_connection():
    connection = pymysql.connect(
        host="localhost",
        user="root",
        password="Chandana@2026",
        database="resume_screening"
    )

    return connection