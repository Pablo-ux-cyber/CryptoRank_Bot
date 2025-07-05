#!/usr/bin/env python3

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time

# Импорт ваших модулей
from crypto_analyzer_cryptocompare import CryptoAnalyzer
from data_cache import DataCache

# Настройка страницы
st.set_page_config(
    page_title="📊 Индикатор ширины криптовалютного рынка",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Заголовок
st.title("📊 Индикатор ширины криптовалютного рынка")
st.markdown("---")

# Инициализация компонентов
@st.cache_resource
def init_components():
    cache = DataCache()
    analyzer = CryptoAnalyzer(cache)
    return cache, analyzer

cache, analyzer = init_components()

# Боковая панель с настройками
st.sidebar.header("⚙️ Настройки анализа")

# Настройки
top_n = st.sidebar.slider("Количество топ монет", min_value=10, max_value=100, value=50, step=5)
ma_period = st.sidebar.slider("Период скользящей средней", min_value=50, max_value=300, value=200, step=10)
history_days = st.sidebar.slider("Дней истории для анализа", min_value=180, max_value=1460, value=365, step=30)

# Информация о кеше
cache_info = cache.get_cache_info()
st.sidebar.subheader("💾 Информация о кеше")
st.sidebar.write(f"Размер кеша: {cache_info['cache_size_mb']:.1f} МБ")
st.sidebar.write(f"Монет в кеше: {cache_info['cached_coins_count']}")

if st.sidebar.button("🗑️ Очистить кеш"):
    cache.clear_all()
    st.sidebar.success("Кеш очищен")
    st.experimental_rerun()

# Кнопка запуска анализа
if st.button("🚀 Запустить анализ", type="primary"):
    with st.spinner('Анализ рынка...'):
        # Получение топ монет
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text('Получение списка топ криптовалют...')
        progress_bar.progress(10)
        
        top_coins = analyzer.get_top_coins(top_n)
        if not top_coins:
            st.error("❌ Не удалось получить список топ монет")
            st.stop()
        
        st.success(f"✅ Получено {len(top_coins)} топ монет")
        
        # Загрузка исторических данных
        status_text.text('Загрузка исторических данных...')
        progress_bar.progress(30)
        
        def progress_callback(current, total):
            progress = 30 + int((current / total) * 50)
            progress_bar.progress(progress)
            status_text.text(f'Загрузка данных: {current}/{total} монет')
        
        historical_data = analyzer.load_historical_data(
            top_coins, 
            ma_period + history_days + 100,
            progress_callback
        )
        
        if not historical_data:
            st.error("❌ Не удалось загрузить исторические данные")
            st.stop()
        
        # Расчет индикатора
        status_text.text('Расчет индикатора ширины рынка...')
        progress_bar.progress(80)
        
        indicator_data = analyzer.calculate_market_breadth(
            historical_data, 
            ma_period, 
            history_days
        )
        
        if indicator_data.empty:
            st.error("❌ Не удалось рассчитать индикатор")
            st.stop()
        
        progress_bar.progress(100)
        status_text.text('Анализ завершен!')
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
        
        # Получение сводной информации
        summary = analyzer.get_market_summary(indicator_data)
        current_value = summary['current_value']
        
        # Определение рыночного сигнала
        if current_value >= 80:
            signal = "🔴"
            condition = "Перекупленность"
            description = "Большинство монет выше MA200, возможна коррекция"
            color = "red"
        elif current_value <= 20:
            signal = "🟢"
            condition = "Перепроданность" 
            description = "Большинство монет ниже MA200, возможен отскок"
            color = "green"
        else:
            signal = "🟡"
            condition = "Нейтральная зона"
            description = "Рынок в состоянии равновесия"
            color = "orange"
        
        # Отображение результатов
        st.markdown("---")
        st.subheader("📈 Результаты анализа")
        
        # Основные метрики
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Текущий индикатор",
                value=f"{current_value:.1f}%",
                delta=f"{signal} {condition}"
            )
        
        with col2:
            st.metric(
                label="Монет выше MA200",
                value=f"{summary['coins_above_ma']}/{len(historical_data)}"
            )
        
        with col3:
            st.metric(
                label="Среднее значение",
                value=f"{summary['avg_value']:.1f}%"
            )
        
        with col4:
            st.metric(
                label="Диапазон",
                value=f"{summary['min_value']:.1f}% - {summary['max_value']:.1f}%"
            )
        
        # Описание сигнала
        if color == "red":
            st.error(f"{signal} {description}")
        elif color == "green":
            st.success(f"{signal} {description}")
        else:
            st.warning(f"{signal} {description}")
        
        # Создание графиков (ваш точный код)
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Bitcoin (BTC)', 'Индикатор ширины рынка'),
            vertical_spacing=0.08,
            row_heights=[0.4, 0.6]
        )
        
        # График Bitcoin сверху
        if 'BTC' in historical_data:
            btc_data = historical_data['BTC'].copy()
            btc_data['date'] = pd.to_datetime(btc_data['date'])
            
            # Фильтрация по тому же периоду
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=history_days)
            btc_data = btc_data[(btc_data['date'].dt.date >= start_date) & (btc_data['date'].dt.date <= end_date)]
            
            if not btc_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=btc_data['date'],
                        y=btc_data['price'],
                        mode='lines',
                        name='Bitcoin',
                        line=dict(color='#F7931A', width=2),
                        hovertemplate='<b>%{x}</b><br>Цена BTC: $%{y:,.0f}<extra></extra>'
                    ),
                    row=1, col=1
                )
        
        # График индикатора снизу  
        indicator_data_reset = indicator_data.reset_index()
        fig.add_trace(
            go.Scatter(
                x=indicator_data_reset['date'],
                y=indicator_data_reset['percentage'],
                mode='lines',
                name='Индикатор ширины',
                line=dict(color='#1f77b4', width=2),
                hovertemplate='<b>%{x}</b><br>Процент: %{y:.1f}%<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Линии уровней для индикатора на нижнем графике
        fig.add_hline(
            y=80, 
            line_dash="dash", 
            line_color="red",
            annotation_text="Перекупленность (80%)",
            annotation_position="bottom right",
            row=2, col=1
        )
        
        fig.add_hline(
            y=20, 
            line_dash="dash", 
            line_color="green",
            annotation_text="Перепроданность (20%)",
            annotation_position="top right",
            row=2, col=1
        )
        
        fig.add_hline(
            y=50, 
            line_dash="dot", 
            line_color="gray",
            annotation_text="Нейтральная зона (50%)",
            annotation_position="middle right",
            row=2, col=1
        )
        
        # Зоны перекупленности и перепроданности
        fig.add_hrect(
            y0=80, y1=100, 
            fillcolor="red", opacity=0.1,
            annotation_text="Перекупленность", 
            annotation_position="top left",
            row=2, col=1
        )
        fig.add_hrect(
            y0=0, y1=20, 
            fillcolor="green", opacity=0.1,
            annotation_text="Перепроданность", 
            annotation_position="bottom left",
            row=2, col=1
        )
        fig.add_hrect(
            y0=20, y1=80, 
            fillcolor="gray", opacity=0.05,
            row=2, col=1
        )
        
        # Настройка макета
        fig.update_layout(
            height=800,
            showlegend=True,
            hovermode='x unified',
            template='plotly_dark'
        )
        
        # Настройка осей
        fig.update_yaxes(title_text="Цена Bitcoin (USD)", row=1, col=1)
        fig.update_yaxes(title_text="Процент монет выше MA (%)", row=2, col=1, range=[0, 100])
        fig.update_xaxes(title_text="Дата", row=2, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Таблица с корреляциями (ваш код)
        st.subheader("🔗 Корреляция с Bitcoin")
        
        if 'BTC' in historical_data:
            btc_data = historical_data['BTC'].copy()
            btc_data['date'] = pd.to_datetime(btc_data['date'])
            btc_data = btc_data.set_index('date')
            
            correlations = []
            
            for coin_symbol, df in historical_data.items():
                if coin_symbol != 'BTC' and df is not None:
                    df = df.copy()
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.set_index('date')
                    
                    # Объединение данных по датам
                    merged = btc_data[['price']].join(df[['price']], rsuffix='_alt', how='inner')
                    
                    if len(merged) > 10:
                        correlation = merged['price'].corr(merged['price_alt'])
                        correlations.append({
                            'Монета': coin_symbol,
                            'Корреляция с BTC': f"{correlation:.3f}"
                        })
            
            if correlations:
                corr_df = pd.DataFrame(correlations)
                corr_df = corr_df.sort_values('Корреляция с BTC', ascending=False)
                st.dataframe(corr_df, use_container_width=True)

# Информация об индикаторе
st.markdown("---")
st.subheader("ℹ️ О индикаторе ширины рынка")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Как работает индикатор:**
    - Показывает процент криптовалют, торгующихся выше скользящей средней
    - Помогает определить общее направление и здоровье рынка
    - Основан на анализе топ криптовалют по капитализации
    """)

with col2:
    st.markdown("""
    **Интерпретация сигналов:**
    - 🔴 **>80%**: Перекупленность, возможна коррекция
    - 🟡 **20-80%**: Нейтральная зона, рынок в равновесии  
    - 🟢 **<20%**: Перепроданность, возможен отскок
    """)

st.markdown("""
**Особенности анализа:**
- Использует данные CryptoCompare API
- Интеллектуальное кеширование для оптимизации
- Настраиваемые параметры анализа
- Корреляционный анализ с Bitcoin
""")