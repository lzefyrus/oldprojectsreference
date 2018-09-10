#!/bin/bash

echo "Starting DynamoDB"
cd /opt
java -jar DynamoDBLocal.jar &

cd /var/www/frontend
npm run build

cd /var/www/backend/server
source /vagrant/virtualenvs/next/bin/activate
if [ $# -ne 1 ]; then
    python main.py
else
    python main.py -p -a
fi