import sys
import os
import django
from pathlib import Path
from fastmcp import FastMCP, Client
from starlette.responses import JSONResponse
from typing import Annotated
from pydantic import Field

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure Django BEFORE importing any functions
print("Configuring Django...")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naia.settings.dev')

try:
    django.setup()
    print("✓ Django configured successfully")
except Exception as django_error:
    print(f"✗ Django setup failed: {django_error}")
    print("Warning: Some functions may not work properly")

# Now import the functions from apps.skills.functions (after Django is set up)
try:
    from apps.skills.functions import (
        simulate_job_interview,
        analyze_professional_appearance,
        generate_training_report,
        list_recent_training_reports,
        get_training_report_html,
        cv_builder,
        send_email
    )
    from apps.researcher.functions import explain_naia_roles
    print("✓ Successfully imported skills trainer functions")
except ImportError as e:
    print(f"✗ Error importing functions: {e}")
    sys.exit(1)

# Initialize MCP server
mcp = FastMCP(
    name="NAIASkillsTrainerMCPServer"
)

@mcp.tool(
        name="skills_job_interview_simulation"
)
def skills_job_interview_simulation(
    job_position: Annotated[str, Field(description="The job position or role for which the interview is being simulated (e.g., 'Software Developer', 'Marketing Manager', 'Data Analyst')")],
    company_type: Annotated[str, Field(description="Type of company or organization (e.g., 'startup', 'large corporation', 'tech company', 'NGO', 'university')")],
    user_instructions: Annotated[str, Field(description="Specific user preferences and customizations for the interview. Examples: 'I want exactly 5 questions', 'Focus on technical questions only', 'Include questions about teamwork and leadership', 'Make it a 15-minute interview', 'Ask me about my experience with Python and databases', 'I want to practice these specific questions: [list]'. If user doesn't specify preferences, use 'standard interview format'.")],
    user_id: Annotated[int, Field(description="The ID of the user requesting the interview simulation")],
    status: Annotated[str, Field(description="A concise description of the simulation task being performed, using conjugated verbs (e.g., 'Creando simulación de entrevista...', 'Generating interview simulation...') in the same language as the user's question")],
    language: Annotated[str, Field(description="The language for the simulation guide and interface. Use the complete language name (e.g., 'Spanish', 'English', 'French')")]
) -> dict:
    """
    Creates a conversational job interview simulation where NAIA acts as a professional interviewer,
    conducting a natural step-by-step interview with personalized questions based on user preferences
    and specific requirements.

    This function generates a comprehensive interview script for NAIA to follow, along with an
    interactive HTML simulation interface. The interview is tailored to the specific job position,
    company type, and user requirements.

    Returns:
        dict: Dictionary with conversational guide for NAIA and visual HTML simulation interface
    """
    try:
        return simulate_job_interview(job_position, company_type, user_instructions, user_id, status, language)
    except Exception as e:
        return {"error": f"Job interview simulation failed: {str(e)}"}

@mcp.tool(
        name="skills_professional_appearance_analysis"
)
def skills_professional_appearance_analysis(
    context: Annotated[str, Field(description="The specific context or event for appearance analysis (e.g., 'job interview', 'business presentation', 'conference', 'formal meeting', 'cocktail event'). This helps the AI generate appropriate analysis and targeted clothing search queries.")],
    user_id: Annotated[int, Field(description="The ID of the user requesting the appearance analysis")],
    status: Annotated[str, Field(description="A concise description of the analysis task being performed, using conjugated verbs (e.g., 'Analyzing professional appearance...', 'Evaluating presentation style...') in the same language as the user's question")]
) -> dict:
    """
    Analyzes user's professional appearance using AI vision and provides intelligent clothing suggestions.
    The LLM analyzes the user's image and dynamically generates specific search queries for clothing
    recommendations. If improvements are needed, displays an interactive carousel with clothing examples.
    If user is well-dressed, provides positive feedback without suggestions. The image is automatically
    handled by the system.

    Returns:
        dict: Structured analysis with image carousel if suggestions are needed
    """
    try:
        return analyze_professional_appearance(context, user_id, status)
    except Exception as e:
        return {"error": f"Professional appearance analysis failed: {str(e)}"}

