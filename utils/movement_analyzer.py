"""Movement analysis module for real-time form feedback."""
import cv2
import mediapipe as mp
import numpy as np
import streamlit as st
from typing import Dict, List, Tuple, Optional
import anthropic
from datetime import datetime
import os

class MovementAnalyzer:
    def __init__(self):
        """Initialize the movement analyzer with required components."""
        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils

        # Initialize Anthropic client for analysis
        self.client = anthropic.Anthropic(
            api_key=os.environ.get('ANTHROPIC_API_KEY')
        )

        # Movement-specific angle thresholds and checkpoints
        self.movement_criteria = {
            "Clean": {
                "start_position": "feet shoulder-width apart, bar over midfoot",
                "key_points": [
                    "maintain straight back",
                    "bar close to shins",
                    "shoulders over bar",
                    "hips above knees"
                ]
            },
            "Snatch": {
                "start_position": "wide grip, feet shoulder-width apart",
                "key_points": [
                    "bar close to body",
                    "explosive hip extension",
                    "full lock-out overhead",
                    "stable receiving position"
                ]
            }
        }

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Process a single frame and return the annotated frame with feedback.
        
        Args:
            frame: Input video frame
            
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
            "confidence": 0.0
        }
        
        if results.pose_landmarks:
            # Draw pose landmarks on frame
            self.mp_draw.draw_landmarks(
                frame,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS
            )
            
            # Analyze pose and get feedback
            feedback = self._analyze_pose(results.pose_landmarks)
            
            # Add feedback overlay to frame
            frame = self._add_feedback_overlay(frame, feedback)
        
        return frame, feedback

    def _analyze_pose(self, landmarks) -> Dict:
        """
        Analyze pose landmarks and generate feedback.
        
        Args:
            landmarks: MediaPipe pose landmarks
            
        Returns:
            Dictionary containing feedback and suggestions
        """
        # Extract key angles and positions
        angles = self._calculate_joint_angles(landmarks)
        
        # Prepare landmark data for AI analysis
        landmark_data = self._prepare_landmark_data(landmarks)
        
        # Get AI-powered feedback
        feedback = self._get_ai_feedback(landmark_data, angles)
        
        return feedback

    def _calculate_joint_angles(self, landmarks) -> Dict[str, float]:
        """Calculate key joint angles from landmarks."""
        angles = {}
        
        # Helper function to calculate angle between three points
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
        
        # Calculate key angles
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
        }
        
        return str(key_points)

    def _get_ai_feedback(self, landmark_data: str, angles: Dict[str, float]) -> Dict:
        """Get AI-powered feedback on form."""
        try:
            # Prepare prompt for Claude
            prompt = f"""Analyze this Olympic weightlifting position:
            Joint Angles: {angles}
            Landmark Data: {landmark_data}
            
            Provide specific feedback on:
            1. Posture and alignment
            2. Potential form issues
            3. Specific corrections
            
            Format response as JSON with keys:
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
            feedback = response.content
            
            return feedback
        except Exception as e:
            print(f"Error getting AI feedback: {str(e)}")
            return {
                "posture": "Unable to analyze",
                "suggestions": [],
                "confidence": 0.0
            }

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

    def start_analysis(self, movement_type: str):
        """Start real-time movement analysis."""
        st.title(f"Real-time {movement_type} Analysis")
        
        # Create placeholder for video feed
        video_placeholder = st.empty()
        
        # Create feedback placeholder
        feedback_placeholder = st.empty()
        
        # Add movement-specific guidelines
        if movement_type in self.movement_criteria:
            st.sidebar.subheader("Movement Guidelines")
            st.sidebar.write(f"Start Position: {self.movement_criteria[movement_type]['start_position']}")
            st.sidebar.write("Key Points:")
            for point in self.movement_criteria[movement_type]['key_points']:
                st.sidebar.write(f"- {point}")
        
        # Initialize video capture
        video_capture = cv2.VideoCapture(0)
        
        try:
            while True:
                ret, frame = video_capture.read()
                if not ret:
                    break
                
                # Process frame
                processed_frame, feedback = self.process_frame(frame)
                
                # Update video feed
                video_placeholder.image(
                    cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB),
                    channels="RGB",
                    use_column_width=True
                )
                
                # Update feedback
                feedback_placeholder.json(feedback)
                
        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
        finally:
            video_capture.release()
