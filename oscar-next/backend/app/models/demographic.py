from __future__ import annotations
from datetime import date, datetime
from sqlalchemy import (
    BigInteger, Column, Date, DateTime, Integer, SmallInteger,
    String, Text, func,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Demographic(Base):
    __tablename__ = "demographic"

    demographic_no = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(10))
    last_name = Column(String(30), nullable=False)
    first_name = Column(String(30), nullable=False)
    middle_names = Column("middleNames", String(100))
    alias = Column(String(70))
    pref_name = Column(String(30))

    # DOB stored as three separate varchars (never changed — schema frozen)
    year_of_birth = Column(String(4))
    month_of_birth = Column(String(2))
    date_of_birth = Column(String(2))

    sex = Column(String(1), nullable=False)

    address = Column(String(60))
    city = Column(String(50))
    province = Column(String(20))
    postal = Column(String(10))
    previousAddress = Column(String(255))

    residentialAddress = Column(String(60))
    residentialCity = Column(String(50))
    residentialProvince = Column(String(20))
    residentialPostal = Column(String(9))

    phone = Column(String(20))
    phone2 = Column(String(20))
    email = Column(String(100))
    consentToUseEmailForCare = Column(SmallInteger)

    hin = Column(String(20))
    ver = Column(String(3))
    hc_type = Column(String(20))
    hc_renew_date = Column(Date)

    roster_status = Column(String(20))
    roster_date = Column(Date)
    roster_termination_date = Column(Date)
    roster_termination_reason = Column(String(2))
    roster_enrolled_to = Column(String(20))

    patient_status = Column(String(20))
    patient_status_date = Column(Date)
    date_joined = Column(Date)
    end_date = Column(Date)
    eff_date = Column(Date)

    provider_no = Column(String(250))
    family_doctor = Column(String(80))
    family_physician = Column(String(80))

    chart_no = Column(String(10))
    official_lang = Column(String(60))
    spoken_lang = Column(String(60))
    citizenship = Column(String(40))
    country_of_origin = Column(String(4))
    pcn_indicator = Column(String(20))
    anonymous = Column(String(32))
    newsletter = Column(String(32))
    children = Column(String(255))
    sourceOfIncome = Column(String(255))
    myOscarUserName = Column(String(255))

    # sin: stored in DB but NEVER included in any API response or log
    sin = Column(String(15))

    lastUpdateUser = Column(String(6))
    lastUpdateDate = Column(DateTime, nullable=False)

    # Relationships
    ext_fields = relationship(
        "DemographicExt",
        primaryjoin="Demographic.demographic_no == DemographicExt.demographic_no",
        foreign_keys="DemographicExt.demographic_no",
        lazy="select",
    )
    contacts = relationship(
        "DemographicContact",
        primaryjoin="Demographic.demographic_no == DemographicContact.demographicNo",
        foreign_keys="DemographicContact.demographicNo",
        lazy="select",
    )
    consents = relationship(
        "Consent",
        primaryjoin="Demographic.demographic_no == Consent.demographic_no",
        foreign_keys="Consent.demographic_no",
        lazy="select",
    )

    @property
    def dob_iso(self) -> str | None:
        """Reconstruct ISO 8601 date from three separate varchar fields."""
        try:
            y = int(self.year_of_birth or 0)
            m = int(self.month_of_birth or 0)
            d = int(self.date_of_birth or 0)
            if y == 0 or m == 0 or d == 0:
                return None
            return f"{y:04d}-{m:02d}-{d:02d}"
        except (TypeError, ValueError):
            return None

    @property
    def age(self) -> int | None:
        """Calculate age in years from DOB."""
        dob_str = self.dob_iso
        if not dob_str:
            return None
        try:
            dob = date.fromisoformat(dob_str)
            today = date.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except (ValueError, AttributeError):
            return None

    @property
    def is_active(self) -> bool:
        return self.patient_status == "AC" and self.end_date is None


class DemographicExt(Base):
    __tablename__ = "demographicExt"

    id = Column(Integer, primary_key=True, autoincrement=True)
    demographic_no = Column(Integer, nullable=True)
    provider_no = Column(String(6))
    key_val = Column(String(64))
    value = Column(Text)
    date_time = Column(DateTime)
    hidden = Column(String(1), default="0")


class DemographicContact(Base):
    __tablename__ = "DemographicContact"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created = Column(DateTime)
    updateDate = Column(DateTime)
    deleted = Column(SmallInteger)
    demographicNo = Column(Integer)
    contactId = Column(String(100))
    role = Column(String(100))
    type = Column(Integer)
    sdm = Column(String(25))
    ec = Column(String(25))
    category = Column(String(100))
    note = Column(String(200))
    facilityId = Column(Integer, nullable=False, default=0)
    creator = Column(String(20), nullable=False, default="")
    consentToContact = Column(SmallInteger)
    active = Column(SmallInteger)
    mrp = Column(SmallInteger)
    best_contact = Column(String(30))
    health_care_team = Column(SmallInteger)


class Contact(Base):
    __tablename__ = "Contact"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(20))
    lastName = Column(String(100))
    firstName = Column(String(100))
    address = Column(String(255))
    address2 = Column(String(255))
    city = Column(String(100))
    province = Column(String(25))
    country = Column(String(25))
    postal = Column(String(25))
    residencePhone = Column(String(30))
    cellPhone = Column(String(30))
    workPhone = Column(String(30))
    workPhoneExtension = Column(String(10))
    email = Column(String(50))
    fax = Column(String(30))
    note = Column(Text)
    specialty = Column(String(255))
    cpso = Column(String(10))
    systemId = Column(String(30))
    deleted = Column(SmallInteger)
    updateDate = Column(DateTime)


class DemographicMerged(Base):
    __tablename__ = "demographic_merged"

    id = Column(Integer, primary_key=True, autoincrement=True)
    demographic_no = Column(Integer, nullable=False)
    merged_to = Column(Integer, nullable=False)
    deleted = Column(Integer, nullable=False, default=0)
    lastUpdateUser = Column(String(6))
    lastUpdateDate = Column(Date)


class DemographicMergeOperation(Base):
    __tablename__ = "DemographicMergeOperation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    oldDemographic = Column(Integer)
    mainDemographic = Column(Integer)
    contentType = Column(String(250))
    contentId = Column(String(60))
    dateMerged = Column(DateTime)
    providerNo = Column(String(6))


class Consent(Base):
    __tablename__ = "Consent"

    id = Column(Integer, primary_key=True, autoincrement=True)
    demographic_no = Column(Integer)
    consent_type_id = Column(Integer)
    explicit = Column(SmallInteger)
    optout = Column(SmallInteger)
    last_entered_by = Column(String(10))
    consent_date = Column(DateTime)
    optout_date = Column(DateTime)
    edit_date = Column(DateTime)
    deleted = Column(SmallInteger)
