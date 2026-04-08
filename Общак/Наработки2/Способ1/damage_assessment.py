#!/usr/bin/env python3
"""
damage_assessment.py
Расчёт экономического ущерба от наводнения на основе методики ВИЭМС.
"""

class FloodDamageAssessment:
    def __init__(self):
        self.base_damage_per_ha = 30.7  # млн руб/га (2006)
        self.inflation_factor = 2.8     # 2006→2026
        self.infrastructure_costs = {
            'road_per_km': 15.0,
            'bridge_per_unit': 50.0,
            'power_line_per_km': 8.0,
            'water_pipe_per_km': 12.0
        }
        # Зоны риска в Пермском крае (условные данные)
        self.risk_zones = {
            'Кудымкарский': {'houses': 120, 'area_ha': 18, 'infra_km': 25},
            'Карагайский': {'houses': 85, 'area_ha': 12, 'infra_km': 20},
            'Кунгурский': {'houses': 150, 'area_ha': 22, 'infra_km': 30},
            'Губахинский': {'houses': 95, 'area_ha': 14, 'infra_km': 18},
            'Александровский': {'houses': 70, 'area_ha': 10, 'infra_km': 15}
        }

    def assess_scenario(self, water_level, warning=150, danger=200):
        if water_level < warning:
            return {'hazard': 'Низкий', 'evacuation': False, 'total_damage_2006': 0.0, 'total_damage_2026': 0.0}
        elif water_level < danger:
            multiplier = 0.5
            hazard = 'Средний'
            evac = True
        else:
            multiplier = 1.0
            hazard = 'Высокий'
            evac = True

        total = 0.0
        for zone, data in self.risk_zones.items():
            factor = multiplier * (water_level - warning) / (danger - warning) if water_level < danger else multiplier
            factor = min(1.0, factor)
            flooded_area = data['area_ha'] * factor
            flooded_houses = int(data['houses'] * factor)
            # Прямой ущерб жилью
            direct = self.base_damage_per_ha * flooded_area
            # Инфраструктура
            infra = (self.infrastructure_costs['road_per_km'] * (data['infra_km']*0.6*factor) +
                     self.infrastructure_costs['bridge_per_unit'] * (data['infra_km']/10*factor) +
                     self.infrastructure_costs['power_line_per_km'] * (data['infra_km']*0.4*factor) +
                     self.infrastructure_costs['water_pipe_per_km'] * (data['infra_km']*0.5*factor))
            # Сельское хозяйство
            agri = flooded_area * 0.25
            # Социальный ущерб (переселение)
            displaced = int(flooded_houses * 2.5 * (0.8 if hazard=='Высокий' else 0.3))
            social = displaced * 14 * (1.5 + 50/30) / 1000  # тыс.руб -> млн руб
            zone_total = direct + infra + agri + social
            total += zone_total
        return {
            'hazard': hazard,
            'evacuation': evac,
            'total_damage_2006': total,
            'total_damage_2026': total * self.inflation_factor
        }

def main():
    assess = FloodDamageAssessment()
    scenarios = [
        (130, "Базовый (норма)"),
        (165, "Повышенный (предупреждение)"),
        (210, "Опасный (паводок)"),
        (250, "Критический (наводнение)")
    ]
    print("\n" + "="*70)
    print("💰 РАСЧЁТ ЭКОНОМИЧЕСКИХ ПОТЕРЬ ПРИ НАВОДНЕНИИ (методика ВИЭМС)")
    print("="*70)
    for level, name in scenarios:
        res = assess.assess_scenario(level)
        print(f"\n📊 {name} (уровень {level} см)")
        print(f"   Степень опасности: {res['hazard']}")
        print(f"   Эвакуация: {'Да' if res['evacuation'] else 'Нет'}")
        print(f"   Ущерб в ценах 2006 г.: {res['total_damage_2006']:.2f} млн руб")
        print(f"   Ущерб в ценах 2026 г.: {res['total_damage_2026']:.2f} млн руб")
    print("\n🏁 Рекомендации: при уровне >150 см вводить режим повышенной готовности, при >200 см – эвакуация.")

if __name__ == "__main__":
    main()