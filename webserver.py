# conda activate tensor 
# poetry shell
# uvicorn webserver:app --reload

from fastapi import FastAPI, Request, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi import File, UploadFile
import json
import os
import mysql.connector
import shutil
from typing import List
from model_loader import load_model
from PIL import Image
import numpy as np
import tensorflow as tf
import logging
from dotenv import load_dotenv



app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

json_dir = "./json"
os.makedirs(json_dir, exist_ok=True)

@app.get("/")
def read_root():
    return FileResponse('index.html')

@app.get("/input")
def read_user_input():
    return FileResponse('UserInput.html')

@app.get("/camera")
def read_camera():
    return FileResponse('camera.html')

photo_dir = "./photos"
os.makedirs(photo_dir, exist_ok=True)

# MySQL 
load_dotenv()

db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_DATABASE")
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

def create_user_measure_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_measure (
            id INT PRIMARY KEY,
            chest FLOAT,
            waist FLOAT,
            hip FLOAT,
            thigh FLOAT
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

create_user_measure_table()

from fastapi import Body

@app.post("/save-user-data")
async def save_user_data(
    height: float = Form(...),  # 신장
    weight: float = Form(...)  # 체중
):
    # BMI 계산
    bmi = weight / ((height / 100) ** 2)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_data (id, height, weight, bmi) 
        VALUES (1, %s, %s, %s)
        ON DUPLICATE KEY UPDATE height = VALUES(height), weight = VALUES(weight), bmi = VALUES(bmi)
    """, (height, weight, bmi))
    conn.commit()
    cursor.close()
    conn.close()
    return JSONResponse(content={"message": "Data saved successfully", "bmi": bmi})


@app.post("/upload-photo")
async def upload_photo(photo: UploadFile = File(...)):
    try:
        # 사진 저장 경로
        photo_path = os.path.join(photo_dir, "front.jpg")
        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)

        return JSONResponse(content={"message": "Photo uploaded successfully!", "photo_path": photo_path})
    except Exception as e:
        logging.error(f"Error uploading photo: {str(e)}")
        return JSONResponse(content={"message": f"Error: {str(e)}"}, status_code=500)

@app.post("/process-saved-photo")
def process_saved_photo():
    try:
        photo_path = os.path.join(photo_dir, "front.jpg")
        if not os.path.exists(photo_path):
            return JSONResponse(content={"message": "Photo not found in photos directory."}, status_code=404)

        # 사진 로드 및 전처리
        image = Image.open(photo_path).resize((256, 256))  
        image_array = np.expand_dims(image, axis=0) 

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT height, bmi FROM user_data WHERE id = 1")
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user_data:
            logging.error("User data not found in database.")
            return JSONResponse(content={"message": "User data not found."}, status_code=400)

        height, bmi = user_data["height"], user_data["bmi"]
        logging.debug(f"Height: {height}, BMI: {bmi}")

        other_input_array = np.array([[height, bmi]])
        
        # 모델 예측
        model = load_model()
        result = model.predict([image_array, other_input_array])
        if result is None or len(result) == 0:
            return JSONResponse(content={"message": "Model failed to return a result."}, status_code=500)

        # 결과 -> 소수점 2자리
        chest = round(float(result[0][8]), 1)
        waist = round(float(result[0][9]), 1)
        hip = round(float(result[0][11]), 1)
        thigh = round(float(result[0][12]), 1)

        # DB에 저장
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_measure (id, chest, waist, hip, thigh)
            VALUES (1, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE chest = VALUES(chest), waist = VALUES(waist), hip = VALUES(hip), thigh = VALUES(thigh)
        """, (chest, waist, hip, thigh))
        conn.commit()
        cursor.close()
        conn.close()

        return JSONResponse(content={"chest": chest, "waist": waist, "hip": hip, "thigh": thigh})
    except Exception as e:
        return JSONResponse(content={"message": f"Error: {str(e)}"}, status_code=500)

# 로깅
logging.basicConfig(
    filename="debug.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

@app.get("/get-user-data")
def get_user_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # height, weight 가져오기
        cursor.execute("SELECT height, weight FROM user_data WHERE id = 1")
        user_data = cursor.fetchone()

        # 신체 사이즈 가져오기
        cursor.execute("SELECT chest, waist, hip, thigh FROM user_measure WHERE id = 1")
        measure_data = cursor.fetchone()

        cursor.close()
        conn.close()

        return JSONResponse(content={"height": user_data["height"], "weight": user_data["weight"], **measure_data})
    except Exception as e:
        return JSONResponse(content={"message": f"Error: {str(e)}"}, status_code=500)
