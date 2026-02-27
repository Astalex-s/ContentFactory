# Подключение платформ (YouTube, VK, TikTok)

Полная инструкция по настройке OAuth для публикации видео из ContentFactory в YouTube, VK и TikTok.

**Этап 8:** Учётные данные OAuth-приложений (client_id, client_secret) хранятся **только в БД** в зашифрованном виде. Добавление и управление OAuth-приложениями — через UI в настройках.

---

## Общие требования

1. **Переменные окружения** — только данные, не меняющиеся при подключении дополнительных аккаунтов:
   - **OAUTH_SECRET_KEY** — ключ Fernet для шифрования токенов и учётных данных (32 байта, base64).  
     Генерация: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - **OAUTH_ENCRYPTION_SALT** — salt для PBKDF2 (случайная строка).  
     Генерация: `python -c "import secrets; print(secrets.token_urlsafe(16))"`
   - **API_BASE_URL** — URL бэкенда, на который OAuth-провайдеры отправляют callback.  
     Локально: `http://localhost:8000` | Продакшен: `https://your-domain.com`
   - **FRONTEND_URL** — URL фронтенда для редиректа после OAuth.  
     Локально: `http://localhost:5173` | Продакшен: `https://your-domain.com`

2. **OAuth-приложения (client_id, client_secret)** — добавляются через UI в настройках (страница Settings → блок «OAuth-приложения»). Все данные хранятся в БД в зашифрованном виде.

3. **Подключение аккаунта** — на странице Creators выбираете платформу и OAuth-приложение из списка (добавленных в настройках), затем нажимаете «Подключить». Если приложений для платформы нет — отображается подсказка с кнопкой перехода в настройки.

**ВАЖНО:** Токены OAuth и учётные данные OAuth-приложений шифруются с помощью Fernet (PBKDF2 + AES) перед сохранением в БД. Требуются оба ключа: `OAUTH_SECRET_KEY` и `OAUTH_ENCRYPTION_SALT`. Без них приложение не сможет сохранять и расшифровывать данные.

---

## 1. YouTube

### 1.1. Создание проекта в Google Cloud

