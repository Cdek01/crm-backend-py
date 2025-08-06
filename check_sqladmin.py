#
# # check_sqladmin.py
# import sqladmin
# from sqladmin import filters
# import inspect
#
# print(f"--- Проверка версии sqladmin ---")
# try:
#     print(f"sqladmin.__version__ = {sqladmin.__version__}")
# except AttributeError:
#     print("Не удалось определить версию через __version__")
#
# print(f"\n--- Проверка содержимого модуля sqladmin.filters ---")
# # Выводим все, что есть внутри модуля filters
# for name, obj in inspect.getmembers(filters):
#     if not name.startswith('__'):
#         print(f"Найдено: {name}")
#
# print("\n--- Проверка завершена ---")
#
# # Пробуем создать экземпляр фильтра, чтобы точно воспроизвести ошибку
# try:
#     # ВАЖНО: Мы не создаем экземпляр, а просто получаем доступ к классу
#     test_filter_class = filters.IntegerFilter
#     print("\nУСПЕХ: Класс 'IntegerFilter' найден!")
# except AttributeError as e:
#     print(f"\nОШИБКА: {e}")

from sqladmin.filters import ForeignKeyFilter
print("Import successful")