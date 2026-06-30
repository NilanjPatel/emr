"""
Demographic service — business logic for patient search, CRUD, merge, and duplicate detection.

All DB operations use async SQLAlchemy sessions. Schema is frozen — no DDL.
SIN is never included in any result set.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import func, or_, text, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.demographic import (
    Demographic, DemographicContact, DemographicExt, DemographicMerged,
    DemographicMergeOperation, Consent, Contact,
)
from app.schemas.demographic import (
    DemographicCreate, DemographicUpdate, DuplicateCandidate,
    PATIENT_STATUS_LABELS,
)


async def get_by_id(db: AsyncSession, demographic_no: int) -> Demographic | None:
    result = await db.execute(
        select(Demographic).where(Demographic.demographic_no == demographic_no)
    )
    return result.scalar_one_or_none()


async def search(
    db: AsyncSession,
    q: str = "",
    hin: str = "",
    chart_no: str = "",
    phone: str = "",
    email: str = "",
    include_inactive: bool = False,
    limit: int = 20,
    page: int = 1,
) -> tuple[int, list[Demographic]]:
    """
    Search patients. Returns (total_count, results_page).
    Uses LIKE for name/phone/email, exact match for HIN/chart_no.
    Falls back to SOUNDEX if LIKE yields 0 name matches.
    """
    stmt = select(Demographic)
    filters = []

    if hin:
        filters.append(Demographic.hin == hin)
    if chart_no:
        filters.append(Demographic.chart_no == chart_no)
    if phone:
        filters.append(or_(
            Demographic.phone.like(f"%{phone}%"),
            Demographic.phone2.like(f"%{phone}%"),
        ))
    if email:
        filters.append(Demographic.email.like(f"%{email}%"))

    if q:
        q_stripped = q.strip()
        # Try name parts: "Smith" or "John Smith"
        parts = q_stripped.split()
        if len(parts) >= 2:
            name_filter = and_(
                Demographic.last_name.like(f"%{parts[-1]}%"),
                Demographic.first_name.like(f"%{parts[0]}%"),
            )
        else:
            name_filter = or_(
                Demographic.last_name.like(f"%{q_stripped}%"),
                Demographic.first_name.like(f"%{q_stripped}%"),
                Demographic.alias.like(f"%{q_stripped}%"),
                Demographic.pref_name.like(f"%{q_stripped}%"),
            )
        filters.append(name_filter)

    if not include_inactive:
        filters.append(Demographic.patient_status != "DE")

    if filters:
        stmt = stmt.where(and_(*filters))

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # If name search returned 0, try soundex fallback
    if total == 0 and q and not hin and not chart_no:
        q_stripped = q.strip()
        soundex_filter = text(
            "SOUNDEX(last_name) = SOUNDEX(:q) OR SOUNDEX(first_name) = SOUNDEX(:q)"
        ).bindparams(q=q_stripped)
        soundex_stmt = select(Demographic).where(soundex_filter)
        if not include_inactive:
            soundex_stmt = soundex_stmt.where(Demographic.patient_status != "DE")
        soundex_count = await db.execute(
            select(func.count()).select_from(soundex_stmt.subquery())
        )
        if soundex_count.scalar_one() > 0:
            stmt = soundex_stmt
            total = soundex_count.scalar_one()

    # Paginate
    offset = (page - 1) * limit
    stmt = stmt.order_by(Demographic.last_name, Demographic.first_name).offset(offset).limit(limit)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return total, list(rows)


async def get_banner_data(db: AsyncSession, demographic_no: int) -> dict | None:
    """
    Lightweight banner: patient identifiers + allergy count + active Rx count.
    Uses raw SQL joins for performance.
    """
    result = await db.execute(
        text("""
            SELECT
                d.demographic_no,
                d.first_name,
                d.last_name,
                d.pref_name,
                d.sex,
                d.year_of_birth,
                d.month_of_birth,
                d.date_of_birth,
                d.hin,
                d.hc_type,
                d.hc_renew_date,
                d.chart_no,
                d.patient_status,
                d.provider_no,
                d.roster_status,
                COALESCE(a.allergy_count, 0) AS allergy_count,
                COALESCE(a.critical_count, 0) AS critical_count,
                COALESCE(rx.active_rx_count, 0) AS active_rx_count
            FROM demographic d
            LEFT JOIN (
                SELECT demographic_no,
                       COUNT(*) AS allergy_count,
                       SUM(CASE WHEN severity_of_reaction = 'Severe' THEN 1 ELSE 0 END) AS critical_count
                FROM allergies
                WHERE demographic_no = :demographic_no
                  AND archived = 0
                GROUP BY demographic_no
            ) a ON a.demographic_no = d.demographic_no
            LEFT JOIN (
                SELECT demographic_no,
                       COUNT(*) AS active_rx_count
                FROM drugs
                WHERE demographic_no = :demographic_no
                  AND archived = 0
                  AND (end_date IS NULL OR end_date >= CURDATE())
                GROUP BY demographic_no
            ) rx ON rx.demographic_no = d.demographic_no
            WHERE d.demographic_no = :demographic_no
        """),
        {"demographic_no": demographic_no},
    )
    row = result.mappings().first()
    if not row:
        return None

    # Build DOB
    try:
        y = int(row["year_of_birth"] or 0)
        m = int(row["month_of_birth"] or 0)
        dd = int(row["date_of_birth"] or 0)
        dob_iso = f"{y:04d}-{m:02d}-{dd:02d}" if y and m and dd else None
    except (TypeError, ValueError):
        dob_iso = None

    age = None
    if dob_iso:
        try:
            dob = date.fromisoformat(dob_iso)
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except ValueError:
            pass

    return {
        "demographic_no": row["demographic_no"],
        "display_name": f"{row['first_name']} {row['last_name']}",
        "pref_name": row["pref_name"],
        "dob_iso": dob_iso,
        "age": age,
        "sex": row["sex"],
        "hin": row["hin"],
        "hc_type": row["hc_type"],
        "hc_renew_date": str(row["hc_renew_date"]) if row["hc_renew_date"] else None,
        "chart_no": row["chart_no"],
        "patient_status": row["patient_status"],
        "patient_status_label": PATIENT_STATUS_LABELS.get(row["patient_status"] or "", None),
        "allergy_count": int(row["allergy_count"]),
        "critical_allergy": int(row["critical_count"]) > 0,
        "active_rx_count": int(row["active_rx_count"]),
        "provider_no": row["provider_no"],
        "roster_status": row["roster_status"],
    }


async def get_ext_fields(db: AsyncSession, demographic_no: int) -> list[DemographicExt]:
    result = await db.execute(
        select(DemographicExt)
        .where(
            DemographicExt.demographic_no == demographic_no,
            DemographicExt.hidden != "1",
        )
        .order_by(DemographicExt.key_val)
    )
    return list(result.scalars().all())


async def upsert_ext_field(
    db: AsyncSession,
    demographic_no: int,
    key_val: str,
    value: str,
    provider_no: str,
) -> None:
    result = await db.execute(
        select(DemographicExt).where(
            DemographicExt.demographic_no == demographic_no,
            DemographicExt.key_val == key_val,
        )
    )
    ext = result.scalar_one_or_none()
    if ext:
        ext.value = value
        ext.provider_no = provider_no
        ext.date_time = datetime.now()
    else:
        db.add(DemographicExt(
            demographic_no=demographic_no,
            key_val=key_val,
            value=value,
            provider_no=provider_no,
            date_time=datetime.now(),
        ))
    await db.flush()


async def get_contacts(
    db: AsyncSession, demographic_no: int
) -> list[tuple[DemographicContact, Contact | None]]:
    """Return active DemographicContact rows joined to Contact entity."""
    dc_result = await db.execute(
        select(DemographicContact).where(
            DemographicContact.demographicNo == demographic_no,
            or_(DemographicContact.deleted == None, DemographicContact.deleted == 0),
            or_(DemographicContact.active == None, DemographicContact.active == 1),
        ).order_by(DemographicContact.id)
    )
    dcs = list(dc_result.scalars().all())

    results = []
    for dc in dcs:
        contact = None
        if dc.contactId:
            try:
                contact_id = int(dc.contactId)
                cr = await db.execute(
                    select(Contact).where(Contact.id == contact_id, or_(Contact.deleted == None, Contact.deleted == 0))
                )
                contact = cr.scalar_one_or_none()
            except (ValueError, TypeError):
                pass
        results.append((dc, contact))
    return results


async def add_contact(
    db: AsyncSession,
    demographic_no: int,
    contact_id: str,
    role: Optional[str],
    sdm: Optional[str],
    ec: Optional[str],
    mrp: Optional[int],
    health_care_team: Optional[int],
    best_contact: Optional[str],
    category: Optional[str],
    note: Optional[str],
    provider_no: str,
) -> DemographicContact:
    dc = DemographicContact(
        demographicNo=demographic_no,
        contactId=contact_id,
        role=role,
        sdm=sdm,
        ec=ec,
        mrp=mrp,
        health_care_team=health_care_team,
        best_contact=best_contact,
        category=category,
        note=note,
        creator=provider_no,
        active=1,
        deleted=0,
        facilityId=0,
        created=datetime.now(),
        updateDate=datetime.now(),
    )
    db.add(dc)
    await db.flush()
    return dc


async def soft_delete_contact(
    db: AsyncSession, contact_link_id: int, demographic_no: int
) -> bool:
    result = await db.execute(
        select(DemographicContact).where(
            DemographicContact.id == contact_link_id,
            DemographicContact.demographicNo == demographic_no,
        )
    )
    dc = result.scalar_one_or_none()
    if not dc:
        return False
    dc.deleted = 1
    dc.active = 0
    await db.flush()
    return True


async def get_consents(db: AsyncSession, demographic_no: int) -> list[Consent]:
    result = await db.execute(
        select(Consent).where(
            Consent.demographic_no == demographic_no,
            or_(Consent.deleted == None, Consent.deleted == 0),
        ).order_by(Consent.consent_date.desc())
    )
    return list(result.scalars().all())


async def add_consent(
    db: AsyncSession,
    demographic_no: int,
    consent_type_id: int,
    explicit: int,
    optout: int,
    provider_no: str,
) -> Consent:
    now = datetime.now()
    c = Consent(
        demographic_no=demographic_no,
        consent_type_id=consent_type_id,
        explicit=explicit,
        optout=optout,
        last_entered_by=provider_no,
        consent_date=now if explicit else None,
        optout_date=now if optout else None,
        edit_date=now,
        deleted=0,
    )
    db.add(c)
    await db.flush()
    return c


async def get_merge_history(
    db: AsyncSession, demographic_no: int
) -> list[DemographicMerged]:
    result = await db.execute(
        select(DemographicMerged).where(
            or_(
                DemographicMerged.demographic_no == demographic_no,
                DemographicMerged.merged_to == demographic_no,
            )
        ).order_by(DemographicMerged.lastUpdateDate.desc())
    )
    return list(result.scalars().all())


async def score_duplicates(
    db: AsyncSession,
    first_name: str,
    last_name: str,
    hin: Optional[str] = None,
    year_of_birth: Optional[str] = None,
    month_of_birth: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    exclude_no: Optional[int] = None,
) -> list[DuplicateCandidate]:
    """
    Score potential duplicate patients. Scoring:
      Exact HIN match:              95
      Exact DOB + exact last_name:  90
      Exact DOB + soundex last_name:75
      Exact DOB + exact first_name: 60
    Returns candidates with score >= 60, sorted descending.
    """
    candidates: dict[int, DuplicateCandidate] = {}

    async def _add(row, score: int):
        no = row.demographic_no
        if exclude_no and no == exclude_no:
            return
        if no not in candidates or candidates[no].score < score:
            candidates[no] = DuplicateCandidate(
                demographic_no=no,
                first_name=row.first_name,
                last_name=row.last_name,
                dob_iso=row.dob_iso,
                hin=row.hin,
                chart_no=row.chart_no,
                patient_status=row.patient_status,
                score=score,
            )

    # Exact HIN match
    if hin:
        r = await db.execute(
            select(Demographic).where(Demographic.hin == hin, Demographic.patient_status != "DE")
        )
        for row in r.scalars():
            await _add(row, 95)

    # DOB-based matches
    if year_of_birth and month_of_birth and date_of_birth:
        dob_filter = and_(
            Demographic.year_of_birth == year_of_birth,
            Demographic.month_of_birth == month_of_birth,
            Demographic.date_of_birth == date_of_birth,
            Demographic.patient_status != "DE",
        )
        dob_result = await db.execute(select(Demographic).where(dob_filter))
        for row in dob_result.scalars():
            if row.last_name.strip().lower() == last_name.strip().lower():
                await _add(row, 90)
            elif row.first_name.strip().lower() == first_name.strip().lower():
                await _add(row, 60)

        # Soundex last name
        soundex_result = await db.execute(
            select(Demographic).where(
                and_(
                    dob_filter,
                    text("SOUNDEX(last_name) = SOUNDEX(:ln)").bindparams(ln=last_name),
                )
            )
        )
        for row in soundex_result.scalars():
            # Only add if not already scored higher
            no = row.demographic_no
            if no not in candidates or candidates[no].score < 75:
                await _add(row, 75)

    return sorted(candidates.values(), key=lambda c: c.score, reverse=True)


async def create_patient(
    db: AsyncSession,
    data: DemographicCreate,
    provider_no: str,
) -> Demographic:
    now = datetime.now()
    patient = Demographic(
        first_name=data.first_name,
        last_name=data.last_name,
        sex=data.sex,
        title=data.title,
        middle_names=data.middle_names,
        alias=data.alias,
        pref_name=data.pref_name,
        year_of_birth=data.year_of_birth,
        month_of_birth=data.month_of_birth,
        date_of_birth=data.date_of_birth,
        phone=data.phone,
        phone2=data.phone2,
        email=data.email,
        consentToUseEmailForCare=data.consentToUseEmailForCare,
        address=data.address,
        city=data.city,
        province=data.province,
        postal=data.postal,
        residentialAddress=data.residentialAddress,
        residentialCity=data.residentialCity,
        residentialProvince=data.residentialProvince,
        residentialPostal=data.residentialPostal,
        hin=data.hin,
        ver=data.ver,
        hc_type=data.hc_type,
        hc_renew_date=data.hc_renew_date,
        roster_status=data.roster_status,
        roster_date=data.roster_date,
        roster_enrolled_to=data.roster_enrolled_to,
        patient_status=data.patient_status or "AC",
        patient_status_date=date.today(),
        date_joined=date.today(),
        provider_no=data.provider_no,
        chart_no=data.chart_no,
        official_lang=data.official_lang,
        spoken_lang=data.spoken_lang,
        citizenship=data.citizenship,
        country_of_origin=data.country_of_origin,
        lastUpdateUser=provider_no,
        lastUpdateDate=now,
    )
    db.add(patient)
    await db.flush()
    return patient


async def update_patient(
    db: AsyncSession,
    demographic_no: int,
    data: DemographicUpdate,
    provider_no: str,
) -> Demographic | None:
    patient = await get_by_id(db, demographic_no)
    if not patient:
        return None

    update_fields = data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(patient, field, value)

    patient.lastUpdateUser = provider_no
    patient.lastUpdateDate = datetime.now()
    await db.flush()
    return patient


async def merge_patients(
    db: AsyncSession,
    surviving_no: int,
    absorbed_no: int,
    provider_no: str,
) -> tuple[bool, str]:
    """
    Merge absorbed_no into surviving_no.
    Returns (success, error_message).
    """
    surviving = await get_by_id(db, surviving_no)
    absorbed = await get_by_id(db, absorbed_no)

    if not surviving:
        return False, f"Surviving patient {surviving_no} not found"
    if not absorbed:
        return False, f"Absorbed patient {absorbed_no} not found"

    # Check absorbed is not already merged elsewhere
    already_merged = await db.execute(
        select(DemographicMerged).where(
            DemographicMerged.demographic_no == absorbed_no,
            DemographicMerged.deleted == 0,
        )
    )
    if already_merged.scalar_one_or_none():
        return False, f"Patient {absorbed_no} has already been merged"

    now = datetime.now()
    today = date.today()

    # Soft-inactivate absorbed patient
    absorbed.patient_status = "DE"
    absorbed.end_date = today
    absorbed.lastUpdateUser = provider_no
    absorbed.lastUpdateDate = now

    # Record merge pointer
    merge_record = DemographicMerged(
        demographic_no=absorbed_no,
        merged_to=surviving_no,
        deleted=0,
        lastUpdateUser=provider_no,
        lastUpdateDate=today,
    )
    db.add(merge_record)

    # Record merge operation for audit trail
    for content_type in [
        "demographic", "appointment", "casemgmt_note", "drugs", "prescription",
        "allergies", "preventions", "measurements", "billing", "document",
    ]:
        op = DemographicMergeOperation(
            oldDemographic=absorbed_no,
            mainDemographic=surviving_no,
            contentType=content_type,
            contentId=None,
            dateMerged=now,
            providerNo=provider_no,
        )
        db.add(op)

    await db.flush()
    return True, ""
