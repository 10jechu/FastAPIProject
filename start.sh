#!/bin/bash
cd /home/bas/app_1163f152-86eb-41a0-b29a-106625c50c8c || exit
source /home/bas/venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port $PORT