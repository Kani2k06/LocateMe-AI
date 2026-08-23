from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
)
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.enums import TA_CENTER

from app.config import settings
from app.core.database import db


router = APIRouter(
    prefix="/detections",
    tags=["Detection Reports"],
)


# ============================================================
# DETECTION LOOKUP
# ============================================================

def find_detection(detection_id: str):
    """
    Find a detection using any identifier exposed by
    the database/frontend mapping.

    The frontend uses values such as:

        DET-260823050411-2CF

    while the database may internally use another field.
    """

    try:
        detections = db.get_detections()
    except Exception as exc:
        print(
            f"[Report] Failed to retrieve detections: {exc}"
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve detection records.",
        ) from exc

    if not detections:
        return None

    target = str(detection_id).strip()

    for item in detections:
        if not isinstance(item, dict):
            continue

        possible_ids = [
            item.get("id"),
            item.get("detection_id"),
            item.get("detection_code"),
            item.get("code"),
            item.get("uuid"),
        ]

        for value in possible_ids:
            if value is None:
                continue

            if str(value).strip() == target:
                return item

    return None


# ============================================================
# LOCAL IMAGE RESOLUTION
# ============================================================

def resolve_local_file(url: str | None) -> Path | None:
    """
    Convert a LocateMe static URL into a local file path.
    """

    if not url:
        return None

    parsed = urlparse(url)
    path = parsed.path

    if not path.startswith("/static/"):
        return None

    relative_path = path.replace(
        "/static/",
        "",
        1,
    )

    storage_root = Path(
        settings.STORAGE_DIR
    ).resolve()

    file_path = (
        storage_root / relative_path
    ).resolve()

    try:
        file_path.relative_to(storage_root)
    except ValueError:
        return None

    if (
        file_path.exists()
        and file_path.is_file()
    ):
        return file_path

    return None


# ============================================================
# LOAD IMAGE
# ============================================================

def load_image_bytes(
    url: str | None,
) -> bytes | None:
    """
    Load an image from:
    - local LocateMe storage
    - HTTP/HTTPS URL
    """

    if not url:
        return None

    local_file = resolve_local_file(url)

    if local_file:
        try:
            return local_file.read_bytes()
        except Exception as exc:
            print(
                f"[Report] Local image read failed: {exc}"
            )
            return None

    if (
        url.startswith("http://")
        or url.startswith("https://")
    ):
        try:
            with urlopen(
                url,
                timeout=15,
            ) as response:
                return response.read()

        except Exception as exc:
            print(
                f"[Report] Remote image download failed: {exc}"
            )
            return None

    return None


# ============================================================
# PDF ENDPOINT
# ============================================================