@mcp.tool(
        name="skills_training_report_generation"
)
def skills_training_report_generation(
    training_type: Annotated[str, Field(description="Type of training session. Supported values: 'job_interview_simulation', 'professional_appearance_analysis'")],
    user_id: Annotated[int, Field(description="The ID of the user for whom the training report is being generated")],
    status: Annotated[str, Field(description="A concise description of the report generation task being performed, using conjugated verbs (e.g., 'Generando reporte de entrevista...', 'Creating training analysis...')")],
    use_synthetic_data: Annotated[bool, Field(description="Whether to generate synthetic/example data for testing instead of using real conversation data. Defaults to false.")] = False,
    special_instructions: Annotated[str, Field(description="Special recommendations, insights, or observations that NAIA detected during the simulation session. These will be incorporated into the report analysis.")] = "",
    session_duration: Annotated[str, Field(description="Duration of the training session (e.g., '45 minutes', '1 hour 15 minutes'). Optional contextual information for the report.")] = "",
    difficulty_level: Annotated[str, Field(description="Difficulty level detected or assigned during the session. Helps contextualize performance analysis.")] = "",
    key_topics_covered: Annotated[str, Field(description="Main topics, skills, or areas that were covered during the training session. Helps focus the report analysis.")] = ""
) -> dict:
    """
    Generates a comprehensive training report in HTML format with visual elements, saves it to the database,
    and returns it for display/PDF conversion. Uses full conversation context for real data analysis or
    generates synthetic data for testing.

    The report includes detailed performance analysis, visual scoring indicators, strengths and improvement
    areas, and actionable recommendations for skill development.

    Returns:
        dict: Dictionary with the generated report and success status
    """
    try:
        return generate_training_report(
            training_type=training_type,
            user_id=user_id,
            status=status,
            use_synthetic_data=use_synthetic_data,
            special_instructions=special_instructions,
            session_duration=session_duration,
            difficulty_level=difficulty_level,
            key_topics_covered=key_topics_covered
        )
    except Exception as e:
        return {"error": f"Training report generation failed: {str(e)}"}

@mcp.tool(
        name="skills_list_training_reports"
)
def skills_list_training_reports(
    user_id: Annotated[int, Field(description="The ID of the user whose training reports are to be listed")],
    status: Annotated[str, Field(description="A concise description of the listing task being performed, using conjugated verbs (e.g., 'Listing recent training reports...', 'Retrieving training history...') in the same language as the user's question")],
    limit: Annotated[int, Field(description="Maximum number of reports to return. Default is 10. Can be adjusted based on user's request (e.g., 'show me my last 5 reports' would be limit=5)")] = 10
) -> dict:
    """
    Lists the most recent training reports for a user. Useful when users want to see their training
    history or previous reports. Returns a list with titles, dates, and IDs of recent training sessions.

    The function generates an HTML interface showing all available reports with dates and training types,
    making it easy for users to identify and select specific reports for viewing or downloading.

    Returns:
        dict: Dictionary with HTML display of recent training reports
    """
    try:
        return list_recent_training_reports(user_id, limit, status)
    except Exception as e:
        return {"error": f"Listing training reports failed: {str(e)}"}

