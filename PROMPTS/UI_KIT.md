Создай масштабируемый UI-kit (Design System) для SaaS-платформы:

AI-платформа продвижения товаров на маркетплейсах через соцсети.

Стек: React (Vite)
Архитектура: Feature-based
Поддержка масштабирования и production-ready подход.

UI должен быть:

чистым

минималистичным

современным (SaaS analytics style)

светлая тема по умолчанию

легко расширяемым

1️⃣ Архитектура UI-kit

Создать структуру:

src/
 ├── ui/
 │   ├── theme/
 │   │   ├── colors.ts
 │   │   ├── typography.ts
 │   │   ├── spacing.ts
 │   │   ├── shadows.ts
 │   │   └── index.ts
 │   │
 │   ├── components/
 │   │   ├── Button/
 │   │   ├── Card/
 │   │   ├── Badge/
 │   │   ├── Input/
 │   │   ├── Select/
 │   │   ├── Table/
 │   │   ├── Modal/
 │   │   ├── Loader/
 │   │   ├── Alert/
 │   │   ├── Tabs/
 │   │   ├── Dropdown/
 │   │   ├── Pagination/
 │   │   └── ChartContainer/
 │   │
 │   └── layout/
 │       ├── AppLayout.tsx
 │       ├── Sidebar.tsx
 │       ├── Header.tsx
 │       └── PageContainer.tsx
2️⃣ 🎨 Дизайн-токены
2.1 Цветовая система

Primary:

500: #4F46E5

600: #4338CA

100: #E0E7FF

Success:

#10B981

Warning:

#F59E0B

Danger:

#EF4444

Gray scale:

900: #111827

700: #374151

500: #6B7280

200: #E5E7EB

100: #F3F4F6

50: #F9FAFB

Background:

page: #F9FAFB

card: #FFFFFF

2.2 Типографика

Font:
Inter / system-ui

Sizes:

H1: 28px / 700

H2: 22px / 600

H3: 18px / 600

Body: 14px / 400

Small: 12px / 400

2.3 Spacing

Базовая единица: 8px

Использовать:

8

16

24

32

40

2.4 Радиусы

small: 6px

medium: 12px

large: 16px

2.5 Тени

Card shadow:

0 4px 12px rgba(0,0,0,0.05)

Hover:

0 6px 18px rgba(0,0,0,0.08)
3️⃣ Базовые компоненты

Все компоненты:

типизированы (TypeScript)

без бизнес-логики

только UI

поддерживают variants

имеют disabled / loading состояния

3.1 Button

Variants:

primary

secondary

outline

danger

ghost

Sizes:

sm

md

lg

Props:

loading

disabled

fullWidth

iconLeft

iconRight

3.2 Card

Props:

title

actions

padding (sm / md / lg)

Используется для:

dashboard блоков

таблиц

аналитики

AI рекомендаций

3.3 Badge

Variants:

success

warning

danger

info

neutral

Использовать для:

статуса контента

статуса публикации

AI статусов

ошибок

3.4 Input

label

error

helperText

fullWidth

disabled

3.5 Select

dropdown с кастомным стилем

поддержка search

disabled

3.6 Table

Функционал:

sortable columns

hover row

empty state

loading state

pagination support

Используется для:

Products

Publishing

Analytics

Creators

3.7 Modal

Используется для:

подтверждения публикации

удаления

генерации контента

3.8 Alert

Типы:

success

warning

error

info

3.9 Loader

Spinner

Skeleton

3.10 Tabs

Использовать для:

карточки товара (Text / Image / Video)

аналитики (Overview / By Platform)

4️⃣ Layout система
4.1 AppLayout

Sidebar слева

Header сверху

Content area справа

4.2 Sidebar

Разделы:

Dashboard

Products

Content

Publishing

Analytics

Creators

Settings

Active state — подсветка primary цветом.

4.3 Header

Содержит:

название страницы

кнопки действия

user dropdown

4.4 PageContainer

max-width 1400px

padding 24px

адаптивность

5️⃣ Специальные UI-компоненты проекта

Создать специализированные компоненты:

5.1 StatusBadge

Для:

Content Status:

No Content

Text Ready

Image Ready

Video Ready

Complete

Publication Status:

Not Scheduled

Scheduled

Published

Failed

5.2 MetricCard

Используется в Dashboard:

title

value

delta %

icon

trend up/down

5.3 PipelineProgress

Горизонтальный flow:

Imported → Text → Media → Scheduled → Published → Analytics

5.4 AIRecommendationCard

Показывает:

рекомендацию

confidence %

кнопку "Apply"

6️⃣ Адаптивность

Поддержка:

Desktop (≥1280px)

Tablet (≥768px)

Mobile

Sidebar:

collapse mode

mobile overlay

7️⃣ Темизация

Подготовить систему для dark mode:

colors в theme

не хардкодить цвета в компонентах

использовать токены

8️⃣ UX-правила

Hover состояния у всех интерактивных элементов

Disabled всегда визуально заметен

Все loading состояния имеют skeleton

Empty state имеет иконку + текст + CTA

9️⃣ Архитектурные правила

UI-kit не содержит API вызовов

Нет зависимости от features

Можно вынести в отдельный пакет

Каждый компонент — отдельная папка

index.ts экспортирует публичный API

🔟 Production mindset

Поддержка accessibility (aria-label)

Кнопки имеют focus state

Таблицы поддерживают keyboard navigation

Код читаемый и масштабируемый

📌 Итог

UI-kit должен:

✔ Покрывать все страницы проекта
✔ Быть масштабируемым
✔ Поддерживать AI-блоки
✔ Поддерживать аналитику
✔ Поддерживать публикации
✔ Работать как полноценная дизайн-система