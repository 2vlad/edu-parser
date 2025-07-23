# Google Sheets Integration Setup

Этот документ описывает, как настроить автоматическую синхронизацию данных с Google Spreadsheets.

## 📋 Что это дает

- ✅ Автоматическая выгрузка данных после каждого запуска скрейперов
- ✅ Данные сохраняются в удобном формате: вуз | программа | количество | дата
- ✅ Отдельный лист для каждой даты (например, `Data_2025_07_23`)
- ✅ Красивое форматирование с заголовками
- ✅ Отметка синхронизированных записей в базе данных

## 🚀 Быстрая настройка

### 1. Установка зависимостей

```bash
pip install google-api-python-client google-auth python-dotenv
```

### 2. Создание Google Cloud проекта

1. Перейти на https://console.cloud.google.com/
2. Создать новый проект или выбрать существующий
3. Включить Google Sheets API:
   - APIs & Services → Library
   - Найти "Google Sheets API"
   - Нажать "Enable"

### 3. Создание Service Account

1. В Google Cloud Console:
   - IAM & Admin → Service Accounts
   - Create Service Account
   - Название: `edu-parser-sheets`
   - Описание: `Service account for edu-parser Google Sheets integration`

2. Создать ключ:
   - Выбрать созданный аккаунт
   - Keys → Add Key → Create new key
   - Тип: JSON
   - Скачать файл

### 4. Создание Google Spreadsheet

1. Создать новую таблицу: https://sheets.new
2. Назвать её, например: "Edu Parser Data"
3. Поделиться с service account:
   - Share → добавить email service account
   - Права: Editor
   - Убрать галочку "Notify people"

4. Скопировать ID таблицы из URL:
   ```
   https://docs.google.com/spreadsheets/d/ВАША_SPREADSHEET_ID/edit
   ```

### 5. Настройка переменных окружения

Добавить в `.env` файл:

```bash
# Google Sheets Integration
GOOGLE_SPREADSHEET_ID=ваша_spreadsheet_id_здесь
GOOGLE_CREDENTIALS_JSON={"type":"service_account","project_id":"your-project-id",...}
```

**Внимание**: Весь JSON credentials нужно разместить в одной строке!

### 6. Автоматическая настройка

Или использовать скрипт автоматической настройки:

```bash
python setup_google_sheets.py
```

Скрипт поможет пошагово настроить интеграцию.

## 🧪 Тестирование

### Проверка конфигурации

```bash
python test_google_sheets.py
```

### Ручная синхронизация

```bash
python -c "from core.google_sheets import sync_to_sheets; sync_to_sheets()"
```

### Синхронизация конкретной даты

```bash
python -c "from core.google_sheets import sync_to_sheets; sync_to_sheets('2025-07-23')"
```

## 📊 Структура данных в Google Sheets

Каждый лист содержит данные в формате:

| вуз | программа | количество заявлений | дата обновления | scraper_id |
|-----|-----------|----------------------|------------------|------------|
| НИУ ВШЭ | ОНЛАЙН Аналитика больших данных | 366 | 2025-07-23 | hse_аналитика_больших_данных |
| МФТИ | Contemporary combinatorics | 14 | 2025-07-23 | mipt_contemporary_combinatorics |
| МИФИ | Науки о данных | 315 | 2025-07-23 | mephi_науки_о_данных |

## 🔄 Автоматическая синхронизация

Синхронизация происходит автоматически:

1. **После каждого cron запуска** (ежедневно в 23:59)
2. **После ручного запуска** через кнопку "Run All Scrapers Now"

Логи синхронизации можно посмотреть в Railway:
```
✅ Successfully synced data to Google Sheets
⚠️ Google Sheets sync skipped (not configured)
❌ Google Sheets sync error: [error details]
```

## 🛠️ Troubleshooting

### Ошибка "Sheets API not enabled"
```
Enable the Google Sheets API in Google Cloud Console
```

### Ошибка "Permission denied"
```
Check that the service account has Editor access to the spreadsheet
```

### Ошибка "Invalid JSON credentials"
```
Verify GOOGLE_CREDENTIALS_JSON is properly formatted JSON in one line
```

### Синхронизация пропускается
```
Check that both GOOGLE_CREDENTIALS_JSON and GOOGLE_SPREADSHEET_ID are set
```

## 📈 Railway Deployment

Для продакшена в Railway добавить переменные окружения:

1. Railway Dashboard → Variables
2. Добавить:
   - `GOOGLE_SPREADSHEET_ID`: ID вашей таблицы
   - `GOOGLE_CREDENTIALS_JSON`: JSON credentials (в одной строке!)

Переменные автоматически подтянутся при следующем деплое.

## 🔒 Безопасность

- ✅ Service Account используется вместо личного аккаунта
- ✅ Минимальные права (только Sheets API)
- ✅ Credentials хранятся в переменных окружения
- ✅ Не требует OAuth потока

## 📝 Дополнительные возможности

### Исторические данные

Загрузить данные за последние N дней:

```python
from core.google_sheets import GoogleSheetsSync

sheets = GoogleSheetsSync()
sheets.sync_historical_data(days=7)  # Последние 7 дней
```

### Создание нового листа

```python
from core.google_sheets import GoogleSheetsSync

sheets = GoogleSheetsSync()
sheet_id = sheets.get_or_create_sheet("Custom_Sheet_Name")
```

## 🆘 Поддержка

При проблемах:

1. Проверить настройки через `python test_google_sheets.py`
2. Убедиться, что все зависимости установлены
3. Проверить права доступа к таблице
4. Посмотреть логи в Railway/локально

---

💡 **Совет**: После настройки создайте тестовую запись, чтобы убедиться, что всё работает правильно!