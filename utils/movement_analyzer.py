"""Movement analysis module for real-time form feedback."""
import cv2
import mediapipe as mp
import numpy as np
import streamlit as st
from typing import Dict, List, Tuple, Optional, Union
import anthropic
import json
from datetime import datetime
import os
from pathlib import Path

class MovementAnalyzer:
    def __init__(self):
        """Initialize the movement analyzer with required components."""
        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=2  # Increased model complexity for better accuracy
        )
        self.mp_draw = mp.solutions.drawing_utils

        # Initialize Anthropic client for analysis
        self.client = anthropic.Anthropic(
            api_key=os.environ.get('ANTHROPIC_API_KEY')
        )

        # Movement-specific angle thresholds and checkpoints
        self.movement_criteria = {
            "Clean": {
                "start_position": {
                    "description": "feet shoulder-width apart, bar over midfoot",
                    "angles": {
                        "hip": (170, 180),  # Nearly straight
                        "knee": (140, 150),  # Slight bend
                        "ankle": (80, 90)    # Neutral position
                    }
                },
                "pulling_position": {
                    "description": "explosive pull, bar close to body",
                    "angles": {
                        "hip": (100, 130),
                        "knee": (120, 140),
                        "ankle": (60, 80)
                    }
                },
                "catch_position": {
                    "description": "fast elbow turnover, full front rack",
                    "angles": {
                        "hip": (130, 150),
                        "knee": (110, 130),
                        "ankle": (70, 90)
                    }
                }
            },
            "Snatch": {
                "start_position": {
                    "description": "wide grip, feet shoulder-width apart",
                    "angles": {
                        "hip": (165, 180),
                        "knee": (135, 145),
                        "ankle": (80, 90)
                    }
                },
                "pulling_position": {
                    "description": "explosive extension, bar close to body",
                    "angles": {
                        "hip": (95, 125),
                        "knee": (115, 135),
                        "ankle": (55, 75)
                    }
                },
                "catch_position": {
                    "description": "locked arms overhead, stable stance",
                    "angles": {
                        "hip": (140, 160),
                        "knee": (120, 140),
                        "shoulder": (170, 180)
                    }
                }
            }
        }

    def start_analysis(self, movement_type: str, input_source: str = "camera", video_file: Union[None, bytes] = None):
        """Start movement analysis from camera or video file."""
        st.title(f"Real-time {movement_type} Analysis")

        # Create placeholders
        video_placeholder = st.empty()
        feedback_placeholder = st.empty()
        form_score_placeholder = st.empty()

        # Add movement-specific guidelines in sidebar
        if movement_type in self.movement_criteria:
            st.sidebar.subheader("Movement Guidelines")
            for phase, details in self.movement_criteria[movement_type].items():
                st.sidebar.markdown(f"**{phase}:**")
                st.sidebar.markdown(f"- {details['description']}")
                if 'angles' in details:
                    st.sidebar.markdown("Target angles:")
                    for joint, (min_angle, max_angle) in details['angles'].items():
                        st.sidebar.markdown(f"- {joint}: {min_angle}° - {max_angle}°")

        try:
            # Initialize video source
            if input_source == "camera":
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    st.error("Error: Could not access camera. Please check your camera connection.")
                    return
            else:
                # Save uploaded video to temporary file
                if video_file is None:
                    st.error("No video file provided")
                    return

                temp_file = Path("temp_video.mp4")
                temp_file.write_bytes(video_file)
                cap = cv2.VideoCapture(str(temp_file))

                if not cap.isOpened():
                    st.error("Error: Could not open video file")
                    temp_file.unlink()  # Clean up temp file
                    return

            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        if input_source != "camera":
                            st.info("Video analysis complete")
                        break

                    # Process frame
                    processed_frame, feedback = self.process_frame(frame, movement_type)

                    # Update video feed
                    video_placeholder.image(
                        cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB),
                        channels="RGB",
                        use_column_width=True
                    )

                    # Update feedback
                    suggestions_list = '\n'.join([f"- {s}" for s in feedback['suggestions']])
                    feedback_text = f"""
                    **Current Phase:** {feedback['phase']}

                    **Posture Assessment:** {feedback['posture']}

                    **Suggestions:**
                    {suggestions_list}
                    """
                    feedback_placeholder.markdown(feedback_text)

                    # Update form score
                    form_score_placeholder.progress(feedback['confidence'])

                    # Add delay for video playback
                    if input_source != "camera":
                        cv2.waitKey(30)

            finally:
                cap.release()
                if input_source != "camera" and 'temp_file' in locals():
                    temp_file.unlink()  # Clean up temp file

        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
            if 'cap' in locals():
                cap.release()
            if input_source != "camera" and 'temp_file' in locals():
                temp_file.unlink()  # Clean up temp file

    def process_frame(self, frame: np.ndarray, movement_type: str) -> Tuple[np.ndarray, Dict]:
        """
        Process a single frame and return the annotated frame with feedback.

        Args:
            frame: Input video frame
            movement_type: Type of movement being analyzed

        Returns:
            Tuple of annotated frame and feedback dictionary
        """
        # Convert frame to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Get pose landmarks
        results = self.pose.process(frame_rgb)

        # Initialize feedback
        feedback = {
            "posture": None,
            "suggestions": [],
            "confidence": 0.0,
            "phase": None
        }

        if results.pose_landmarks:
            # Draw pose landmarks
            self._draw_advanced_pose(frame, results.pose_landmarks)

            # Analyze pose and get feedback
            feedback = self._analyze_pose(results.pose_landmarks, movement_type)

            # Add feedback overlay
            frame = self._add_enhanced_feedback_overlay(frame, feedback, movement_type)

        return frame, feedback

    def _draw_advanced_pose(self, frame: np.ndarray, landmarks) -> None:
        """Draw enhanced pose landmarks with joint angles."""
        # Draw basic pose
        self.mp_draw.draw_landmarks(
            frame,
            landmarks,
            self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=self.mp_draw.DrawingSpec(
                color=(0, 255, 0),
                thickness=2,
                circle_radius=2
            ),
            connection_drawing_spec=self.mp_draw.DrawingSpec(
                color=(245, 117, 66),
                thickness=2
            )
        )

        # Draw joint angles
        angles = self._calculate_joint_angles(landmarks)
        for joint, angle in angles.items():
            if joint in ['hip', 'knee', 'ankle']:
                landmark = landmarks.landmark[getattr(self.mp_pose.PoseLandmark, f"{joint.upper()}_RIGHT")]
                position = (
                    int(landmark.x * frame.shape[1]),
                    int(landmark.y * frame.shape[0])
                )
                cv2.putText(
                    frame,
                    f"{joint}: {angle:.1f}°",
                    position,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    2
                )

    def _analyze_pose(self, landmarks, movement_type: str) -> Dict:
        """Analyze pose landmarks and generate feedback."""
        angles = self._calculate_joint_angles(landmarks)
        landmark_data = self._prepare_landmark_data(landmarks)
        feedback = self._get_ai_feedback(landmark_data, angles, movement_type)
        return feedback

    def _calculate_joint_angles(self, landmarks) -> Dict[str, float]:
        """Calculate key joint angles from landmarks."""
        angles = {}

        def calculate_angle(a, b, c) -> float:
            a = np.array([a.x, a.y, a.z])
            b = np.array([b.x, b.y, b.z])
            c = np.array([c.x, c.y, c.z])

            radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - \
                     np.arctan2(a[1]-b[1], a[0]-b[0])
            angle = np.abs(radians*180.0/np.pi)

            if angle > 180.0:
                angle = 360-angle

            return angle

        try:
            # Hip angle
            angles['hip'] = calculate_angle(
                landmarks.landmark[self.mp_pose.PoseLandmark.SHOULDER_RIGHT],
                landmarks.landmark[self.mp_pose.PoseLandmark.HIP_RIGHT],
                landmarks.landmark[self.mp_pose.PoseLandmark.KNEE_RIGHT]
            )

            # Knee angle
            angles['knee'] = calculate_angle(
                landmarks.landmark[self.mp_pose.PoseLandmark.HIP_RIGHT],
                landmarks.landmark[self.mp_pose.PoseLandmark.KNEE_RIGHT],
                landmarks.landmark[self.mp_pose.PoseLandmark.ANKLE_RIGHT]
            )

            # Ankle angle
            angles['ankle'] = calculate_angle(
                landmarks.landmark[self.mp_pose.PoseLandmark.KNEE_RIGHT],
                landmarks.landmark[self.mp_pose.PoseLandmark.ANKLE_RIGHT],
                landmarks.landmark[self.mp_pose.PoseLandmark.HEEL_RIGHT]
            )

            # Back angle (relative to vertical)
            shoulder = landmarks.landmark[self.mp_pose.PoseLandmark.SHOULDER_RIGHT]
            hip = landmarks.landmark[self.mp_pose.PoseLandmark.HIP_RIGHT]
            vertical = mp.solutions.pose.PoseLandmark(x=shoulder.x, y=0, z=shoulder.z)
            angles['back'] = calculate_angle(vertical, shoulder, hip)

        except Exception as e:
            print(f"Error calculating angles: {str(e)}")
            return {}

        return angles

    def _prepare_landmark_data(self, landmarks) -> str:
        """Prepare landmark data for AI analysis."""
        key_points = {
            "hip_angle": self._calculate_joint_angles(landmarks).get('hip', 0),
            "knee_angle": self._calculate_joint_angles(landmarks).get('knee', 0),
            "back_angle": self._calculate_joint_angles(landmarks).get('back', 0),
            "ankle_angle": self._calculate_joint_angles(landmarks).get('ankle', 0)
        }

        return str(key_points)

    def _get_ai_feedback(self, landmark_data: str, angles: Dict[str, float], movement_type: str) -> Dict:
        """Get AI-powered feedback on form."""
        try:
            # Prepare prompt for Claude
            prompt = f"""Analyze this Olympic weightlifting position for a {movement_type}:
            Joint Angles: {angles}
            Landmark Data: {landmark_data}

            Determine the current phase (e.g., start, pulling, catch).
            Provide specific feedback on posture and alignment, potential form issues, and specific corrections.

            Format response as JSON with keys:
            - phase: Current movement phase
            - posture: Overall posture assessment
            - suggestions: List of specific suggestions
            - confidence: Confidence score (0-1)
            """

            # Get AI response
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.2,
                max_tokens=150
            )

            # Parse response
            try:
                feedback_text = response.content
                feedback = json.loads(feedback_text)
            except (json.JSONDecodeError, AttributeError):
                feedback = {
                    "phase": "Unknown",
                    "posture": "Analysis failed",
                    "suggestions": ["Unable to analyze movement"],
                    "confidence": 0.0
                }
            return feedback
        except Exception as e:
            print(f"Error getting AI feedback: {str(e)}")
            return {
                "phase": "Unknown",
                "posture": "Unable to analyze",
                "suggestions": ["System error occurred"],
                "confidence": 0.0
            }

    def _add_enhanced_feedback_overlay(self, frame: np.ndarray, feedback: Dict, movement_type: str) -> np.ndarray:
        """Add enhanced feedback overlay with movement-specific guidance."""
        # Create semi-transparent overlay
        overlay = frame.copy()
        alpha = 0.7

        # Add movement phase indicator
        if feedback["phase"]:
            cv2.putText(
                overlay,
                f"Phase: {feedback['phase']}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

        # Add posture feedback with color coding
        if feedback["posture"]:
            color = (0, 255, 0) if feedback["confidence"] > 0.7 else (0, 255, 255)
            cv2.putText(
                overlay,
                feedback["posture"],
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

        # Add suggestions with visual indicators
        for i, suggestion in enumerate(feedback["suggestions"]):
            cv2.putText(
                overlay,
                f"→ {suggestion}",
                (10, 110 + (i * 30)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 200, 0),
                2
            )

        # Add confidence meter
        confidence_width = int(200 * feedback["confidence"])
        cv2.rectangle(
            overlay,
            (10, frame.shape[0] - 40),
            (210, frame.shape[0] - 20),
            (100, 100, 100),
            -1
        )
        cv2.rectangle(
            overlay,
            (10, frame.shape[0] - 40),
            (10 + confidence_width, frame.shape[0] - 20),
            (0, 255, 0),
            -1
        )
        cv2.putText(
            overlay,
            f"Form Score: {int(feedback['confidence'] * 100)}%",
            (10, frame.shape[0] - 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        # Blend overlay with original frame
        return cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    def _add_feedback_overlay(self, frame: np.ndarray, feedback: Dict) -> np.ndarray:
        """Add feedback overlay to frame."""
        # Create semi-transparent overlay
        overlay = frame.copy()

        # Add feedback text
        if feedback["posture"]:
            cv2.putText(
                overlay,
                f"Posture: {feedback['posture']}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

        # Add suggestions
        for i, suggestion in enumerate(feedback["suggestions"]):
            cv2.putText(
                overlay,
                suggestion,
                (10, 70 + (i * 30)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 0),
                2
            )

        # Add confidence score
        cv2.putText(
            overlay,
            f"Confidence: {feedback['confidence']:.2f}",
            (10, frame.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

        # Blend overlay with original frame
        alpha = 0.7
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

        return frame