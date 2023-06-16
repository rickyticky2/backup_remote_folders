import paramiko
import yaml
import getpass
import os
import datetime
import logging

# настройка логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
file_handler = logging.FileHandler('app.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def backup_server(server):
    # Создание SSH-соединения с удаленным сервером
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Получение пароля и ключа из файла конфигурации или из ssh-agent
    if 'password' in server:
        password = server['password']
    else:
        password = None
    if 'key' in server:
        key_filename = server['key'] # Получение key файла
        if 'key_passphrase' in server:
            key_passphrase = server['key_passphrase'] # Получение passphrase
        else:
            key_passphrase = None
        key = paramiko.RSAKey.from_private_key_file(key_filename, password=key_passphrase)
    else:
    # ssh-agent
        agent = paramiko.agent.Agent()
        keys = agent.get_keys()
        if len(keys) == 0:
            raise ValueError("No keys found in ssh-agent.")
        key = keys[0]


    # Подключение к серверу
    try:
        client.connect(server['hostname'], username=server['username'], password=password, pkey=key)

        # Получаем текущую дату и время
        now = datetime.datetime.now()

        # Создание архива директории с использованием текущей даты и времени
        backup_name = f"{server['name']}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.tgz"
        command = f"tar -czf {backup_name} {server['directory']}"
        stdin, stdout, stderr = client.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            logger.error(f"Error creating backup on {server['name']}: {stderr.read().decode('utf-8')}")
        else:
            # Скачивание архива с удаленного сервера
            scp = client.open_sftp()
            remote_file = backup_name
            local_dir = server.get('local_dir', '/home/ubuntu/Project/lanit/scripts/test')

            local_file = os.path.join(local_dir, backup_name)
            scp.get(remote_file, local_file)
            scp.close()
            logger.info(f"Backup created successfully for {server['name']} and saved locally as {backup_name}")

            # Удаление старых бэкапов
            if 'delete_old' in server and server['delete_old'] == True:
                keep_days = server.get('keep_days', 7) # Если параметр keep_days не задан, то устанавливаем значение по умолчанию равным 7
                delete_old_backups(local_file, keep_days)

    except Exception as e:
        logger.exception(f"Failed to create backup for {server['name']}: {str(e)}")
    finally:
        # Удаление архива на удаленном сервере
        remove_command = f"rm -rf {backup_name}"
        stdin, stdout, stderr = client.exec_command(remove_command)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            logger.info(f"Remote backup file deleted for {server['name']}")
        client.close()


def delete_old_backups(current_backup, keep_days):

    # Получение списка всех файлов в текущей директории
    directory = os.path.dirname(current_backup)
    all_files = os.listdir(directory)

    # Фильтрация только файлов с расширением tgz и содержащих имя сервера
    backup_files = [f for f in all_files if f.endswith('.tgz') and current_backup.split('_')[0] in f]

    # Определение даты для удаления старых бэкапов
    now = datetime.datetime.now()
    remove_before = now - datetime.timedelta(days=keep_days)

    # Удаление старых бэкапов
    for backup_file in backup_files:
        # Извлечение даты из имени файла
        backup_date = datetime.datetime.strptime(backup_file.split('_')[1], '%Y-%m-%d_%H-%M-%S')
        if backup_date < remove_before and backup_file != os.path.basename(current_backup):
            os.remove(os.path.join(directory, backup_file))
            logger.info(f"Old backup file removed: {backup_file}")

# Загрузка конфигурации из файла
with open('config.yaml') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

# Создание бэкапа для каждого сервера в конфигурации
for server in config['servers']:
    backup_server(server)