@mcp.tool(
        name="skills_get_training_report"
)
def skills_get_training_report(
    report_id: Annotated[int, Field(description="The ID of the specific training report to retrieve. This should come from a previous list of reports or be provided by the user")],
    user_id: Annotated[int, Field(description="The ID of the user requesting the report. Used for security validation")],
    status: Annotated[str, Field(description="A concise description of the retrieval task being performed, using conjugated verbs (e.g., 'Retrieving training report...', 'Preparing report for download...') in the same language as the user's question")]
) -> dict:
    """
    Retrieves the HTML content of a specific training report for download or viewing. Returns the report
    content with 'pdf' key for frontend processing. Use when users want to download or view a specific
    training report.

    Includes security validation to ensure users can only access their own reports.

    Returns:
        dict: Dictionary with HTML content of the specified training report
    """
    try:
        return get_training_report_html(report_id, user_id, status)
    except Exception as e:
        return {"error": f"Training report retrieval failed: {str(e)}"}

@mcp.tool(
        name="skills_cv_builder"
)
def skills_cv_builder(
    personal_info: Annotated[dict, Field(description="Personal information including full_name, email, phone, location, and optional linkedin, portfolio, github")],
    cv_type: Annotated[str, Field(description="Type of CV desired. Examples: 'academic', 'technical', 'creative', 'corporate', 'startup', 'consulting', 'research', or any specific description")],
    experience_level: Annotated[str, Field(description="Level of experience. Examples: 'student', 'recent graduate', 'junior', 'mid-level', 'senior', 'executive', or any specific description")],
    target_industry: Annotated[str, Field(description="Target industry. Examples: 'technology', 'healthcare', 'education', 'finance', 'marketing', 'engineering', or any specific industry")],
    design_style: Annotated[str, Field(description="Desired design style. Examples: 'minimalist', 'modern', 'classic', 'creative', 'bold', 'elegant', or any style description")],
    sections_to_include: Annotated[list, Field(description="List of sections to include in the CV. Examples: ['experience', 'education', 'skills', 'projects', 'achievements', 'certifications', 'languages', 'volunteer', 'publications', 'awards'] or any custom sections")],
    primary_focus: Annotated[str, Field(description="Primary focus of the CV. Examples: 'technical_skills', 'achievements', 'experience', 'academic', 'leadership', 'creativity', or any specific focus")],
    desired_length: Annotated[str, Field(description="Desired CV length. Examples: 'one_page', 'two_pages', 'comprehensive', or any length description")],
    language: Annotated[str, Field(description="Language for the CV. Examples: 'spanish', 'english', 'portuguese', 'french', or any specific language")],
    user_id: Annotated[int, Field(description="The ID of the user requesting the CV")],
    status: Annotated[str, Field(description="A concise description of the CV building task being performed, using conjugated verbs (e.g., 'Construyendo CV...', 'Generating resume...') in the same language as the user's question")],
    experience_details: Annotated[list, Field(description="Optional list of detailed work experiences")] = None,
    education_details: Annotated[list, Field(description="Optional list of detailed education information")] = None,
    skills_list: Annotated[list, Field(description="Optional list of technical and soft skills")] = None,
    projects_list: Annotated[list, Field(description="Optional list of relevant projects")] = None,
    achievements_list: Annotated[list, Field(description="Optional list of notable achievements")] = None,
    languages_list: Annotated[list, Field(description="Optional list of languages and proficiency levels")] = None,
    certifications_list: Annotated[list, Field(description="Optional list of certifications")] = None,
    additional_sections: Annotated[dict, Field(description="Optional additional custom sections in key-value format")] = None
) -> dict:
    """
    Builds a personalized CV/resume in markdown format with high variability. Creates unique CVs
    completely adapted to user specifications without limitations on style or format.

    The function generates professional CVs tailored to specific industries, experience levels, and
    design preferences, with flexible section ordering and content focus based on user requirements.

    Returns:
        dict: Dictionary with markdown CV content ready for download or further processing
    """
    try:
        return cv_builder(
            user_id=user_id,
            personal_info=personal_info,
            cv_type=cv_type,
            experience_level=experience_level,
            target_industry=target_industry,
            design_style=design_style,
            sections_to_include=sections_to_include,
            primary_focus=primary_focus,
            desired_length=desired_length,
            language=language,
            experience_details=experience_details,
            education_details=education_details,
            skills_list=skills_list,
            projects_list=projects_list,
            achievements_list=achievements_list,
            languages_list=languages_list,
            certifications_list=certifications_list,
            additional_sections=additional_sections,
            status=status
        )
    except Exception as e:
        return {"error": f"CV building failed: {str(e)}"}

