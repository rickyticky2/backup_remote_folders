# Скрипт бэкапа папок с удаленных серверов.

Папки архивируются tar , копируются на локальный сервер. Имена архивов - **{name}_{date}**

Конфиг берется из yaml файла (**config.yaml**)
*Авторизоваться на серверах можно по файлу ключа(**key**), **password**. Если не заданы файл ключа или пароль - скрипт будет пытаться взять ключ из ssh-add. *

пример конфигов - в **config.yaml**

**keep_days: 7** - время хранения файлов
