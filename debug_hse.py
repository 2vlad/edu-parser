#!/usr/bin/env python3
"""
Детальная отладка HSE скрейпера
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.logging_config import setup_logging, get_logger
from scrapers.hse import download_hse_excel, APPLICATION_COUNT_COLUMNS, HSE_TARGET_PROGRAMS

setup_logging(log_level="DEBUG")
logger = get_logger(__name__)

def debug_hse_excel():
    """Детальный анализ HSE Excel файла"""
    print("🔍 ДЕТАЛЬНАЯ ОТЛАДКА HSE EXCEL")
    print("=" * 60)
    
    # Скачиваем Excel
    print("\n1️⃣ Скачиваем Excel файл...")
    df = download_hse_excel()
    
    if df is None:
        print("❌ Не удалось скачать Excel файл")
        return
    
    print(f"✅ Excel загружен: {len(df)} строк, {len(df.columns)} колонок")
    
    # Показываем колонки
    print(f"\n2️⃣ Доступные колонки ({len(df.columns)}):")
    for i, col in enumerate(df.columns):
        print(f"   {i}: '{col}'")
    
    # Ищем колонку с заявлениями
    print(f"\n3️⃣ Поиск колонки с заявлениями...")
    found_column = None
    for col_name in APPLICATION_COUNT_COLUMNS:
        if col_name in df.columns:
            found_column = col_name
            print(f"✅ Найдена колонка: '{col_name}'")
            break
    
    if not found_column:
        print("❌ Не найдена колонка с заявлениями")
        print("\nПопробуем найти похожие:")
        for col in df.columns:
            if any(word in col.lower() for word in ['заявл', 'количество', 'кол']):
                print(f"   Похожая: '{col}'")
        return
    
    # Анализируем данные в колонке
    print(f"\n4️⃣ Анализ колонки '{found_column}':")
    app_count_data = df[found_column]
    
    print(f"   Всего записей: {len(app_count_data)}")
    print(f"   Не-null записей: {app_count_data.notna().sum()}")
    print(f"   Уникальных значений: {app_count_data.nunique()}")
    
    # Показываем первые 10 значений
    print(f"\n   Первые 10 значений:")
    for i, val in enumerate(app_count_data.head(10)):
        print(f"     {i}: '{val}' (тип: {type(val)})")
    
    # Ищем строки с программами
    print(f"\n5️⃣ Поиск целевых программ...")
    
    # Проверяем есть ли колонка с названиями программ
    program_columns = []
    for col in df.columns:
        if any(word in col.lower() for word in ['программ', 'направл', 'специальн']):
            program_columns.append(col)
    
    if program_columns:
        print(f"✅ Найдены колонки с программами: {program_columns}")
        
        for program_col in program_columns:
            print(f"\n   Анализ колонки '{program_col}':")
            programs = df[program_col].dropna()
            print(f"   Записей: {len(programs)}")
            
            # Показываем программы содержащие "ОНЛАЙН"
            online_programs = programs[programs.str.contains('ОНЛАЙН', na=False, case=False)]
            print(f"   ОНЛАЙН программ: {len(online_programs)}")
            
            if len(online_programs) > 0:
                print("   Найденные ОНЛАЙН программы:")
                for i, prog in enumerate(online_programs.head(10)):
                    print(f"     {i}: '{prog}'")
            
            # Проверяем наши целевые программы
            print(f"\n   Проверка целевых программ:")
            for target_prog in HSE_TARGET_PROGRAMS[:5]:  # Проверяем первые 5
                matches = programs[programs.str.contains(target_prog, na=False, case=False)]
                if len(matches) > 0:
                    print(f"     ✅ '{target_prog}': найдено {len(matches)} совпадений")
                    # Показываем соответствующие значения заявлений
                    for idx in matches.index:
                        count_val = df.loc[idx, found_column]
                        print(f"        Заявлений: '{count_val}'")
                else:
                    print(f"     ❌ '{target_prog}': не найдено")
    else:
        print("❌ Не найдены колонки с названиями программ")
        
        # Показываем все колонки для анализа
        print("\n   Показываем первые строки всех колонок:")
        print(df.head(3).to_string())
    
    # Сохраняем Excel для анализа
    print(f"\n6️⃣ Сохранение Excel для ручного анализа...")
    try:
        df.to_excel('debug_hse_data.xlsx', index=False)
        print("✅ Данные сохранены в debug_hse_data.xlsx")
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")

if __name__ == "__main__":
    debug_hse_excel()