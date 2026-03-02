# Загрузка видео с постом в VK — официальный способ

Документ описывает рабочий flow загрузки видео и публикации поста в VK на основе официального OAuth API.

---

## Ограничение VK API

**Метод `video.save` требует одобрения от VK.** По умолчанию приложения VK ID могут не иметь доступа к этому методу. Для получения доступа отправьте запрос в поддержку разработчиков VK: **devsupport@corp.vk.com**. Укажите ID приложения, опишите сценарий использования (загрузка видео через API для маркетингового контента). После одобрения загрузка видео будет работать через OAuth-токен.

---

## Официальный flow (3 шага)

### Этап 1: Получить URL для загрузки

**Метод:** `video.save`  
**URL:** `https://api.vk.com/method/video.save`  
**Версия API:** 5.199

**Ключевые параметры:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `name` | string | Название видео (до 128 символов) |
| `description` | string | Описание (до 5000 символов). При `wallpost=1` используется как текст поста |
| `wallpost` | 0/1 | 1 — после загрузки сразу опубликовать пост на стене |
| `is_private` | 0/1 | 1 — приватное, 0 — публичное |
| `access_token` | string | OAuth-токен пользователя (scope: video, wall) |
| `v` | string | Версия API (5.199) |

**Ответ:** `{ "response": { "upload_url": "...", "video_id": 123, "owner_id": 123456 } }`

### Этап 2: Загрузить файл

**Метод:** POST на `upload_url`  
**Content-Type:** `multipart/form-data`  
**Поле:** `video_file` — бинарные данные MP4

### Этап 3: Ожидание обработки

VK обрабатывает видео асинхронно. Опрашивать `video.get` до `processing=0`.

---

## Требования

- **OAuth (VK ID):** scope `vkid.personal_info video wall`
- **Одобрение VK:** запрос в devsupport@corp.vk.com для доступа к `video.save`
- Публикация идёт на **личную стену** пользователя (без group_id)

---

## Ссылки

- [video.save](https://dev.vk.com/method/video.save) — официальная документация
- [VK ID scopes](https://id.vk.com/about/business/go/docs/ru/vkid/latest/vk-id/connection/work-with-user-info/scopes)
