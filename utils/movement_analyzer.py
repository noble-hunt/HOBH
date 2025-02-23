"""Movement analysis module with video stabilization for form feedback."""
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
            model_complexity=2
        )
        self.mp_draw = mp.solutions.drawing_utils

        # Initialize video stabilization components
        self.prev_gray = None
        self.prev_points = None
        self.transform_matrix = None
        self.smooth_transform = None
        self.stabilization_window = 30  # Number of frames for smoothing

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

    def _stabilize_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Stabilize video frame using optical flow and motion smoothing.
        """
        try:
            # Convert frame to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Initialize previous frame and points if needed
            if self.prev_gray is None:
                self.prev_gray = gray
                # Detect feature points in the first frame
                points = cv2.goodFeaturesToTrack(
                    gray, maxCorners=200, qualityLevel=0.01, 
                    minDistance=30, blockSize=3
                )
                if points is None:
                    return frame
                self.prev_points = points
                return frame

            # Calculate optical flow
            curr_points, status, err = cv2.calcOpticalFlowPyrLK(
                self.prev_gray, gray, self.prev_points, None
            )

            # Filter valid points
            if curr_points is None or self.prev_points is None:
                return frame

            idx = np.where(status == 1)[0]
            if len(idx) < 4:  # Need at least 4 points for perspective transform
                return frame

            curr_points = curr_points[idx]
            prev_points = self.prev_points[idx]

            # Estimate transform matrix
            transform = cv2.estimateAffinePartial2D(prev_points, curr_points)[0]
            if transform is None:
                return frame

            # Apply smoothing to transform
            if self.transform_matrix is None:
                self.transform_matrix = transform
            else:
                # Smooth the transformation using exponential moving average
                smooth_factor = 0.8
                self.transform_matrix = (smooth_factor * self.transform_matrix + 
                                      (1 - smooth_factor) * transform)

            # Apply stabilization transform
            height, width = frame.shape[:2]
            stabilized = cv2.warpAffine(
                frame, self.transform_matrix, (width, height),
                borderMode=cv2.BORDER_REPLICATE
            )

            # Update previous frame and points
            self.prev_gray = gray
            self.prev_points = curr_points.reshape(-1, 1, 2)

            return stabilized

        except Exception as e:
            print(f"Stabilization error: {str(e)}")
            return frame

    def start_analysis(self, movement_type: str, input_source: str = "camera", 
                      video_file: Union[None, bytes] = None):
        """Start movement analysis with optional video stabilization."""
        st.title(f"Real-time {movement_type} Analysis")

        # Add stabilization toggle
        enable_stabilization = st.sidebar.checkbox(
            "Enable Video Stabilization", 
            value=True,
            help="Reduce camera shake for better analysis"
        )

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

                try:
                    # Create a temporary directory if it doesn't exist
                    temp_dir = Path("temp")
                    temp_dir.mkdir(exist_ok=True)

                    # Create temporary file with unique name
                    temp_file = temp_dir / f"temp_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                    temp_file.write_bytes(video_file)

                    cap = cv2.VideoCapture(str(temp_file))
                    if not cap.isOpened():
                        st.error("Error: Could not open video file")
                        return
                except Exception as e:
                    st.error(f"Error processing video file: {str(e)}")
                    return

            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        if input_source != "camera":
                            st.info("Video analysis complete")
                        break

                    # Apply video stabilization if enabled
                    if enable_stabilization:
                        frame = self._stabilize_frame(frame)

                    # Process frame
                    processed_frame, feedback = self.process_frame(frame, movement_type)

                    # Update video feed
                    video_placeholder.image(
                        cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB),
                        channels="RGB",
                        use_container_width=True
                    )

                    # Update feedback with error handling
                    if feedback.get('error'):
                        feedback_text = f"""
                        ⚠️ **Analysis Status:** {feedback['error']}

                        **Joint Angles:**
                        {feedback.get('angles', 'Not available')}
                        """
                    else:
                        phase = feedback.get('phase', 'Unknown')
                        posture = feedback.get('posture', 'Analyzing...')
                        suggestions = feedback.get('suggestions', [])

                        suggestions_list = '\n'.join([f"- {s}" for s in suggestions]) if suggestions else "- Analyzing movement..."

                        feedback_text = f"""
                        **Current Phase:** {phase}

                        **Posture Assessment:** {posture}

                        **Suggestions:**
                        {suggestions_list}
                        """
                    feedback_placeholder.markdown(feedback_text)

                    # Update form score
                    confidence = feedback.get('confidence', 0.0)
                    form_score_placeholder.progress(confidence)

                    # Add delay for video playback
                    if input_source != "camera":
                        cv2.waitKey(30)

            finally:
                cap.release()

        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
        finally:
            # Clean up resources
            if 'cap' in locals():
                cap.release()
            if input_source != "camera" and 'temp_file' in locals():
                try:
                    temp_file.unlink()  # Delete temporary file
                    if temp_dir.exists():
                        # Remove temp directory if empty
                        if not any(temp_dir.iterdir()):
                            temp_dir.rmdir()
                except Exception as e:
                    print(f"Error cleaning up temporary files: {str(e)}")

            # Reset stabilization variables
            self.prev_gray = None
            self.prev_points = None
            self.transform_matrix = None
            self.smooth_transform = None

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
            "phase": "Unknown",
            "posture": None,
            "suggestions": [],
            "confidence": 0.0
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
            # First check if we have valid angles data
            if not angles:
                return {
                    "error": "Unable to detect body positions accurately",
                    "angles": "No valid angles detected",
                    "confidence": 0.0
                }

            # Build detailed prompt for better analysis
            movement_criteria = self.movement_criteria.get(movement_type, {})
            prompt = f"""You are an Olympic weightlifting coach analyzing a {movement_type} movement.