1. Откройте [Google Cloud Console](https://console.cloud.google.com/).
2. Создайте проект или выберите существующий.
3. В боковом меню: **APIs & Services** → **Library**.
4. Найдите **YouTube Data API v3** и включите его.

### 1.2. Настройка OAuth consent screen

1. **APIs & Services** → **OAuth consent screen**.
2. Выберите **External** (внешние пользователи).
3. Заполните:
   - **App name**: ContentFactory
   - **User support email**: ваш email
   - **Developer contact**: ваш email
4. **Scopes** → **Add or remove scopes** → добавьте:
   - `https://www.googleapis.com/auth/youtube.upload`
   - `https://www.googleapis.com/auth/youtube`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`
5. **Test users** (если приложение в режиме Testing): добавьте email для тестирования.
6. Сохраните.

### 1.3. Создание OAuth 2.0 credentials

1. **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth client ID**.
2. **Application type**: **Web application**.
3. **Name**: ContentFactory (или любое).
4. **Authorized JavaScript origins** (если нужен):
   - `http://localhost:5173` (локально)
   - `https://your-domain.com` (продакшен)
5. **Authorized redirect URIs** (обязательно, **точное совпадение**):
   - `http://localhost:8000/social/callback/youtube` (если `API_BASE_URL=http://localhost:8000`)
   - `http://127.0.0.1:8000/social/callback/youtube` (если используете 127.0.0.1 — добавьте оба)
   - `https://your-domain.com/social/callback/youtube` (продакшен)
6. **Create** → скопируйте **Client ID** и **Client Secret**.

### 1.4. Добавление OAuth-приложения в ContentFactory

1. Перейдите в **Settings** (Настройки) → блок **«OAuth-приложения для подключения аккаунтов»**.
2. Нажмите **«+ Добавить OAuth-приложение»**.
3. Заполните форму:
   - **Платформа**: YouTube
   - **Название**: Мое YouTube приложение (или любое)
   - **Client ID**: скопируйте из Google Cloud Console
   - **Client Secret**: скопируйте из Google Cloud Console
   - **Redirect URI**: оставьте пустым (будет использован по умолчанию из `API_BASE_URL`)
4. Нажмите **«Сохранить»**.

### 1.5. Подключение аккаунта YouTube

1. Перейдите в **Creators** (Подключенные аккаунты).
2. Выберите **Платформа**: YouTube.
3. Выберите **OAuth-приложение** из списка (добавленное в настройках).
4. Нажмите **«Подключить»**.
5. Должен открыться Google OAuth.
6. После авторизации — редирект на `FRONTEND_URL/?social=connected&platform=youtube`.

### 1.6. Как изменить параметры в Google Cloud Console

Если credentials уже созданы и нужно изменить redirect URI, Client ID, scopes и т.д.:

#### Открыть настройки OAuth

1. Перейдите на [Google Cloud Console](https://console.cloud.google.com/).
2. Выберите нужный проект (справа вверху).
3. В боковом меню: **APIs & Services** → **Credentials**.
4. В списке **OAuth 2.0 Client IDs** найдите своё приложение (например, ContentFactory).
5. Нажмите на **название** или иконку **карандаша (Edit)** справа.

#### Изменить OAuth consent screen (экран согласия)

1. **APIs & Services** → **OAuth consent screen**.
2. Нажмите **EDIT APP**.
3. **App information** — изменить название, email.
4. **Scopes** → **ADD OR REMOVE SCOPES** — добавить/удалить:
   - `https://www.googleapis.com/auth/youtube.upload`
   - `https://www.googleapis.com/auth/youtube`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`
5. **Test users** — добавить email для тестирования (если приложение в режиме Testing).
6. **SAVE AND CONTINUE** → **BACK TO DASHBOARD**.

#### Изменить OAuth Client (Client ID, redirect URI)

1. **APIs & Services** → **Credentials**.
2. В блоке **OAuth 2.0 Client IDs** нажмите на имя клиента (или иконку редактирования).
3. Откроется форма **Edit OAuth client**:
   - **Name** — название приложения.
   - **Authorized JavaScript origins** — домены, с которых разрешены запросы (например, `http://localhost:5173`).
   - **Authorized redirect URIs** — **обязательно** добавьте точный URL:
     - `http://localhost:8000/social/callback/youtube`
     - `http://127.0.0.1:8000/social/callback/youtube` (если используете 127.0.0.1)
     - `https://your-domain.com/social/callback/youtube` (продакшен)
4. Нажмите **SAVE**.

#### Важно

- **Client ID** и **Client Secret** изменить нельзя — только скопировать. Если нужен новый секрет, создайте новый OAuth client.
- Изменения в redirect URI вступают в силу **сразу** (иногда с задержкой 1–5 минут).
- URL в **Authorized redirect URIs** должен **точно** совпадать с `API_BASE_URL` + `/social/callback/youtube` (без лишнего слеша в конце).

#### Прямые ссылки

- [Credentials](https://console.cloud.google.com/apis/credentials)
- [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)

---

## 2. VK (ВКонтакте)

### 2.1. Создание приложения (старая платформа)

1. Откройте [Создание приложения VK](https://vk.com/editapp?act=create).
2. Выберите тип **Веб-сайт**.
3. Заполните:
   - **Название**: ContentFactory
   - **Адрес сайта**: `http://localhost:5173` (локально) или `https://your-domain.com`
   - **Базовый домен**: `localhost` или `your-domain.com`
4. Подтвердите SMS-кодом.
5. **Настройки** → **Стандартные приложения**:
   - Включите **Доступ к API**.
   - **Права доступа**: `video` (для загрузки видео).

### 2.2. Альтернатива: VK ID (новая платформа)

1. Откройте [VK ID для бизнеса](https://id.vk.com/business/go).
2. Войдите через VK Бизнес ID.
3. **Мои приложения** → **Добавить приложение**.
4. Выберите платформу **Web**.
5. Укажите **Доверенный redirect URL**:
   - `http://localhost:8000/social/callback/vk` (локально)
   - `https://your-domain.com/social/callback/vk` (продакшен)
6. **Профиль бизнеса** нужно подтвердить в течение 60 дней.

> **Примечание:** ContentFactory использует OAuth по адресу `oauth.vk.ru`. Если приложение создано в VK ID, убедитесь, что redirect URI совпадает с настройками.

### 2.3. Получение ID и Secret

**Старая платформа:**

1. В [Мои приложения](https://vk.com/apps?act=manage) откройте приложение.
2. **ID приложения** (Client ID) — в URL или в настройках.
3. **Защищённый ключ** (Client Secret) — в разделе **Настройки**.

**VK ID:**

1. В кабинете VK ID — **ID приложения** и **Сервисный ключ доступа** или **Защищённый ключ**.

### 2.4. Добавление OAuth-приложения в ContentFactory

1. Перейдите в **Settings** (Настройки) → блок **«OAuth-приложения для подключения аккаунтов»**.
2. Нажмите **«+ Добавить OAuth-приложение»**.
3. Заполните форму:
   - **Платформа**: VK
   - **Название**: Мое VK приложение (или любое)
   - **Client ID**: ID приложения из VK ID
   - **Client Secret**: Защищённый ключ из VK ID
   - **Redirect URI**: оставьте пустым (будет использован по умолчанию из `API_BASE_URL`)
4. Нажмите **«Сохранить»**.

### 2.5. Подключение аккаунта VK

1. Перейдите в **Creators** (Подключенные аккаунты).
2. Выберите **Платформа**: VK.
3. Выберите **OAuth-приложение** из списка (добавленное в настройках).
4. Нажмите **«Подключить»**.
5. Должен открыться VK ID OAuth.
6. После авторизации — редирект на `FRONTEND_URL/?social=connected&platform=vk`.

**Redirect URI:** Callback должен быть доступен по адресу:
- Локально: `http://localhost:8000/social/callback/vk`
- Продакшен: `https://your-domain.com/social/callback/vk`

Убедитесь, что этот URL введён в настройках приложения VK.

### 2.6. Проверка

- Нажмите «Подключить VK», пройдите авторизацию.
- Редирект на `FRONTEND_URL/?social=connected&platform=vk`.

---

## 3. TikTok

### 3.1. Ограничения

**TikTok предоставляет ограниченный API для загрузки видео.**

- OAuth-подключение реализовано в ContentFactory (можно подключать аккаунт).
- Загрузка видео (`upload_video`) возвращает `NotImplementedError` — пока нет полной интеграции.

### 3.2. Создание приложения

1. Откройте [TikTok for Developers](https://developers.tiktok.com/) и создайте приложение.
2. Включите нужные scopes (video.upload, user.info и т.д.).
3. Настройте Redirect URI в настройках приложения.

### 3.3. Redirect URI

- Локально: `http://localhost:8000/social/callback/tiktok`
- Продакшен: `https://your-domain.com/social/callback/tiktok`

### 3.4. Добавление OAuth-приложения в ContentFactory

1. Перейдите в **Settings** (Настройки) → блок **«OAuth-приложения для подключения аккаунтов»**.
2. Нажмите **«+ Добавить OAuth-приложение»**.
3. Заполните форму:
   - **Платформа**: TikTok
   - **Название**: Мое TikTok приложение (или любое)
   - **Client ID**: Client Key из TikTok Developer Portal
   - **Client Secret**: Client Secret из TikTok Developer Portal
   - **Redirect URI**: оставьте пустым (будет использован по умолчанию из `API_BASE_URL`)
4. Нажмите **«Сохранить»**.

### 3.5. Подключение аккаунта TikTok

1. Перейдите в **Creators** (Подключенные аккаунты).
2. Выберите **Платформа**: TikTok.
3. Выберите **OAuth-приложение** из списка (добавленное в настройках).
4. Нажмите **«Подключить»».
5. Должен открыться TikTok OAuth.
6. После авторизации — редирект на `FRONTEND_URL/?social=connected&platform=tiktok`.

### 3.6. Текущий статус

- Кнопка «Подключить TikTok» есть в UI.
- OAuth flow реализован; при наличии credentials приложение должно работать.
- Публикация видео на TikTok пока недоступна (ограниченный API).

---

## 4. Сводка переменных `.env`

```env
# OAuth & Social — ключи шифрования (обязательные)
OAUTH_SECRET_KEY=              # python -c "import secrets; print(secrets.token_urlsafe(32))"
OAUTH_ENCRYPTION_SALT=         # python -c "import secrets; print(secrets.token_urlsafe(16))"
DEFAULT_USER_ID=00000000-0000-0000-0000-000000000001

# URLs (для OAuth callback и редиректов)
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173

# VK video upload (токен сообщества, опционально)
VK_SERVICE_KEY=
VK_GROUP_ID=
VK_COMMUNITY_TOKEN=
```

> **Важно:** YOUTUBE_CLIENT_ID, VK_CLIENT_ID, TIKTOK_CLIENT_KEY и их секреты
> **не хранятся** в `.env`. Все OAuth-приложения (client_id, client_secret)
> добавляются через UI (Настройки) и хранятся **только в БД** в зашифрованном виде.

**Продакшен:**

```env
API_BASE_URL=https://your-domain.com
FRONTEND_URL=https://your-domain.com
```

---

## 5. Продакшен: nginx и callback

Убедитесь, что callback-эндпоинты доступны снаружи:

- `https://your-domain.com/social/callback/youtube`
- `https://your-domain.com/social/callback/vk`
- `https://your-domain.com/social/callback/tiktok`

Если API за nginx — проксируйте `/social/` на backend.

---

## 6. Устранение неполадок

| Ошибка | Причина | Решение |
|-------|---------|---------|
| `Missing required parameter: client_id` | Не добавлено OAuth-приложение | Добавьте OAuth-приложение в Настройках (UI) |
| `redirect_uri_mismatch` | Redirect URI не совпадает | Добавьте точный URL в настройках приложения |
| `DEFAULT_USER_ID is not set` | Не задан `DEFAULT_USER_ID` | Добавьте UUID в `.env` |
| `OAUTH_SECRET_KEY` ошибки | Пустой или неверный ключ | Сгенерируйте Fernet-ключ |
| `invalid_grant` (Google) | Истёк code, повторное использование или **redirect_uri не совпадает** | Пройдите OAuth заново; проверьте, что redirect URI в Google Console **точно** совпадает с `API_BASE_URL` + `/social/callback/youtube` |
| VK: приложение заблокировано | Профиль не подтверждён | Подтвердите бизнес-профиль в VK ID |

---

## 7. Безопасность

- Никогда не коммитьте `.env` в Git.
- Храните `OAUTH_SECRET_KEY` и client secrets в защищённом хранилище (GitHub Secrets, Vault и т.п.).
- В продакшене используйте HTTPS для `API_BASE_URL` и `FRONTEND_URL`.
