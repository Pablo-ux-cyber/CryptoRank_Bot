import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Загрузка данных
df = pd.read_csv('historical_data.csv')

# Преобразование даты в формат datetime
df['date'] = pd.to_datetime(df['date'])

# Создание графика
plt.figure(figsize=(12, 8))

# Инвертировать оси Y, так как меньшие числа означают лучший рейтинг
plt.gca().invert_yaxis()

# Построение графиков для каждой категории
plt.plot(df['date'], df['iPhone - Free - Finance'], 'b-', label='iPhone - Free - Finance')
plt.plot(df['date'], df['iPhone - Free - Apps'], 'r-', label='iPhone - Free - Apps')
plt.plot(df['date'], df['iPhone - Free - Overall'], 'g-', label='iPhone - Free - Overall')

# Добавление меток и заголовка
plt.xlabel('Дата')
plt.ylabel('Позиция в рейтинге (ниже = лучше)')
plt.title('Динамика рейтингов Coinbase за последние 30 дней')
plt.grid(True, linestyle='--', alpha=0.7)

# Добавление легенды
plt.legend()

# Форматирование оси X для более читаемых дат
plt.gcf().autofmt_xdate()

# Вторичная ось Y для общего рейтинга (так как у него другой масштаб)
ax2 = plt.twinx()
ax2.plot(df['date'], df['iPhone - Free - Overall'], 'g-')
ax2.set_ylabel('Позиция в общем рейтинге', color='g')
ax2.tick_params(axis='y', labelcolor='g')
ax2.invert_yaxis()  # Инвертировать и эту ось тоже

# Сохранение графика
plt.tight_layout()
plt.savefig('rankings_chart.png')
print("График сохранен как rankings_chart.png")