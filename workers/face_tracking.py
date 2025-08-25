import os
import sys
import cv2
import numpy as np
import tempfile
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import mediapipe as mp

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from database import Database
from utils import generate_id
from schemas import JobStatus

db = Database()

class FaceTracker:
    def __init__(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize MediaPipe solutions
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.5
        )
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=5,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
    def detect_faces_in_video(self, video_path: str) -> List[Dict]:
        """Detect and track faces throughout the video."""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        face_tracking_data = []
        frame_index = 0
        
        # Process every 10th frame for efficiency
        sample_rate = 10
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_index % sample_rate == 0:
                timestamp = frame_index / fps
                
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Detect faces
                face_results = self.face_detection.process(rgb_frame)
                
                frame_data = {
                    "timestamp": timestamp,
                    "frame_index": frame_index,
                    "faces": [],
                    "frame_center": (frame.shape[1] // 2, frame.shape[0] // 2)
                }
                
                if face_results.detections:
                    for detection in face_results.detections:
                        # Get bounding box
                        bbox = detection.location_data.relative_bounding_box
                        h, w, _ = frame.shape
                        
                        face_data = {
                            "bbox": {
                                "x": int(bbox.xmin * w),
                                "y": int(bbox.ymin * h),
                                "width": int(bbox.width * w),
                                "height": int(bbox.height * h)
                            },
                            "confidence": detection.score[0],
                            "center": (
                                int((bbox.xmin + bbox.width / 2) * w),
                                int((bbox.ymin + bbox.height / 2) * h)
                            )
                        }
                        
                        # Add face landmarks for more detailed tracking
                        mesh_results = self.face_mesh.process(rgb_frame)
                        if mesh_results.multi_face_landmarks:
                            landmarks = mesh_results.multi_face_landmarks[0]
                            face_data["landmarks"] = [
                                {"x": landmark.x * w, "y": landmark.y * h, "z": landmark.z}
                                for landmark in landmarks.landmark
                            ]
                        
                        frame_data["faces"].append(face_data)
                
                face_tracking_data.append(frame_data)
            
            frame_index += 1
        
        cap.release()
        return face_tracking_data
    
    def detect_pose_in_video(self, video_path: str) -> List[Dict]:
        """Detect and track human poses throughout the video."""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        pose_tracking_data = []
        frame_index = 0
        sample_rate = 10
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_index % sample_rate == 0:
                timestamp = frame_index / fps
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process pose
                pose_results = self.pose.process(rgb_frame)
                
                frame_data = {
                    "timestamp": timestamp,
                    "frame_index": frame_index,
                    "pose_detected": False,
                    "keypoints": []
                }
                
                if pose_results.pose_landmarks:
                    frame_data["pose_detected"] = True
                    h, w, _ = frame.shape
                    
                    for idx, landmark in enumerate(pose_results.pose_landmarks.landmark):
                        frame_data["keypoints"].append({
                            "id": idx,
                            "x": landmark.x * w,
                            "y": landmark.y * h,
                            "z": landmark.z,
                            "visibility": landmark.visibility
                        })
                
                pose_tracking_data.append(frame_data)
            
            frame_index += 1
        
        cap.release()
        return pose_tracking_data
    
    def calculate_smart_crop_regions(self, face_data: List[Dict], pose_data: List[Dict], 
                                   video_dimensions: Tuple[int, int], target_ratio: str) -> List[Dict]:
        """Calculate optimal crop regions based on face and pose tracking."""
        width, height = video_dimensions
        crop_regions = []
        
        for i, face_frame in enumerate(face_data):
            timestamp = face_frame["timestamp"]
            
            # Default to center crop
            crop_region = self._get_center_crop(width, height, target_ratio)
            crop_region["timestamp"] = timestamp
            crop_region["tracking_method"] = "center"
            
            # If faces detected, prioritize face-based cropping
            if face_frame["faces"]:
                crop_region = self._get_face_based_crop(
                    face_frame["faces"], width, height, target_ratio
                )
                crop_region["timestamp"] = timestamp
                crop_region["tracking_method"] = "face"
            
            # If pose detected but no face, use pose-based cropping
            elif i < len(pose_data) and pose_data[i]["pose_detected"]:
                crop_region = self._get_pose_based_crop(
                    pose_data[i]["keypoints"], width, height, target_ratio
                )
                crop_region["timestamp"] = timestamp
                crop_region["tracking_method"] = "pose"
            
            crop_regions.append(crop_region)
        
        # Smooth crop regions to avoid jittery movement
        smoothed_regions = self._smooth_crop_regions(crop_regions)
        
        return smoothed_regions
    
    def _get_face_based_crop(self, faces: List[Dict], width: int, height: int, target_ratio: str) -> Dict:
        """Calculate crop region based on detected faces."""
        if not faces:
            return self._get_center_crop(width, height, target_ratio)
        
        # For multiple faces, focus on the largest/most confident face
        primary_face = max(faces, key=lambda f: f["confidence"] * f["bbox"]["width"] * f["bbox"]["height"])
        face_center = primary_face["center"]
        
        if target_ratio == "9:16":
            # Vertical crop
            crop_width = min(width, height * 9 // 16)
            crop_height = height
            
            # Center crop horizontally around face
            crop_x = max(0, min(face_center[0] - crop_width // 2, width - crop_width))
            crop_y = 0
            
        elif target_ratio == "1:1":
            # Square crop
            crop_size = min(width, height)
            
            # Center around face
            crop_x = max(0, min(face_center[0] - crop_size // 2, width - crop_size))
            crop_y = max(0, min(face_center[1] - crop_size // 2, height - crop_size))
            crop_width = crop_height = crop_size
            
        else:  # "16:9"
            # Horizontal crop
            crop_width = width
            crop_height = min(height, width * 9 // 16)
            
            # Center crop vertically around face
            crop_x = 0
            crop_y = max(0, min(face_center[1] - crop_height // 2, height - crop_height))
        
        return {
            "x": crop_x,
            "y": crop_y,
            "width": crop_width,
            "height": crop_height,
            "confidence": primary_face["confidence"]
        }
    
    def _get_pose_based_crop(self, keypoints: List[Dict], width: int, height: int, target_ratio: str) -> Dict:
        """Calculate crop region based on pose keypoints."""
        if not keypoints:
            return self._get_center_crop(width, height, target_ratio)
        
        # Find torso center (average of shoulder and hip keypoints)
        relevant_points = []
        
        # MediaPipe pose landmark indices
        torso_indices = [11, 12, 23, 24]  # shoulders and hips
        
        for point in keypoints:
            if point["id"] in torso_indices and point["visibility"] > 0.5:
                relevant_points.append((point["x"], point["y"]))
        
        if not relevant_points:
            return self._get_center_crop(width, height, target_ratio)
        
        # Calculate center of torso
        center_x = sum(p[0] for p in relevant_points) / len(relevant_points)
        center_y = sum(p[1] for p in relevant_points) / len(relevant_points)
        
        return self._calculate_crop_around_center(
            (center_x, center_y), width, height, target_ratio
        )
    
    def _get_center_crop(self, width: int, height: int, target_ratio: str) -> Dict:
        """Calculate center crop region."""
        center = (width // 2, height // 2)
        return self._calculate_crop_around_center(center, width, height, target_ratio)
    
    def _calculate_crop_around_center(self, center: Tuple[float, float], 
                                    width: int, height: int, target_ratio: str) -> Dict:
        """Calculate crop region around a center point."""
        center_x, center_y = center
        
        if target_ratio == "9:16":
            crop_width = min(width, height * 9 // 16)
            crop_height = height
            crop_x = max(0, min(int(center_x - crop_width // 2), width - crop_width))
            crop_y = 0
            
        elif target_ratio == "1:1":
            crop_size = min(width, height)
            crop_x = max(0, min(int(center_x - crop_size // 2), width - crop_size))
            crop_y = max(0, min(int(center_y - crop_size // 2), height - crop_size))
            crop_width = crop_height = crop_size
            
        else:  # "16:9"
            crop_width = width
            crop_height = min(height, width * 9 // 16)
            crop_x = 0
            crop_y = max(0, min(int(center_y - crop_height // 2), height - crop_height))
        
        return {
            "x": crop_x,
            "y": crop_y,
            "width": crop_width,
            "height": crop_height,
            "confidence": 0.5
        }
    
    def _smooth_crop_regions(self, regions: List[Dict], smoothing_factor: float = 0.3) -> List[Dict]:
        """Smooth crop regions to reduce jitter."""
        if len(regions) <= 1:
            return regions
        
        smoothed = [regions[0]]
        
        for i in range(1, len(regions)):
            current = regions[i]
            previous = smoothed[-1]
            
            # Exponential moving average
            smooth_x = int(previous["x"] * (1 - smoothing_factor) + current["x"] * smoothing_factor)
            smooth_y = int(previous["y"] * (1 - smoothing_factor) + current["y"] * smoothing_factor)
            
            smoothed_region = {
                **current,
                "x": smooth_x,
                "y": smooth_y
            }
            
            smoothed.append(smoothed_region)
        
        return smoothed

def analyze_video_subjects(video_id: str, job_id: str) -> Dict:
    """Analyze video for face and pose tracking data."""
    try:
        print(f"Starting subject analysis for video {video_id}")
        
        tracker = FaceTracker()
        
        # Update job status
        db.update_job(job_id, {
            "status": JobStatus.PROCESSING.value,
            "progress": 10,
            "updated_at": datetime.utcnow().isoformat()
        })
        
        # Get video record
        video = db.get_video(video_id)
        if not video:
            raise Exception("Video not found")
        
        # Download video
        file_data = db.storage.download_file(video["file_path"])
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            temp_file.write(file_data)
            temp_path = temp_file.name
        
        try:
            # Get video dimensions
            cap = cv2.VideoCapture(temp_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
            # Update progress
            db.update_job(job_id, {
                "progress": 30,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            # Detect faces
            face_data = tracker.detect_faces_in_video(temp_path)
            
            # Update progress
            db.update_job(job_id, {
                "progress": 60,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            # Detect poses
            pose_data = tracker.detect_pose_in_video(temp_path)
            
            # Update progress
            db.update_job(job_id, {
                "progress": 80,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            # Calculate smart crop regions for each aspect ratio
            crop_regions = {
                "9:16": tracker.calculate_smart_crop_regions(face_data, pose_data, (width, height), "9:16"),
                "1:1": tracker.calculate_smart_crop_regions(face_data, pose_data, (width, height), "1:1"),
                "16:9": tracker.calculate_smart_crop_regions(face_data, pose_data, (width, height), "16:9")
            }
            
            # Analyze tracking quality
            face_detection_rate = sum(1 for frame in face_data if frame["faces"]) / len(face_data) if face_data else 0
            pose_detection_rate = sum(1 for frame in pose_data if frame["pose_detected"]) / len(pose_data) if pose_data else 0
            
            analysis_result = {
                "video_id": video_id,
                "video_dimensions": {"width": width, "height": height},
                "face_detection_rate": face_detection_rate,
                "pose_detection_rate": pose_detection_rate,
                "total_faces_detected": sum(len(frame["faces"]) for frame in face_data),
                "crop_regions": crop_regions,
                "tracking_quality": "high" if face_detection_rate > 0.7 else "medium" if face_detection_rate > 0.3 else "low"
            }
            
            # Store analysis in database metadata
            db.update_video(video_id, {
                "metadata": analysis_result,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            # Update job as completed
            db.update_job(job_id, {
                "status": JobStatus.COMPLETED.value,
                "progress": 100,
                "metadata": {
                    "face_detection_rate": face_detection_rate,
                    "tracking_quality": analysis_result["tracking_quality"]
                },
                "updated_at": datetime.utcnow().isoformat()
            })
            
            print(f"Subject analysis completed for video {video_id}")
            return analysis_result
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        print(f"Error analyzing video subjects for {video_id}: {str(e)}")
        db.update_job(job_id, {
            "status": JobStatus.FAILED.value,
            "error_message": str(e),
            "updated_at": datetime.utcnow().isoformat()
        })
        raise
