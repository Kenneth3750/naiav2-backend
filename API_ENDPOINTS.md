# API Endpoints Documentation

Base URL: `{base_url}/api/v1/`

## Quick Reference

| Role | Base Path | Endpoints |
|------|-----------|-----------|
| UniGuide | `/uniguide/functions/` | 7 |
| Researcher | `/researcher/functions/` | 9 |
| Personal | `/personal/functions/` | 8 |
| Recepcionist | `/recepcionist/functions/` | 7 |
| Skills | `/skills/functions/` | 6 |

**Total:** 37 endpoints

---

## Important: Tool Names

Each endpoint includes a **Tool Name** which is the function identifier used in the realtime session tools. When the AI calls a function during a realtime session, it uses this tool name to match with the correct endpoint.

**Example:**
- **Tool Name:** `query_university_rag`
- **Endpoint URL:** `/api/v1/uniguide/functions/rag-query/`

When the realtime AI calls `query_university_rag`, the frontend should make a POST request to the corresponding endpoint URL with the parameters specified.

---

## UniGuide Endpoints

Base: `{base_url}/api/v1/uniguide/functions/`

### 1. RAG Query
**Tool Name:** `query_university_rag`
**POST** `{base_url}/api/v1/uniguide/functions/rag-query/`

```json
{
  "question": "string",
  "user_id": "integer",
  "k": "integer (optional, default: 3)",
  "status": "string"
}
```

### 2. Campus Calendar
**Tool Name:** `get_university_calendar_multi_month`
**POST** `{base_url}/api/v1/uniguide/functions/calendar/`

```json
{
  "months_to_search": "array[integer]",
  "user_id": "integer",
  "status": "string"
}
```

### 3. Virtual Campus Tour
**Tool Name:** `get_virtual_campus_tour`
**POST** `{base_url}/api/v1/uniguide/functions/tour/`

```json
{
  "area_filter": "string (optional)",
  "place_name": "string (optional)",
  "language": "string",
  "user_id": "integer",
  "status": "string"
}
```

### 4. Internet Search
**Tool Name:** `search_internet_for_uni_answers`
**POST** `{base_url}/api/v1/uniguide/functions/search/`

```json
{
  "query": "string",
  "user_id": "integer",
  "image_query": "string",
  "status": "string"
}
```

### 5. Send Email
**Tool Name:** `send_email`
**POST** `{base_url}/api/v1/uniguide/functions/email/`

```json
{
  "to_email": "string",
  "subject": "string",
  "body": "string",
  "user_id": "integer",
  "status": "string"
}
```

### 6. Search Contacts
**Tool Name:** `search_contacts_by_name`
**POST** `{base_url}/api/v1/uniguide/functions/contacts/`

```json
{
  "name": "string",
  "user_id": "integer",
  "status": "string"
}
```

### 7. Create Calendar Event
**Tool Name:** `create_calendar_event`
**POST** `{base_url}/api/v1/uniguide/functions/calendar-event/`

```json
{
  "title": "string",
  "start_datetime": "string (YYYY-MM-DDTHH:MM)",
  "end_datetime": "string (YYYY-MM-DDTHH:MM)",
  "user_id": "integer",
  "description": "string (optional)",
  "status": "string"
}
```

---

## Researcher Endpoints

Base: `{base_url}/api/v1/researcher/functions/`

### 1. Scholar Search
**Tool Name:** `scholar_search`
**POST** `{base_url}/api/v1/researcher/functions/scholar-search/`

```json
{
  "query": "string",
  "query_2": "string (optional)",
  "num_results": "integer (optional, default: 3)",
  "status": "string",
  "user_id": "integer",
  "language1": "string (optional, default: 'en')",
  "language2": "string (optional, default: 'en')"
}
```

### 2. Create Document
**Tool Name:** `write_document`
**POST** `{base_url}/api/v1/researcher/functions/document/`

```json
{
  "query": "string",
  "user_id": "integer",
  "status": "string",
  "document_type": "string",
  "use_internet": "boolean",
  "use_rag": "boolean",
  "context": "string (optional)",
  "query_for_references": "string (optional, default: 'None')",
  "num_results": "integer (optional, default: 5)",
  "language_for_references": "string (optional, default: 'en')",
  "specific_documents": "array[string] (optional)"
}
```

### 3. Search User Documents
**Tool Name:** `answer_from_user_rag`
**POST** `{base_url}/api/v1/researcher/functions/user-documents/`

```json
{
  "user_id": "integer",
  "pregunta": "string",
  "status": "string",
  "k": "integer (optional, default: 3)",
  "specific_documents": "array[string] (optional)"
}
```

### 4. Web Search
**Tool Name:** `factual_web_query`
**POST** `{base_url}/api/v1/researcher/functions/web-search/`

