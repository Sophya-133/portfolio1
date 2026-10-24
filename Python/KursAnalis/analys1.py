
volume_data = int(input("Введите объем данных: "))


def formula_limit_volume_data(volume_data):
    time_processing = 10 * 60 + (5 * volume_data) / 100  
    errors = 5 + (volume_data / 1000)  
    cost_errors = 100 + (volume_data * 0.1)  
    limit_volume_data = volume_data * time_processing * errors / cost_errors
    return limit_volume_data


def formula_limit_interface(volume_data):
    interface_system = 6 / 10 + (volume_data / 1000)  
    errors_interface = 3 + (volume_data / 10000)  
    cost_errors_interface = 50 + (volume_data * 0.01)  
    limit_interface = interface_system * errors_interface / cost_errors_interface
    return limit_interface


def formula_limit_time_processing(volume_data):
    errors = 5 + (volume_data / 1000)  
    cost_errors = 100 + (volume_data * 0.1)  
    limit_time_processing = volume_data * errors / cost_errors
    return limit_time_processing


def formula_limit_errors(volume_data):
    time_processing = 10 * 60 + (5 * volume_data) / 100  
    cost_errors = 100 + (volume_data * 0.1)  
    limit_errors = volume_data * time_processing / cost_errors
    return limit_errors

def test_limit_volume_data(volume_data):
    time_processing = 10 * 60 + (5 * volume_data) / 100  
    errors = 5 + (volume_data / 1000) 
    cost_errors = 100 + (volume_data * 0.1)  
    limit_volume_data = volume_data * time_processing * errors / cost_errors
    return limit_volume_data


def test_limit_interface(volume_data):
    interface_system = 6 / 10 + (volume_data / 1000) 
    errors_interface = 3 + (volume_data / 10000)  
    cost_errors_interface = 50 + (volume_data * 0.01)  
    limit_interface = interface_system * errors_interface / cost_errors_interface
    return limit_interface

def test_limit_time_processing(volume_data):
    errors = 5 + (volume_data / 1000) 
    cost_errors = 100 + (volume_data * 0.1)  
    limit_time_processing = volume_data * errors / cost_errors
    return limit_time_processing

def test_limit_errors(volume_data):
    time_processing = 10 * 60 + (5 * volume_data) / 100  
    cost_errors = 100 + (volume_data * 0.1)  
    limit_errors = volume_data * time_processing / cost_errors
    return limit_errors

if __name__ == "__main__":
    print("Испытание 1: Ограничение по объему данных")
    print("Результат:", test_limit_volume_data(volume_data))
    print("\nИспытание 2: Недостатки по интерфейсу")
    print("Результат:", test_limit_interface(volume_data))
    print("\nИспытание 3: Ограничение по времени обработки")
    print("Результат:", test_limit_time_processing(volume_data))
    print("\nИспытание 4: Недостатки по ошибкам")
    print("Результат:", test_limit_errors(volume_data))
