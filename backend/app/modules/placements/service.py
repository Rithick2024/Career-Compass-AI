from typing import Sequence, Optional
from app.modules.placements.models import Placement
from app.modules.placements.schemas import PlacementCreate, PlacementUpdate
from app.modules.placements.repository import PlacementRepository
from app.modules.applications.repository import ApplicationRepository
from app.modules.applications.models import ApplicationStatus
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError


from app.modules.students.repository import StudentRepository

class PlacementService:
    def __init__(
        self,
        placement_repo: PlacementRepository,
        application_repo: ApplicationRepository,
        student_repo: StudentRepository,
    ):
        self._repo = placement_repo
        self._application_repo = application_repo
        self._student_repo = student_repo

    async def list_for_staff(
        self,
        search: Optional[str] = None,
        company_id: Optional[int] = None,
        department_id: Optional[int] = None,
        offer_accepted: Optional[bool] = None,
    ) -> Sequence[Placement]:
        return await self._repo.list_for_staff(
            search=search,
            company_id=company_id,
            department_id=department_id,
            offer_accepted=offer_accepted,
        )

    async def list_for_student(self, user_id: int) -> Sequence[Placement]:
        student = await self._student_repo.get_by_user_id(user_id)
        if not student:
            return []
        return await self._repo.list_for_student(student.id)

    async def get_placement_for_staff(self, placement_id: int) -> Placement:
        placement = await self._repo.get_by_id(placement_id)
        if not placement:
            raise NotFoundError("Placement not found.")
        return placement

    async def get_placement_for_student(self, user_id: int, placement_id: int) -> Placement:
        student = await self._student_repo.get_by_user_id(user_id)
        if not student:
            raise NotFoundError("Placement not found.")
            
        placement = await self._repo.get_by_id(placement_id)
        if not placement or placement.application.student_id != student.id:
            raise NotFoundError("Placement not found.")
        return placement

    async def create_placement(self, data: PlacementCreate) -> Placement:
        application = await self._application_repo.get_by_id(data.application_id)
        if not application:
            raise NotFoundError("Application not found.")

        if application.status != ApplicationStatus.OFFERED:
            raise BadRequestError("Only Offered applications can be converted into placements.")

        existing_placement = await self._repo.get_by_application_id(data.application_id)
        if existing_placement:
            raise ConflictError("This application already has a placement.")

        if data.offer_accepted:
            accepted_placement = await self._repo.get_student_accepted_placement(application.student_id)
            if accepted_placement:
                raise ConflictError("This student already has an accepted placement.")

        return await self._repo.create(data)

    async def update_placement(self, placement_id: int, data: PlacementUpdate) -> Placement:
        placement = await self._repo.get_by_id(placement_id)
        if not placement:
            raise NotFoundError("Placement not found.")

        if data.offer_accepted is True:
            # Verify no other accepted placement exists
            accepted_placement = await self._repo.get_student_accepted_placement(placement.application.student_id)
            if accepted_placement and accepted_placement.id != placement_id:
                raise ConflictError("This student already has an accepted placement.")

        return await self._repo.update(placement, data)
