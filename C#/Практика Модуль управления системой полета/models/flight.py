
from datetime import datetime
from enum import Enum

class FlightStatus(Enum):
    SCHEDULED = "запланирован"
    DELAYED = "задержан"
    IN_AIR = "в воздухе"
    LANDED = "приземлился"

class Flight:
    def __init__(self, flight_number: str, departure: str, destination: str,
                 departure_time: datetime, status: FlightStatus):
        self.flight_number = flight_number
        self.departure = departure
        self.destination = destination
        self.departure_time = departure_time
        self.status = status

    def display_info(self):
        return (f"Рейс {self.flight_number}: {self.departure} → {self.destination}, "
                f"Вылет: {self.departure_time.strftime('%d.%m.%Y %H:%M')}, "
                f"Статус: {self.status.value}")