@mcp.tool(
        name="skills_send_email"
)
def skills_send_email(
    to_email: Annotated[str, Field(description="The email of the user to send the email to. If the user wants to send the email to himself, put 'myself' and the function manages it internally. If the user wants to send the email to another person, put the email of that person here.")],
    subject: Annotated[str, Field(description="The subject of the email to send.")],
    body: Annotated[str, Field(description="The body of the email to send.")],
    user_id: Annotated[int, Field(description="The ID of the user requesting the email")],
    status: Annotated[str, Field(description="A concise description of the email task being performed, using conjugated verbs (e.g., 'Enviando correo a...', 'Sending email about...') in the same language as the user's question")]
) -> dict:
    """
    Send an email to the user or specified recipient. This function is used to send an email with
    information provided by the user, including training reports, CV documents, or other relevant content.

    The function can automatically detect when users want to send emails to themselves and handles
    user authentication and email formatting appropriately.

    Returns:
        dict: Dictionary with success confirmation or error message
    """
    try:
        return send_email(to_email, subject, body, status, user_id)
    except Exception as e:
        return {"error": f"Email sending failed: {str(e)}"}

@mcp.tool(
        name="skills_explain_naia_roles"
)
def skills_explain_naia_roles(
    user_id: Annotated[int, Field(description="The ID of the user requesting the role explanation")],
    status: Annotated[str, Field(description="A concise description of the role explanation task being performed, using conjugated verbs (e.g., 'Explicando los roles de NAIA...', 'Showing NAIA's capabilities...') in the same language as the user's question")],
    auto_slide_interval: Annotated[int, Field(description="The interval in milliseconds for auto-advancing the carousel slides. Default is 3000ms (3 seconds).")] = 3000
) -> dict:
    """
    Generate a carousel with explanations of all five NAIA roles. ALWAYS use this function when users
    ask about what roles NAIA has or ask for an explanation of NAIA's capabilities.

    This creates an interactive visual presentation showing all available NAIA roles including
    Skills Trainer, Researcher, Personal Assistant, UniGuide, and Receptionist with their respective
    capabilities and use cases.

    Returns:
        dict: Dictionary with interactive carousel displaying all NAIA roles and capabilities
    """
    try:
        return explain_naia_roles(auto_slide_interval, user_id, status)
    except Exception as e:
        return {"error": f"NAIA roles explanation failed: {str(e)}"}

@mcp.resource("file://skills/info")
def skills_info():
    """Basic information about Skills Trainer services and available tools."""
    return {
        "role": "Skills Trainer",
        "description": "Professional skills development and training services",
        "location": "Universidad del Norte, Barranquilla, Colombia",
        "available_services": [
            "Job interview simulations",
            "Professional appearance analysis",
            "Training report generation",
            "CV/Resume building",
            "Skills assessment",
            "Professional development coaching",
            "Email services",
            "NAIA roles explanation"
        ],
        "specializations": [
            "Interview preparation",
            "Professional image consulting",
            "Communication skills",
            "Leadership development",
            "Career guidance",
            "Personal branding"
        ],
        "server_info": "MCP server providing comprehensive skills training and professional development services"
    }

@mcp.custom_route("/health", methods=["GET"])
async def health(request):
    return JSONResponse({"status": "ok", "server": "NAIA Skills Trainer MCP"})

