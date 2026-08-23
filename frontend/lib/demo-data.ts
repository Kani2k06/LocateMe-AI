export type CaseStatus =
  | "active_alert"
  | "found_safe"
  | "pending_verification";

export type MissingPerson = {
  id: string;
  name: string;
  photoUrl: string | null;
  age: number;
  sex: "M" | "F";
  height: string;
  missingSince: string;
  relativeTime: string;
  lastKnownLocation: string;
  status: CaseStatus;
};

export type Detection = {
  id: string;
  personId: string;
  personName: string;
  personPhoto: string | null;
  frameUrl: string;
  confidence: number;
  location: string;
  cameraId: string;
  date: string;
  detectedAt: string;
  verificationStatus: "pending" | "verified" | "rejected";
};

export type AlertItem = {
  id: string;
  title: string;
  detail: string;
  severity: "critical" | "high" | "info";
  time: string;
  caseId: string;
};

export type CctvJob = {
  id: string;
  filename: string;
  location: string;
  cameraId: string;
  uploadedAt: string;
  status: "queued" | "extracting" | "matching" | "complete";
  frames: number;
  faces: number;
  matches: number;
};

export const MISSING_PERSONS: MissingPerson[] = [
  {
    id: "MP-24-0891",
    name: "Mateo Reyes",
    photoUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuAVzFtN5pLntfiq2-hdR4vadg9pE0TBAa5-6V5lZi8WGzFO67c1ISnA2yZAnNg_SrsyrL0Xn6sKRjzgY96Kn4fX-eOd9tfrEGBaVXv4A51Z5nLI4oT26m7T-usJAPqRKcoF6vTEKVBwxUKcURN1OghdpgU2ujynM54EKsTGu2DvGzh00v3MJIY6RQ8EKYfBPYB-7xpKknAiv4yfewnUWBPv_kBEFQ3sT_kbanPvNnEE1Bcu-xFMQYRryg",
    age: 17,
    sex: "M",
    height: "5'9\"",
    missingSince: "Aug 06, 2026",
    relativeTime: "14 Days Ago",
    lastKnownLocation: "Downtown Transit Center, Sector 4",
    status: "active_alert",
  },
  {
    id: "MP-24-0842",
    name: "Eleanor Vance",
    photoUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuDmBqxkZnGby7rzupo2Cy4Mg2jUwvPca4waDz4wIz_IX9mUSaY2_Pup2gAnv3pEz-TaCo9YMKV5h1I-LeOOhPmBIKcUB7Kqbik72qXwHVbM5EnnuqDE9wgjzYsKsxquw74rZhnb5nqlR_Ei-zUekw6Y2qK4inchBmeKRnwWHwcBuPLCwoDH0ai-4Yc9RbwCyyzrUEKTgWSWMuhR1k_e3PFt7MUko2XY87h3_FkuDeX5EL50m1zHYF4rlA",
    age: 78,
    sex: "F",
    height: "5'2\"",
    missingSince: "Aug 18, 2026",
    relativeTime: "2 Days Ago",
    lastKnownLocation: "Pinecrest Nursing Facility (Wandering)",
    status: "active_alert",
  },
  {
    id: "MP-24-0711",
    name: "David Chen",
    photoUrl: null,
    age: 34,
    sex: "M",
    height: "6'1\"",
    missingSince: "Jul 05, 2026",
    relativeTime: "Resolved",
    lastKnownLocation: "Riverside Park Trailhead",
    status: "found_safe",
  },
  {
    id: "MP-24-0899",
    name: "Aaliyah Jenkins",
    photoUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuBVC-pR3Z3T9YELE8OOViqCkcgInyOMCBg7IpzT1jRRJ0xcmZOxdOiQtjEtvMh9FQyzHtJJs1qCdaSAdWoo_mxOcoyy1RaSMqVe7yYimmXELZZ76Z75JDcvVcg-QPJPH8L9mGcMFvtqLbqtgsC2_BRec5UBGxsECYR9RoT2y4AagiwOx2AFzs1kb_y1JoM1wwmGOxlfpEUxsettvyj4hdrr0480gEuI3MeraSIjx8znDdUisUOdVQwW7g",
    age: 22,
    sex: "F",
    height: "5'6\"",
    missingSince: "Aug 20, 2026",
    relativeTime: "Today",
    lastKnownLocation: "State University Campus, South Lot",
    status: "pending_verification",
  },
  {
    id: "MP-24-0903",
    name: "Noah Patel",
    photoUrl: null,
    age: 9,
    sex: "M",
    height: "4'4\"",
    missingSince: "Aug 19, 2026",
    relativeTime: "Yesterday",
    lastKnownLocation: "Harborview Mall, Food Court",
    status: "active_alert",
  },
  {
    id: "MP-24-0866",
    name: "Sofia Alvarez",
    photoUrl: null,
    age: 41,
    sex: "F",
    height: "5'5\"",
    missingSince: "Aug 11, 2026",
    relativeTime: "9 Days Ago",
    lastKnownLocation: "I-95 Rest Stop, Mile 214",
    status: "pending_verification",
  },
];

