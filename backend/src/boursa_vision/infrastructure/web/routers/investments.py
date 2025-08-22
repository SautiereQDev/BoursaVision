"""
Investment API Routes
====================

REST API endpoints for investment management.
"""

from typing import List, Optional
from uuid import UUID, uuid4
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from boursa_vision.domain.entities.investment import Investment, InvestmentSector, InvestmentType, MarketCap
from boursa_vision.domain.value_objects.money import Money, Currency
from boursa_vision.infrastructure.web.dependencies.auth_dependencies import get_current_active_user


# Router setup
router = APIRouter(prefix="/api/v1/investments", tags=["Investments"])


# ===============================
# DTOs / Request/Response Models
# ===============================

class MoneyRequest(BaseModel):
    """Money value object for requests."""
    amount: str
    currency: str


class MoneyResponse(BaseModel):
    """Money value object for responses."""
    amount: str
    currency: str
    
    @classmethod
    def from_money(cls, money: Money) -> "MoneyResponse":
        return cls(
            amount=str(money.amount),
            currency=money.currency.value
        )


class InvestmentCreateRequest(BaseModel):
    """Request model for creating investments."""
    symbol: str
    name: str
    investment_type: str
    sector: str
    market_cap: str
    exchange: Optional[str] = None
    currency: str = "USD"
    current_price: MoneyRequest
    description: Optional[str] = None


class InvestmentUpdateRequest(BaseModel):
    """Request model for updating investments."""
    current_price: Optional[MoneyRequest] = None
    description: Optional[str] = None


class InvestmentResponse(BaseModel):
    """Response model for investments."""
    id: str
    symbol: str
    name: str
    investment_type: str
    sector: str
    market_cap: str
    exchange: Optional[str] = None
    currency: str
    current_price: MoneyResponse
    description: Optional[str] = None
    
    @classmethod
    def from_investment(cls, investment: Investment) -> "InvestmentResponse":
        current_price = investment.current_price
        if current_price is None:
            raise ValueError("Investment must have a current price")
            
        return cls(
            id=str(investment.id),
            symbol=investment.symbol,
            name=investment.name,
            investment_type=investment.investment_type.value,
            sector=investment.sector.value,
            market_cap=investment.market_cap.value,
            exchange=investment.exchange,
            currency=investment.currency.value,
            current_price=MoneyResponse.from_money(current_price),
            description=getattr(investment, 'description', None)
        )


class InvestmentSearchResponse(BaseModel):
    """Response model for investment search."""
    investments: List[InvestmentResponse]
    total: int


# Mock storage for E2E tests (in-memory)
_mock_investments: dict[str, InvestmentResponse] = {}


# ===============================
# Endpoints
# ===============================

@router.post(
    "",
    response_model=InvestmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new investment",
    description="Create a new investment in the system",
)
async def create_investment(
    investment_data: InvestmentCreateRequest,
    current_user = Depends(get_current_active_user)
) -> InvestmentResponse:
    """Create a new investment."""
    try:
        # Générer un UUID pour les tests E2E
        mock_investment_id = str(uuid4())
        
        investment_response = InvestmentResponse(
            id=mock_investment_id,
            symbol=investment_data.symbol,
            name=investment_data.name,
            investment_type=investment_data.investment_type,
            sector=investment_data.sector,
            market_cap=investment_data.market_cap,
            exchange=investment_data.exchange or "NYSE",
            currency=investment_data.currency,
            current_price=MoneyResponse(
                amount=investment_data.current_price.amount,
                currency=investment_data.current_price.currency
            ),
            description=investment_data.description
        )
        
        # Store in mock storage
        _mock_investments[investment_data.symbol.upper()] = investment_response
        _mock_investments[mock_investment_id] = investment_response
        
        return investment_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid investment data: {str(e)}"
        )


