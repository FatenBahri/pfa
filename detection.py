from ultralytics import YOLO
import cv2
import csv
import os
from datetime import datetime
import time
import qrcode
import numpy as np

# Charger le modèle YOLOv8
model = YOLO("yolov8n.pt")

# Ouvrir la webcam
cap = cv2.VideoCapture(0)

# Nom du fichier CSV
csv_file = "bottle_trash_counts.csv"
last_increment_time = 0
increment_delay = 3

# Vérifier si le fichier existe, sinon créer avec en-tête
if not os.path.exists(csv_file):
    with open(csv_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Heure", "Nouvelles bouteilles", "Bouteilles dans corbeille", "ID Corbeille", "QR Code"])

previous_bottles = set()
total_bottles = 0
trash_bin_id = "CBL-001"  # Identifiant de la corbeille
qr_img = None
qr_filename_display = ""

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Détection des objets
    results = model(frame)

    current_bottles = set()
    not_plastic_detected = False  # Variable pour suivre si un objet autre qu'une bouteille est détecté

    for result in results:
        for box in result.boxes:
            cls = int(box.cls[0])  # Classe de l'objet détecté
            label = model.names[cls]  # Nom de l'objet détecté

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            if label == "bottle":  # Si c'est une bouteille
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                current_bottles.add((center_x, center_y))

                # Dessiner le rectangle et l'étiquette en vert
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, "Bouteille", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            else:  # Si ce n'est pas une bouteille
                not_plastic_detected = True  # Détecter un objet non plastique

                # Dessiner le rectangle en rouge et afficher "Ce n'est pas du plastique"
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame, "Ce n'est pas du plastique", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    # Détecter les nouvelles bouteilles ajoutées
    new_bottles = 0
    current_time = time.time()
    for bottle in current_bottles:
        is_new = True
        for previous_bottle in previous_bottles:
            distance = ((bottle[0] - previous_bottle[0]) ** 2 + (bottle[1] - previous_bottle[1]) ** 2) ** 0.5
            if distance < 50:
                is_new = False
                break
        if is_new:
            new_bottles += 1

    # Mettre à jour le nombre total UNIQUEMENT si une nouvelle bouteille est détectée
    if new_bottles > 0 and (current_time - last_increment_time > increment_delay):
        total_bottles += new_bottles
        last_increment_time = current_time

        # Générer un ID unique pour l'événement
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        event_id = f"{trash_bin_id}-{int(time.time())}"

        # Générer le contenu du QR code
        qr_data = f"Date: {date_str}\nHeure: {time_str}\nNouvelles bouteilles: {new_bottles}\nTotal bouteilles: {total_bottles}\nID Corbeille: {trash_bin_id}\nÉvénement: {event_id}"

        # Créer et enregistrer le QR code
        qr = qrcode.make(qr_data)
        qr_filename = f"qrcodes/{event_id}.png"
        os.makedirs("qrcodes", exist_ok=True)  # Créer le dossier s'il n'existe pas
        qr.save(qr_filename)

        # Mettre à jour le nom affiché
        qr_filename_display = os.path.basename(qr_filename)

        # Enregistrer dans le CSV
        with open(csv_file, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([date_str, time_str, new_bottles, total_bottles, trash_bin_id, qr_filename])

        # Convertir le QR code en image pour affichage
        qr_img = cv2.imread(qr_filename)

    # Mise à jour des bouteilles précédentes
    previous_bottles = current_bottles.copy()

    # Affichage des informations
    cv2.putText(frame, f"Nouvelles bouteilles: {new_bottles}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(frame, f"Bouteilles dans corbeille: {total_bottles}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    # Afficher un message d'avertissement si un objet autre que du plastique est détecté
    if not_plastic_detected:
        cv2.putText(frame, "Attention : Objet non plastique détecté !", (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # Afficher la détection
    cv2.imshow("Détection Bouteilles", frame)

    # Afficher le QR code si un nouvel événement est détecté
    if qr_img is not None:
        cv2.imshow("QR Code", qr_img)
        cv2.putText(qr_img, qr_filename_display, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Quitter avec 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