```json
{
  "query": "string",
  "user_id": "integer",
  "status": "string (optional, default: 'Searching the web...')"
}
```

### 5. Generate Graph
**Tool Name:** `create_graph`
**POST** `{base_url}/api/v1/researcher/functions/graph/`

```json
{
  "user_query": "string",
  "information_for_graph": "string",
  "user_id": "integer",
  "status": "string",
  "internet_is_required": "boolean"
}
```

### 6. Send Email
**Tool Name:** `send_email`
**POST** `{base_url}/api/v1/researcher/functions/email/`

```json
{
  "to_email": "string",
  "subject": "string",
  "body": "string",
  "user_id": "integer",
  "status": "string (optional, default: 'Sending email...')"
}
```

### 7. Get Current News
**Tool Name:** `get_current_news`
**POST** `{base_url}/api/v1/researcher/functions/news/`

```json
{
  "location": "string",
  "user_id": "integer",
  "status": "string",
  "query": "string",
  "language": "string"
}
```

### 8. Explain Roles
**Tool Name:** `explain_naia_roles`
**POST** `{base_url}/api/v1/researcher/functions/roles/`

```json
{
  "user_id": "integer",
  "status": "string"
}
```

### 9. Deep Content Analysis
**Tool Name:** `deep_content_analysis_for_specific_information`
**POST** `{base_url}/api/v1/researcher/functions/deep-analysis/`

```json
{
  "url": "string",
  "user_query": "string",
  "user_id": "integer",
  "status": "string"
}
```

---

## Personal Assistant Endpoints

Base: `{base_url}/api/v1/personal/functions/`

### 1. Get News
**Tool Name:** `get_current_news`
**POST** `{base_url}/api/v1/personal/functions/news/`

```json
{
  "location": "string",
  "user_id": "integer",
  "status": "string",
  "query": "string",
  "language": "string"
}
```

### 2. Get Weather Info
**Tool Name:** `get_weather`
**POST** `{base_url}/api/v1/personal/functions/weather/`

```json
{
  "location": "string",
  "user_id": "integer",
  "status": "string"
}
```

### 3. Send Email
**Tool Name:** `send_email_on_behalf_of_user`
**POST** `{base_url}/api/v1/personal/functions/email/`

```json
{
  "to_email_or_name": "string",
  "subject": "string",
  "body": "string",
  "user_id": "integer",
  "status": "string"
}
```

### 4. Search Contacts
**Tool Name:** `search_contacts_by_name`
**POST** `{base_url}/api/v1/personal/functions/contacts/`

```json
{
  "name": "string",
  "user_id": "integer",
  "status": "string"
}
```

### 5. Read Calendar
**Tool Name:** `read_calendar_events`
**POST** `{base_url}/api/v1/personal/functions/calendar/`

```json
{
  "start_date": "string (YYYY-MM-DD)",
  "end_date": "string (YYYY-MM-DD)",
  "user_id": "integer",
  "status": "string"
}
```

### 6. Create Event
**Tool Name:** `create_calendar_event`
**POST** `{base_url}/api/v1/personal/functions/calendar-event/`

```json
{
  "title": "string",
  "start_datetime": "string (YYYY-MM-DDTHH:MM)",
  "end_datetime": "string (YYYY-MM-DDTHH:MM)",
  "user_id": "integer",
  "description": "string (optional)",
  "status": "string (optional, default: 'Creating calendar event...')"
}
```

### 7. Read Emails
**Tool Name:** `read_user_emails`
**POST** `{base_url}/api/v1/personal/functions/emails/`

```json
{
  "user_id": "integer",
  "max_emails": "integer (optional, default: 10)",
  "unread_only": "boolean (optional, default: false)",
  "search_query": "string (optional)",
  "read_full_content": "boolean (optional, default: false)",
  "specific_subject": "string (optional)",
  "status": "string (optional, default: 'Reading emails...')"
}
```

### 8. Explain Roles
**Tool Name:** `explain_naia_roles`
**POST** `{base_url}/api/v1/personal/functions/roles/`

```json
{
  "user_id": "integer",
  "status": "string",
  "auto_slide_interval": "integer (optional)"
}
```

---

## Recepcionist Endpoints

Base: `{base_url}/api/v1/recepcionist/functions/`

### 1. Search Contacts
**Tool Name:** `search_contacts_by_name`
**POST** `{base_url}/api/v1/recepcionist/functions/contacts/`

```json
{
  "name": "string",
  "user_id": "integer (optional, default: 1)",
  "status": "string (optional, default: 'Searching contacts...')"
}
```

### 2. Get Premises Info
**Tool Name:** `answer_question_of_uni_premises`
**POST** `{base_url}/api/v1/recepcionist/functions/premises/`

```json
{
  "place": "string",
  "user_id": "integer (optional, default: 1)",
  "status": "string (optional, default: 'Getting premises information...')"
}
```

