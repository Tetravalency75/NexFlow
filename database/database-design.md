# NEXFlow — Database Architecture & Schema Design

## 1. Overview
The database schema for **NEXFlow — Team Responsibility Management System** is built on SQLite using Django's ORM and migration engine. It models the core concepts of responsibility governance, RACI accountability, proof-of-work verification, transparent leaderboard scoring, and meeting minutes tracking.

Database Location: `database/db.sqlite3`

---

## 2. Entity Relationship Overview

```
 [User (accounts)] 1 ──< [Task (tasks)] (created_by)
 [User (accounts)] 1 ──< [Task (tasks)] (assigned_to)
 [Task (tasks)]   1 ──< [ProofOfWork (tasks)]
 [User (accounts)] 1 ──< [ProofOfWork (tasks)] (user)
 [User (accounts)] 1 ──< [ProofOfWork (tasks)] (reviewed_by)
 [User (accounts)] 1 ──< [Meeting (meetings)] (host)
 [Meeting (meetings)] >──< [User (accounts)] (attendees)
 [Meeting (meetings)] 1 ──< [AttendanceResponse (meetings)]
 [Meeting (meetings)] 1 ──< [HostNotification (meetings)]
 [Meeting (meetings)] 1 ──< [ActionItem (meetings)]
 [ActionItem (meetings)] 1 ──0..1 [Task (tasks)] (converted_task)
```

---

## 3. Data Models Specification

### 3.1. `accounts_user`
Inherits from Django's `AbstractUser` to maintain built-in authentication security, hashed passwords, and session handling.
- `id` (BigAutoField, PK)
- `username` (CharField, Unique)
- `email` (EmailField)
- `password` (CharField, PBKDF2 SHA256 hashed)
- `role` (CharField): `Authority` | `Lead` | `Member` | `Learner`
- `job_title` (CharField, max_length=120)
- `avatar` (CharField, SVG icon path)
- `department` (CharField, default='Engineering')
- `points` (IntegerField, default=0, synchronized leaderboard score)
- `is_active`, `is_staff`, `is_superuser`, `date_joined`, `last_login`

### 3.2. `tasks_task`
Encapsulates individual tasks and RACI accountability units.
- `id` (BigAutoField, PK)
- `title` (CharField, max_length=200)
- `description` (TextField)
- `status` (CharField): `TODO` | `IN_PROGRESS` | `DONE`
- `priority` (CharField): `LOW` | `MEDIUM` | `HIGH` | `URGENT`
- `raci_role` (CharField): `R` (Responsible) | `A` (Accountable) | `C` (Consulted) | `I` (Informed)
- `created_by_id` (FK -> `accounts_user`)
- `assigned_to_id` (FK -> `accounts_user`)
- `due_date` (DateField, nullable)
- `created_at` (DateTimeField, auto_now_add=True)
- `updated_at` (DateTimeField, auto_now=True)

### 3.3. `tasks_proofofwork`
Captures tangible evidence of work completed by Leads, Members, and Learners for Authority verification.
- `id` (BigAutoField, PK)
- `task_id` (FK -> `tasks_task`)
- `user_id` (FK -> `accounts_user`)
- `description` (TextField)
- `proof_file` (FileField, stored in `media/proofs/`, max 10MB, safe extensions)
- `proof_url` (URLField, optional external link)
- `status` (CharField): `PENDING` | `APPROVED` | `REJECTED`
- `reviewed_by_id` (FK -> `accounts_user`, nullable)
- `review_feedback` (TextField)
- `reviewed_at` (DateTimeField, nullable)
- `points_awarded` (IntegerField, default=0)
- `created_at` (DateTimeField, auto_now_add=True)
- **Constraint:** `reviewed_by_id != user_id` (Authorities cannot approve their own submissions).

### 3.4. `meetings_meeting`
Maintains team standups, reviews, and architecture sessions.
- `id` (BigAutoField, PK)
- `title` (CharField, max_length=200)
- `agenda` (TextField)
- `date` (DateField)
- `start_time` (TimeField)
- `meeting_link` (URLField, HTTPS validated)
- `host_id` (FK -> `accounts_user`)
- `minutes` (TextField)
- `created_at` (DateTimeField, auto_now_add=True)

### 3.5. `meetings_attendanceresponse`
Tracks RSVP and absence explanations.
- `id` (BigAutoField, PK)
- `meeting_id` (FK -> `meetings_meeting`)
- `attendee_id` (FK -> `accounts_user`)
- `status` (CharField): `ATTENDING` | `ABSENT`
- `absence_reason` (TextField)
- `submitted_at` (DateTimeField, auto_now=True)
- **Unique Constraint:** `(meeting_id, attendee_id)` (one response per attendee per meeting).

### 3.6. `meetings_hostnotification`
In-app alerts notifying hosts when invitees submit an absence reason.
- `id` (BigAutoField, PK)
- `host_id` (FK -> `accounts_user`)
- `meeting_id` (FK -> `meetings_meeting`)
- `attendee_id` (FK -> `accounts_user`)
- `reason` (TextField)
- `is_read` (BooleanField, default=False)
- `created_at` (DateTimeField, auto_now_add=True)

### 3.7. `meetings_actionitem`
Tracks actionable takeaways and links directly to tasks without duplicate creation.
- `id` (BigAutoField, PK)
- `meeting_id` (FK -> `meetings_meeting`)
- `description` (CharField, max_length=255)
- `owner_id` (FK -> `accounts_user`)
- `due_date` (DateField, nullable)
- `is_converted` (BooleanField, default=False)
- `converted_task_id` (OneToOneField -> `tasks_task`, nullable)
- `created_at` (DateTimeField, auto_now_add=True)

---

## 4. Scoring Algorithm & Leaderboard Calculation
The leaderboard calculates real-time scores directly from verified database records:
- **Approved Proof of Work:** `+10 points`
- **Completed Task:** `+5 points`
- **Ties:** Consistently ordered by total points descending, then completed tasks descending.

---

## 5. Migration & Backup Instructions
Before modifying or executing schema migrations:
1. **Backup Database:**
   ```powershell
   Copy-Item database/db.sqlite3 database/db.sqlite3.backup
   ```
2. **Create Migrations:**
   ```powershell
   python backend/manage.py makemigrations accounts tasks meetings
   ```
3. **Apply Migrations:**
   ```powershell
   python backend/manage.py migrate
   ```
4. **Seed Demo Accounts:**
   ```powershell
   python backend/manage.py seed_demo_accounts
   ```