@router.get(
    "/{detection_id}/report"
)
def download_detection_report(
    detection_id: str,
):
    """
    Generate a PDF report for a verified detection.
    """

    print(
        f"[Report] Requested detection: {detection_id}"
    )

    # --------------------------------------------------------
    # 1. FIND DETECTION
    # --------------------------------------------------------

    detection = find_detection(
        detection_id
    )

    if not detection:
        print(
            "[Report] Detection not found."
        )

        raise HTTPException(
            status_code=404,
            detail="Detection record not found.",
        )

    print(
        f"[Report] Detection found: {detection}"
    )

    # --------------------------------------------------------
    # 2. VERIFY STATUS
    # --------------------------------------------------------

    verification_status = (
        detection.get(
            "verification_status"
        )
        or detection.get(
            "verificationStatus"
        )
        or detection.get(
            "status"
        )
    )

    if verification_status != "verified":
        raise HTTPException(
            status_code=400,
            detail=(
                "A match report can only be "
                "generated for a verified detection."
            ),
        )

    # --------------------------------------------------------
    # 3. FIND PERSON
    # --------------------------------------------------------

    person_id = (
        detection.get("person_id")
        or detection.get("personId")
    )

    person = None

    if person_id:
        person = db.get_person(
            str(person_id)
        )

    # Sometimes the detection already contains
    # person information.
    if not person:
        person = {
            "name": detection.get(
                "person_name"
            ),
            "case_id": detection.get(
                "case_id"
            ),
            "photo_url": detection.get(
                "person_photo"
            ),
            "age": detection.get(
                "age"
            ),
            "gender": detection.get(
                "gender"
            ),
            "height": detection.get(
                "height"
            ),
        }

        if not person.get("name"):
            person = None

    if not person:
        raise HTTPException(
            status_code=404,
            detail=(
                "The missing-person record "
                "associated with this detection "
                "was not found."
            ),
        )

    # --------------------------------------------------------
    # 4. PERSON DETAILS
    # --------------------------------------------------------

    person_name = (
        person.get("name")
        or detection.get("person_name")
        or "Unknown"
    )

    case_id = (
        person.get("case_id")
        or detection.get("case_id")
        or person.get("id")
        or "Unknown"
    )

    age = (
        person.get("age")
        or "Unknown"
    )

    gender = (
        person.get("gender")
        or person.get("sex")
        or "Unknown"
    )

    height = (
        person.get("height")
        or "Unknown"
    )

    # --------------------------------------------------------
    # 5. CCTV DETAILS
    # --------------------------------------------------------

    location = (
        detection.get("location")
        or detection.get("cctv_location")
        or "Unknown"
    )

    camera_id = (
        detection.get("camera_id")
        or detection.get("cameraId")
        or "Unknown"
    )

    detected_at = (
        detection.get("detected_at")
        or detection.get("detectedAt")
        or detection.get("timestamp")
        or "Unknown"
    )

    detection_code = (
        detection.get("detection_code")
        or detection.get("detection_id")
        or detection.get("id")
        or detection_id
    )

    # --------------------------------------------------------
    # 6. CONFIDENCE
    # --------------------------------------------------------

    confidence = (
        detection.get("confidence")
        or detection.get("similarity")
        or 0
    )

    try:
        confidence_value = float(
            confidence
        )

        # Your application may store:
        #
        # 0.82  -> 82%
        #
        # OR
        #
        # 82    -> 82%
        #
        # Handle both.

        if confidence_value <= 1:
            confidence_value *= 100

        confidence_text = (
            f"{confidence_value:.1f}%"
        )

    except (
        TypeError,
        ValueError,
    ):
        confidence_text = "Unknown"

    # --------------------------------------------------------
    # 7. IMAGE URLs
    # --------------------------------------------------------

    person_photo = (
        person.get("photo_url")
        or detection.get("person_photo")
    )

    frame_url = (
        detection.get("frame_url")
        or detection.get("frameUrl")
        or detection.get("cctv_frame")
    )

    # --------------------------------------------------------
    # 8. CREATE PDF
    # --------------------------------------------------------

    output = BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="LocateMe Verified Match Report",
        author="LocateMe",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=22,
        leading=26,
        alignment=TA_CENTER,
        spaceAfter=5 * mm,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=7 * mm,
    )

    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=5 * mm,
        spaceAfter=3 * mm,
    )

    normal_style = ParagraphStyle(
        "NormalReport",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13,
    )

    story = []

    # ========================================================
    # HEADER
    # ========================================================

    story.append(
        Paragraph(
            "LOCATEME",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "MISSING PERSON MATCH REPORT",
            subtitle_style,
        )
    )

    status_table = Table(
        [
            [
                Paragraph(
                    "<b>VERIFIED MATCH</b>",
                    ParagraphStyle(
                        "VerifiedStatus",
                        fontSize=13,
                        alignment=TA_CENTER,
                        textColor=colors.white,
                    ),
                )
            ]
        ],
        colWidths=[
            170 * mm
        ],
    )

    status_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(
                        "#176B3A"
                    ),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor(
                        "#176B3A"
                    ),
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.append(
        status_table
    )

    story.append(
        Spacer(1, 6 * mm)
    )

    # ========================================================
    # PERSON DETAILS
    # ========================================================

    story.append(
        Paragraph(
            "PERSON DETAILS",
            section_style,
        )
    )

    person_table = Table(
        [
            [
                "Name",
                str(person_name),
            ],
            [
                "Case ID",
                str(case_id),
            ],
            [
                "Age",
                str(age),
            ],
            [
                "Gender",
                str(gender),
            ],
            [
                "Height",
                str(height),
            ],
        ],
        colWidths=[
            45 * mm,
            125 * mm,
        ],
    )

    person_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor(
                        "#F2F4F7"
                    ),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor(
                        "#D0D5DD"
                    ),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(
        person_table
    )

    # ========================================================
    # VISUAL EVIDENCE
    # ========================================================

    story.append(
        Paragraph(
            "VISUAL EVIDENCE",
            section_style,
        )
    )

    person_image = load_image_bytes(
        person_photo
    )

    frame_image = load_image_bytes(
        frame_url
    )

    image_width = 78 * mm
    image_height = 58 * mm

    image_cells = []

    if person_image:
        image_cells.append(
            RLImage(
                BytesIO(person_image),
                width=image_width,
                height=image_height,
            )
        )
    else:
        image_cells.append(
            Paragraph(
                "Reference photograph unavailable",
                normal_style,
            )
        )

    if frame_image:
        image_cells.append(
            RLImage(
                BytesIO(frame_image),
                width=image_width,
                height=image_height,
            )
        )
    else:
        image_cells.append(
            Paragraph(
                "CCTV frame unavailable",
                normal_style,
            )
        )

    visual_table = Table(
        [
            image_cells,
            [
                Paragraph(
                    "Missing Person Reference",
                    ParagraphStyle(
                        "CaptionPerson",
                        fontSize=8,
                        alignment=TA_CENTER,
                        textColor=colors.grey,
                    ),
                ),
                Paragraph(
                    "CCTV Detection Frame",
                    ParagraphStyle(
                        "CaptionFrame",
                        fontSize=8,
                        alignment=TA_CENTER,
                        textColor=colors.grey,
                    ),
                ),
            ],
        ],
        colWidths=[
            image_width,
            image_width,
        ],
    )

    visual_table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor(
                        "#D0D5DD"
                    ),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor(
                        "#D0D5DD"
                    ),
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(
        visual_table
    )

    # ========================================================
    # MATCH DETAILS
    # ========================================================

    story.append(
        Paragraph(
            "MATCH DETAILS",
            section_style,
        )
    )

    match_table = Table(
        [
            [
                "Detection ID",
                str(detection_code),
            ],
            [
                "Confidence",
                confidence_text,
            ],
            [
                "Verification Status",
                "VERIFIED MATCH",
            ],
        ],
        colWidths=[
            55 * mm,
            115 * mm,
        ],
    )

    match_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor(
                        "#F2F4F7"
                    ),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor(
                        "#D0D5DD"
                    ),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(
        match_table
    )

    # ========================================================
    # CCTV DETAILS
    # ========================================================

    story.append(
        Paragraph(
            "CCTV DETAILS",
            section_style,
        )
    )

    cctv_table = Table(
        [
            [
                "Location",
                str(location),
            ],
            [
                "Camera ID",
                str(camera_id),
            ],
            [
                "Detected Timestamp",
                str(detected_at),
            ],
        ],
        colWidths=[
            55 * mm,
            115 * mm,
        ],
    )

    cctv_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor(
                        "#F2F4F7"
                    ),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor(
                        "#D0D5DD"
                    ),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(
        cctv_table
    )

    # ========================================================
    # REPORT INFORMATION
    # ========================================================

    story.append(
        Paragraph(
            "REPORT INFORMATION",
            section_style,
        )
    )

    generated_at = datetime.now().strftime(
        "%d %b %Y, %H:%M:%S"
    )

    report_table = Table(
        [
            [
                "Generated By",
                "LocateMe",
            ],
            [
                "Generated On",
                generated_at,
            ],
        ],
        colWidths=[
            55 * mm,
            115 * mm,
        ],
    )

    report_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor(
                        "#F2F4F7"
                    ),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor(
                        "#D0D5DD"
                    ),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(
        report_table
    )

    story.append(
        Spacer(1, 8 * mm)
    )

    story.append(
        Paragraph(
            "This report contains details of a "
            "verified missing-person CCTV match.",
            ParagraphStyle(
                "Footer",
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER,
            ),
        )
    )

    # ========================================================
    # BUILD PDF
    # ========================================================

    document.build(
        story
    )

    pdf_bytes = output.getvalue()

    output.close()

    safe_name = "".join(
        character
        if character.isalnum()
        else "_"
        for character in str(person_name)
    ).strip("_")

    filename = (
        f"LocateMe_{safe_name}"
        "_match_report.pdf"
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )