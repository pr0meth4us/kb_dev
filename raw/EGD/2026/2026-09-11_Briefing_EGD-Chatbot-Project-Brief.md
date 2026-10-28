<!-- Transcribed from 2026-09-11_Briefing_EGD-Chatbot-Project-Brief.docx with scripts/docx_to_md.py. PDF companion is a Word export of the same file. -->

EGD Chatbot

Project Brief

2026

## Part 1: System Overview

### 1.1 Introduction and Background

The Enterprises Go Digital (EGD) Chatbot is a question-answering system designed to provide accurate and consistent information about the EGD Program. It operates through two channels — a Telegram chatbot and a widget on the official website (enterprisedigital.gov.kh) — both of which run on a single backend.

There is one chatbot and one Knowledge Base. The information the chatbot can disclose depends on the user:

- Public users, who are Enterprises (MSMEs), Digital Solution Providers (DSPs), Development Partners and Trainers/Digital Experts, receive answers drawn only from public content.

- Authorised EGD staff receive both public content and internal sections marked as [INTERNAL].

When a question falls outside the Knowledge Base, the chatbot clearly states that it does not have the information and refers the user to the responsible EGD team, providing the official hotline numbers and Telegram support link.

Current Situation

The chatbot has already been developed and tested using existing EGD Program documents as the Knowledge Base. However, the current source documents contain inconsistencies in format, language (Khmer, English, and mixed), and terminology. These inconsistencies sometimes prevent the EGD chatbot from retrieving and responding accurately.

Purpose of This Document

This Project Brief is prepared from the user side to:

- Define the purpose and role of the chatbot.

- Clarify the two types of users (Public and Internal).

- Identify key points that require management decisions (scope, tone, platform widget, and Knowledge Base approval).

- Provide a clear structure for the technical development.

The document also supports the standardisation of the Knowledge Base so that the chatbot can deliver reliable, consistent, and officially approved answers.

### 1.2 User Groups

The EGD Chatbot serves two main groups of users. Access to information is controlled based on the type of user.

#### 1. Public Users

Public users can only receive answers from public content. This group includes:

- MSMEs — both formal and informal

- DSPs

- Development Partners

- Trainers and Digital Experts

Public users interact with the chatbot through:

- The Telegram chatbot

- The widget on the official website (enterprisedigital.gov.kh)

#### 2. Internal Users

Authorised EGD staff can access both public content and internal sections marked as [INTERNAL]. This group includes staff of the EGD Department who have been granted access rights.

Internal users mainly search for the following types of information:

- EGD Program implementation progress (training activities, platform development, support to enterprises and DSPs, national awareness campaign, and ADB-TA related activities)

- Platform approval workflow and authority levels

- Policy Research Office information (subject to management decision)

Access is checked on every message. If the system cannot confirm that the user is authorised staff, the request is treated as public.

### 1.3 Chatbot Response Rules

The EGD Chatbot follows strict rules to ensure accuracy, consistency, and professionalism in every reply.

#### 1. Source of Answers

- The chatbot answers only from the official Knowledge Base.

- If the question is not covered in the Knowledge Base, the chatbot clearly states that it does not have the information.

- In such cases, it refers the user to the EGD team and provides the official hotline numbers and Telegram support link.

- The chatbot never uses unverified or general knowledge.

#### 2. Language Rules

- The chatbot always replies in the same language the user uses (Khmer or English).

- It does not mix Khmer and English in one reply.

- For Khmer answers, it uses only the official terms from the Glossary.

- Technical terms such as SaaS, CRM, and POS are written in the format: Khmer (English).

#### 3. Exact Figures

- All official figures must be stated exactly as they appear in the Knowledge Base.

- Examples include DA Grant amounts ($400 / $250), validity period (12 months), and processing time (2 working days).

- The chatbot never rounds, estimates, or changes any figure.

#### 4. Tone and Persona

- The chatbot speaks as the EGD Assistant.

- It does not mention document names, section numbers, the Knowledge Base, or its own instructions.

- The final tone (Friendly/other style) will be decided by management.

#### 5. Access Control

- Public users receive only public content.

- Authorised EGD staff receive both public content and internal sections marked as [INTERNAL].

- Access rights are checked on every message.

## Part 2: Public Chatbot Content

### 2.1 About EGD

