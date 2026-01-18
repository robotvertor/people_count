import cv2
from ultralytics import YOLO
import json
import asyncio
from telegram import Bot

VIDEO_PATH = '2432216-hd_1920_1080_24fps.mp4'
MODEL_PATH = 'yolov8x.pt'

TELEGRAM_TOKEN = "8324375966:AAGJi5dFA8dlz97n91w6ZzlxaVzLK02bpx0"
CHAT_ID = 5195588776

PEOPLE_THRESHOLD = 5
SEND_ONLY_ONE_MESSAGE = True

SETTINGS_FILE = "cropping_settings.json"

crop_top = crop_bottom = crop_left = crop_right = 0
bot = Bot(token=TELEGRAM_TOKEN)
total_count = 0
threshold_exceeded = False
message_sent = False
seen_ids = set()


def load_crop():
    global crop_top, crop_bottom, crop_left, crop_right
    try:
        with open(SETTINGS_FILE) as f:
            s = json.load(f)
            crop_top = s["crop_top"]
            crop_bottom = s["crop_bottom"]
            crop_left = s["crop_left"]
            crop_right = s["crop_right"]
    except:
        pass


def save_crop():
    s = {"crop_top": crop_top, "crop_bottom": crop_bottom,
         "crop_left": crop_left, "crop_right": crop_right}
    with open(SETTINGS_FILE, "w") as f:
        json.dump(s, f)


def nothing(x): pass


def setup_crop(frame):
    global crop_top, crop_bottom, crop_left, crop_right
    h, w = frame.shape[:2]
    crop_top = max(0, min(crop_top, h))
    crop_bottom = max(crop_bottom, crop_top + 50)
    crop_left = max(0, min(crop_left, w))
    crop_right = max(crop_right, crop_left + 50)

    cv2.namedWindow("Adjust Cropping")
    cv2.createTrackbar("Top", "Adjust Cropping", crop_top, h, nothing)
    cv2.createTrackbar("Bottom", "Adjust Cropping", crop_bottom, h, nothing)
    cv2.createTrackbar("Left", "Adjust Cropping", crop_left, w, nothing)
    cv2.createTrackbar("Right", "Adjust Cropping", crop_right, w, nothing)

    while True:
        temp = frame.copy()
        t = cv2.getTrackbarPos("Top", "Adjust Cropping")
        b = cv2.getTrackbarPos("Bottom", "Adjust Cropping")
        l = cv2.getTrackbarPos("Left", "Adjust Cropping")
        r = cv2.getTrackbarPos("Right", "Adjust Cropping")
        crop_top, crop_bottom, crop_left, crop_right = t, b, l, r

        if b > t + 30 and r > l + 30:
            cv2.rectangle(temp, (l, t), (r, b), (0, 255, 0), 2)

        disp = cv2.resize(temp, (1000, 600))
        cv2.imshow("Adjust Cropping", disp)

        if cv2.waitKey(1) != -1:
            save_crop()
            break

    cv2.destroyWindow("Adjust Cropping")


async def main():
    global total_count, threshold_exceeded, message_sent

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print("Не удалось открыть видео!")
        return

    model = YOLO(MODEL_PATH)

    ret, first_frame = cap.read()
    if not ret:
        print("Не удалось прочитать кадр из видео")
        return

    load_crop()

    need_setup = input("Настроить зону? (y/n): ").strip().lower() == "y"
    if need_setup:
        setup_crop(first_frame)

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if crop_bottom <= crop_top or crop_right <= crop_left:
            continue

        roi = frame[crop_top:crop_bottom, crop_left:crop_right]
        if roi.size == 0:
            continue

        results = model.track(roi, persist=True, classes=0, tracker="bytetrack.yaml", verbose=False)

        current_ids = {int(b.id.item()) for r in results for b in r.boxes if b.id is not None}
        for tid in current_ids:
            if tid not in seen_ids:
                seen_ids.add(tid)
                total_count += 1

        now_exceeded = len(current_ids) >= PEOPLE_THRESHOLD

        if now_exceeded != threshold_exceeded:
            threshold_exceeded = now_exceeded
            if not (SEND_ONLY_ONE_MESSAGE and message_sent):
                status = "много" if now_exceeded else "мало"
                msg = f"Сейчас в кадре {len(current_ids)} чел. — {status} (порог {PEOPLE_THRESHOLD})"
                await bot.send_message(chat_id=CHAT_ID, text=msg)
                message_sent = True if SEND_ONLY_ONE_MESSAGE else False

        disp = cv2.resize(roi, (1000, 600))
        cv2.putText(disp, f"Total: {total_count}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0,255,255), 3)
        cv2.putText(disp, f"Now: {len(current_ids)}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255,255,0), 3)
        cv2.imshow("People Counter", disp)

        if cv2.waitKey(1) == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    asyncio.run(main())