export const DETECTIONS: Detection[] = [
  {
    id: "DET-88421",
    personId: "MP-24-0891",
    personName: "Mateo Reyes",
    personPhoto: MISSING_PERSONS[0].photoUrl,
    frameUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuAVzFtN5pLntfiq2-hdR4vadg9pE0TBAa5-6V5lZi8WGzFO67c1ISnA2yZAnNg_SrsyrL0Xn6sKRjzgY96Kn4fX-eOd9tfrEGBaVXv4A51Z5nLI4oT26m7T-usJAPqRKcoF6vTEKVBwxUKcURN1OghdpgU2ujynM54EKsTGu2DvGzh00v3MJIY6RQ8EKYfBPYB-7xpKknAiv4yfewnUWBPv_kBEFQ3sT_kbanPvNnEE1Bcu-xFMQYRryg",
    confidence: 0.94,
    location: "Downtown Transit Center, Sector 4",
    cameraId: "CAM-04-DT-12",
    date: "Aug 20, 2026",
    detectedAt: "14:22:08 EDT",
    verificationStatus: "pending",
  },
  {
    id: "DET-88418",
    personId: "MP-24-0842",
    personName: "Eleanor Vance",
    personPhoto: MISSING_PERSONS[1].photoUrl,
    frameUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuDmBqxkZnGby7rzupo2Cy4Mg2jUwvPca4waDz4wIz_IX9mUSaY2_Pup2gAnv3pEz-TaCo9YMKV5h1I-LeOOhPmBIKcUB7Kqbik72qXwHVbM5EnnuqDE9wgjzYsKsxquw74rZhnb5nqlR_Ei-zUekw6Y2qK4inchBmeKRnwWHwcBuPLCwoDH0ai-4Yc9RbwCyyzrUEKTgWSWMuhR1k_e3PFt7MUko2XY87h3_FkuDeX5EL50m1zHYF4rlA",
    confidence: 0.88,
    location: "Pinecrest Nursing Facility, East Gate",
    cameraId: "CAM-19-PC-03",
    date: "Aug 19, 2026",
    detectedAt: "06:41:55 EDT",
    verificationStatus: "verified",
  },
  {
    id: "DET-88390",
    personId: "MP-24-0899",
    personName: "Aaliyah Jenkins",
    personPhoto: MISSING_PERSONS[3].photoUrl,
    frameUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuBVC-pR3Z3T9YELE8OOViqCkcgInyOMCBg7IpzT1jRRJ0xcmZOxdOiQtjEtvMh9FQyzHtJJs1qCdaSAdWoo_mxOcoyy1RaSMqVe7yYimmXELZZ76Z75JDcvVcg-QPJPH8L9mGcMFvtqLbqtgsC2_BRec5UBGxsECYR9RoT2y4AagiwOx2AFzs1kb_y1JoM1wwmGOxlfpEUxsettvyj4hdrr0480gEuI3MeraSIjx8znDdUisUOdVQwW7g",
    confidence: 0.81,
    location: "State University Campus, South Lot",
    cameraId: "CAM-07-SU-21",
    date: "Aug 20, 2026",
    detectedAt: "09:13:02 EDT",
    verificationStatus: "pending",
  },
  {
    id: "DET-88311",
    personId: "MP-24-0903",
    personName: "Noah Patel",
    personPhoto: null,
    frameUrl: "",
    confidence: 0.73,
    location: "Harborview Mall, Level 2",
    cameraId: "CAM-02-HV-08",
    date: "Aug 19, 2026",
    detectedAt: "18:04:41 EDT",
    verificationStatus: "rejected",
  },
];

