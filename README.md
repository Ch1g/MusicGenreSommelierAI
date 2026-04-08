# Music Genre Sommelier AI

## Структура репозитория

Один уровень вложенности (документация и доменный Python — в `docs/` и `app/src/`).

```text
.
├── AGENTS.md # (см .gitignore)
├── README.md
├── docker-compose.yml
├── app/                 # образ приложения: Python, app.py, зависимости
│   └── src/music_genre_sommelier/
│       ├── models/      # модели данных (SQLModel)
│       ├── services/    # сервисный слой (бизнес-логика)
│       └── utils/       # утилиты (БД, enum'ы)
├── db/                  # образ PostgreSQL
├── mb/                  # образ RabbitMQ (management)
├── web-proxy/           # образ nginx (reverse proxy)
└── docs/                # architecture.md, stack.md, drift-check.md, decisions.md (см. .gitignore)
```

## Описание

Классификатор жанров музыкальных произведений на основе спектрограмм.

## Сущности

### Структура классов

```mermaid
classDiagram
    direction TB

    class User {
        <<ABC>>
        +get_balance()* 
    }

    class CommonUser {
        +get_balance()
    }

    class AdminUser {
        +get_balance()
    }

    class AudioFile {
        +record_failure(error)
        +record_success()
        -_set_status(status)
    }

    class SpectrogramFile {
        <<data record>>
    }

    class AudioSpectrogram {
        +record_failure(error)
        +record_success()
        -_set_status(status)
    }

    class MLModel {
        <<data record>>
    }

    class MLTask {
        +record_failure(error)
        +record_success(result)
        -_set_status(status)
    }

    class Transaction {
        +check_funds()
        +get_balance(user_id) $
        +approve()
        +cancel()
        +fail_insufficient_funds()
        _is_sufficient()
    }

    User <|-- CommonUser
    User <|-- AdminUser

    MLTask ..> User : user_id
    MLTask ..> Transaction : transaction_id
    MLTask ..> MLModel : ml_model_id
    MLTask ..> AudioSpectrogram : audio_spectrogram_id
    Transaction ..> User : user_id
    AudioSpectrogram ..> AudioFile : audio_file_id
    AudioSpectrogram ..> SpectrogramFile : spectrogram_file_id
```

### Структура БД

Диаграмма сущностей и связей (контракт совпадает с `docs/architecture.md`).

```mermaid
erDiagram
    User {
        int id PK
        varchar email UK
        varchar username
        varchar encrypted_password
        boolean is_admin
        datetime created_at
        datetime updated_at
    }

    AudioFile {
        int id PK
        varchar file_path
        enum upload_status
        text upload_error "nullable"
        datetime created_at
        datetime updated_at
    }

    SpectrogramFile {
        int id PK
        varchar file_path
        datetime created_at
        datetime updated_at
    }

    AudioSpectrogram {
        int id PK
        int audio_file_id FK
        int spectrogram_file_id FK "nullable"
        enum status
        text error "nullable"
        datetime created_at
        datetime updated_at
    }

    MLModel {
        int id PK
        varchar model_path
        int prediction_cost
        datetime created_at
        datetime updated_at
    }

    MLTask {
        int id PK
        int audio_spectrogram_id FK
        int transaction_id FK
        int ml_model_id FK
        int ml_task_id FK
        enum status
        json result "nullable"
        varchar error "nullable"
        datetime created_at
        datetime updated_at
    }

    Transaction {
        int id PK
        int user_id FK
        int amount
        enum status
        datetime created_at
        datetime updated_at
    }

    User ||--o{ MLTask : ""
    User ||--o{ Transaction : ""
    MLTask ||--o{ Transaction : "ml_task_id"
    MLModel ||--o{ MLTask : ""
    AudioFile ||--o{ AudioSpectrogram : ""
    AudioSpectrogram }o--|| SpectrogramFile : "spectrogram_file_id"
    AudioSpectrogram ||--o{ MLTask : ""
```

**Перечисления (ENUM)** — в реальной БД: тип `ENUM(...)` / аналог по СУБД; на диаграмме они обозначены как `enum`.

| Сущность | Поле | Допустимые значения |
|----------|------|---------------------|
| `AudioFile` | `upload_status` | `pending`, `success`, `failure` |
| `AudioSpectrogram` | `status` | `pending`, `success`, `failure` |
| `MLTask` | `status` | `pending`, `success`, `failure` |
| `Transaction` | `status` | `pending`, `fail_insufficient_funds`, `fail_canceled`, `success` |

## Мета-информация

### Использование ИИ-агентов и GPT

- Домашнее задание 1: Агенты не использовались при проектировании, GPT использовался для однократного ревью законченного черновика сущностей (данные и классы). Агент использовался для отрисовки Mermaid диаграм и ведения агентской документации (личные нужды на случай желания продолжать поддерживать проект).
- Домашнее задание 2: Агент использовался для создания блока [Структура проекта](#структура-проекта), GPT использовался для поиска причины несохранения данных после перезапуска контейнера PostgreSQL (образ 18-й версии использует по умолчанию этот путь /var/lib/postgresql/18/docker)
- Домашнее задание 3: Агент использовался для рефакторинга моделей данных — вынос готовой сервисной логики в отдельный слой `services/`, перенос файлов моделей в `models/`.  