Current position data:
Joint Angles: {angles}
Landmark Data: {landmark_data}

Movement criteria:
{json.dumps(movement_criteria, indent=2)}

Based on this data, provide a detailed analysis in JSON format with the following structure:
{{
    "phase": "start_position|pulling_position|catch_position",
    "posture": "Clear description of current posture",
    "suggestions": ["Specific, actionable feedback points"],
    "confidence": "Score between 0-1 based on form accuracy"
}}

Focus on comparing current angles with ideal ranges and providing specific corrections."""

            # Get AI response with retry logic
            try:
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
                if hasattr(response, 'content'):
                    try:
                        # Extract JSON from the response content
                        content = response.content
                        if isinstance(content, str):
                            # Find JSON-like content within the string
                            start_idx = content.find('{')
                            end_idx = content.rfind('}') + 1
                            if start_idx >= 0 and end_idx > start_idx:
                                json_str = content[start_idx:end_idx]
                                feedback = json.loads(json_str)
                                # Validate required fields
                                if all(k in feedback for k in ['phase', 'posture', 'suggestions', 'confidence']):
                                    return feedback

                    except json.JSONDecodeError:
                        pass  # Fall through to default response

            except Exception as api_error:
                print(f"API Error: {str(api_error)}")

            # If API fails or response is invalid, provide basic feedback based on angles
            return self._generate_basic_feedback(angles, movement_type)

        except Exception as e:
            print(f"Error in form analysis: {str(e)}")
            return {
                "error": "Form analysis temporarily unavailable",
                "angles": str(angles),
                "confidence": 0.0
            }

    def _generate_basic_feedback(self, angles: Dict[str, float], movement_type: str) -> Dict:
        """Generate basic feedback when AI analysis is unavailable."""
        movement_criteria = self.movement_criteria.get(movement_type, {})
        feedback = {
            "phase": "Unknown",
            "posture": "Basic form analysis",
            "suggestions": [],
            "confidence": 0.5
        }

        for phase, criteria in movement_criteria.items():
            if 'angles' in criteria:
                matches = 0
                total = 0
                for joint, (min_angle, max_angle) in criteria['angles'].items():
                    if joint in angles:
                        total += 1
                        if min_angle <= angles[joint] <= max_angle:
                            matches += 1
                            feedback["suggestions"].append(f"Good {joint} angle")
                        else:
                            feedback["suggestions"].append(
                                f"Adjust {joint} angle (current: {angles[joint]:.1f}°, target: {min_angle}°-{max_angle}°)"
                            )

                if total > 0 and matches/total > 0.7:
                    feedback["phase"] = phase
                    feedback["confidence"] = matches/total

        if not feedback["suggestions"]:
            feedback["suggestions"] = ["Maintain proper form", "Keep core engaged", "Stay balanced"]

        return feedback

    def _add_enhanced_feedback_overlay(self, frame: np.ndarray, feedback: Dict, movement_type: str) -> np.ndarray:
        """Add enhanced feedback overlay with movement-specific guidance."""
        # Create semi-transparent overlay
        overlay = frame.copy()
        alpha = 0.7

        # Add movement phase indicator
        if feedback.get("phase"):
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
        if feedback.get("posture"):
            color = (0, 255, 0) if feedback.get("confidence", 0) > 0.7 else (0, 255, 255)
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
        for i, suggestion in enumerate(feedback.get("suggestions", [])):
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
        confidence = feedback.get("confidence", 0)
        confidence_width = int(200 * confidence)
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
            f"Form Score: {int(confidence * 100)}%",
            (10, frame.shape[0] - 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        # Blend overlay with original frame
        return cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)