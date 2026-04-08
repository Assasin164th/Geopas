#!/usr/bin/env python3
"""
Расчёт экономического ущерба от превышения EC.
Методика: ущерб рыбному хозяйству, промышленности, водоснабжению.
"""

class ECDamage:
    def __init__(self):
        self.inflation = 2.8
        self.zones = {
            'Широковский': {'pop': 1200, 'fish': 1, 'industry': 0},
            'Кияево': {'pop': 800, 'fish': 0, 'industry': 1},
            'Губаха': {'pop': 23000, 'fish': 0, 'industry': 3},
            'Устье': {'pop': 5000, 'fish': 2, 'industry': 1}
        }

    def assess(self, ec):
        if ec < 4000:
            return {'hazard': 'Низкий', 'evac': False, 'damage_2006': 0.0, 'damage_2026': 0.0}
        severity = 0.5 if ec < 5000 else 1.0
        hazard = 'Средний' if ec < 5000 else 'Высокий'
        total = 0.0
        for z, d in self.zones.items():
            fish = d['fish'] * 50 * severity
            ind = d['industry'] * 30 * severity
            social = (d['pop'] / 1000) * 10 * severity
            total += fish + ind + social
        return {
            'hazard': hazard,
            'evac': True,
            'damage_2006': total,
            'damage_2026': total * self.inflation
        }

def main():
    d = ECDamage()
    print("\nЭКОНОМИЧЕСКИЙ УЩЕРБ ОТ ЗАГРЯЗНЕНИЯ ВОДЫ (EC)")
    print("="*60)
    for ec, name in [(2800,"Норма"), (3800,"Повышенная"), (4500,"Опасная"), (5500,"Критическая")]:
        res = d.assess(ec)
        print(f"\n{name} (EC={ec} мкСм/см)")
        print(f"  Степень: {res['hazard']} | Эвакуация: {'Да' if res['evac'] else 'Нет'}")
        print(f"  Ущерб 2006 г.: {res['damage_2006']:.2f} млн руб")
        print(f"  Ущерб 2026 г.: {res['damage_2026']:.2f} млн руб")

if __name__ == "__main__":
    main()