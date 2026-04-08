# Допущения:
# - Опасное явление: подъём воды + ухудшение качества (EC > 5000 µS/cm)
# - Зона затопления: 5 км² сельхозугодий и 200 домов
# - Длительность: 10 дней

area_ha = 500  # 5 км² = 500 га
damage_per_ha_rub = 50000  # ущерб сельхозугодьям (руб/га)
houses = 200
damage_per_house_rub = 300000
infrastructure_loss = 2_000_000  # дороги, ЛЭП
cleanup_cost = 1_500_000

agricultural_loss = area_ha * damage_per_ha_rub
residential_loss = houses * damage_per_house_rub
total_loss = agricultural_loss + residential_loss + infrastructure_loss + cleanup_cost

print("=== Экономические потери от опасного явления (паводок) ===")
print(f"Сельское хозяйство: {agricultural_loss:,.0f} руб")
print(f"Жилой сектор: {residential_loss:,.0f} руб")
print(f"Инфраструктура: {infrastructure_loss:,.0f} руб")
print(f"Ликвидация последствий: {cleanup_cost:,.0f} руб")
print(f"ИТОГО: {total_loss:,.0f} руб")

# Обоснование: использованы средние данные МЧС по Пермскому краю