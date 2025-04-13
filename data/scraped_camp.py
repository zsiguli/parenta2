from typing import Optional

from pydantic import BaseModel, Field
from typing_extensions import Literal


class ScrapedCamp(BaseModel):
    title: str = Field(description="The title of the camp.")
    subtitle: Optional[str] = Field(
        default=None, description="If provided, subtitle for the camp."
    )
    description: str = Field(
        description="The description of the camp as extracted from the website"
    )
    images: list[str] = Field(
        default_factory=list,
        description="Full url for images corresponding to this camp.",
    )
    location: Optional[str] = Field(
        default=None, description="The location of the camp, if provided."
    )
    date_range: str = Field(
        description="Starting/ending of the camp -- we'll process it later"
    )
    daily_format: Literal["moring", "afternoon", "full_day", "overnight"] = Field(
        description="The daily format of the camp. Can be one of morning, afternoon, full_day or overnight."
    )
    age_range: Optional[str] = Field(
        default=None,
        description="Age range of the camp, if provided. We'll process it later.",
    )
    gender_restriction: Optional[Literal["boys", "girls"]] = Field(
        default=None,
        description="If provided whtehre it's girls-only or boys-only camp.",
    )
    price_range: Optional[str] = Field(
        default=None,
        description="Price range of the camp, if provided. We'll process it later.",
    )
    registration_deadline: Optional[str] = Field(
        default=None,
        description="Registration deadline for the camp in YYYY-MM-DD format",
    )
    contact_phone: Optional[str] = Field(
        default=None, description="Contact phone number for the camp"
    )
    contact_email: Optional[str] = Field(
        default=None, description="Contact email for the camp"
    )
    availability_url: Optional[str] = Field(
        default=None,
        description="URL to check availability for the camp",
    )
    availability_css_selector: Optional[str] = Field(
        default=None,
        description="CSS selector to check availability for the camp",
    )
