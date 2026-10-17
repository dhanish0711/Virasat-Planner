import io
import html
import re
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

def clean_pdf_text(text) -> str:
    """
    Sanitizes text for safe ReportLab XML embedding and replaces characters
    unsupported by standard Type-1 Helvetica (such as the Rupee symbol and non-Latin glyphs)
    to prevent black boxes or character rendering errors.
    """
    if text is None:
        return ""
    s = str(text)
    # Replace Indian Rupee symbol with 'Rs. '
    s = s.replace("₹", "Rs. ")
    # Replace non-standard typographic quotes/dashes
    s = s.replace("\u2018", "'").replace("\u2019", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u2013", "-").replace("\u2014", "--")
    s = s.replace("\u2022", "*").replace("\u2026", "...")
    # Strip any accidental Devanagari or non-latin characters that cause black box rendering in Helvetica
    s = re.sub(r'[\u0900-\u097F]', '', s)
    return html.escape(s.strip())


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to draw legal double-line borders, running headers, and 'Page X of Y' footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Formal Legal Double Border around each page
        self.setStrokeColor(colors.HexColor("#0f766e"))
        self.setLineWidth(1.2)
        self.rect(34, 34, 527, 774)
        
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.rect(38, 38, 519, 766)

        # Running Header (Pages > 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#0f766e"))
            self.drawString(48, 786, "LAST WILL AND TESTAMENT — FORMAL LEGAL INSTRUMENT")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748b"))
            self.drawRightString(546, 786, "Under Sec 63, Indian Succession Act 1925")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(48, 780, 546, 780)

        # Running Footer (All pages)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#475569"))
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(48, 50, 546, 50)
        
        self.drawString(48, 38, "Private & Confidential • Validly effective upon execution before two independent attesting witnesses")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.setFont("Helvetica-Bold", 8)
        self.drawRightString(546, 38, page_text)
        self.restoreState()


def generate_will_pdf(profile, will_data, members, assets, allocations) -> bytes:
    """
    Generates an authentic, legally formatted Indian Last Will and Testament document.
    Compliant with Section 63 of the Indian Succession Act, 1925 and Hindu Succession Act, 1956.
    Uses clean typography and Latin-encoded guidance to guarantee zero black boxes across all PDF viewers.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=50,
        rightMargin=50,
        topMargin=58,
        bottomMargin=58
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'FormalWillTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        alignment=1, # Center
        textColor=colors.HexColor("#0f766e"),
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'FormalWillSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        alignment=1,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=4
    )

    caption_style = ParagraphStyle(
        'FormalWillCaption',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        alignment=1,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=8
    )

    notice_box_style = ParagraphStyle(
        'LegalNoticeBox',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        alignment=1,
        textColor=colors.HexColor("#92400e")
    )

    clause_heading = ParagraphStyle(
        'ClauseHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#0f766e"),
        spaceBefore=11,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'FormalBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor("#0f172a"),
        alignment=4, # Justified
        spaceAfter=6
    )

    bold_body = ParagraphStyle(
        'FormalBoldBody',
        parent=body_style,
        fontName='Helvetica-Bold',
        alignment=0 # Left
    )

    story = []

    # -------------------------------------------------------------
    # 1. FORMAL LEGAL TITLE & BANNER
    # -------------------------------------------------------------
    karta_name = clean_pdf_text(profile.karta_name)
    karta_name_upper = karta_name.upper()
    city = clean_pdf_text(profile.city)
    state = clean_pdf_text(profile.state)
    biz_name = clean_pdf_text(profile.business_name)
    biz_type = clean_pdf_text(profile.business_type)
    gov_law = clean_pdf_text(profile.governing_law)

    story.append(Spacer(1, 4))
    story.append(Paragraph("LAST WILL AND TESTAMENT", title_style))
    story.append(Paragraph(f"OF SHRI / SMT. {karta_name_upper}", subtitle_style))
    story.append(Paragraph(f"Resident of {city}, {state}, India • Governed by {gov_law}", caption_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f766e"), spaceAfter=6))

    # Formal Legal Notice Banner
    notice_table = Table(
        [[Paragraph(
            "<b>STATUTORY ADVISORY:</b> This document is formulated in accordance with Section 63 of the Indian Succession Act, 1925. "
            "It takes full testamentary legal effect upon signing by the Testator in the joint presence of two independent adult attesting witnesses. "
            "Registration in Book 3 at the local Sub-Registrar Office (SRO) is strongly advised for complete evidentiary immunity.",
            notice_box_style
        )]],
        colWidths=[495]
    )
    notice_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fef3c7")),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#f59e0b")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(notice_table)
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # 2. PREAMBLE & SOLEMN RECITALS
    # -------------------------------------------------------------
    preamble_html = f"""
    <b>I, {karta_name}</b>, residing at {city}, {state}, India, 
    carrying on business under the name and commercial style of <b>"{biz_name}"</b> ({biz_type}), 
    by faith/religion Hindu, of sound physical health and disposing state of mind, 
    do hereby make, publish, and declare this as my <b>LAST WILL AND TESTAMENT</b>, 
    hereby revoking, canceling, and declaring null and void all former Wills, Codicils, Testaments, 
    and Testamentary Dispositions made by me at any time heretofore.
    """
    story.append(Paragraph(preamble_html, body_style))

    # Clause 1: Free Volition & Sound Mind
    story.append(Paragraph("<b>CLAUSE I: DECLARATION OF SOUND MIND & FREE VOLITION</b>", clause_heading))
    c1_text = """
    I declare that I am executing this Will out of my own free will, volition, and desire, without any coercion, 
    compulsion, duress, undue influence, fraud, misrepresentation, or persuasion from any family member, associate, or stranger whatsoever. 
    I have thoroughly evaluated all my worldly assets, commercial properties, liabilities, and familial obligations, 
    and I am fully conscious of the nature and effect of the testamentary dispositions made herein.
    """
    story.append(Paragraph(c1_text, body_style))

    # Clause 2: Appointment of Executor
    story.append(Paragraph("<b>CLAUSE II: APPOINTMENT OF EXECUTOR AND TRUSTEE</b>", clause_heading))
    executor_name = clean_pdf_text(will_data.get('executor_name') or 'Designated Executor')
    executor_rel = clean_pdf_text(will_data.get('executor_relationship') or 'Family Member / Legal Representative')
    alt_executor = clean_pdf_text(will_data.get('alternate_executor_name') or 'A qualified Advocate or Chartered Accountant')

    c2_text = f"""
    I hereby nominate, constitute, and appoint my <b>{executor_rel}</b>, <b>{executor_name}</b>, 
    to be the sole and absolute Executor and Trustee of this my Last Will and Testament. 
    In the unfortunate event that {executor_name} predeceases me, or is incapacitated, unable, or unwilling to act as Executor, 
    I hereby appoint <b>{alt_executor}</b> as the Alternate Executor with identical powers and immunities. 
    I direct that no administration bond, security, or court surety shall be required from my Executor for administering my estate.
    """
    story.append(Paragraph(c2_text, body_style))

    # Clause 3: Testamentary Guardian (if applicable)
    guardian_name = will_data.get('guardian_minor_name')
    if guardian_name and guardian_name.strip():
        guardian_clean = clean_pdf_text(guardian_name)
        guardian_rel = clean_pdf_text(will_data.get('guardian_relationship') or 'Guardian')
        story.append(Paragraph("<b>CLAUSE III: TESTAMENTARY GUARDIAN FOR MINORS (Section 60 ISA)</b>", clause_heading))
        c3_text = f"""
        In the event of my demise prior to any of my children or grandchildren attaining the age of legal majority (18 years), 
        I hereby appoint <b>{guardian_clean}</b> ({guardian_rel}) as the lawful Testamentary Guardian of their person 
        and of their allotted shares of property, to manage the same in trust for their welfare and education until they attain full majority.
        """
        story.append(Paragraph(c3_text, body_style))

    # Clause 4: Discharge of Debts, Commercial Dues & Taxes
    story.append(Paragraph("<b>CLAUSE IV: DISCHARGE OF LIABILITIES, TAXES & TESTAMENTARY EXPENSES</b>", clause_heading))
    c4_text = """
    I direct my Executor to first pay and satisfy all my just, lawful, and enforceable debts, trade liabilities, supplier dues, 
    mortgages, outstanding income-tax and GST assessments, medical expenses, and reasonable funeral and obsequies expenses 
    out of my liquid bank balances, current deposits, or cash reserves before distributing specific bequests to the beneficiaries.
    """
    story.append(Paragraph(c4_text, body_style))

    # -------------------------------------------------------------
    # 3. SCHEDULE OF SPECIFIC BEQUESTS (Clean Table, No Broken Glyphs)
    # -------------------------------------------------------------
    story.append(Paragraph("<b>CLAUSE V: SPECIFIC BEQUESTS & SCHEDULE OF ESTATE ASSETS</b>", clause_heading))
    story.append(Paragraph(
        "Subject to the payments stipulated hereinabove, I hereby devise, bequeath, apportion, and assign my properties, "
        "business establishments, bank accounts, gold ornaments, and investments as set forth in the following Schedule of Bequests:",
        body_style
    ))

    member_map = {m.id: m for m in members}
    asset_map = {a.id: a for a in assets}

    bequest_rows = [
        [
            Paragraph("<b>Asset Title / Business</b>", bold_body),
            Paragraph("<b>Category & Details</b>", bold_body),
            Paragraph("<b>Designated Beneficiary</b>", bold_body),
            Paragraph("<b>Share %</b>", bold_body),
            Paragraph("<b>Est. Value</b>", bold_body)
        ]
    ]

    for alloc in allocations:
        ast = asset_map.get(alloc.asset_id)
        ben = member_map.get(alloc.beneficiary_id)
        if ast and ben:
            allocated_val = (alloc.share_percentage / 100.0) * ast.estimated_value_inr
            ast_title = clean_pdf_text(ast.title)
            ast_desc = clean_pdf_text(ast.description or '')
            ast_cat = clean_pdf_text(ast.category.replace('_', ' ').title())
            ast_ident = clean_pdf_text(ast.identifier_number or 'N/A')
            ben_name = clean_pdf_text(ben.name)
            ben_rel = clean_pdf_text(ben.relation)

            bequest_rows.append([
                Paragraph(f"<b>{ast_title}</b><br/><font size=7 color='#64748b'>{ast_desc}</font>", body_style),
                Paragraph(f"{ast_cat}<br/><font size=7 color='#64748b'>ID: {ast_ident}</font>", body_style),
                Paragraph(f"<b>{ben_name}</b><br/><font size=7 color='#0f766e'>({ben_rel})</font>", body_style),
                Paragraph(f"{alloc.share_percentage:.1f}%", body_style),
                Paragraph(f"Rs. {allocated_val:,.0f}", body_style)
            ])

    if len(bequest_rows) == 1:
        bequest_rows.append([
            Paragraph("All Estate Assets", body_style),
            Paragraph("Entire Combined Estate", body_style),
            Paragraph(f"<b>{karta_name}'s Legal Heirs</b>", body_style),
            Paragraph("100.0%", body_style),
            Paragraph("Total Estate Value", body_style)
        ])

    bequest_table = Table(bequest_rows, colWidths=[125, 105, 115, 50, 100])
    bequest_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f766e")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    story.append(bequest_table)
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # 4. BUSINESS SUCCESSION, NOMINEE & RESIDUARY CLAUSES
    # -------------------------------------------------------------
    story.append(Paragraph("<b>CLAUSE VI: COMMERCIAL ENTERPRISE SUCCESSION & GOODWILL CONTINUITY</b>", clause_heading))
    c6_text = f"""
    With respect to my trading concern, proprietorship, or partnership interest in <b>"{biz_name}"</b>, 
    I specifically instruct that the commercial goodwill, registered trade names, GST credentials, tenancy rights, 
    commercial shop inventory, bank current accounts, and trading agencies shall devolve uninterrupted upon the designated 
    beneficiaries without dissolution, liquidation, or partitioning of the running enterprise. 
    All trade partners, suppliers, and distributors are requested to cooperate with my Executor for an immediate and peaceful transition.
    """
    story.append(Paragraph(c6_text, body_style))

    story.append(Paragraph("<b>CLAUSE VII: NOMINEE HARMONIZATION UNDER SARBATI DEVI JURISPRUDENCE</b>", clause_heading))
    c7_text = """
    I expressly declare that any nomination forms executed by me with banks, post offices, companies, or insurance providers 
    are made solely for statutory convenience of collection and transmission under the landmark Supreme Court ruling in 
    <i>Sarbati Devi v. Usha Devi (1984) 1 SCC 424</i> and <i>Ram Chander Talwar v. Devender Kumar Talwar (2010) 10 SCC 671</i>. 
    My nominees shall hold all such proceeds strictly in fiduciary trust and are legally bound to hand over the entire proceeds 
    to the specific beneficiaries designated in this Will.
    """
    story.append(Paragraph(c7_text, body_style))

    story.append(Paragraph("<b>CLAUSE VIII: COMPREHENSIVE RESIDUARY ESTATE CLAUSE</b>", clause_heading))
    c8_text = """
    All the rest, residue, and remainder of my estate, whether real, personal, tangible, or intangible, of every nature and description 
    whatsoever and wheresoever situated, including any property, rights, or claims which I may acquire after the date of execution hereof, 
    or any bequests which may lapse by reason of predecease, shall devolve equally upon my surviving Class I legal heirs who survive me.
    """
    story.append(Paragraph(c8_text, body_style))

    story.append(Paragraph("<b>CLAUSE IX: SOLEMN APPEAL FOR FAMILY HARMONY</b>", clause_heading))
    c9_text = """
    I make this testamentary disposition out of deep affection for all members of my family. I earnestly counsel and enjoin 
    all my heirs and successors to accept this disposition in good faith and with mutual respect, preserving the unity, 
    name, and honor of our family across generations without recourse to acrimonious civil litigation.
    """
    story.append(Paragraph(c9_text, body_style))

    # -------------------------------------------------------------
    # 5. TESTIMONIUM & SIGNATURES (Kept Together on Same Page)
    # -------------------------------------------------------------
    story.append(Spacer(1, 8))
    execution_elements = []

    exec_date_str = datetime.now().strftime("%d day of %B, %Y")
    testimonium_text = f"""
    <b>IN WITNESS WHEREOF</b>, I, the said <b>{karta_name}</b>, the Testator herein, have set and subscribed my hand 
    and signature to this my LAST WILL AND TESTAMENT on this <b>{exec_date_str}</b> at {city}, {state}, India, 
    in the joint presence of the two independent attesting witnesses who have signed below at my request.
    """
    execution_elements.append(Paragraph(testimonium_text, body_style))
    execution_elements.append(Spacer(1, 8))

    phys_loc = clean_pdf_text(will_data.get('original_physical_location') or '_______________________________')
    sro_office = clean_pdf_text(will_data.get('sub_registrar_office') or '_______________________________')

    sign_data = [
        [
            Paragraph(f"<b>TESTATOR'S SIGNATURE / THUMB IMPRESSION:</b><br/><br/><br/>___________________________________<br/><b>{karta_name}</b><br/>(Testator)", body_style),
            Paragraph(f"<b>PHYSICAL DOCUMENT CUSTODY:</b><br/>{phys_loc}<br/><br/><b>INTENDED SRO JURISDICTION:</b><br/>{sro_office}", body_style)
        ]
    ]
    sign_table = Table(sign_data, colWidths=[245, 250])
    sign_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0f766e")),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    execution_elements.append(sign_table)
    execution_elements.append(Spacer(1, 10))

    # Attestation by Two Witnesses
    execution_elements.append(Paragraph(
        "<b>ATTESTATION BY TWO INDEPENDENT WITNESSES (Mandatory under Section 63, Indian Succession Act, 1925)</b>",
        clause_heading
    ))
    attestation_desc = f"""
    Signed, published, and declared by the above-named Testator, <b>{karta_name}</b>, as and for their Last Will and Testament, 
    in the presence of us, who at their request, in their presence, and in the presence of each other, 
    all being present at the same time, have hereunto subscribed our names as attesting witnesses, 
    confirming that the Testator appeared to be of sound disposing mind, memory, and understanding at the time of execution.
    """
    execution_elements.append(Paragraph(attestation_desc, body_style))
    execution_elements.append(Spacer(1, 6))

    w1_name = clean_pdf_text(will_data.get('witness1_name') or '___________________________________')
    w1_addr = clean_pdf_text(will_data.get('witness1_address') or '___________________________________')
    w2_name = clean_pdf_text(will_data.get('witness2_name') or '___________________________________')
    w2_addr = clean_pdf_text(will_data.get('witness2_address') or '___________________________________')

    witness_data = [
        [
            Paragraph(f"<b>FIRST ATTESTING WITNESS:</b><br/><br/>Signature: ______________________<br/>Name: <b>{w1_name}</b><br/>Address: {w1_addr}<br/>Photo ID / Aadhaar: ________________________", body_style),
            Paragraph(f"<b>SECOND ATTESTING WITNESS:</b><br/><br/>Signature: ______________________<br/>Name: <b>{w2_name}</b><br/>Address: {w2_addr}<br/>Photo ID / Aadhaar: ________________________", body_style)
        ]
    ]
    witness_table = Table(witness_data, colWidths=[245, 250])
    witness_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#0f766e")),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ffffff")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    execution_elements.append(witness_table)
    story.append(KeepTogether(execution_elements))

    # -------------------------------------------------------------
    # 6. SCHEDULE I: MEDICAL FITNESS CERTIFICATE
    # -------------------------------------------------------------
    story.append(Spacer(1, 10))
    doc_name = clean_pdf_text(will_data.get('doctor_name') or '___________________________________')
    doc_reg = clean_pdf_text(will_data.get('doctor_reg_no') or '________________')
    doctor_data = [
        [
            Paragraph(f"""<b>SCHEDULE I: REGISTERED MEDICAL PRACTITIONER'S FITNESS CERTIFICATE</b><br/>
            <i>(Recommended under Indian case law to rebut potential claims of cognitive infirmity):</i><br/><br/>
            I, <b>Dr. {doc_name}</b> (MCI / State Medical Council Reg No. {doc_reg}), hereby certify that I have medically examined 
            Shri / Smt. <b>{karta_name}</b> on this date and confirm that they are in sound mental and physical health, possessing full 
            cognitive faculties and an unclouded testamentary capacity to understand the nature, scope, and effect of this Will.<br/><br/>
            Doctor's Signature & Official Stamp: ____________________________    Date: _______________
            """, body_style)
        ]
    ]
    doctor_table = Table(doctor_data, colWidths=[495])
    doctor_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0f766e")),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f0fdfa")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(doctor_table)

    # -------------------------------------------------------------
    # 7. SCHEDULE II & III: SRO REGISTRATION & FAMILY GUIDANCE
    # -------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("SCHEDULE II: SUB-REGISTRAR OFFICE (SRO) BOOK 3 MEMORANDUM", title_style))
    story.append(Paragraph("OFFICIAL REGISTRATION PARTICULARS (UNDER INDIAN REGISTRATION ACT, 1908)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f766e"), spaceAfter=12))

    sro_memo_data = [
        [
            Paragraph("<b>Registration Jurisdiction:</b>", bold_body),
            Paragraph(f"Sub-Registrar Office, {city}, {state}", body_style)
        ],
        [
            Paragraph("<b>Register Classification:</b>", bold_body),
            Paragraph("Book 3 (Register of Wills and Authorities to Adopt)", body_style)
        ],
        [
            Paragraph("<b>Stamp Duty:</b>", bold_body),
            Paragraph("NIL (Zero Stamp Duty across all Indian States on Wills)", body_style)
        ],
        [
            Paragraph("<b>Government Registration Fee:</b>", bold_body),
            Paragraph("Nominal statutory fee (Rs. 100 to Rs. 500 depending on state schedule)", body_style)
        ],
        [
            Paragraph("<b>Mandatory Documents:</b>", bold_body),
            Paragraph("Original Will, Testator's Original Aadhaar / PAN, 2 Independent Witnesses with Original Photo IDs, Doctor's Certificate", body_style)
        ]
    ]
    sro_table = Table(sro_memo_data, colWidths=[160, 335])
    sro_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f8fafc")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(sro_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("SCHEDULE III: EXECUTOR & FAMILY SUCCESSION DIRECTIVES", title_style))
    story.append(Paragraph("PRACTICAL LEGAL GUIDELINES FOR FAMILY HARMONY & TRANSMISSION", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#d97706"), spaceAfter=10))

    guide_1 = """
    <b>1. NOMINEE (AMANATDAR) VS. LEGAL HEIR (WAARIS) MANDATE:</b><br/>
    The Supreme Court of India in landmark precedents (<i>Sarbati Devi, 1984</i> and <i>Ram Chander Talwar, 2010</i>) 
    has established that a nominee in bank accounts, FDRs, and demat accounts acts strictly as a trustee (Amanatdar), 
    not the beneficial owner. The nominee's role is confined to receiving transmission from the bank and delivering 
    the proceeds to the beneficiaries named in this Will. Family members must not litigate over nominee designations.
    """
    story.append(Paragraph(guide_1, body_style))

    guide_2 = """
    <b>2. COMMERCIAL CONTINUITY (DUKAAN & BUSINESS ASSETS):</b><br/>
    To safeguard ongoing trade operations, vendor credibility, GST compliance, and shop goodwill, the Executor 
    shall ensure seamless transition of commercial assets to the designated successors without partition or disruption.
    """
    story.append(Paragraph(guide_2, body_style))

    guide_3 = """
    <b>3. SRO BOOK 3 REGISTRATION PROTECTION:</b><br/>
    While Section 18 of the Registration Act, 1908 makes will registration optional, recording this Will in Book 3 
    at the local Sub-Registrar Office provides conclusive evidentiary value in court, effectively eliminating spurious claims 
    of fabrication, undue influence, or mental infirmity.
    """
    story.append(Paragraph(guide_3, body_style))

    guide_4 = """
    <b>4. CUSTODY OF ORIGINAL TITLE DEEDS & SAFE STORAGE:</b><br/>
    All original sale deeds, share certificates, partnership instruments, and the signed original of this Will 
    are secured in the designated physical vault / bank locker. Upon demise of the Testator, the Executor shall produce 
    this document to effectuate immediate mutation and revenue record entries.
    """
    story.append(Paragraph(guide_4, body_style))

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()
