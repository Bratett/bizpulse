from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PeriodType(str, Enum):
    VAT_MONTHLY = "VAT_MONTHLY"
    CIT_ANNUAL = "CIT_ANNUAL"
    WHT_MONTHLY = "WHT_MONTHLY"


class PeriodStatus(str, Enum):
    DRAFT = "DRAFT"
    COMPUTED = "COMPUTED"
    REVIEWED = "REVIEWED"
    FILED = "FILED"


class TaxCategory(str, Enum):
    STANDARD_RATED = "STANDARD_RATED"
    ZERO_RATED = "ZERO_RATED"
    EXEMPT = "EXEMPT"
    NON_DEDUCTIBLE = "NON_DEDUCTIBLE"


class CreateTaxPeriodRequest(BaseModel):
    period_type: PeriodType
    start_date: date
    end_date: date


class MarkFiledRequest(BaseModel):
    filing_reference: Optional[str] = None
    filing_method: str = "MANUAL"
    notes: Optional[str] = None


class TaxPeriodResponse(BaseModel):
    id: str
    business_id: str
    period_type: str
    start_date: date
    end_date: date
    status: str
    computed_at: Optional[datetime] = None
    filed_at: Optional[datetime] = None
    created_at: datetime
    total_liability_pesewas: int = 0


class TaxComputationItem(BaseModel):
    rate_type: str
    rate_code: str
    base_amount_pesewas: int
    rate_bps: int
    computed_amount_pesewas: int
    computation_details: Optional[dict] = None


class TaxSummaryResponse(BaseModel):
    business_id: str
    total_outstanding_pesewas: int
    next_deadline: Optional[date] = None
    periods: list[TaxPeriodResponse]
    rates_as_of: date


class VATReportResponse(BaseModel):
    period_id: str
    business_name: str
    business_tin: Optional[str] = None
    period_start: date
    period_end: date
    taxable_sales_pesewas: int
    output_vat_pesewas: int
    taxable_purchases_pesewas: int
    input_vat_pesewas: int
    net_vat_payable_pesewas: int
    nhil_pesewas: int
    getfund_pesewas: int
    total_payable_pesewas: int
    computation_date: Optional[datetime] = None


class CITReportResponse(BaseModel):
    period_id: str
    business_name: str
    business_tin: Optional[str] = None
    period_start: date
    period_end: date
    total_revenue_pesewas: int
    total_deductible_expenses_pesewas: int
    non_deductible_expenses_pesewas: int
    net_profit_pesewas: int
    cit_rate_bps: int
    cit_liability_pesewas: int
    computation_date: Optional[datetime] = None


class InvoiceLineItem(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price_pesewas: int
    vat_applicable: bool = True


class InvoicePreviewRequest(BaseModel):
    customer_name: str
    customer_tin: Optional[str] = None
    line_items: list[InvoiceLineItem] = Field(..., min_length=1)
    notes: Optional[str] = None
