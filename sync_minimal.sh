#!/bin/bash
# Абсолютно минимальный скрипт синхронизации

cd /root/coinbaserank_bot
git pull origin main
systemctl restart coinbasebot