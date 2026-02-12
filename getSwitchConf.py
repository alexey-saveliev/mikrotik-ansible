import yaml
import gspread
from google.oauth2.service_account import Credentials
from typing import Dict, List
import os
import re

# Добавляем Dumper для сохранения порядка в YAML, отключаем якоря и устанавливаем отступ 2 пробела
class OrderedDumper(yaml.Dumper):
    def ignore_aliases(self, data):
        return True  # Отключаем использование якорей и ссылок
    
    def increase_indent(self, flow=False, indentless=False):
        return super(OrderedDumper, self).increase_indent(flow, False)

def _dict_representer(dumper, data):
    return dumper.represent_mapping(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        data.items()
    )

OrderedDumper.add_representer(dict, _dict_representer)

# Настройка доступа к Google Sheets API
def setup_gsheets_api(credentials_file: str = '.GScredentials.json'):
    """Настройка подключения к Google Sheets API"""
    
    # Область доступа
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets.readonly',
        'https://www.googleapis.com/auth/drive.readonly'
    ]
    
    # Аутентификация
    creds = Credentials.from_service_account_file(
        credentials_file, 
        scopes=scopes
    )
    
    return gspread.authorize(creds)

def parse_settings(settings_str: str):
    """
    Парсит строку настроек в структуру YAML
    Преобразует tagged в формат списка [11, 20, 30]
    """
    if not settings_str:
        return None
    
    try:
        # Пробуем распарсить как YAML строку
        parsed = yaml.safe_load(settings_str)
        
        # Если получился словарь, обрабатываем его
        if isinstance(parsed, dict):
            for key, value in parsed.items():
                # Обрабатываем только ключ tagged
                if key == 'tagged':
                    if isinstance(value, str):
                        # Пробуем распарсить строку как список
                        # Убираем квадратные скобки, если есть, и разбиваем по запятым
                        clean_str = value.strip('[]').strip()
                        if clean_str:
                            # Разбиваем по запятым и преобразуем в числа
                            items = []
                            for item in clean_str.split(','):
                                item = item.strip()
                                if item.isdigit():
                                    items.append(int(item))
                                else:
                                    items.append(item)
                            parsed[key] = items
                    elif isinstance(value, list):
                        # Если это уже список, убеждаемся что числа целые
                        parsed[key] = [int(v) if isinstance(v, str) and v.isdigit() else v for v in value]
            
            return parsed
        else:
            return parsed
    except Exception:
        # Если не получилось, пробуем другие форматы
        try:
            # Проверяем, не является ли строка форматом "tagged: [11,20,30]"
            if 'tagged:' in settings_str:
                result = {}
                lines = settings_str.strip().split('\n')
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == 'tagged':
                            # Обрабатываем как список
                            clean_value = value.strip('[]').strip()
                            if clean_value:
                                items = []
                                for item in clean_value.split(','):
                                    item = item.strip()
                                    if item.isdigit():
                                        items.append(int(item))
                                    else:
                                        items.append(item)
                                result[key] = items
                            else:
                                result[key] = []
                        else:
                            # Для остальных ключей оставляем как есть
                            result[key] = value
                return result
            else:
                # Возвращаем как строку
                return settings_str
        except:
            return settings_str

def get_port_profiles(client, spreadsheet_id: str) -> Dict[str, str]:
    """
    Получение профилей портов из листа 'Port profiles'
    
    Args:
        client: Авторизованный клиент gspread
        spreadsheet_id: ID Google таблицы
        
    Returns:
        Словарь {описание: настройки}
    """
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # Ищем лист с названием "Port profiles"
        try:
            worksheet = spreadsheet.worksheet("Port profiles")
        except gspread.WorksheetNotFound:
            print("Лист 'Port profiles' не найден, пропускаю загрузку профилей")
            return {}
        
        print("Загружаю профили портов из листа 'Port profiles'...")
        
        # Получаем все данные из листа
        data = worksheet.get_all_values()
        
        if not data:
            print("Лист 'Port profiles' пуст")
            return {}
        
        # Предполагаем, что первая строка - заголовки
        headers = data[0]
        rows = data[1:]
        
        # Ищем нужные столбцы
        try:
            desc_idx = headers.index('Description')
            settings_idx = headers.index('Settings')
        except ValueError as e:
            print(f"В листе 'Port profiles' не найдены необходимые столбцы: {e}")
            return {}
        
        # Формируем словарь профилей
        profiles = {}
        for i, row in enumerate(rows, start=2):
            if len(row) <= max(desc_idx, settings_idx):
                continue
            
            description = row[desc_idx].strip()
            settings = row[settings_idx].strip()
            
            if description and settings:
                profiles[description] = settings
        
        print(f"Загружено {len(profiles)} профилей портов")
        return profiles
        
    except Exception as e:
        print(f"Ошибка при получении профилей портов: {e}")
        return {}