### 3. Search Menus
**Tool Name:** `query_recepcionist_rag`
**POST** `{base_url}/api/v1/recepcionist/functions/menus/`

```json
{
  "question": "string",
  "user_id": "integer (optional, default: 1)",
  "status": "string (optional, default: 'Searching menu information...')",
  "k": "integer (optional, default: 3)",
  "restaurant_menus": "array[string] (optional)"
}
```

### 4. Find Events
**Tool Name:** `get_location_events`
**POST** `{base_url}/api/v1/recepcionist/functions/events/`

```json
{
  "location": "string (optional, default: 'Barranquilla')",
  "event_query": "string (optional, default: 'concerts')",
  "user_id": "integer (optional, default: 1)",
  "status": "string (optional, default: 'Searching for events...')"
}
```

### 5. Find Restaurants
**Tool Name:** `get_restaurants`
**POST** `{base_url}/api/v1/recepcionist/functions/restaurants/`

```json
{
  "location": "string (optional, default: 'Barranquilla')",
  "food_query": "string (optional, default: 'restaurants')",
  "user_id": "integer (optional, default: 1)",
  "status": "string (optional, default: 'Searching for restaurants...')"
}
```

### 6. Discover Places
**Tool Name:** `get_location_places`
**POST** `{base_url}/api/v1/recepcionist/functions/places/`

```json
{
  "location": "string (optional, default: 'Barranquilla')",
  "user_id": "integer (optional, default: 1)",
  "status": "string (optional, default: 'Searching for places to visit...')",
  "location_query": "string (optional)"
}
```

### 7. Send Email
**Tool Name:** `send_email`
**POST** `{base_url}/api/v1/recepcionist/functions/email/`

```json
{
  "to_email": "string",
  "subject": "string",
  "body": "string",
  "user_id": "integer (optional, default: 1)",
  "status": "string (optional, default: 'Sending email...')"
}
```

---

## Skills Trainer Endpoints

Base: `{base_url}/api/v1/skills/functions/`

### 1. Job Interview Simulation
**Tool Name:** `simulate_job_interview`
**POST** `{base_url}/api/v1/skills/functions/interview/`

```json
{
  "job_position": "string",
  "company_type": "string",
  "user_instructions": "string",
  "user_id": "integer",
  "status": "string",
  "language": "string"
}
```

### 2. Professional Appearance Analysis
**Tool Name:** `analyze_professional_appearance`
**POST** `{base_url}/api/v1/skills/functions/appearance/`

```json
{
  "context": "string",
  "user_id": "integer",
  "status": "string"
}
```

### 3. Generate Training Report
**Tool Name:** `generate_training_report`
**POST** `{base_url}/api/v1/skills/functions/report/`

```json
{
  "training_type": "string",
  "user_id": "integer",
  "status": "string",
  "use_synthetic_data": "boolean (optional, default: false)",
  "special_instructions": "string (optional)",
  "session_duration": "string (optional)",
  "difficulty_level": "string (optional)",
  "key_topics_covered": "string (optional)"
}
```

### 4. List Training Reports
**Tool Name:** `list_recent_training_reports`
**POST** `{base_url}/api/v1/skills/functions/reports/`

```json
{
  "user_id": "integer",
  "status": "string",
  "limit": "integer (optional, default: 10)"
}
```

### 5. Get Training Report
**Tool Name:** `get_training_report_html`
**POST** `{base_url}/api/v1/skills/functions/report/<int:report_id>/`

```json
{
  "report_id": "integer",
  "user_id": "integer",
  "status": "string"
}
```

### 6. Build CV
**Tool Name:** `cv_builder`
**POST** `{base_url}/api/v1/skills/functions/cv/`

```json
{
  "personal_info": "object",
  "cv_type": "string",
  "experience_level": "string",
  "target_industry": "string",
  "design_style": "string",
  "sections_to_include": "array[string]",
  "primary_focus": "string",
  "desired_length": "string",
  "language": "string",
  "user_id": "integer",
  "status": "string",
  "experience_details": "string (optional)",
  "education_details": "string (optional)",
  "skills_list": "string (optional)",
  "projects_list": "string (optional)",
  "achievements_list": "string (optional)",
  "languages_list": "string (optional)",
  "certifications_list": "string (optional)",
  "additional_sections": "string (optional)"
}
```

---

## Data Types Reference

- **string**: Text value
- **integer**: Numeric value (whole number)
- **boolean**: `true` or `false`
- **array[type]**: List of values of specified type
- **object**: JSON object with key-value pairs
- **(optional)**: Parameter is not required
- **(default: value)**: Default value if not provided

## HTTP Method
All endpoints use **POST** method.

## Content-Type
All requests should include header:
```
Content-Type: application/json
```

## Response Format
All endpoints return JSON responses with the data from the function execution.
