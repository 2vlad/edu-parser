#!/usr/bin/env python3
"""
Проверка данных в production Supabase
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.storage import Storage

def check_production_data():
    """Проверка данных в Supabase."""
    print("🔍 ПРОВЕРКА PRODUCTION ДАННЫХ")
    print("=" * 50)
    
    # Проверка подключения
    print("\n1️⃣ Проверка подключения к Supabase...")
    try:
        storage = Storage()
        print("✅ Подключение успешно!")
        print(f"   URL: {os.getenv('SUPABASE_URL')[:30]}...")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return
    
    # Проверка последних данных
    print("\n2️⃣ Проверка последних данных скрейпинга...")
    try:
        # Последние 7 дней
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        results = storage.client.table('applicant_counts')\
            .select('*')\
            .gte('date', start_date.isoformat())\
            .order('created_at', desc=True)\
            .limit(20)\
            .execute()
        
        if results.data:
            print(f"✅ Найдено {len(results.data)} записей за последние 7 дней")
            
            # Группировка по датам
            by_date = {}
            for r in results.data:
                date = r['date']
                if date not in by_date:
                    by_date[date] = {'success': 0, 'error': 0, 'total': 0}
                by_date[date]['total'] += 1
                if r['status'] == 'success':
                    by_date[date]['success'] += 1
                else:
                    by_date[date]['error'] += 1
            
            print("\n📊 Статистика по дням:")
            for date in sorted(by_date.keys(), reverse=True):
                stats = by_date[date]
                success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
                print(f"   {date}: {stats['total']} скрейперов | "
                      f"✅ {stats['success']} успешно | "
                      f"❌ {stats['error']} ошибок | "
                      f"📈 {success_rate:.1f}% успех")
            
            # Показать последние результаты
            print("\n📝 Последние 5 результатов:")
            for r in results.data[:5]:
                status_icon = '✅' if r['status'] == 'success' else '❌'
                count = r.get('count', 'N/A')
                print(f"   {status_icon} {r['date']} | {r['name']} | Заявок: {count}")
                
        else:
            print("❌ Нет данных за последние 7 дней")
            
            # Проверим вообще есть ли данные
            all_results = storage.client.table('applicant_counts')\
                .select('date')\
                .order('date', desc=True)\
                .limit(1)\
                .execute()
            
            if all_results.data:
                print(f"ℹ️  Последние данные от: {all_results.data[0]['date']}")
            else:
                print("❌ В базе нет данных вообще")
                
    except Exception as e:
        print(f"❌ Ошибка при получении данных: {e}")
    
    # Проверка конфигурации скрейперов
    print("\n3️⃣ Проверка конфигурации скрейперов...")
    try:
        scrapers = storage.client.table('scrapers_config')\
            .select('*')\
            .execute()
        
        if scrapers.data:
            enabled = [s for s in scrapers.data if s.get('enabled', False)]
            print(f"✅ Всего скрейперов в конфиге: {len(scrapers.data)}")
            print(f"✅ Включено: {len(enabled)}")
            
            if enabled:
                print("\n🔧 Включенные скрейперы:")
                for s in enabled[:5]:
                    print(f"   - {s['scraper_id']}: {s['name']}")
                if len(enabled) > 5:
                    print(f"   ... и еще {len(enabled) - 5}")
        else:
            print("⚠️  Нет конфигурации скрейперов")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке конфигурации: {e}")
    
    # Проверка Railway переменных
    print("\n4️⃣ Проверка переменных окружения для dashboard...")
    dashboard_vars = {
        'SUPABASE_URL': '✅' if os.getenv('SUPABASE_URL') else '❌',
        'SUPABASE_KEY': '✅' if os.getenv('SUPABASE_KEY') else '❌',
        'FLASK_SECRET_KEY': '✅' if os.getenv('FLASK_SECRET_KEY') else '⚠️ (используется default)',
        'DASHBOARD_ALLOWED_IPS': os.getenv('DASHBOARD_ALLOWED_IPS', 'Не установлено (доступ для всех)')
    }
    
    for var, status in dashboard_vars.items():
        print(f"   {var}: {status}")
    
    print("\n" + "=" * 50)
    print("✅ Проверка завершена!")
    
    # Рекомендации
    print("\n💡 Рекомендации:")
    print("1. Если нет данных - запустите скрейперы: python main.py")
    print("2. Dashboard доступен по адресу: https://artistic-surprise.up.railway.app/")
    print("3. Health check: https://artistic-surprise.up.railway.app/health")
    print("4. Для ограничения доступа установите DASHBOARD_ALLOWED_IPS в Railway")


if __name__ == "__main__":
    check_production_data()