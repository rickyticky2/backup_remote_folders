#!/bin/bash
#ip адрес сервера бэкапов
remote_ip=34.118.126.130
#Дирриктория
dir_addr_b=/home/azverev/Project/
#Дирриктория бэкапов
dir_addr_r=/home/azverev/backup/
#Пользователь сервера бэкапов
remote_user=azverev

#создаем файлы
cd ~/Project/1/
for i in {1..5}; do
    echo $RANDOM > ${i}.sample;
done;

#копируем на сервер
rsync -avz ${dir_addr_b} ${remote_user}@${remote_ip}:${dir_addr_r}"$(date +"%d%m%Y")"

#удаляем старше 7 дней
ssh ${remote_user}@${remote_ip} 'find ${dir_addr_b} -type d -name *202* -mtime +7 -exec rm -r {} \;'