# REST API Endpoints (optional - for ease of use)
@mcp.custom_route("/api/tools", methods=["GET"])
async def list_tools_endpoint(request):
    """List all available tools in REST format"""
    tools = [
        {"name": "skills_job_interview_simulation", "description": "Create interactive job interview simulations", "endpoint": "/api/interview"},
        {"name": "skills_professional_appearance_analysis", "description": "Analyze professional appearance with AI", "endpoint": "/api/appearance"},
        {"name": "skills_training_report_generation", "description": "Generate comprehensive training reports", "endpoint": "/api/report"},
        {"name": "skills_list_training_reports", "description": "List user's training history", "endpoint": "/api/reports"},
        {"name": "skills_get_training_report", "description": "Retrieve specific training report", "endpoint": "/api/report/get"},
        {"name": "skills_cv_builder", "description": "Build personalized CV/resume", "endpoint": "/api/cv"},
        {"name": "skills_send_email", "description": "Send email with training content", "endpoint": "/api/email"},
        {"name": "skills_explain_naia_roles", "description": "Explain all NAIA roles and capabilities", "endpoint": "/api/roles"}
    ]
    return JSONResponse({"tools": tools, "mcp_endpoint": "/mcp/v1", "protocol": "MCP + REST"})

@mcp.custom_route("/api/interview", methods=["POST"])
async def interview_simulation_rest(request):
    """REST endpoint for job interview simulation"""
    try:
        data = await request.json()
        result = simulate_job_interview(
            job_position=data.get("job_position", ""),
            company_type=data.get("company_type", ""),
            user_instructions=data.get("user_instructions", "standard interview format"),
            user_id=data.get("user_id", 1),
            status=data.get("status", "Creating interview simulation..."),
            language=data.get("language", "English")
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@mcp.custom_route("/api/appearance", methods=["POST"])
async def appearance_analysis_rest(request):
    """REST endpoint for professional appearance analysis"""
    try:
        data = await request.json()
        result = analyze_professional_appearance(
            context=data.get("context", "professional meeting"),
            user_id=data.get("user_id", 1),
            status=data.get("status", "Analyzing appearance...")
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@mcp.custom_route("/api/cv", methods=["POST"])
async def cv_builder_rest(request):
    """REST endpoint for CV building"""
    try:
        data = await request.json()
        result = cv_builder(
            user_id=data.get("user_id", 1),
            personal_info=data.get("personal_info", {}),
            cv_type=data.get("cv_type", "professional"),
            experience_level=data.get("experience_level", "mid-level"),
            target_industry=data.get("target_industry", "technology"),
            design_style=data.get("design_style", "modern"),
            sections_to_include=data.get("sections_to_include", ["experience", "education", "skills"]),
            primary_focus=data.get("primary_focus", "experience"),
            desired_length=data.get("desired_length", "two_pages"),
            language=data.get("language", "english"),
            status=data.get("status", "Building CV...")
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@mcp.custom_route("/api/email", methods=["POST"])
async def send_email_rest(request):
    """REST endpoint for sending emails"""
    try:
        data = await request.json()
        result = send_email(
            to_email=data.get("to_email", ""),
            subject=data.get("subject", ""),
            body=data.get("body", ""),
            status=data.get("status", "Sending email..."),
            user_id=data.get("user_id", 1)
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    print("Starting NAIA Skills Trainer MCP Server...")
    print(f"Project root: {project_root}")
    print()
    print("MCP Tools:")
    print("   - skills_job_interview_simulation")
    print("   - skills_professional_appearance_analysis")
    print("   - skills_training_report_generation")
    print("   - skills_list_training_reports")
    print("   - skills_get_training_report")
    print("   - skills_cv_builder")
    print("   - skills_send_email")
    print("   - skills_explain_naia_roles")
    print()
    print("REST Endpoints:")
    print("   - GET  /api/tools (list all tools)")
    print("   - POST /api/interview (job interview simulation)")
    print("   - POST /api/appearance (appearance analysis)")
    print("   - POST /api/cv (CV builder)")
    print("   - POST /api/email (send email)")
    print("   - GET  /health (health check)")
    print()
    print("MCP Protocol: http://localhost:9002/mcp/v1")

    mcp.run(transport="http",
    host="0.0.0.0",
    port=9002)