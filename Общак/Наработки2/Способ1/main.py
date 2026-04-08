#!/usr/bin/env python3
import subprocess
import sys
import os

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def run(script):
    print(f"\nЗапуск {script}...")
    subprocess.run([sys.executable, script])

def main():
    while True:
        clear()
        print("="*60)
        print("🏞️ ЦИФРОВОЙ ДВОЙНИК EC (р. Косьва)")
        print("="*60)
        print("1. Прогноз EC на 72 часа (forecast_ec.py)")
        print("2. Карты цифрового двойника (digital_twin_map.py)")
        print("3. Расчёт экономического ущерба (damage_ec.py)")
        print("4. Оценка качества прогноза (evaluate_ec.py)")
        print("5. Симулятор IoT-датчика (iot_simulator.py)")
        print("0. Выход")
        print("-"*60)
        choice = input("Выберите действие: ").strip()
        if choice == '1':
            run('forecast_ec.py')
        elif choice == '2':
            run('digital_twin_map.py')
        elif choice == '3':
            run('damage_ec.py')
        elif choice == '4':
            run('evaluate_ec.py')
        elif choice == '5':
            run('iot_simulator.py')
        elif choice == '0':
            break
        else:
            print("Неверный ввод")
        input("Нажмите Enter...")

if __name__ == "__main__":
    main()