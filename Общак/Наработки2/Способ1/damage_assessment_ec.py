#!/usr/bin/env python3
"""
damage_assessment_ec.py
Расчёт экономического ущерба при загрязнении воды (превышение EC).
Основано на методике ущерба водным биоресурсам и рыбному хозяйству.
"""

class ECDamageAssessment:
    def __init__(self):
        self.inflation_factor = 2.8
        # Пороги EC для реки Косьва
        self.ec_thresholds = {
            'norm': 3000,
            'warning': 4000,
            'danger': 5000
        }
        # Зоны риска (населённые пункты вдоль Косьвы)
        self.risk_zones = {
            'Широковский': {'population': 1200, 'fish_farms': 1, 'industry': 0},
            'Кияево': {'population': 800, 'fish_farms': 0, 'industry': 1},
            'Губаха': {'population': 23000, 'fish_farms': 0, 'industry': 3},
            'Устье Косьвы': {'population': 5000, 'fish_farms': 2, 'industry': 1}
        }

    def assess_damage(self, ec_level):
        """Расчёт ущерба в зависимости от EC."""
        if ec_level < self.ec_thresholds['warning']:
            return {'hazard': 'Низкий', 'evacuation': False, 'damage_million_2006': 0, 'damage_million_2026': 0}
        
        # Коэффициент превышения
        if ec_level < self.ec_thresholds['danger']:
            severity = 0.5
            hazard = 'Средний'
        else:
            severity = 1.0
            hazard = 'Высокий'
        
        total_damage = 0
        for zone, data in self.risk_zones.items():
            # Ущерб рыбному хозяйству (потеря рыбы, очистка)
            fish_damage = data['fish_farms'] * 50 * severity  # 50 млн руб на ферму
            # Ущерб промышленности (остановка производства из-за плохой воды)
            industry_damage = data['industry'] * 30 * severity
            # Социальный ущерб (затраты на альтернативное водоснабжение)
            social_damage = (data['population'] / 1000) * 10 * severity
            zone_total = fish_damage + industry_damage + social_damage
            total_damage += zone_total
        
        return {
            'hazard': hazard,
            'evacuation': hazard != 'Низкий',
            'damage_million_2006': total_damage,
            'damage_million_2026': total_damage * self.inflation_factor,
            'ec_level': ec_level
        }

def main():
    assess = ECDamageAssessment()
    scenarios = [
        (2800, "Норма (EC < 3000)"),
        (3800, "Повышенная (3000-4000)"),
        (4500, "Опасная (4000-5000)"),
        (5500, "Критическая (>5000)")
    ]
    print("\n" + "="*70)
    print("💰 РАСЧЁТ ЭКОНОМИЧЕСКОГО УЩЕРБА ОТ ЗАГРЯЗНЕНИЯ ВОДЫ (EC)")
    print("="*70)
    for ec, name in scenarios:
        res = assess.assess_damage(ec)
        print(f"\n📊 {name} (EC = {ec} мкСм/см)")
        print(f"   Степень опасности: {res['hazard']}")
        print(f"   Эвакуация/особый режим: {'Да' if res['evacuation'] else 'Нет'}")
        print(f"   Ущерб в ценах 2006 г.: {res['damage_million_2006']:.2f} млн руб")
        print(f"   Ущерб в ценах 2026 г.: {res['damage_million_2026']:.2f} млн руб")
    print("\n🏁 Рекомендации: при EC > 4000 мкСм/см вводить ограничения на водопользование.")

if __name__ == "__main__":
    main()