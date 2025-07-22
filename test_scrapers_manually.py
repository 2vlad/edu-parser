#!/usr/bin/env python3
"""
Ручной тест отдельных скрейперов для проверки их работоспособности
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.storage import Storage
from core.logging_config import setup_logging, get_logger

# Setup logging
setup_logging(log_level="INFO")
logger = get_logger(__name__)

def test_single_scraper():
    """Протестировать один скрейпер на выбор"""
    print("🧪 ТЕСТ ОТДЕЛЬНЫХ СКРЕЙПЕРОВ")
    print("=" * 60)
    
    # Доступные скрейперы для теста
    test_scrapers = [
        ("HSE Excel", "scrapers.hse", "scrape_hse_online_cs_2024"),
        ("MIPT HTML", "scrapers.mipt", "scrape_mipt_data_science"),
        ("MEPhI HTML", "scrapers.mephi", "scrape_mephi_machine_learning")
    ]
    
    print("Выберите скрейпер для тестирования:")
    for i, (name, module, func) in enumerate(test_scrapers, 1):
        print(f"{i}. {name}")
    print("4. Тестировать все")
    print("5. Показать доступные скрейперы")
    
    try:
        choice = input("\nВведите номер (1-5): ").strip()
        
        if choice == "5":
            show_available_scrapers()
            return
        elif choice == "4":
            test_multiple_scrapers()
            return
        elif choice in ["1", "2", "3"]:
            idx = int(choice) - 1
            name, module_name, func_name = test_scrapers[idx]
            
            print(f"\n🔍 Тестируем {name}...")
            print("-" * 40)
            
            # Import and run scraper
            try:
                module = __import__(module_name, fromlist=[func_name])
                scraper_func = getattr(module, func_name)
                
                print(f"⏳ Запуск {func_name}...")
                start_time = datetime.now()
                
                result = scraper_func()
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                print(f"⏱️  Время выполнения: {duration:.2f}s")
                print(f"📊 Результат:")
                print(f"   Status: {result.get('status', 'unknown')}")
                print(f"   Count: {result.get('count', 'N/A')}")
                print(f"   Name: {result.get('name', 'N/A')}")
                if result.get('error'):
                    print(f"   Error: {result['error']}")
                
                # Save to database
                if input("\n💾 Сохранить результат в базу? (y/n): ").lower() == 'y':
                    save_result_to_db(result)
                    
            except Exception as e:
                print(f"❌ Ошибка при запуске скрейпера: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("❌ Неверный выбор")
            
    except KeyboardInterrupt:
        print("\n⏹️  Тест прерван пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


def show_available_scrapers():
    """Показать все доступные скрейперы"""
    print("\n📋 ДОСТУПНЫЕ СКРЕЙПЕРЫ")
    print("=" * 60)
    
    try:
        from core.registry import ScraperRegistry
        
        # Mock storage
        class MockStorage:
            def load_enabled_scrapers(self): return []
        
        registry = ScraperRegistry(storage=MockStorage())
        count = registry.discover_scrapers()
        
        print(f"Найдено {count} скрейперов:\n")
        
        # Group by module
        by_module = {}
        for scraper_id, info in registry.scrapers.items():
            module = info['module']
            if module not in by_module:
                by_module[module] = []
            by_module[module].append((scraper_id, info['config'].get('name', 'Unknown')))
        
        for module_name, scrapers in sorted(by_module.items()):
            print(f"📁 {module_name}:")
            for scraper_id, name in scrapers:
                print(f"   - {scraper_id}: {name}")
            print()
            
    except Exception as e:
        print(f"❌ Ошибка при получении списка: {e}")


def test_multiple_scrapers():
    """Протестировать несколько скрейперов"""
    print("\n🚀 ТЕСТ НЕСКОЛЬКИХ СКРЕЙПЕРОВ")
    print("=" * 60)
    
    # Выберем по одному скрейперу из каждого модуля для быстрой проверки
    test_scrapers = [
        ("HSE", "scrapers.hse", lambda: test_hse_scraper()),
        ("MIPT", "scrapers.mipt", lambda: test_mipt_scraper()),
        ("MEPhI", "scrapers.mephi", lambda: test_mephi_scraper())
    ]
    
    results = []
    
    for name, module_name, test_func in test_scrapers:
        print(f"\n🔍 Тестируем {name}...")
        try:
            result = test_func()
            results.append((name, result))
            
            status_icon = "✅" if result.get('status') == 'success' else "❌"
            print(f"{status_icon} {name}: {result.get('status')} | Count: {result.get('count', 'N/A')}")
            
        except Exception as e:
            print(f"❌ {name}: Ошибка - {e}")
            results.append((name, {'status': 'error', 'error': str(e)}))
    
    # Summary
    print("\n📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("-" * 30)
    successful = sum(1 for _, r in results if r.get('status') == 'success')
    print(f"Успешно: {successful}/{len(results)}")
    
    if successful > 0:
        print(f"\n💾 Сохранить {successful} успешных результатов в базу? (y/n): ", end="")
        if input().lower() == 'y':
            for name, result in results:
                if result.get('status') == 'success':
                    save_result_to_db(result)
                    print(f"✅ {name} сохранен")


def test_hse_scraper():
    """Тестировать один HSE скрейпер"""
    from scrapers.hse import get_scrapers
    scrapers = get_scrapers()
    if scrapers:
        scraper_func, config = scrapers[0]  # Берем первый
        print(f"   Тестируем: {config['name']}")
        return scraper_func(config)  # Передаем config как аргумент
    else:
        return {'status': 'error', 'error': 'No HSE scrapers found'}


def test_mipt_scraper():
    """Тестировать один MIPT скрейпер"""
    from scrapers.mipt import get_scrapers
    scrapers = get_scrapers()
    if scrapers:
        scraper_func, config = scrapers[0]  # Берем первый
        print(f"   Тестируем: {config['name']}")
        return scraper_func(config)  # Передаем config как аргумент
    else:
        return {'status': 'error', 'error': 'No MIPT scrapers found'}


def test_mephi_scraper():
    """Тестировать один MEPhI скрейпер"""
    from scrapers.mephi import get_scrapers
    scrapers = get_scrapers()
    if scrapers:
        scraper_func, config = scrapers[0]  # Берем первый
        print(f"   Тестируем: {config['name']}")
        return scraper_func(config)  # Передаем config как аргумент
    else:
        return {'status': 'error', 'error': 'No MEPhI scrapers found'}


def save_result_to_db(result):
    """Сохранить результат в базу данных"""
    try:
        storage = Storage()
        success = storage.save_scraper_result(
            scraper_id=result.get('scraper_id', 'manual_test'),
            name=result.get('name', 'Manual Test'),
            count=result.get('count'),
            status=result.get('status', 'unknown'),
            error=result.get('error'),
            date=datetime.now().date()
        )
        
        if success:
            print("✅ Результат сохранен в базу данных")
            print("🌐 Обновите dashboard для просмотра: https://web-production-5db6.up.railway.app/")
        else:
            print("❌ Ошибка при сохранении в базу")
            
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")


def quick_health_check():
    """Быстрая проверка системы"""
    print("\n🏥 БЫСТРАЯ ПРОВЕРКА СИСТЕМЫ")
    print("=" * 40)
    
    # Database connection
    try:
        storage = Storage()
        print("✅ Подключение к Supabase")
    except Exception as e:
        print(f"❌ Подключение к Supabase: {e}")
        return
    
    # Scraper discovery
    try:
        from core.registry import ScraperRegistry
        
        class MockStorage:
            def load_enabled_scrapers(self): return []
        
        registry = ScraperRegistry(storage=MockStorage())
        count = registry.discover_scrapers()
        print(f"✅ Обнаружено скрейперов: {count}")
    except Exception as e:
        print(f"❌ Обнаружение скрейперов: {e}")
    
    # Recent data
    try:
        from datetime import timedelta
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        results = storage.client.table('applicant_counts')\
            .select('date')\
            .gte('date', yesterday.isoformat())\
            .execute()
        
        print(f"✅ Данных за последние 2 дня: {len(results.data)}")
    except Exception as e:
        print(f"❌ Проверка данных: {e}")


def main():
    """Главное меню"""
    print("🔧 РУЧНОЕ ТЕСТИРОВАНИЕ СКРЕЙПЕРОВ")
    print("=" * 60)
    print("Dashboard: https://web-production-5db6.up.railway.app/")
    print("=" * 60)
    
    while True:
        print("\nВыберите действие:")
        print("1. Протестировать один скрейпер")
        print("2. Быстрый тест (по одному из каждого модуля)")
        print("3. Показать все доступные скрейперы")
        print("4. Быстрая проверка системы")
        print("5. Выход")
        
        choice = input("\nВведите номер: ").strip()
        
        if choice == "1":
            test_single_scraper()
        elif choice == "2":
            test_multiple_scrapers()
        elif choice == "3":
            show_available_scrapers()
        elif choice == "4":
            quick_health_check()
        elif choice == "5":
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Программа завершена пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()