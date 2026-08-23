import os
import cv2
import numpy as np
import torch

from typing import List, Tuple, Optional
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1


class FaceEngine:
    """
    OpenCV + FaceNet face recognition engine.

    OpenCV:
        - Reads and processes images/video frames.

    MTCNN:
        - Detects and aligns faces.

    FaceNet / InceptionResnetV1:
        - Generates 512-dimensional face embeddings.
    """

    def __init__(self):
        self.embedding_dim = 512

        # Use CPU for compatibility with normal laptops.
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

        print(f"[FaceEngine] Using device: {self.device}")

        # Face detector + alignment
        self.mtcnn = MTCNN(
            image_size=160,
            margin=20,
            min_face_size=20,
            thresholds=[0.6, 0.7, 0.7],
            factor=0.709,
            post_process=True,
            device=self.device,
            keep_all=True,
        )

        # FaceNet model
        self.facenet = InceptionResnetV1(
            pretrained="vggface2"
        ).eval().to(self.device)

        print("[FaceEngine] FaceNet model loaded successfully.")

    # ---------------------------------------------------------
    # FACE DETECTION
    # ---------------------------------------------------------

    def detect_faces(
        self,
        image: np.ndarray
    ) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces using FaceNet's MTCNN detector.

        Returns:
            [(x, y, width, height), ...]
        """

        if image is None or image.size == 0:
            return []

        try:
            # OpenCV uses BGR.
            # PIL / MTCNN expects RGB.
            rgb_image = cv2.cvtColor(
                image,
                cv2.COLOR_BGR2RGB
            )

            pil_image = Image.fromarray(rgb_image)

            boxes, probabilities = self.mtcnn.detect(
                pil_image
            )

            if boxes is None:
                return []

            h, w = image.shape[:2]

            faces = []

            for box, probability in zip(
                boxes,
                probabilities if probabilities is not None else [1.0] * len(boxes)
            ):
                if probability is not None and probability < 0.80:
                    continue

                x1, y1, x2, y2 = box

                x1 = max(0, int(x1))
                y1 = max(0, int(y1))
                x2 = min(w, int(x2))
                y2 = min(h, int(y2))

                box_w = x2 - x1
                box_h = y2 - y1

                if box_w > 0 and box_h > 0:
                    faces.append(
                        (x1, y1, box_w, box_h)
                    )

            return faces

        except Exception as exc:
            print(
                f"[FaceEngine] Face detection error: {exc}"
            )
            return []

    # ---------------------------------------------------------
    # FACE CROP
    # ---------------------------------------------------------

    def extract_face_crop(
        self,
        image: np.ndarray,
        bbox: Tuple[int, int, int, int]
    ) -> np.ndarray:
        """
        Extracts a face crop from an OpenCV image.

        Returns a 160x160 BGR image.
        """

        x, y, w, h = bbox

        h_img, w_img = image.shape[:2]

        # Add a small margin around the detected face.
        pad_x = int(w * 0.10)
        pad_y = int(h * 0.10)

        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y)
        x2 = min(w_img, x + w + pad_x)
        y2 = min(h_img, y + h + pad_y)

        crop = image[y1:y2, x1:x2]

        if crop.size == 0:
            return np.empty((0, 0, 3), dtype=np.uint8)

        return cv2.resize(
            crop,
            (160, 160),
            interpolation=cv2.INTER_AREA
        )

    # ---------------------------------------------------------
    # FACENET EMBEDDING
    # ---------------------------------------------------------

    def generate_embedding(
        self,
        face_crop: np.ndarray
    ) -> List[float]:
        """
        Generates a real 512-dimensional FaceNet embedding.

        The output is L2-normalized so cosine similarity
        can be calculated directly by the matcher.
        """

        if face_crop is None or face_crop.size == 0:
            return [0.0] * self.embedding_dim

        try:
            # BGR → RGB
            rgb = cv2.cvtColor(
                face_crop,
                cv2.COLOR_BGR2RGB
            )

            # PIL image
            pil_image = Image.fromarray(rgb)

            # MTCNN-compatible tensor preprocessing.
            # We use the same normalization expected by
            # facenet-pytorch.
            face_tensor = self._prepare_face_tensor(
                pil_image
            )

            if face_tensor is None:
                return [0.0] * self.embedding_dim

            face_tensor = face_tensor.unsqueeze(0).to(
                self.device
            )

            with torch.no_grad():
                embedding = self.facenet(
                    face_tensor
                )

            # L2 normalize.
            embedding = torch.nn.functional.normalize(
                embedding,
                p=2,
                dim=1
            )

            vector = (
                embedding
                .squeeze(0)
                .cpu()
                .numpy()
                .astype(np.float32)
            )

            if vector.shape[0] != self.embedding_dim:
                print(
                    "[FaceEngine] Unexpected embedding dimension:",
                    vector.shape
                )
                return [0.0] * self.embedding_dim

            return vector.tolist()

        except Exception as exc:
            print(
                f"[FaceEngine] Embedding generation error: {exc}"
            )
            return [0.0] * self.embedding_dim

    # ---------------------------------------------------------
    # FACENET PREPROCESSING
    # ---------------------------------------------------------

    def _prepare_face_tensor(
        self,
        image: Image.Image
    ) -> Optional[torch.Tensor]:
        """
        Converts a PIL face image into the normalized tensor
        expected by InceptionResnetV1.
        """

        try:
            image = image.convert("RGB")
            image = image.resize(
                (160, 160),
                Image.Resampling.BILINEAR
            )

            array = np.asarray(
                image,
                dtype=np.float32
            )

            # Convert [0,255] → [-1,1]
            array = (array - 127.5) / 128.0

            # HWC → CHW
            tensor = torch.from_numpy(
                array.transpose(2, 0, 1)
            )

            return tensor

        except Exception as exc:
            print(
                f"[FaceEngine] Preprocessing error: {exc}"
            )
            return None

    # ---------------------------------------------------------
    # REGISTER PERSON PHOTO
    # ---------------------------------------------------------

    def process_person_photo(
        self,
        image_bytes: bytes
    ) -> Tuple[Optional[List[float]], Optional[str]]:
        """
        Processes a reference photograph.

        1. Decode image.
        2. Detect faces.
        3. Select the largest face.
        4. Generate FaceNet 512-d embedding.
        """

        try:
            nparr = np.frombuffer(
                image_bytes,
                np.uint8
            )

            image = cv2.imdecode(
                nparr,
                cv2.IMREAD_COLOR
            )

            if image is None:
                return (
                    None,
                    "Unable to decode uploaded image."
                )

            faces = self.detect_faces(image)

            if not faces:
                return (
                    None,
                    "No clear face was detected in the reference photograph."
                )

            # Select the largest detected face.
            faces.sort(
                key=lambda box: box[2] * box[3],
                reverse=True
            )

            primary_face = faces[0]

            crop = self.extract_face_crop(
                image,
                primary_face
            )

            if crop.size == 0:
                return (
                    None,
                    "Unable to extract the detected face."
                )

            embedding = self.generate_embedding(
                crop
            )

            if not embedding or np.linalg.norm(
                np.asarray(embedding)
            ) < 1e-6:
                return (
                    None,
                    "Unable to generate a valid face embedding."
                )

            return embedding, None

        except Exception as exc:
            print(
                f"[FaceEngine] Reference photo error: {exc}"
            )

            return (
                None,
                "Face processing failed. Please use a clear frontal photograph."
            )


face_engine = FaceEngine()