# main.py
from clinic_app import launch_gui
from DB.neo_connection import close

if __name__ == "__main__":
    try:
        launch_gui()
    finally:
        # close driver on exit
        close()
