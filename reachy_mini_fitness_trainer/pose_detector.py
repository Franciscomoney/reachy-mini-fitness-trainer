"""
Pose Detection using MediaPipe Tasks API
Tracks body landmarks and calculates joint angles for exercise detection
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, List

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


@dataclass
class PoseResult:
    """Result from pose detection"""
    landmarks: Optional[List] = None
    left_knee_angle: float = 180.0
    right_knee_angle: float = 180.0
    avg_knee_angle: float = 180.0
    left_shoulder_angle: float = 0.0
    right_shoulder_angle: float = 0.0
    avg_shoulder_angle: float = 0.0
    is_valid: bool = False
    confidence: float = 0.0


class PoseDetector:
    """MediaPipe Pose detector for fitness tracking using Tasks API"""

    # MediaPipe landmark indices
    # Lower body
    LEFT_HIP = 23
    LEFT_KNEE = 25
    LEFT_ANKLE = 27
    RIGHT_HIP = 24
    RIGHT_KNEE = 26
    RIGHT_ANKLE = 28
    # Upper body
    LEFT_SHOULDER = 11
    LEFT_ELBOW = 13
    LEFT_WRIST = 15
    RIGHT_SHOULDER = 12
    RIGHT_ELBOW = 14
    RIGHT_WRIST = 16

    def __init__(self, model_path: Optional[str] = None):
        # Download model if not provided
        if model_path is None:
            import urllib.request
            import os
            model_path = "/tmp/pose_landmarker_lite.task"
            if not os.path.exists(model_path):
                print("Downloading pose model...")
                urllib.request.urlretrieve(
                    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
                    model_path
                )

        # Create pose landmarker with very lenient thresholds for partial body detection
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.2,  # Very lenient for partial body
            min_pose_presence_confidence=0.2,   # Very lenient
            min_tracking_confidence=0.2         # Very lenient
        )
        self.detector = vision.PoseLandmarker.create_from_options(options)

    def calculate_angle(self, a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]) -> float:
        """
        Calculate angle at point B given three points A, B, C
        Returns angle in degrees (0-180)
        """
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)

        ba = a - b
        bc = c - b

        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
        angle = np.arccos(cosine_angle)

        return math.degrees(angle)

    def get_landmark_coords(self, landmarks, idx: int) -> Tuple[float, float]:
        """Get x, y coordinates for a landmark"""
        lm = landmarks[idx]
        return (lm.x, lm.y)

    def process_frame(self, frame) -> PoseResult:
        """
        Process a video frame and detect pose
        Returns PoseResult with knee angles for squat detection
        Now works with partial body visibility (just one leg visible is enough)
        """
        import cv2

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Create MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # Detect pose
        result = self.detector.detect(mp_image)

        if not result.pose_landmarks or len(result.pose_landmarks) == 0:
            return PoseResult(is_valid=False)

        landmarks = result.pose_landmarks[0]  # First detected pose

        # Check visibility of each leg separately - only need ONE leg visible
        left_leg_landmarks = [self.LEFT_HIP, self.LEFT_KNEE, self.LEFT_ANKLE]
        right_leg_landmarks = [self.RIGHT_HIP, self.RIGHT_KNEE, self.RIGHT_ANKLE]

        left_visibility = sum(landmarks[i].visibility for i in left_leg_landmarks) / 3
        right_visibility = sum(landmarks[i].visibility for i in right_leg_landmarks) / 3

        # Use very lenient threshold (0.1) - even partially visible legs work
        # MediaPipe often estimates occluded landmarks quite well
        MIN_VISIBILITY = 0.1
        left_valid = left_visibility >= MIN_VISIBILITY
        right_valid = right_visibility >= MIN_VISIBILITY

        # If neither leg meets even the low threshold, try using estimated landmarks anyway
        # This allows squat detection even when legs are partially occluded
        if not left_valid and not right_valid:
            # Fall back: if we have ANY landmark data, try to use it
            if left_visibility > 0 or right_visibility > 0:
                # Use whichever leg has more visibility
                left_valid = left_visibility >= right_visibility
                right_valid = not left_valid
            else:
                avg_visibility = max(left_visibility, right_visibility)
                return PoseResult(is_valid=False, confidence=avg_visibility)

        # Calculate knee angles for visible legs
        left_knee_angle = 180.0
        right_knee_angle = 180.0

        if left_valid:
            left_hip = self.get_landmark_coords(landmarks, self.LEFT_HIP)
            left_knee = self.get_landmark_coords(landmarks, self.LEFT_KNEE)
            left_ankle = self.get_landmark_coords(landmarks, self.LEFT_ANKLE)
            left_knee_angle = self.calculate_angle(left_hip, left_knee, left_ankle)

        if right_valid:
            right_hip = self.get_landmark_coords(landmarks, self.RIGHT_HIP)
            right_knee = self.get_landmark_coords(landmarks, self.RIGHT_KNEE)
            right_ankle = self.get_landmark_coords(landmarks, self.RIGHT_ANKLE)
            right_knee_angle = self.calculate_angle(right_hip, right_knee, right_ankle)

        # Average knee angle - use only visible legs
        if left_valid and right_valid:
            avg_knee_angle = (left_knee_angle + right_knee_angle) / 2
        elif left_valid:
            avg_knee_angle = left_knee_angle
        else:
            avg_knee_angle = right_knee_angle

        # Calculate shoulder angles (for arm exercises)
        left_shoulder_angle = 0.0
        right_shoulder_angle = 0.0

        # Check arm visibility
        left_arm_landmarks = [self.LEFT_SHOULDER, self.LEFT_ELBOW, self.LEFT_HIP]
        right_arm_landmarks = [self.RIGHT_SHOULDER, self.RIGHT_ELBOW, self.RIGHT_HIP]

        left_arm_visibility = sum(landmarks[i].visibility for i in left_arm_landmarks) / 3
        right_arm_visibility = sum(landmarks[i].visibility for i in right_arm_landmarks) / 3

        if left_arm_visibility >= MIN_VISIBILITY:
            left_hip = self.get_landmark_coords(landmarks, self.LEFT_HIP)
            left_shoulder = self.get_landmark_coords(landmarks, self.LEFT_SHOULDER)
            left_elbow = self.get_landmark_coords(landmarks, self.LEFT_ELBOW)
            # Angle at shoulder (hip-shoulder-elbow)
            left_shoulder_angle = self.calculate_angle(left_hip, left_shoulder, left_elbow)

        if right_arm_visibility >= MIN_VISIBILITY:
            right_hip = self.get_landmark_coords(landmarks, self.RIGHT_HIP)
            right_shoulder = self.get_landmark_coords(landmarks, self.RIGHT_SHOULDER)
            right_elbow = self.get_landmark_coords(landmarks, self.RIGHT_ELBOW)
            right_shoulder_angle = self.calculate_angle(right_hip, right_shoulder, right_elbow)

        # Average shoulder angle
        if left_arm_visibility >= MIN_VISIBILITY and right_arm_visibility >= MIN_VISIBILITY:
            avg_shoulder_angle = (left_shoulder_angle + right_shoulder_angle) / 2
        elif left_arm_visibility >= MIN_VISIBILITY:
            avg_shoulder_angle = left_shoulder_angle
        else:
            avg_shoulder_angle = right_shoulder_angle

        avg_visibility = max(left_visibility, right_visibility, left_arm_visibility, right_arm_visibility)

        return PoseResult(
            landmarks=landmarks,
            left_knee_angle=left_knee_angle,
            right_knee_angle=right_knee_angle,
            avg_knee_angle=avg_knee_angle,
            left_shoulder_angle=left_shoulder_angle,
            right_shoulder_angle=right_shoulder_angle,
            avg_shoulder_angle=avg_shoulder_angle,
            is_valid=True,
            confidence=avg_visibility
        )

    def close(self):
        """Release resources"""
        pass  # Tasks API handles cleanup automatically
