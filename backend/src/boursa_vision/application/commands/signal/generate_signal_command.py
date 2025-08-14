from dataclasses import dataclass
from uuid import UUID

from src.application.common import ICommand


@dataclass(frozen=True)
class GenerateSignalCommand(ICommand):
    """Command to generate trading signal for an investment"""

    investment_id: UUID
    force_refresh: bool = False