export const ALERTS: AlertItem[] = [
  {
    id: "AL-1022",
    title: "High-confidence match",
    detail:
      "Mateo Reyes — 94% at Downtown Transit Center (CAM-04-DT-12).",
    severity: "critical",
    time: "2 min ago",
    caseId: "MP-24-0891",
  },
  {
    id: "AL-1021",
    title: "Pending verification",
    detail:
      "Aaliyah Jenkins — 81% at State University South Lot.",
    severity: "high",
    time: "18 min ago",
    caseId: "MP-24-0899",
  },
  {
    id: "AL-1018",
    title: "Match verified",
    detail:
      "Eleanor Vance confirmed at Pinecrest East Gate.",
    severity: "info",
    time: "5 hr ago",
    caseId: "MP-24-0842",
  },
];

export const CCTV_JOBS: CctvJob[] = [
  {
    id: "JOB-441",
    filename: "transit_center_cam12_2026-08-20.mp4",
    location: "Downtown Transit Center, Sector 4",
    cameraId: "CAM-04-DT-12",
    uploadedAt: "Aug 20, 2026 14:05",
    status: "complete",
    frames: 1840,
    faces: 126,
    matches: 3,
  },
  {
    id: "JOB-440",
    filename: "south_lot_loop_am.mp4",
    location: "State University Campus, South Lot",
    cameraId: "CAM-07-SU-21",
    uploadedAt: "Aug 20, 2026 09:02",
    status: "matching",
    frames: 960,
    faces: 44,
    matches: 1,
  },
  {
    id: "JOB-438",
    filename: "pinecrest_east_gate.mp4",
    location: "Pinecrest Nursing Facility",
    cameraId: "CAM-19-PC-03",
    uploadedAt: "Aug 19, 2026 06:30",
    status: "complete",
    frames: 720,
    faces: 18,
    matches: 2,
  },
];

export const DASHBOARD_STATS = [
  {
    label: "Active cases",
    value: "118",
    hint: "Across 14 agencies",
    icon: "person_search",
  },
  {
    label: "Matches today",
    value: "7",
    hint: "Above 80% threshold",
    icon: "biotech",
  },
  {
    label: "Open alerts",
    value: "12",
    hint: "3 critical",
    icon: "notifications_active",
  },
  {
    label: "CCTV jobs",
    value: "4",
    hint: "1 still processing",
    icon: "videocam",
  },
];

export const ANALYTICS = {
  matchRate: "6.4%",
  avgConfidence: "87%",
  medianTimeToMatch: "4.2 hr",
  camerasOnline: "142 / 150",

  byStatus: [
    { label: "Active", value: 86 },
    { label: "Pending", value: 21 },
    { label: "Resolved", value: 17 },
  ],

  byLocation: [
    { label: "Transit hubs", value: 34 },
    { label: "Campus", value: 22 },
    { label: "Care facilities", value: 18 },
    { label: "Highways", value: 11 },
    { label: "Other", value: 15 },
  ],
};

export const CURRENT_USER = {
  name: "Command Admin",
  org: "Federal Bureau",
  photoUrl:
    "https://lh3.googleusercontent.com/aida-public/AB6AXuC7enGws5anfvJp8C-4CNYwijbfBggsi1fStrYpNeQgXkalCCaGjo0W2ssmdUXJYuCQ6wkDQ1jlqUf4HzriqBnjFqrBEXRaYlLTrn_ORTlr3ohtTC0b_FMTeQtv556tPsGhf377aKZ1O9HoMtGpaj7gxd1zlNZX8AZvMswg-m1OCJg9hM-x121wSZxOdVQr8PaLr_RLoC0ahiYNT23sov_l7yB3NHWfjQiHp1id7qRwMQHFhIRhgFHY4w",
};

export const LOGO_URL =
  "https://lh3.googleusercontent.com/aida-public/AB6AXuBY1k_cNdlresEh7_pVBzPk_4gMTqeAjYL_dr9fHA8LaqDlfaEc5s49rmi15dJOhHkhv8ad7bsSVvCt6OQ0bG8EW_8w5IUJBAVxFasTXMY3E4XIh8msZFldQazQuhkFtg6Hh1OX85PJRorFG9SOvO4CGjtFeqoyWd8Om1uFtCSdvAem8XKYyANmZRfPw2gmOQF4k2W8kPHKQRnecQTvU4XYkMfgVSTNUPKs0IOLlwXz5fl2irOIBFdgjg";