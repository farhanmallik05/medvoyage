"""Post-procedure aftercare and continuous patient recovery tracker with storage persistence."""

from typing import Dict, List, Optional
from medvoyage.models import AftercareMilestone
from medvoyage.storage import MedVoyageStorage


class AftercareManager:
    def __init__(self, storage: Optional[MedVoyageStorage] = None):
        self._storage = storage
        self._milestones: Dict[str, List[AftercareMilestone]] = {}

    def set_storage(self, storage: MedVoyageStorage):
        self._storage = storage

    def generate_plan(
        self, booking_id: str, treatment_category: str = "Orthopedics"
    ) -> List[AftercareMilestone]:
        if treatment_category == "Orthopedics":
            schedule = [
                (1, "Post-Operative Inpatient Mobility Assessment", "Gentle range of motion exercise guided by hospital physiotherapist.", False),
                (3, "Wound Dressing & Drain Inspection", "Sterile wound dressing change and surgical site infection check.", False),
                (7, "Pre-Discharge Rehabilitation Clearance", "Walking with crutches/walker validation and flight clearance assessment.", False),
                (14, "Fit-to-Fly Telehealth Evaluation", "Virtual range-of-motion review with primary surgeon prior to departure.", True),
                (30, "Home Country 30-Day Digital Follow-Up", "Upload local X-ray imaging and progress report for surgical review.", True),
                (90, "Final Outcomes & Long-Term Function Review", "Joint flexion score evaluation and release to unrestricted activity.", True),
            ]
        else:
            schedule = [
                (1, "Immediate Post-Op Monitoring", "Vital sign stabilization and recovery suite check.", False),
                (3, "Surgical Site Evaluation", "Wound inspection and pain management protocol titration.", False),
                (7, "Discharge & Medication Counseling", "Review take-home pharmaceutical instructions and concierge handover.", False),
                (14, "Telehealth Check-In #1", "Virtual consultation with surgical team.", True),
                (30, "Telehealth Check-In #2", "Review lab markers and activity recovery.", True),
            ]

        items = [
            AftercareMilestone(
                booking_id=booking_id,
                day_post_op=day,
                title=title,
                instructions=instr,
                telehealth_checkin_required=telehealth,
            )
            for day, title, instr, telehealth in schedule
        ]
        if self._storage:
            self._storage.save_aftercare_milestones(booking_id, items)
        else:
            self._milestones[booking_id] = items
        return items

    def get_plan(self, booking_id: str) -> List[AftercareMilestone]:
        if self._storage:
            return self._storage.get_aftercare_milestones(booking_id)
        return self._milestones.get(booking_id, [])

    def complete_milestone(self, booking_id: str, milestone_id: str) -> bool:
        if self._storage:
            return self._storage.complete_aftercare_milestone(booking_id, milestone_id)
        items = self._milestones.get(booking_id, [])
        for m in items:
            if m.id == milestone_id:
                m.is_completed = True
                return True
        return False


AFTERCARE_MANAGER = AftercareManager()