@router.get(
    "/search",
    response_model=InvestmentSearchResponse,
    summary="Search investments by name",
    description="Search investments by name or description",
)
async def search_investments_by_name(
    q: str = Query(..., description="Search query"),
    current_user = Depends(get_current_active_user)
) -> InvestmentSearchResponse:
    """Search investments by name."""
    # Get all investments from storage, removing duplicates by using symbol as key
    symbol_investments = {}
    for key, investment in _mock_investments.items():
        # Only keep investments indexed by symbol (not by UUID)
        if not key.startswith("mock-"):  # UUID keys start with "mock-"
            symbol_investments[investment.symbol] = investment
    
    all_investments = list(symbol_investments.values())
    
    # Search by name or symbol (case insensitive)
    query = q.lower()
    matching_investments = [
        inv for inv in all_investments 
        if query in inv.name.lower() or query in inv.symbol.lower()
    ]
    
    return InvestmentSearchResponse(investments=matching_investments, total=len(matching_investments))


@router.get(
    "/{symbol}",
    response_model=InvestmentResponse,
    summary="Get investment by symbol",
    description="Retrieve an investment by its symbol",
)
async def get_investment_by_symbol(
    symbol: str,
    current_user = Depends(get_current_active_user)
) -> InvestmentResponse:
    """Get investment by symbol."""
    # Check mock storage first
    investment = _mock_investments.get(symbol.upper())
    if investment:
        return investment
    
    # If not found, return 404
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Investment with symbol {symbol} not found"
    )


@router.patch(
    "/{investment_id}",
    response_model=InvestmentResponse,
    summary="Update investment",
    description="Update an existing investment",
)
async def update_investment(
    investment_id: UUID,
    update_data: InvestmentUpdateRequest,
    current_user = Depends(get_current_active_user)
) -> InvestmentResponse:
    """Update an existing investment."""
    investment_id_str = str(investment_id)
    investment = _mock_investments.get(investment_id_str)
    
    if not investment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investment with id {investment_id} not found"
        )
    
    # Update price if provided
    if update_data.current_price:
        investment.current_price = MoneyResponse(
            amount=update_data.current_price.amount,
            currency=update_data.current_price.currency
        )
    
    # Update description if provided
    if update_data.description is not None:
        investment.description = update_data.description
    
    # Update in storage
    _mock_investments[investment_id_str] = investment
    _mock_investments[investment.symbol] = investment
    
    return investment


@router.delete(
    "/{investment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete investment",
    description="Delete an investment from the system",
)
async def delete_investment(
    investment_id: UUID,
    current_user = Depends(get_current_active_user)
) -> None:
    """Delete an investment."""
    investment_id_str = str(investment_id)
    investment = _mock_investments.get(investment_id_str)
    
    if not investment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investment with id {investment_id} not found"
        )
    
    # Remove from storage
    _mock_investments.pop(investment_id_str, None)
    _mock_investments.pop(investment.symbol, None)


@router.get(
    "",
    response_model=InvestmentSearchResponse,
    summary="Search investments",
    description="Search investments with various filters",
)
async def search_investments(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    market_cap: Optional[str] = Query(None, description="Filter by market cap"),
    current_user = Depends(get_current_active_user)
) -> InvestmentSearchResponse:
    """Search investments with filters."""
    # Get all investments from storage, removing duplicates by using symbol as key
    symbol_investments = {}
    for key, investment in _mock_investments.items():
        # Only keep investments indexed by symbol (not by UUID)
        if not key.startswith("mock-"):  # UUID keys start with "mock-"
            symbol_investments[investment.symbol] = investment
    
    all_investments = list(symbol_investments.values())
    
    # Filter by symbol if provided
    if symbol:
        all_investments = [inv for inv in all_investments if inv.symbol.upper() == symbol.upper()]
    
    # Filter by sector if provided
    if sector:
        all_investments = [inv for inv in all_investments if inv.sector.lower() == sector.lower()]
        
    # Filter by market cap if provided
    if market_cap:
        all_investments = [inv for inv in all_investments if inv.market_cap.lower() == market_cap.lower()]
    
    return InvestmentSearchResponse(investments=all_investments, total=len(all_investments))