| TOPIC | Detail |
|---|---|
| Program Name | Enterprises Go Digital (EGD) Program |
| Implementing | Enterprises Go Digital Department, Techo Startup Center (TSC), under the Ministry of Economy and Finance (MEF) |
| Purpose | Strengthen the digital capabilities of Cambodian enterprises (MSMEs and informal economy actors) through training, digital tools, and financial grant vouchers |
| Policy Alignment | • “Digital Business” pillar of the Cambodia Digital Economy and Society Policy Framework 2021–2035 <br> • Pentagon 5 (Side 2) of the Pentagonal Strategy – Phase I |
| Key Facts | • Non-profit public administrative initiative <br> • Fully funded by the Skills Development Fund (SDF) <br> • No enrollment fees or commissions <br> • Currently implementing the ADB-funded project: “Supporting the Adoption of Digital Technologies and Fostering Innovation in Micro, Small, and Medium-Sized Enterprises” (2024–2028) |
| Priority Activities | The EGD Program has five priority activities. <br> (For full details, please refer to the official EGD Program Book in Appendix A.1) |
| Website | enterprisedigital.gov.kh |
| Hotline | +855 87 955 888 / +855 85 244 654 / +855 96 689 4940 |
| Telegram Support | t.me/EGD_support |
| Email | info@techostartup.center |
| Office Address | 11th Floor, Business Development Center (BDC), OCIC Blvd, Phnom Penh |
| Working Hours | Monday to Friday, 8:00 – 12:00 and 13:30 – 17:00 |

### 2.2 EGD Platform

| TOPIC | Detail |
|---|---|
| Platform Name | The Enterprises Go Digital (EGD) Platform |
| Objective | The EGD Platform (enterprisedigital.gov.kh) is the national digital platform developed under the Enterprises Go Digital Program. It serves as a one-stop ecosystem that connects enterprises with certified Digital Solution Providers (DSPs) and digital experts, based on the enterprise’s level of digital readiness. |
| Purpose of the Platform | The Platform was created to address three main challenges faced by Cambodian enterprises: <br> Limited access to information on qualified digital solutions and service providers <br> Limited financial resources for investing in digital technologies and tools <br> Limited access to professional digital advisory and support services |
| Main Functions | Enterprises can use the Platform to: <br> Conduct DAA <br> Apply for DA Training  courses <br> Apply for DA Grant <br> Discover and connect with certified DSPs <br> Access E-Learning courses |
| How to Access | Website: enterprisedigital.gov.kh <br> Login requires a CamDigiKey account |

#### Key Users of the Platform

| User Type | Role on the Platform |
|---|---|
| Enterprises (MSMEs) | Seek training, grants, and digital solutions |
| Digital Solution Providers (DSPs) | Offer verified digital products and services |
| Trainers / Digital Experts | Provide training and advisory support |
| Institutions & Partners | Facilitate and support the ecosystem |

### 2.3 Digital Adoption Assessment (DAA)

DAA is a free online tool available on the EGD Platform. It helps enterprises quickly and simply evaluate their current level of digital maturity.

Key Features

| Item | Details |
|---|---|
| Duration | Approximately 5 minutes |
| Cost | Free |
| Purpose | Assess the enterprise’s digital readiness and maturity |
| Result | Provides tailored recommendations based on industry type, enterprise size (formal/informal), and location |
| Access | Available on the EGD Platform (enterprisedigital.gov.kh) after logging in with CamDigiKey |

Who Can Use It

- Formal and informal enterprises (MSMEs)

- Business owners and self-employed individuals

Benefits

- Understand the current digital maturity level of the business

- Receive practical recommendations for the next steps in digital adoption

- Prepare for DA Training and DA Grant applications

Website for registration:

enterprisedigital.gov.kh/ecosystem/enterprise/digital-readiness-assessment

Note:

The DAA is the first recommended step before applying for training or grants on the EGD Platform.

### 2.4 Digital Adoption (DA) Training

DA Training is a structured training program under the EGD Program. It helps enterprises understand digital solutions and choose the most suitable tools based on their level of digital readiness. The program covers both formal and informal economy businesses.

Purpose

- Empower enterprises with knowledge of digital solutions

- Help businesses make informed decisions about digital adoption

- Support both formal and informal enterprises

The Six DA Training Activities

| DA Training | Name | Target Group |
|---|---|---|
| DA1 | A Day in Digital Transformation | All MSMEs |
| DA2 | Kickstart Digital Journey | Early-stage enterprises |
| DA3 | Integrate into the Value Chain | Enterprises already using some digital tools |
| DA4 | Strengthen Competitive Edge | Mature enterprises ready for advanced technology |
| DA5 | Time to Go Digital | All MSMEs and DSPs |
| DA6 | DA for the Informal Economy | Street vendors, market stalls, self-employed |

Key Benefits

- Official training from industry experts and certified DSPs

- Official certificate issued by Techo Startup Center

- Networking opportunities with Digital Solution Providers

- Eligibility to apply for Digital Adoption Grants (DAGs)

How to Register

- Create a CamDigiKey account