def get_sheet_data(client, spreadsheet_id: str, port_profiles: Dict[str, str]) -> Dict[str, List[Dict]]:
    """
    Получение данных из всех листов Google таблицы
    
    Args:
        client: Авторизованный клиент gspread
        spreadsheet_id: ID Google таблицы
        port_profiles: Словарь профилей портов
        
    Returns:
        Словарь с данными по листам
    """
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
        all_data = {}
        
        for worksheet in spreadsheet.worksheets():
            # Пропускаем лист с профилями портов
            if worksheet.title == "Port profiles":
                continue
                
            sheet_name = worksheet.title
            print(f"Обрабатываю лист: {sheet_name}")
            
            # Получаем все данные из листа
            data = worksheet.get_all_values()
            
            if not data or len(data) < 2:  # Проверяем, что есть хотя бы 2 строки (заголовки + данные)
                print(f"Лист '{sheet_name}' не содержит достаточно данных, пропускаю")
                continue
            
            # Заголовки находятся во второй строке (индекс 1)
            headers = data[1]
            # Данные начинаются с третьей строки (индекс 2)
            rows = data[2:]
            
            # Ищем нужные столбцы
            try:
                port_idx = headers.index('Порт')
                dest_idx = headers.index('Назначение')
                desc_idx = headers.index('Описание')
            except ValueError as e:
                print(f"В листе '{sheet_name}' не найдены необходимые столбцы: {e}")
                print(f"Доступные заголовки: {headers}")
                continue
            
            # Формируем список словарей с данными
            sheet_data = []
            for i, row in enumerate(rows, start=3):  # start=3 потому что данные начинаются с 3-й строки
                if len(row) <= max(port_idx, dest_idx, desc_idx):
                    print(f"Предупреждение: строка {i} в листе '{sheet_name}' имеет недостаточно данных")
                    continue
                
                port = row[port_idx].strip() if port_idx < len(row) else ""
                destination = row[dest_idx].strip() if dest_idx < len(row) else ""
                description = row[desc_idx].strip() if desc_idx < len(row) else ""
                
                if port:  # Добавляем только если есть порт
                    # Создаем запись
                    record = {
                        'name': port,
                        'comment': description
                    }
                    
                    # Добавляем Назначение только если оно не пустое
                    # if destination:
                    #     record['Назначение'] = destination
                    
                    # Проверяем, есть ли настройки для этого назначения в профилях портов
                    settings_str = None
                    if destination in port_profiles:
                        settings_str = port_profiles[destination]
                    elif description in port_profiles:  # Проверяем также по описанию
                        settings_str = port_profiles[description]
                    
                    # Добавляем Settings если нашли профиль
                    if settings_str:
                        settings_parsed = parse_settings(settings_str)
                        if settings_parsed:
                            # Если settings_parsed это словарь, добавляем все его ключи в record
                            if isinstance(settings_parsed, dict):
                                for key, value in settings_parsed.items():
                                    record[key] = value
                            else:
                                # Если это не словарь, сохраняем как есть
                                record['Settings'] = settings_parsed
                    
                    sheet_data.append(record)
            
            all_data[sheet_name] = sheet_data
            print(f"  - Загружено записей: {len(sheet_data)}")
            
        return all_data
        
    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
        raise

def convert_tagged_to_flow_style(obj):
    """
    Рекурсивно преобразует все значения ключа 'tagged' в списки
    и помечает их для вывода в flow style через словарь-обертку
    """
    if isinstance(obj, dict):
        new_dict = {}
        for key, value in obj.items():
            if key == 'tagged' and isinstance(value, list):
                # Вместо создания кастомного класса, создаем словарь-обертку
                # который будет обработан специальным representer
                new_dict[key] = {'__flow_style_list__': True, 'data': value}
            else:
                new_dict[key] = convert_tagged_to_flow_style(value)
        return new_dict
    elif isinstance(obj, list):
        return [convert_tagged_to_flow_style(item) for item in obj]
    else:
        return obj

