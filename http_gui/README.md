# HTTP-клиент и сервер с GUI на Python

Учебный проект реализует HTTP/1.1 клиент и многопоточный сервер поверх `socket`, без `requests`, Flask и `http.server`. GUI сделан на стандартном `tkinter`.

## Возможности

- HTTP-клиент: GET/POST, пользовательские заголовки и тело, `set_timeout(ms)`, HTTP/HTTPS, Content-Length, chunked-ответы.
- Бонус: `follow_redirects(max)` для 301/302/303/307/308.
- `HttpError(status)` доступен через `HttpClient.raise_for_status(response)`, при этом обычный GET сохраняет Response для тестов `/status/404`.
- GUI клиента: цветовая подсветка статуса, HTTP-заголовков, JSON и HTML; ошибки красным; ответ read-only.
- HTTP-сервер: `/`, `/echo`, `/time`, `/headers`, `/status/{code}`, 404 и 400.
- Каждый серверный ответ содержит Content-Type, Content-Length и Date.
- Connection close/keep-alive и отдельный поток на соединение.
- GUI выполняет запросы и запуск/остановку сервера в фоновых потоках.
- Логирование через `logging`: в `http_gui.log` и структурированно в GUI через `GuiQueueLogHandler`.
- 79 автоматических тестов + stress test на 100 параллельных запросов.
- `flake8`: 0 ошибок; `pylint`: 10.00/10.

## Установка и запуск

```bash
pip install -r requirements.txt
python -m src.main
```

## Тесты

```bash
pytest tests/ -v
pytest tests/test_integration.py -v
python -X dev -m pytest -q
python tools/stress_test.py
python -m compileall -q src tests tools
```

## Линтеры

```bash
flake8 src/ tests/
pylint src/
```

Конфигурации находятся в `.flake8` и `.pylintrc`.

## Ручная проверка

После запуска сервера на 8080:

```bash
curl -v http://localhost:8080/
curl -v -X POST -H "Content-Type: text/plain" -d "hello" http://localhost:8080/echo
curl -v http://localhost:8080/status/418
curl -v http://localhost:8080/nonexistent
```

## Документация сдачи

- `REPORT.md` — отчёт и анализ.
- `architecture.puml` — PlantUML-диаграмма классов.
- `screenshots/` — полный комплект S1–S13, включая фактические результаты
  `pytest`, `flake8` и 100 параллельных запросов.