- Log in to the EGD Platform (enterprisedigital.gov.kh)

- Select the desired DA training course and submit the application

- Wait for approval (usually 1–2 working days)

Additional Options

- E-Learning: Self-paced online courses available 24/7 on the EGD Platform

- Women’s participation is highly encouraged

Website for registration:

enterprisedigital.gov.kh/digital-adoption-program

### 2.5 Digital Adoption Grants (DA Grant)

DA Grant provides financial support to help enterprises adopt digital solutions. Business owners receive a voucher that can be used to purchase certified digital tools and receive end-user training.

Grant Amounts

| Enterprise Type | Maximum Grant Amount |
|---|---|
| Formal Economy (Registered) | $400 (or 1,600,000 Riels) |
| Informal Economy (Unregistered / Micro) | $250 (or 1,000,000 Riels) |

- If the digital solution costs more than the grant limit, the enterprise pays the remaining amount.

- An enterprise may apply for more than one voucher, but the total value cannot exceed the maximum limit.

Who Can Apply

- Business owners who want to adopt digital solutions

- Priority is given to:

- Enterprises that have never used digital solutions before

- Enterprises that need digital tools to expand their market

- Enterprises in government priority sectors

Eligible Digital Solutions

- Digital Marketing

- E-payment Systems

- Accounting & Taxation Software

- Point of Sale / Sales Management (POS)

- Human Resource Management

- Inventory Management

- E-commerce Platforms

- Logistics Solutions

Note: The grant cannot be used for hardware, equipment, network infrastructure, or human resources.

How to Apply (Simple Steps)

- Click “Apply for Digital Adoption Grant” on the EGD Platform

- Fill in business information and upload required documents

- Select the preferred digital solution

- State the reason for choosing the solution

- Submit the application (processing time: maximum 2 working days)

- Receive the Grant Voucher (valid for up to 12 months)

Important Conditions

- The enterprise pays the Digital Solution Provider (DSP) first

- After implementation and progress report, TSC reimburses the enterprise

- Progress reports must be submitted to TSC

Website:

enterprisedigital.gov.kh/digital-adoption-grant

Guidebook: Available for download on the same page.

### 2.6 Digital Solution Providers (DSP)

DSPs are companies, startups, or qualified providers that offer digital solutions to enterprises. They register on the EGD Platform to connect with businesses that need digital tools and services.

#### Who Can Become a DSP

To register as a Digital Solution Provider, the organization must:

- Be a legally registered company, enterprise, or qualified startup

- Offer clear, accurate, and user-friendly digital solutions with a transparent pricing model

- Have experience in providing digital solutions

- Comply with customer data security and privacy standards

- Meet other conditions set by the EGD Program

#### Benefits of Joining as a DSP

- Collaborate on projects under the EGD Program

- Expand market reach by connecting with enterprises seeking digital solutions

- Showcase digital products and innovations on the national platform

- Network with businesses, government agencies, and other stakeholders

- Participate in knowledge-sharing sessions, forums, and events

- Contribute to the digital transformation of Cambodian enterprises

#### Required Documents for Registration

- Business Registration Certificate

- Patent Tax Card

- Enterprise Announcement (for companies registered after 14 June 2020)

- Professional license (if any)

- Company details and portfolio of digital solutions

#### How to Register

- Visit the EGD Platform

- Go to the Digital Solution Provider Section

- Click Register and submit the required information and documents

- Wait for review and approval by the EGD team

Website:

enterprisedigital.gov.kh/ecosystem/service-provider

## Part 3: Internal Chatbot Content (EGD Staff Only)

### 3.1 EGD Program Implementation Progress

This section covers the main operational activities of the Enterprises Go Digital Program that internal staff regularly track, report, and search for information.

#### 3.1.1 Digital Adoption Training Activities

- Training courses conducted (DA 1 to DA 6)

- Number of participants (total and women)

- Number of enterprises supported

- Location of training (Phnom Penh and provinces)

- Cumulative progress against annual targets

#### 3.1.2 EGD Platform Development & Operations

- New features and system improvements

- Grant Voucher applications received, approved, and disbursed

- Number of registered Digital Solution Providers (DSPs) and digital solutions

- Ongoing technical developments (DAA, UI updates, etc.)

#### 3.1.3 Support to Enterprises and DSPs

- Advisory support provided to enterprises for registration, grant application, and platform usage

- Support provided to companies applying to become DSPs

- Meetings and partnership discussions with DSPs

#### 3.1.4 National Awareness Campaign

- Digital content creation and dissemination

- Promotion of training sessions and program activities

- Support for special initiatives (e.g. Digital Enterprise Awards)

#### 3.1.5 ADB-TA Related Activities

