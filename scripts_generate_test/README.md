# Генератор тестовых товаров

Временная папка. Можно удалить после копирования `products_test.csv` в нужное место.

## Запуск

```powershell
python generate_test_products.py
```

## Результат

- `products_marketplace.json` — 50 товаров в формате маркетплейса
- `products_test.csv` — CSV для импорта через POST /products/import
