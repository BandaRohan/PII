# face_detection.py
from PIL import Image
import face_recognition as fr
import numpy as np
import os
import cv2 as cv
from pymongo import MongoClient
mongo_client = MongoClient('mongodb://localhost:27017/')
mongo_db = mongo_client['total_records']
encodings_collection = mongo_db['encodings']

def detect_faces(image_path):
    # Load the image with face_recognition library
    image = fr.load_image_file(image_path)
    # Find all face locations in the image
    face_locations = fr.face_locations(image)

    return face_locations

def usr_encoding(img,face_locations):
    all_encoding_list =  []

    for location in face_locations:
        current_face_encodings = fr.face_encodings(img,[location])
        all_encoding_list.extend(current_face_encodings[0])
    return all_encoding_list

def cosine_similarity(img1, img2):
    img1_arr = np.array(img1).flatten()
    img2_arr = np.array(img2).flatten()

    magnitude1 = np.linalg.norm(img1_arr)
    magnitude2 = np.linalg.norm(img2_arr)

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    dot_product = np.dot(img1_arr, img2_arr)
    cosine_similarity = dot_product / (magnitude1 * magnitude2)
    return cosine_similarity
def load_embeddings():
    data = []
    for entry in encodings_collection.find():
        data.append(entry)
    return data

def mainone(image_paths):
    known_embedding = load_embeddings()

    for user_image_path in image_paths:
        target_images = fr.load_image_file(user_image_path)
        target_location = fr.face_locations(target_images)
        print("Length:", len(target_location))
        target_encodings = fr.face_encodings(target_images, target_location)
        user_image_name = (user_image_path.split("/")[-1]).split(".")[0]

        if not target_encodings:
            print(f"No faces found in {user_image_path}")
            continue

        for i, target_encoding in enumerate(target_encodings):
            max_score = 0
            recognized_person = None
            faces = target_location[i]

            for entry in known_embedding:
                stored_face_encodings = entry['encodings']
                similarity_score = cosine_similarity(target_encoding.reshape(1, -1), np.array(stored_face_encodings))
                current_max_score = np.max(similarity_score)
                if current_max_score > max_score:
                    max_score = current_max_score
                    recognized_person = entry['name']

            if max_score > 0.9:
                recognized_person_folder = os.path.join(recognized_faces_folder, recognized_person)
                os.makedirs(recognized_person_folder, exist_ok=True)

                recognized_image_path = os.path.join(recognized_person_folder, os.path.basename(user_image_path))
                cv.imwrite(recognized_image_path, cv.cvtColor(target_images, cv.COLOR_BGR2RGB))
                print(f"The {user_image_name} recognized as {recognized_person} and saved in {recognized_person_folder}")
            else:
                print("Match not found")