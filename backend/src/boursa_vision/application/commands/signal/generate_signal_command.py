from dataclasses import dataclass
from uuid import UUID

from boursa_vision.application.common import ICommand


@dataclass(frozen=True)
class GenerateSignalCommand(ICommand):
    """Command to generate trading signal for an investment"""

    investment_id: UUID
    force_refresh: bool = False
