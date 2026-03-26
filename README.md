# Music Genre Sommelier AI

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
        +upload()
    }

    class SpectrogramFile {
        <<data record>>
    }

    class AudioSpectrogram {
        +convert()
        +get_spectrogram()
        -_set_status()
    }

    class MLModel {
        +predict(spectrogram_path)
    }

    class MLTask {
        +process()
        -_set_status()
    }

    class Transaction {
        +check_funds(user_id, amount)
        +get_balance(user_id)
        +approve()
        +reject(status)
        -_set_status()
    }

    User <|-- CommonUser
    User <|-- AdminUser

    AudioSpectrogram --> AudioFile : reads
    AudioSpectrogram --> SpectrogramFile : produces

    MLTask --> AudioSpectrogram : precondition
    MLTask --> MLModel : predict()

    MLTask ..> User : user_id
    Transaction ..> User : user_id
    Transaction ..> MLTask : ml_task_id
```

> Замечание: `SpectrogramFile` — только запись о файле, без доменной логики (**RULE-05**, `AGENTS.md`). У `AudioSpectrogram`, `MLTask` и `Transaction` префикс `-` в диаграмме — **private** (UML): `_set_status` централизует смену поля **`status`** в БД (у `AudioSpectrogram`, `MLTask` и `Transaction` — разные таблицы; имена колонок совпадают там, где это уместно); вызывать снаружи класса не следует (см. `AGENTS.md`).

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
        int user_id FK
        int model_id FK
        enum status
        json result "nullable"
        varchar error "nullable"
        datetime created_at
        datetime updated_at
    }

    Transaction {
        int id PK
        int user_id FK
        int ml_task_id FK "nullable"
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

- Домашнее задание 1: Агенты не использовались при проектировании, GPT использовался для однократного ревью законченного черновика сущностей (данные и классы). Агент использовался для отрисовки Mermaid диаграм и ведения агентскной документации (личные нужды на случай желания продолжать поддерживать проект).
