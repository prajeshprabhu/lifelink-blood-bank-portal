"""Initialize the MySQL schema and administrator account."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import initialize_schema
from utils.authentication import initialize_admin


def main():
    initialize_schema()
    initialize_admin()
    print("Database and administrator initialized.")


if __name__ == "__main__":
    main()