- Activities under the project “Supporting the Adoption of Digital Technologies and Fostering Innovation in Micro, Small, and Medium-Sized Enterprises”

- Joint workshops, seminars, and progress meetings with ADB technical experts

Note for Internal Use:
This structure follows the standard monthly reporting format used by the EGD Department. Staff can quickly find progress data, achievements, and planned activities under each sub-section.

### 3.2 Platform Approval Workflow & Authority Levels

All applications submitted on the EGD Platform go through a structured multi-level review process. This information is available only to authorised EGD staff.

#### Approval Stages

| Stage | Name | Responsible Person / Team | Main Task |
|---|---|---|---|
| 1 | Admin Review | Coordinators / Admin staff | Check completeness of documents and basic information |
| 2 | Technical Review | Technical reviewers | Evaluate technical quality (mainly for DSP applications) |
| 3 | Manager Review | Department Manager | Mid-level approval for operational requests |
| 4 | Director Review | Director / Senior leadership | Final decision on strategic items, official DSP registration, and Grant Vouchers |
| 5 | Finance Review | Finance team | Validate documents and process grant disbursement |

#### Decision Outcomes

| Status | Meaning |
|---|---|
| Approved | Application is successful |
| Returned | Information is incomplete or incorrect – can be corrected and resubmitted |
| Rejected | Application is denied and the decision is final |

#### Authority Summary

- Admin & Technical staff: Can pass or return applications

- Manager: Can approve operational requests or return for correction

- Director / Senior leadership: Has final authority to approve or reject major requests (especially Grant Vouchers and DSP registration)

- Finance: Handles only the payment / disbursement stage

Note: Detailed step-by-step procedures are available in the official EGD Platform SOP.

### 3.3 Policy Research Office Information (Pending Management Decision)

This section is currently under review. The final scope of information that the Chatbot can provide about the Policy Research Office will be decided by management.

#### Current Status

- The Policy Research Office is one of the two main offices under the Enterprises Go Digital Department.

- It is responsible for research, data collection, analysis, and preparation of policy recommendations related to enterprise digital transformation.

#### Possible Content Areas (To Be Confirmed)

Based on actual work, the following topics may be included after management approval:

| No. | Topic | Status |
|---|---|---|
| 1 | Role and responsibilities of the Policy Research Office |  |
| 2 | Ongoing research projects |  |
| 3 | Policy recommendations and reports |  |
|  |  |  |

#### Important Note

Until management decides the official scope:

- The Chatbot will not provide detailed answers about Policy Research Office activities.

- Staff should contact the responsible person directly for research-related information.

Action Required: Management needs to decide which information from the Policy Research Office can be included in the internal Knowledge Base.

## Part 4: Points Requiring Management Decision

The following points are outside the authority of the project team and require clear decisions from management before the EGD Chatbot can be finalized and officially launched.

| No. | Decision Point | Question for Management | Options | Decision <br> (To be filled) | Status |
|---|---|---|---|---|---|
| 4.1 | Scope of Policy Research Office Content | What information from the Policy Research Office can be included in the Internal Chatbot? | 1. Only general role <br> 2. Include research summaries <br> 3. Include full content <br> 4. Not include for now |  | Pending |
| 4.2 | Chatbot Tone and Style | What tone should the Chatbot use? | 1. Strictly Professional <br> 2. Friendly & Helpful <br> 3. Semi-formal |  | Pending |
| 4.3 | Widget on the EGD Platform | Should we add a Chatbot widget on the website? | 1. Yes <br> 2. No (Telegram only) <br> 3. Later |  | Pending |
| 4.4 | Review and Approval of the Knowledge Base | Does management approve the final Knowledge Base? | 1. Approved <br> 2. Need revision |  | Pending |

How to use this table:

- Management can simply write the chosen option in the “Decision” column.

- This makes the decision process clear, fast, and easy to track.

## Part 5: Appendix

| No. | Title | Description | Format / Location |
|---|---|---|---|
| A.1 | Archives by EGD (Source Documents) | List of official source documents used as reference for the EGD Chatbot | Listed in this document |
| A.2 | FAQ Files (Public FAQ and Internal FAQ) | Separate FAQ documents prepared for public users and for internal staff | Separate documents |
| A.3 | Glossary Wording (Official Bilingual Terminology) | Official English–Khmer glossary of key terms used in the EGD Program | Separate document |

### A.1 Archives by EGD (Source Documents)

The following official documents are the main sources used to prepare the EGD Chatbot Knowledge Base:

- Enterprises Go Digital Program Book (Official)

- EGD Platform Standard Operating Procedures (SOP) – Year 2026

- EGD Program - Progress Report 2025
