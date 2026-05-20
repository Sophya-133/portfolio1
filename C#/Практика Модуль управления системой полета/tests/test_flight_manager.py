# tests/test_flight_manager.py
import unittest
from datetime import datetime
from models.flight import Flight, FlightStatus
from services.flight_manager import FlightManager

class TestFlightManager(unittest.TestCase):
    def setUp(self):
        self.fm = FlightManager()
        self.flight = Flight("SU123", "Москва", "Сочи",
                             datetime(2026, 1, 10, 10, 0),
                             FlightStatus.SCHEDULED)

    def test_add_flight(self):
        self.fm.add_flight(self.flight)
        self.assertIn(self.flight, self.fm.flights)

    def test_remove_flight(self):
        self.fm.add_flight(self.flight)
        self.fm.remove_flight("SU123")
        self.assertNotIn(self.flight, self.fm.flights)

    def test_find_flight(self):
        self.fm.add_flight(self.flight)
        found = self.fm.find_flight_by_number("SU123")
        self.assertEqual(found, self.flight)

if __name__ == '__main__':
    unittest.main()
