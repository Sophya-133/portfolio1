# services/flight_manager.py
from typing import List, Optional
from models.flight import Flight, FlightStatus

class FlightManager:
    def __init__(self):
        self.flights: List[Flight] = []

    def add_flight(self, flight: Flight):
        self.flights.append(flight)

    def remove_flight(self, flight_number: str):
        self.flights = [f for f in self.flights if f.flight_number != flight_number]

    def find_flight_by_number(self, flight_number: str) -> Optional[Flight]:
        for flight in self.flights:
            if flight.flight_number == flight_number:
                return flight
        return None

    def get_flights_by_status(self, status: FlightStatus) -> List[Flight]:
        return [f for f in self.flights if f.status == status]

    def list_all_flights(self):
        if not self.flights:
            print("Нет доступных рейсов.")
            return
        for flight in self.flights:
            print(flight.display_info())
