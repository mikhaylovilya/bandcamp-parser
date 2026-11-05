# Тест-кейсы

| ID    | Область  | Кейс                      | Ожидание                                | Автоматизация                                          |
| ----- | -------- | ------------------------- | --------------------------------------- | ------------------------------------------------------ |
| TC-01 | Парсер   | Валидный HTML альбома     | заголовок, артист, 10 треков, errors=[] | test_parser::test_parse_album                          |
| TC-02 | Парсер   | Валидный HTML трека       | type=track, есть lyrics                 | test_parser::test_parse_track                          |
| TC-03 | Парсер   | Пустой HTML               | ParseError                              | test_parser::test_parse_empty_raises                   |
| TC-04 | Парсер   | Отсутствует data-tralbum  | ошибка в списке, без падения            | test_parser::test_parse_missing_tralbum_reports_errors |
| TC-05 | API      | Health                    | 200 ok                                  | test_api::test_health                                  |
| TC-06 | API      | Parse валидный            | 200, отчёт сохранён                     | test_api::test_parse_persists_report                   |
| TC-07 | API      | Parse не-bandcamp URL     | 400                                     | test_api::test_parse_invalid_url                       |
| TC-08 | API      | Parse пустое тело         | 400/422                                 | test_api::test_parse_missing_url                       |
| TC-09 | API      | Список отчётов            | 200, массив                             | test_api::test_parse_persists_report                   |
| TC-10 | API      | Получение отчёта          | 200, data.title                         | test_api::test_get_report                              |
| TC-11 | API      | Получение несуществующего | 404                                     | test_api::test_get_missing_report                      |
| TC-12 | API      | Удаление отчёта           | 200, список пуст                        | test_api::test_delete_report                           |
| TC-13 | API      | Удаление несуществующего  | 404                                     | test_api::test_delete_missing_report                   |
| TC-14 | API      | Swagger UI                | 200                                     | test_api::test_swagger                                 |
| TC-15 | Фронтенд | Отрисовка заголовка       | присутствует                            | App.test.js                                            |
| TC-16 | Фронтенд | Пустой URL                | показана ошибка                         | App.test.js                                            |
| TC-17 | Фронтенд | Успешный parse            | заголовок показан                       | App.test.js                                            |
| TC-18 | Парсер   | Fallback даты релиза      | без ошибки (wishedbone)                 | вручную                                                |
| TC-19 | Парсер   | Описание не дублируется   | description=null при ==about            | вручную                                                |