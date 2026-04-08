#!/usr/bin/env python3
import subprocess
import sys
import argparse

def run(script):
    print(f"\n▶️ Запуск {script}...")
    subprocess.run([sys.executable, script])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', default='all', choices=['all','forecast','visualize','damage','evaluate','simulator'])
    args = parser.parse_args()
    if args.mode == 'all':
        run('forecast_ec_model.py')
        run('visualization_ec.py')
        run('damage_assessment_ec.py')
        run('evaluate_forecast_ec.py')
    elif args.mode == 'forecast':
        run('forecast_ec_model.py')
    elif args.mode == 'visualize':
        run('visualization_ec.py')
    elif args.mode == 'damage':
        run('damage_assessment_ec.py')
    elif args.mode == 'evaluate':
        run('evaluate_forecast_ec.py')
    elif args.mode == 'simulator':
        run('iot_simulator.py')

if __name__ == "__main__":
    main()