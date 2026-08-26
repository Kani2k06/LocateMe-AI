import gc
from typing import List, Tuple, Optional

import cv2
import numpy as np
import torch

from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1


class FaceEngine:
    """
    Lightweight OpenCV + FaceNet face recognition engine.

    Optimized for low-memory CPU environments such as Render.

    Pipeline:
        OpenCV
            ↓
        Resize frame for detection
            ↓
        MTCNN face detection
            ↓
        Face crop
            ↓
        FaceNet / InceptionResnetV1
            ↓
        512-dimensional normalized embedding
    """

    def __init__(self):

        # =========================================================
        # BASIC CONFIGURATION
        # =========================================================

        self.embedding_dim = 512

        # Maximum dimension used for MTCNN detection.
        # This dramatically reduces memory consumption when
        # CCTV videos contain 1080p/4K frames.
        self.max_detection_size = 640

        # CPU is intentionally used on Render.
        self.device = torch.device("cpu")

        # Limit PyTorch CPU threads.
        # This helps prevent excessive memory usage.
        try:
            torch.set_num_threads(1)
        except Exception:
            pass

        try:
            torch.set_num_interop_threads(1)
        except Exception:
            pass

        print(
            f"[FaceEngine] Using device: {self.device}"
        )

        # =========================================================
        # MTCNN FACE DETECTOR
        # =========================================================

        self.mtcnn = MTCNN(
    image_size=160,
    margin=20,
    min_face_size=40,
    thresholds=[0.6, 0.7, 0.7],
    factor=0.709,
    post_process=True,
    device=self.device,
    keep_all=True,
)

        # =========================================================
        # FACENET MODEL
        # =========================================================

        self.facenet = (
            InceptionResnetV1(
                pretrained="vggface2"
            )
            .eval()
            .to(self.device)
        )

        # Make absolutely sure inference mode is used.
        for parameter in self.facenet.parameters():
            parameter.requires_grad_(False)

        print(
            "[FaceEngine] FaceNet model loaded successfully."
        )

    # =============================================================
    # RESIZE FRAME FOR DETECTION
    # =============================================================

    def _resize_for_detection(
        self,
        image: np.ndarray,
    ) -> Tuple[np.ndarray, float]:
        """
        Resize large CCTV frames before MTCNN detection.

        Returns:
            resized_image
            scale_factor

        scale_factor maps coordinates from the resized image
        back to the original image.
        """

        if image is None or image.size == 0:
            return image, 1.0

        height, width = image.shape[:2]

        largest_dimension = max(
            height,
            width,
        )

        if largest_dimension <= self.max_detection_size:
            return image, 1.0

        scale = (
            self.max_detection_size
            / float(largest_dimension)
        )

        new_width = max(
            1,
            int(width * scale),
        )

        new_height = max(
            1,
            int(height * scale),
        )

        resized = cv2.resize(
            image,
            (
                new_width,
                new_height,
            ),
            interpolation=cv2.INTER_AREA,
        )

        return resized, scale

    # =============================================================
    # FACE DETECTION
    # =============================================================

    def detect_faces(
        self,
        image: np.ndarray,
    ) -> List[
        Tuple[int, int, int, int]
    ]:
        """
        Detect faces using MTCNN.

        The image is resized before detection when necessary
        to reduce memory consumption.

        Returns:
            [(x, y, width, height), ...]
        """

        if image is None or image.size == 0:
            return []

        resized_image = None
        rgb_image = None
        pil_image = None

        try:

            # -----------------------------------------------------
            # RESIZE FOR MEMORY-EFFICIENT DETECTION
            # -----------------------------------------------------

            resized_image, scale = (
                self._resize_for_detection(
                    image
                )
            )

            # -----------------------------------------------------
            # BGR → RGB
            # -----------------------------------------------------

            rgb_image = cv2.cvtColor(
                resized_image,
                cv2.COLOR_BGR2RGB,
            )

            pil_image = Image.fromarray(
                rgb_image
            )

            # -----------------------------------------------------
            # MTCNN DETECTION
            # -----------------------------------------------------

            with torch.inference_mode():

                boxes, probabilities = (
                    self.mtcnn.detect(
                        pil_image
                    )
                )

            if boxes is None:
                return []

            original_height, original_width = (
                image.shape[:2]
            )

            faces = []

            if probabilities is None:
                probabilities = [
                    1.0
                ] * len(boxes)

            # -----------------------------------------------------
            # CONVERT BOXES BACK TO ORIGINAL IMAGE COORDINATES
            # -----------------------------------------------------

            for box, probability in zip(
                boxes,
                probabilities,
            ):

                if (
                    probability is not None
                    and probability < 0.80
                ):
                    continue

                x1, y1, x2, y2 = box

                # Convert resized coordinates to original
                # coordinates.
                if scale != 1.0:

                    x1 /= scale
                    y1 /= scale
                    x2 /= scale
                    y2 /= scale

                x1 = max(
                    0,
                    int(x1),
                )

                y1 = max(
                    0,
                    int(y1),
                )

                x2 = min(
                    original_width,
                    int(x2),
                )

                y2 = min(
                    original_height,
                    int(y2),
                )

                box_width = x2 - x1
                box_height = y2 - y1

                if (
                    box_width > 0
                    and box_height > 0
                ):

                    faces.append(
                        (
                            x1,
                            y1,
                            box_width,
                            box_height,
                        )
                    )

            return faces

        except Exception as exc:

            print(
                "[FaceEngine] Face detection error:",
                exc,
            )

            return []

        finally:

            # -----------------------------------------------------
            # RELEASE TEMPORARY OBJECTS
            # -----------------------------------------------------

            del resized_image
            del rgb_image
            del pil_image

            gc.collect()

    # =============================================================
    # FACE CROP
    # =============================================================

    def extract_face_crop(
        self,
        image: np.ndarray,
        bbox: Tuple[
            int,
            int,
            int,
            int,
        ],
    ) -> np.ndarray:
        """
        Extract a 160x160 face crop.

        Only the required region of the original frame is copied.
        """

        if image is None or image.size == 0:
            return np.empty(
                (0, 0, 3),
                dtype=np.uint8,
            )

        x, y, w, h = bbox

        image_height, image_width = (
            image.shape[:2]
        )

        # Small margin around face.
        pad_x = int(
            w * 0.10
        )

        pad_y = int(
            h * 0.10
        )

        x1 = max(
            0,
            x - pad_x,
        )

        y1 = max(
            0,
            y - pad_y,
        )

        x2 = min(
            image_width,
            x + w + pad_x,
        )

        y2 = min(
            image_height,
            y + h + pad_y,
        )

        crop = image[
            y1:y2,
            x1:x2,
        ]

        if crop.size == 0:
            return np.empty(
                (0, 0, 3),
                dtype=np.uint8,
            )

        # copy() prevents the returned crop from keeping
        # the entire original video frame alive in memory.
        crop = crop.copy()

        resized_crop = cv2.resize(
            crop,
            (
                160,
                160,
            ),
            interpolation=cv2.INTER_AREA,
        )

        del crop

        return resized_crop

    # =============================================================
    # FACENET EMBEDDING
    # =============================================================

    def generate_embedding(
        self,
        face_crop: np.ndarray,
    ) -> List[float]:
        """
        Generate a normalized 512-dimensional FaceNet embedding.

        Uses inference_mode() to minimize memory usage.
        """

        if (
            face_crop is None
            or face_crop.size == 0
        ):
            return [
                0.0
            ] * self.embedding_dim

        face_tensor = None
        embedding = None
        vector = None

        try:

            # -----------------------------------------------------
            # BGR → RGB
            # -----------------------------------------------------

            rgb = cv2.cvtColor(
                face_crop,
                cv2.COLOR_BGR2RGB,
            )

            # -----------------------------------------------------
            # PIL
            # -----------------------------------------------------

            pil_image = Image.fromarray(
                rgb
            )

            del rgb

            # -----------------------------------------------------
            # PREPROCESS
            # -----------------------------------------------------

            face_tensor = (
                self._prepare_face_tensor(
                    pil_image
                )
            )

            del pil_image

            if face_tensor is None:

                return [
                    0.0
                ] * self.embedding_dim

            # -----------------------------------------------------
            # BATCH DIMENSION
            # -----------------------------------------------------

            face_tensor = (
                face_tensor
                .unsqueeze(0)
                .to(self.device)
            )

            # -----------------------------------------------------
            # FACENET INFERENCE
            # -----------------------------------------------------

            with torch.inference_mode():

                embedding = self.facenet(
                    face_tensor
                )

                # L2 normalization.
                embedding = (
                    torch.nn.functional.normalize(
                        embedding,
                        p=2,
                        dim=1,
                    )
                )

                # Copy result immediately to CPU.
                vector = (
                    embedding
                    .squeeze(0)
                    .cpu()
                    .numpy()
                    .astype(
                        np.float32
                    )
                )

            # -----------------------------------------------------
            # VALIDATE DIMENSION
            # -----------------------------------------------------

            if (
                vector.shape[0]
                != self.embedding_dim
            ):

                print(
                    "[FaceEngine] Unexpected embedding "
                    "dimension:",
                    vector.shape,
                )

                return [
                    0.0
                ] * self.embedding_dim

            result = vector.tolist()

            return result

        except Exception as exc:

            print(
                "[FaceEngine] Embedding generation error:",
                exc,
            )

            return [
                0.0
            ] * self.embedding_dim

        finally:

            # -----------------------------------------------------
            # RELEASE TEMPORARY TENSORS
            # -----------------------------------------------------

            del face_tensor
            del embedding
            del vector

            gc.collect()

    # =============================================================
    # FACENET PREPROCESSING
    # =============================================================

    def _prepare_face_tensor(
        self,
        image: Image.Image,
    ) -> Optional[torch.Tensor]:
        """
        Converts PIL image into the normalized tensor expected
        by InceptionResnetV1.
        """

        array = None

        try:

            image = image.convert(
                "RGB"
            )

            image = image.resize(
                (
                    160,
                    160,
                ),
                Image.Resampling.BILINEAR,
            )

            array = np.asarray(
                image,
                dtype=np.float32,
            )

            # [0,255] → [-1,1]
            array = (
                array - 127.5
            ) / 128.0

            # HWC → CHW
            tensor = torch.from_numpy(
                array.transpose(
                    2,
                    0,
                    1,
                ).copy()
            )

            return tensor

        except Exception as exc:

            print(
                "[FaceEngine] Preprocessing error:",
                exc,
            )

            return None

        finally:

            del array

    # =============================================================
    # REGISTER PERSON PHOTO
    # =============================================================

    def process_person_photo(
        self,
        image_bytes: bytes,
    ) -> Tuple[
        Optional[List[float]],
        Optional[str],
    ]:
        """
        Process a missing-person reference photograph.

        Steps:
            1. Decode image.
            2. Detect faces.
            3. Select largest face.
            4. Generate 512-d embedding.
        """

        image = None
        crop = None

        try:

            # -----------------------------------------------------
            # DECODE
            # -----------------------------------------------------

            nparr = np.frombuffer(
                image_bytes,
                np.uint8,
            )

            image = cv2.imdecode(
                nparr,
                cv2.IMREAD_COLOR,
            )

            del nparr

            if image is None:

                return (
                    None,
                    "Unable to decode uploaded image.",
                )

            # -----------------------------------------------------
            # DETECT
            # -----------------------------------------------------

            faces = self.detect_faces(
                image
            )

            if not faces:

                return (
                    None,
                    "No clear face was detected in the reference photograph.",
                )

            # -----------------------------------------------------
            # LARGEST FACE
            # -----------------------------------------------------

            faces.sort(
                key=lambda box:
                box[2] * box[3],
                reverse=True,
            )

            primary_face = faces[0]

            # -----------------------------------------------------
            # CROP
            # -----------------------------------------------------

            crop = (
                self.extract_face_crop(
                    image,
                    primary_face,
                )
            )

            if (
                crop is None
                or crop.size == 0
            ):

                return (
                    None,
                    "Unable to extract the detected face.",
                )

            # -----------------------------------------------------
            # EMBEDDING
            # -----------------------------------------------------

            embedding = (
                self.generate_embedding(
                    crop
                )
            )

            if (
                not embedding
                or np.linalg.norm(
                    np.asarray(
                        embedding,
                        dtype=np.float32,
                    )
                ) < 1e-6
            ):

                return (
                    None,
                    "Unable to generate a valid face embedding.",
                )

            return (
                embedding,
                None,
            )

        except Exception as exc:

            print(
                "[FaceEngine] Reference photo error:",
                exc,
            )

            return (
                None,
                "Face processing failed. Please use a clear frontal photograph.",
            )

        finally:

            del image
            del crop

            gc.collect()


# =============================================================
# GLOBAL INSTANCE
# =============================================================

face_engine = FaceEngine()