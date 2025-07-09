import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import os
from crypto_analyzer_cryptocompare import CryptoAnalyzer

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

# Инициализация анализатора без кеширования
@st.cache_resource
def init_components():
    analyzer = CryptoAnalyzer(cache=None)
    return analyzer

analyzer = init_components()

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
    if st.button("2г", help="2 года"):
        st.session_state.history_days = 730
        st.rerun()
with col4:
    if st.button("3г", help="3 года"):
        st.session_state.history_days = 1095
        st.rerun()

# Информация о данных
st.sidebar.markdown("---")
st.sidebar.header("📊 Данные")
st.sidebar.info("Всегда загружаются свежие данные из CryptoCompare API")

# Кнопка анализа
st.sidebar.markdown("---")
if st.sidebar.button("🚀 Запустить анализ", type="primary"):
    st.session_state['start_analysis'] = True

# Анализ данных
if st.session_state.get('start_analysis', False):
    # Сброс флага анализа
    st.session_state['start_analysis'] = False
    
    with st.container():
        try:
            # Индикатор прогресса
            progress_bar = st.progress(0)
            status_text = st.empty()
            
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
        
        # График Bitcoin (если есть данные)
        if 'BTC' in historical_data:
            btc_data = historical_data['BTC'].reset_index()
            fig.add_trace(
                go.Scatter(
                    x=btc_data['Date'],
                    y=btc_data['Close'],
                    mode='lines',
                    name='Bitcoin',
                    line=dict(color='orange', width=2),
                    hovertemplate='<b>Bitcoin</b><br>Дата: %{x}<br>Цена: $%{y:,.0f}<extra></extra>'
                ),
                row=1, col=1
            )
        
        # График индикатора ширины рынка
        fig.add_trace(
            go.Scatter(
                x=indicator_data.index,
                y=indicator_data['percentage'],
                mode='lines+markers',
                name='Индикатор ширины рынка',
                line=dict(color='cyan', width=3),
                marker=dict(size=4),
                hovertemplate='<b>Ширина рынка</b><br>Дата: %{x}<br>Процент: %{y:.1f}%<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Добавляем уровни перекупленности/перепроданности
        fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.7, row=2, col=1,
                      annotation_text="Перекупленность (80%)", annotation_position="top right")
        fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.7, row=2, col=1,
                      annotation_text="Перепроданность (20%)", annotation_position="bottom right")
        fig.add_hline(y=50, line_dash="dot", line_color="yellow", opacity=0.5, row=2, col=1,
                      annotation_text="Нейтрально (50%)", annotation_position="middle right")
        
        # Заливка зон
        fig.add_hrect(y0=80, y1=100, fillcolor="red", opacity=0.1, row=2, col=1)
        fig.add_hrect(y0=0, y1=20, fillcolor="green", opacity=0.1, row=2, col=1)
        fig.add_hrect(y0=20, y1=80, fillcolor="yellow", opacity=0.05, row=2, col=1)
        
        # Настройки макета
        fig.update_layout(
            height=800,
            showlegend=True,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Форматирование осей
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
        
        # Форматирование цены Bitcoin
        fig.update_yaxes(tickformat='$,.0f', row=1, col=1)
        
        # Форматирование процентов
        fig.update_yaxes(tickformat='.0f', ticksuffix='%', row=2, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Дополнительные графики
        st.markdown("### 📊 Детальная статистика")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Гистограмма распределения значений
            st.markdown("#### Распределение значений индикатора")
            fig_hist = px.histogram(
                indicator_data, 
                x='percentage',
                nbins=20,
                title="Распределение значений ширины рынка",
                labels={'percentage': 'Процент монет выше MA', 'count': 'Количество дней'}
            )
            fig_hist.update_layout(height=400)
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            # Индикатор текущего значения
            st.markdown("#### Текущий уровень")
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=current_value,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Ширина рынка (%)"},
                delta={'reference': avg_value, 'suffix': '% от среднего'},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "cyan"},
                    'steps': [
                        {'range': [0, 20], 'color': "lightgreen"},
                        {'range': [20, 80], 'color': "lightyellow"},
                        {'range': [80, 100], 'color': "lightcoral"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig_gauge.update_layout(height=400)
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Корреляционный анализ
        st.markdown("### 🔗 Корреляционный анализ")
        
        # Выбор монет для корреляции
        available_coins = list(historical_data.keys())
        selected_coins = st.multiselect(
            "Выберите монеты для анализа корреляции с индикатором:",
            available_coins,
            default=['BTC', 'ETH'] if all(coin in available_coins for coin in ['BTC', 'ETH']) else available_coins[:2]
        )
        
        if selected_coins:
            # Расчет корреляций
            correlations = {}
            for coin in selected_coins:
                if coin in historical_data:
                    coin_data = historical_data[coin].reset_index()
                    # Синхронизируем данные по датам
                    merged_data = pd.merge(
                        indicator_data.reset_index(),
                        coin_data[['Date', 'Close']],
                        left_on='Date',
                        right_on='Date',
                        how='inner'
                    )
                    if len(merged_data) > 10:  # Минимум данных для корреляции
                        corr = merged_data['percentage'].corr(merged_data['Close'])
                        correlations[coin] = corr
            
            if correlations:
                # График корреляций
                corr_df = pd.DataFrame(list(correlations.items()), columns=['Монета', 'Корреляция'])
                fig_corr = px.bar(
                    corr_df, 
                    x='Монета', 
                    y='Корреляция',
                    title="Корреляция индикатора ширины рынка с ценами монет",
                    color='Корреляция',
                    color_continuous_scale='RdYlBu_r'
                )
                fig_corr.update_layout(height=400)
                st.plotly_chart(fig_corr, use_container_width=True)
                
                # Таблица корреляций
                st.dataframe(corr_df.style.format({'Корреляция': '{:.3f}'}))
            else:
                st.warning("Недостаточно данных для анализа корреляции")
        
        # Экспорт данных
        st.markdown("### 💾 Экспорт данных")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV экспорт
            csv_data = indicator_data.to_csv()
            st.download_button(
                label="📁 Скачать CSV",
                data=csv_data,
                file_name=f"market_breadth_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # JSON экспорт
            json_data = indicator_data.to_json(orient='records', date_format='iso')
            st.download_button(
                label="📄 Скачать JSON",
                data=json_data,
                file_name=f"market_breadth_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

# Информационная панель
if not st.session_state.get('analysis_complete', False):
    st.info("👈 Настройте параметры в боковой панели и нажмите 'Запустить анализ' для начала работы")

# Подвал
st.markdown("---")
st.markdown(
    "💡 **Индикатор ширины рынка** показывает процент криптовалют из топ-N, торгующихся выше своей скользящей средней. "
    "Высокие значения (>80%) могут указывать на перекупленность рынка, низкие (<20%) — на перепроданность."
)