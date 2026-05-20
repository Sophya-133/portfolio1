# main.py
from datetime import datetime
from services.flight_manager import FlightManager
from views.cli_view import run_cli
from models.flight import Flight, FlightStatus

if __name__ == "__main__":
    fm = FlightManager()

    # Добавляем несколько тестовых рейсов
    flights_data = [
        ("SU123", "Москва", "Сочи", datetime(2026, 1, 10, 10, 0), FlightStatus.SCHEDULED),
        ("AFL456", "Санкт-Петербург", "Новосибирск", datetime(2026, 1, 10, 12, 30), FlightStatus.DELAYED),
        ("TK789", "Казань", "Анапа", datetime(2026, 1, 10, 14, 15), FlightStatus.SCHEDULED),
        ("GH321", "Уфа", "Симферополь", datetime(2026, 1, 10, 16, 45), FlightStatus.IN_AIR),
        ("MN654", "Екатеринбург", "Сочи", datetime(2026, 1, 10, 18, 0), FlightStatus.DELAYED),
    ]

    for code, dep, arr, dt, status in flights_data:
        flight = Flight(code, dep, arr, dt, status)
        fm.add_flight(flight)

    run_cli(fm)

