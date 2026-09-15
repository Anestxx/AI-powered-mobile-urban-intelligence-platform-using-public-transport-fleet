"""Save the detected box with surrounding road context for operator review."""
import base64
from pathlib import Path


def make_evidence(frame, bbox, source, frame_id, video_time):
    import cv2
    height, width = frame.shape[:2]
    left, top, right, bottom = (int(value) for value in bbox)
    left, top, right, bottom = max(0, left), max(0, top), min(width, right), min(height, bottom)
    if right <= left or bottom <= top:
        raise ValueError("Cannot save evidence outside the frame")
    crop_width = min(width, max(320, 3 * (right - left)))
    crop_height = min(height, max(240, 3 * (bottom - top)))
    crop_left = min(max(0, (left + right - crop_width) // 2), width - crop_width)
    crop_top = min(max(0, (top + bottom - crop_height) // 2), height - crop_height)
    crop = frame[crop_top:crop_top + crop_height, crop_left:crop_left + crop_width].copy()
    scale = min(1, 480 / max(crop.shape[:2]))
    if scale < 1:
        crop = cv2.resize(crop, (max(1, round(crop.shape[1] * scale)), max(1, round(crop.shape[0] * scale))))
    box_left, box_top = round((left - crop_left) * scale), round((top - crop_top) * scale)
    box_right, box_bottom = round((right - crop_left) * scale), round((bottom - crop_top) * scale)
    box_right, box_bottom = min(crop.shape[1] - 1, box_right), min(crop.shape[0] - 1, box_bottom)
    cv2.rectangle(crop, (box_left, box_top), (box_right, box_bottom), (0, 210, 255), 2)
    cv2.putText(crop, "POTHOLE", (max(2, min(box_left, crop.shape[1] - 85)), max(16, box_top - 7)),
                cv2.FONT_HERSHEY_SIMPLEX, .45, (0, 210, 255), 1, cv2.LINE_AA)
    ok, encoded = cv2.imencode(".jpg", crop, [cv2.IMWRITE_JPEG_QUALITY, 75])
    if not ok or len(encoded) > 192 * 1024:
        raise ValueError("Evidence JPEG could not be encoded within its size limit")
    return {"jpeg_base64": base64.b64encode(encoded.tobytes()).decode("ascii"),
            "source_name": ("camera_" + str(source)) if str(source).isdigit() else Path(source).name[:160],
            "frame_id": frame_id, "video_time": video_time}
