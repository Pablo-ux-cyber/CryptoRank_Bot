import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import os
from crypto_analyzer_cryptocompare import CryptoAnalyzer
from data_cache import DataCache

# Настройка страницы
st.set_page_config(
    page_title="Crypto Market Breadth Indicator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Заголовок приложения
st.title("📊 Индикатор ширины криптовалютного рынка")
st.markdown("**Процент топ-50 криптовалют выше MA200**")

# Инициализация кеша и анализатора
@st.cache_resource
def init_components():
    cache = DataCache()
    analyzer = CryptoAnalyzer(cache)
    return cache, analyzer

cache, analyzer = init_components()

# Боковая панель с настройками
st.sidebar.header("⚙️ Настройки")

# Параметры анализа
top_n = st.sidebar.slider("Количество топ монет", 10, 100, 50, 5)
ma_period = st.sidebar.slider("Период MA", 50, 300, 200, 10)
history_days = st.sidebar.slider("Дней истории для анализа", 180, 1460, 1095, 30)
st.sidebar.caption("📅 Периоды: 365 дней ≈ 1 год, 730 дней ≈ 2 года, 1095 дней ≈ 3 года, 1460 дней ≈ 4 года")

# Быстрые кнопки для популярных периодов
st.sidebar.markdown("**Быстрый выбор периода:**")
col1, col2, col3, col4 = st.sidebar.columns(4)
with col1:
    if st.button("6м", help="6 месяцев"):
        st.session_state.history_days = 180
        st.rerun()
with col2:
    if st.button("1г", help="1 год"):
        st.session_state.history_days = 365
        st.rerun()
with col3:
    if st.button("3г ⭐", help="3 года (стандарт)"):
        st.session_state.history_days = 1095
        st.rerun()
with col4:
    if st.button("4г", help="4 года"):
        st.session_state.history_days = 1460
        st.rerun()

# Синхронизация с session state
if 'history_days' in st.session_state:
    history_days = st.session_state.history_days

# Кнопки управления
col1, col2 = st.sidebar.columns(2)
with col1:
    run_analysis = st.button("🔄 Запустить анализ", type="primary")
with col2:
    clear_cache = st.button("🗑️ Очистить кеш")

if clear_cache:
    cache.clear_all()
    st.sidebar.success("Кеш очищен!")
    st.rerun()

# Информация о кеше
cache_info = cache.get_cache_info()
if cache_info:
    st.sidebar.markdown("### 📁 Информация о кеше")
    st.sidebar.text(f"Монет в кеше: {cache_info['coins_count']}")
    st.sidebar.text(f"Последнее обновление: {cache_info['last_update']}")

# Основная логика приложения
if run_analysis or st.session_state.get('analysis_complete', False):
    
    if run_analysis:
        # Прогресс бар и статус
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Получение топ монет
            status_text.text("🔍 Получение списка топ криптовалют...")
            progress_bar.progress(10)
            
            top_coins = analyzer.get_top_coins(top_n)
            if not top_coins:
                st.error("❌ Не удалось получить список топ монет")
                st.stop()
            
            st.success(f"✅ Получено {len(top_coins)} монет")
            
            # Загрузка исторических данных
            status_text.text("📈 Загрузка исторических данных...")
            progress_bar.progress(30)
            
            historical_data = analyzer.load_historical_data(
                top_coins, 
                ma_period + history_days + 100,  # Увеличенный запас данных для больших периодов
                progress_callback=lambda p: progress_bar.progress(30 + int(p * 0.5))
            )
            
            if not historical_data:
                st.error("❌ Не удалось загрузить исторические данные")
                st.stop()
            
            # Расчет индикатора
            status_text.text("🧮 Расчет индикатора ширины рынка...")
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
            status_text.text("✅ Анализ завершен!")
            
            # Сохранение результатов в session state
            st.session_state['indicator_data'] = indicator_data
            st.session_state['historical_data'] = historical_data
            st.session_state['analysis_complete'] = True
            st.session_state['analysis_params'] = {
                'top_n': top_n,
                'ma_period': ma_period,
                'history_days': history_days
            }
            
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            st.error(f"❌ Ошибка при анализе: {str(e)}")
            st.stop()
    
    # Отображение результатов
    if st.session_state.get('analysis_complete', False):
        indicator_data = st.session_state['indicator_data']
        historical_data = st.session_state['historical_data']
        params = st.session_state.get('analysis_params', {})
        
        # Метрики
        col1, col2, col3, col4 = st.columns(4)
        
        current_value = indicator_data['percentage'].iloc[-1]
        avg_value = indicator_data['percentage'].mean()
        max_value = indicator_data['percentage'].max()
        min_value = indicator_data['percentage'].min()
        
        with col1:
            st.metric("📊 Текущий уровень", f"{current_value:.1f}%")
        with col2:
            st.metric("📈 Средний уровень", f"{avg_value:.1f}%")
        with col3:
            st.metric("🔝 Максимум", f"{max_value:.1f}%")
        with col4:
            st.metric("🔻 Минимум", f"{min_value:.1f}%")
        
        # Определение рыночных условий
        if current_value >= 80:
            market_condition = "🔴 Перекупленность"
            condition_color = "red"
        elif current_value <= 20:
            market_condition = "🟢 Перепроданность"
            condition_color = "green"
        else:
            market_condition = "🟡 Нейтральная зона"
            condition_color = "orange"
        
        st.markdown(f"### Текущие рыночные условия: <span style='color:{condition_color}'>{market_condition}</span>", unsafe_allow_html=True)
        
        # Объединенный график с подграфиками
        st.markdown("### 📈 Bitcoin и индикатор ширины рынка")
        
        from plotly.subplots import make_subplots
        
        # Создаем подграфики
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=('Цена Bitcoin (USD)', f'Процент монет выше MA{params.get("ma_period", ma_period)} (%)'),
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
        fig.add_trace(
            go.Scatter(
                x=indicator_data['date'],
                y=indicator_data['percentage'],
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
        
        # Область между уровнями
        fig.add_hrect(
            y0=20, y1=80,
            fillcolor="lightgray",
            opacity=0.1,
            layer="below",
            line_width=0,
            row=2, col=1
        )
        
        # Настройка общего графика
        fig.update_layout(
            height=700,
            showlegend=True,
            hovermode='x unified',
            title_text="Анализ Bitcoin и ширины криптовалютного рынка"
        )
        
        # Настройка осей
        fig.update_xaxes(showgrid=True, row=1, col=1)
        fig.update_xaxes(showgrid=True, title_text="Дата", row=2, col=1)
        fig.update_yaxes(showgrid=True, title_text="Цена (USD)", row=1, col=1)
        fig.update_yaxes(showgrid=True, title_text="Процент (%)", range=[0, 100], row=2, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Корреляционный анализ
        if 'BTC' in historical_data:
            st.markdown("### 🔄 Корреляционный анализ")
            
            btc_data = historical_data['BTC'].copy()
            btc_data['date'] = pd.to_datetime(btc_data['date'])
            
            # Фильтрация по тому же периоду
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=history_days)
            btc_data = btc_data[(btc_data['date'].dt.date >= start_date) & (btc_data['date'].dt.date <= end_date)]
            
            if not btc_data.empty:
                # Объединение данных по датам для корреляции
                merged_data = pd.merge(
                    indicator_data[['date', 'percentage']], 
                    btc_data[['date', 'price']], 
                    on='date', 
                    how='inner'
                )
                
                if len(merged_data) > 10:
                    correlation = merged_data['percentage'].corr(merged_data['price'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("📈 Корреляция с Bitcoin", f"{correlation:.3f}")
                    with col2:
                        if abs(correlation) > 0.7:
                            corr_strength = "Сильная"
                        elif abs(correlation) > 0.3:
                            corr_strength = "Умеренная"
                        else:
                            corr_strength = "Слабая"
                        
                        st.metric("🔍 Сила связи", corr_strength)
                    
                    st.markdown(f"""
                    **Интерпретация корреляции:**
                    - **Корреляция**: {correlation:.3f} (чем ближе к ±1, тем сильнее связь)
                    - **Сила связи**: {corr_strength.lower()} корреляция
                    - **Данные**: {len(merged_data)} совпадающих дат для анализа
                    """)
            else:
                st.warning("Недостаточно данных Bitcoin за выбранный период")
        else:
            st.warning("Данные Bitcoin недоступны для сравнения")
        
        # Статистика анализа
        st.markdown("### 📊 Статистика анализа")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Параметры анализа:**")
            st.text(f"• Топ монет: {params.get('top_n', top_n)}")
            st.text(f"• Период MA: {params.get('ma_period', ma_period)} дней")
            st.text(f"• Период анализа: {params.get('history_days', history_days)} дней")
            st.text(f"• Монет с достаточными данными: {len(historical_data)}")
        
        with col2:
            st.markdown("**Распределение уровней:**")
            above_80 = (indicator_data['percentage'] >= 80).sum()
            below_20 = (indicator_data['percentage'] <= 20).sum()
            neutral = len(indicator_data) - above_80 - below_20
            
            st.text(f"• Дней в перекупленности (≥80%): {above_80}")
            st.text(f"• Дней в перепроданности (≤20%): {below_20}")
            st.text(f"• Дней в нейтральной зоне: {neutral}")
            st.text(f"• Волатильность: {indicator_data['percentage'].std():.1f}%")
        
        # Кнопки экспорта
        st.markdown("### 💾 Экспорт данных")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV экспорт
            csv_data = indicator_data.to_csv(index=False)
            st.download_button(
                label="📄 Скачать CSV",
                data=csv_data,
                file_name=f"market_breadth_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # PNG экспорт
            if st.button("🖼️ Сохранить график PNG"):
                fig.write_image("market_breadth_chart.png", width=1200, height=600)
                st.success("График сохранен как market_breadth_chart.png")
        
        # Таблица с последними данными
        st.markdown("### 📋 Последние 10 дней")
        recent_data = indicator_data.tail(10).copy()
        recent_data['date'] = recent_data['date'].dt.strftime('%Y-%m-%d')
        recent_data['percentage'] = recent_data['percentage'].round(1)
        
        # Проверяем количество колонок и корректно переименовываем
        if len(recent_data.columns) == 4:
            recent_data.columns = ['Дата', 'Процент (%)', 'Монет выше MA', 'Всего монет']
        else:
            recent_data.columns = ['Дата', 'Процент монет выше MA200 (%)', 'Количество монет выше MA200']
        
        st.dataframe(
            recent_data.iloc[::-1],  # Reverse to show newest first
            use_container_width=True,
            hide_index=True
        )

else:
    # Приветственный экран
    st.markdown("""
    ## 👋 Добро пожаловать в анализатор ширины криптовалютного рынка!
    
    Этот индикатор показывает процент топ-50 криптовалют, торгующихся выше своей 200-дневной скользящей средней (MA200).
    
    ### 📈 Что показывает индикатор:
    - **≥80%** - Рынок может быть перекуплен (сигнал к продаже)
    - **≤10%** - Рынок может быть перепродан (сигнал к покупке)
    - **10-80%** - Нейтральная зона
    
    ### 🚀 Как использовать:
    1. Настройте параметры в боковой панели
    2. Нажмите "Запустить анализ"
    3. Изучите результаты и экспортируйте данные
    
    ### ⚙️ Возможности:
    - Интерактивные графики с Plotly
    - Кеширование данных для быстрой работы
    - Экспорт в CSV и PNG
    - Настраиваемые параметры анализа
    
    **Нажмите "Запустить анализ" в боковой панели для начала работы!**
    """)
    
    # Информация об API
    st.markdown("""
    ---
    **📡 Источник данных:** CryptoCompare API (публичный, без ключа)
    
    **⏱️ Время выполнения:** 1-3 минуты (в зависимости от параметров)
    
    **💾 Кеширование:** Данные кешируются локально для ускорения повторных запусков
    """)