def create_yaml_files(data: Dict[str, List[Dict]], output_dir: str = 'tmp'):
    """
    Создание YAML-файлов из данных
    Специальная обработка для ключа 'tagged' - вывод в flow style
    Отступ - 2 пробела
    
    Args:
        data: Словарь с данными по листам
        output_dir: Директория для сохранения файлов
    """
    
    # Создаем директорию, если её нет
    os.makedirs(output_dir, exist_ok=True)
    
    # Создаем кастомный Dumper с representer для flow style списков и отступом 2 пробела
    class TaggedFlowDumper(OrderedDumper):
        def increase_indent(self, flow=False, indentless=False):
            return super(TaggedFlowDumper, self).increase_indent(flow, False)
    
    # Representer для словарей-оберток flow style списков
    def represent_flow_style_wrapper(dumper, data):
        if isinstance(data, dict) and data.get('__flow_style_list__'):
            # Извлекаем оригинальный список и представляем его в flow style
            return dumper.represent_sequence(
                'tag:yaml.org,2002:seq', 
                data['data'], 
                flow_style=True
            )
        # Для обычных словарей используем стандартный representer
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            data.items()
        )
    
    TaggedFlowDumper.add_representer(dict, represent_flow_style_wrapper)
    
    for sheet_name, sheet_data in data.items():
        if not sheet_data:
            print(f"Лист '{sheet_name}' не содержит данных, пропускаю")
            continue
        
        # Преобразуем данные: помечаем списки tagged для flow style
        modified_data = convert_tagged_to_flow_style(sheet_data)
        
        # Формируем структуру для YAML
        yaml_structure = {
            'bridge_port': modified_data
        }
        
        # Создаем имя файла (без недопустимых символов)
        safe_filename = ''.join(c for c in sheet_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        yaml_filename = f"{safe_filename}.yaml"
        filepath = os.path.join(output_dir, yaml_filename)
        
        try:
            # Записываем YAML с отступом 2 пробела
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(
                    yaml_structure, 
                    f, 
                    Dumper=TaggedFlowDumper,
                    allow_unicode=True, 
                    default_flow_style=False,
                    sort_keys=False,
                    indent=2,  # Явно указываем отступ 2 пробела
                    width=1000  # Увеличиваем ширину строки, чтобы избежать переносов
                )
            
            print(f"Создан файл: {filepath}")
            print(f"  - Количество записей: {len(sheet_data)}")
            
            # Дополнительно выводим первые несколько записей для проверки
            for j, record in enumerate(sheet_data[:3]):
                if 'tagged' in record:
                    print(f"    Запись {j+1}: tagged = {record['tagged']}")
            
        except Exception as e:
            print(f"Ошибка при создании файла {yaml_filename}: {e}")

def main():
    # Конфигурация
    SPREADSHEET_ID = '1-ED5c6a-u5HnJh07HS_YKUyIdqrz5GfYz1DFoRyiIng'  # Замените на ваш ID
    CREDENTIALS_FILE = '.GScredentials.json'  # Файл с учетными данными
    OUTPUT_DIR = 'tmp'  # Директория для сохранения YAML файлов
    
    try:
        # 1. Настройка API
        print("Настройка подключения к Google Sheets API...")
        client = setup_gsheets_api(CREDENTIALS_FILE)
        
        # 2. Получение профилей портов
        print(f"Получение данных из таблицы с ID: {SPREADSHEET_ID}")
        port_profiles = get_port_profiles(client, SPREADSHEET_ID)
        
        # 3. Получение данных с подстановкой профилей
        print("Получение данных из остальных листов...")
        data = get_sheet_data(client, SPREADSHEET_ID, port_profiles)
        
        if not data:
            print("Не удалось получить данные из таблицы")
            return
        
        # 4. Создание YAML файлов
        print(f"\nСоздание YAML файлов в директории: {OUTPUT_DIR}")
        create_yaml_files(data, OUTPUT_DIR)
        
        print("\nГотово!")
        
    except FileNotFoundError:
        print(f"Файл учетных данных '{CREDENTIALS_FILE}' не найден")
        print("Создайте сервисный аккаунт в Google Cloud Console и скачайте credentials.json")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    main()

#    1-ED5c6a-u5HnJh07HS_YKUyIdqrz5GfYz1DFoRyiIng