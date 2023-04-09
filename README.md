# Сервис получения ИНН

Пишем сервис получения ИНН через сайт nalog.ru на Python с RabbitMQ. 


## Описание сервиса

Сервис принимает запросы через шину данных, организованную на базе RabbitMQ. Результат отправляется в очередь, 
указанную в заголовке сообщения reply-to.

Фактический запрос на ИНН производится через сервис https://service.nalog.ru/inn-proc.do методом POST запроса.

## Как начать работу

Сделать копию env-файла из .env.example в .env .

```shell
docker compose build
docker compose up
```

Сервис по умолчанию слушает очередь, указанную в .env-файле. Подключиться к админке RabbitMQ в браузере. 

Отправить запрос:
```json
{
  "requestId": "b48bc1b5-996f-4a8b-99b2-2dcf85224070",
  "firstName": "Иван", 
  "lastName": "Петров",
  "middleName": "Владимирович",
  "birthDate": "1990-07-15",
  "birthPlace": "",
  "documentSerial": "0914",
  "documentNumber": "453696",
  "documentDate": "2021-12-31"
}
```

Результат будет отправлен в очередь, указанную в reply-to заголовка сообщения. Формат ответа:

```json
{
  "requestId": "b48bc1b5-996f-4a8b-99b2-2dcf85224070",
  "inn":"125441241013",
  "details": "",
  "cashed": false,
  "elapsed_time": 0.1425
}
```