import cv2

import mediapipe as mp
import numpy as np
import time


# CONSTANTS  

EAR_THRESHOLD       = 0.25   # Below this → eyes are closing
DROWSY_TIME_LIMIT   = 2.0    # Seconds of low EAR before → DROWSY
DISTRACTED_TIME_LIMIT = 5.0  # Seconds of off-gaze before → DISTRACTED

# MediaPipe landmark indices for EAR 

LEFT_EYE_IDX  = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]

# Iris landmarks (for gaze direction)

LEFT_IRIS_IDX  = [469, 470, 471, 472]
RIGHT_IRIS_IDX = [474, 475, 476, 477]



# HELPER FUNCTIONS


def euclidean(p1, p2):
    """Distance between two 2D points."""
    return np.linalg.norm(np.array(p1) - np.array(p2))


def calculate_EAR(landmarks, eye_indices, frame_w, frame_h):
    """
    EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
    Points: p1=corner_left, p2=top_outer, p3=top_inner,
            p4=corner_right, p5=bot_inner, p6=bot_outer
    """
    pts = []
    for idx in eye_indices:
        lm = landmarks[idx]
        pts.append((lm.x * frame_w, lm.y * frame_h))

    p1, p2, p3, p4, p5, p6 = pts
    vertical_1 = euclidean(p2, p6)
    vertical_2 = euclidean(p3, p5)
    horizontal = euclidean(p1, p4)

    ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
    return ear


def calculate_gaze_offset(landmarks, eye_indices, iris_indices, frame_w, frame_h):
    """
    Returns how far the iris is from the center of the eye (normalized 0–1).
    If offset > 0.35 in any direction → looking away.
    """
    eye_pts = [(landmarks[i].x * frame_w, landmarks[i].y * frame_h) for i in eye_indices]
    iris_pts = [(landmarks[i].x * frame_w, landmarks[i].y * frame_h) for i in iris_indices]

    eye_center_x = np.mean([p[0] for p in eye_pts])
    eye_center_y = np.mean([p[1] for p in eye_pts])

    iris_center_x = np.mean([p[0] for p in iris_pts])
    iris_center_y = np.mean([p[1] for p in iris_pts])

    eye_width = euclidean(eye_pts[0], eye_pts[3])  # p1 to p4
    if eye_width == 0:
        return 0.0

    offset = euclidean(
        (iris_center_x, iris_center_y),
        (eye_center_x, eye_center_y)
    ) / eye_width

    return offset


def draw_status(frame, status, ear, gaze_offset, drowsy_elapsed, distracted_elapsed):
    """Draw colored overlay text on the frame."""
    h, w = frame.shape[:2]

    # Status color

    color_map = {
        "FOCUSED":     (0, 220, 0),
        "DROWSY":      (0, 100, 255),
        "DISTRACTED":  (0, 165, 255),
    }
    color = color_map.get(status, (255, 255, 255))

    # Semi-transparent banner at top

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 80), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

    # Status text

    cv2.putText(frame, f"STATUS: {status}", (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.4, color, 3)

    # Small info at bottom

    info = f"EAR: {ear:.3f}  |  Gaze Offset: {gaze_offset:.3f}  |  Drowsy: {drowsy_elapsed:.1f}s  |  Distracted: {distracted_elapsed:.1f}s"
    cv2.putText(frame, info, (10, h - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    # Warning flashes

    if status == "DROWSY":
        cv2.putText(frame, "⚠ Wake up! Take a break.", (20, h - 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 100, 255), 2)
    elif status == "DISTRACTED":
        cv2.putText(frame, "⚠ Eyes on screen!", (20, h - 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)



# MAIN — WebcamMonitor class


class WebcamMonitor:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,    # IMPORTANT: enables iris landmarks
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

        # Timers
        self.drowsy_start      = None
        self.distracted_start  = None

        # State for logging (Phase 2 will use these)

        self.current_status    = "FOCUSED"
        self.status_log        = []   # list of (timestamp, status)

    def get_status(self):
        """Returns the current attention status string."""
        return self.current_status

    def run(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print(" Could not open webcam. Check if it's connected.")
            return

        print(" Webcam started. Press 'Q' to quit.")

        while True:
            ret, frame = cap.read()
            if not ret:
                print(" Failed to grab frame.")
                break

            frame = cv2.flip(frame, 1)   # Mirror so it feels natural
            h, w = frame.shape[:2]
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            results = self.face_mesh.process(rgb_frame)

            ear          = 0.0
            gaze_offset  = 0.0
            status       = "FOCUSED"

            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0].landmark

                # EAR Calculation 

                left_ear  = calculate_EAR(landmarks, LEFT_EYE_IDX, w, h)
                right_ear = calculate_EAR(landmarks, RIGHT_EYE_IDX, w, h)
                ear = (left_ear + right_ear) / 2.0

                #  Gaze Calculation 

                left_gaze  = calculate_gaze_offset(landmarks, LEFT_EYE_IDX,  LEFT_IRIS_IDX,  w, h)
                right_gaze = calculate_gaze_offset(landmarks, RIGHT_EYE_IDX, RIGHT_IRIS_IDX, w, h)
                gaze_offset = (left_gaze + right_gaze) / 2.0

                now = time.time()

                # Drowsiness Logic 

                if ear < EAR_THRESHOLD:
                    if self.drowsy_start is None:
                        self.drowsy_start = now
                else:
                    self.drowsy_start = None   # Reset timer when eyes open

                #  Distraction Logic 

                if gaze_offset > 0.35:
                    if self.distracted_start is None:
                        self.distracted_start = now
                else:
                    self.distracted_start = None

                #  Determine Final Status 

                drowsy_elapsed     = (now - self.drowsy_start)     if self.drowsy_start     else 0.0
                distracted_elapsed = (now - self.distracted_start) if self.distracted_start else 0.0

                if drowsy_elapsed >= DROWSY_TIME_LIMIT:
                    status = "DROWSY"
                elif distracted_elapsed >= DISTRACTED_TIME_LIMIT:
                    status = "DISTRACTED"
                else:
                    status = "FOCUSED"

            else:
                # No face detected

                status = "DISTRACTED"
                drowsy_elapsed     = 0.0
                distracted_elapsed = 0.0

            # Update state

            self.current_status = status
            self.status_log.append((time.time(), status))

            # Draw on frame

            draw_status(frame, status, ear, gaze_offset,
                        drowsy_elapsed if self.drowsy_start else 0.0,
                        distracted_elapsed if self.distracted_start else 0.0)

            cv2.imshow("Study Monitor — Phase 1", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        print(f"\n Session ended. Total states logged: {len(self.status_log)}")

        # Preview log

        print("\nLast 10 status entries:")
        for ts, s in self.status_log[-10:]:
            print(f"  {time.strftime('%H:%M:%S', time.localtime(ts))} → {s}")

        return self.status_log



# ENTRY POINT

if __name__ == "__main__":
    monitor = WebcamMonitor()
    monitor.run()