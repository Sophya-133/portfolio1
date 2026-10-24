# views/cli_view.py
from services.flight_manager import FlightManager
from models.flight import Flight, FlightStatus
from datetime import datetime

def run_cli(fm: FlightManager):
    while True:
        print("\n=== Система управления полётами ===")
        print("1. Добавить рейс")
        print("2. Удалить рейс")
        print("3. Просмотреть все рейсы")
        print("4. Найти рейс по номеру")
        print("5. Рейсы по статусу")
        print("6. Выход")

        choice = input("Выберите действие: ")

        if choice == '1':
            try:
                num = input("Номер рейса: ")
                dep = input("Пункт отправления: ")
                dest = input("Пункт назначения: ")
                dt_str = input("Дата и время вылета (ГГГГ-ММ-ДД ЧЧ:ММ): ")
                dt = datetime.fromisoformat(dt_str)
                status = FlightStatus(input("Статус (запланирован/задержан/в воздухе/приземлился): "))
                flight = Flight(num, dep, dest, dt, status)
                fm.add_flight(flight)
                print("✅ Рейс добавлен.")
            except Exception as e:
                print(f"❌ Ошибка при добавлении рейса: {e}")

        elif choice == '2':
            num = input("Введите номер рейса для удаления: ")
            fm.remove_flight(num)
            print("🗑️ Рейс удалён.")

        elif choice == '3':
            fm.list_all_flights()

        elif choice == '4':
            num = input("Введите номер рейса: ")
            flight = fm.find_flight_by_number(num)
            if flight:
                print(flight.display_info())
            else:
                print("🚫 Рейс не найден.")

        elif choice == '5':
            try:
                status_input = input("Введите статус: ").upper()
                status_enum = getattr(FlightStatus, status_input)
                flights = fm.get_flights_by_status(status_enum)
                for f in flights:
                    print(f.display_info())
            except AttributeError:
                print("🚫 Неверный статус.")

        elif choice == '6':
            print("👋 До свидания!")
            break

        else:
            print("🚫 Неверный выбор.")
