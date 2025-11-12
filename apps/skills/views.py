from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .functions import (
    simulate_job_interview,
    analyze_professional_appearance,
    generate_training_report,
    list_recent_training_reports,
    get_training_report_html,
    cv_builder
)


@api_view(['POST'])
def job_interview_simulation(request):
    """Create job interview simulation"""
    try:
        job_position = request.data.get('job_position')
        company_type = request.data.get('company_type')
        user_instructions = request.data.get('user_instructions')
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status')
        language = request.data.get('language')

        if not all([job_position, company_type, user_instructions, user_id, status_msg, language]):
            return Response(
                {'error': 'job_position, company_type, user_instructions, user_id, status, and language are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = simulate_job_interview(job_position, company_type, user_instructions, user_id, status_msg, language)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def professional_appearance_analysis(request):
    """Analyze professional appearance"""
    try:
        context = request.data.get('context')
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status')

        if not all([context, user_id, status_msg]):
            return Response(
                {'error': 'context, user_id, and status are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = analyze_professional_appearance(context, user_id, status_msg)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def training_report_generation(request):
    """Generate training report"""
    try:
        training_type = request.data.get('training_type')
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status')
        use_synthetic_data = request.data.get('use_synthetic_data', False)
        special_instructions = request.data.get('special_instructions', '')
        session_duration = request.data.get('session_duration', '')
        difficulty_level = request.data.get('difficulty_level', '')
        key_topics_covered = request.data.get('key_topics_covered', '')

        if not all([training_type, user_id, status_msg]):
            return Response(
                {'error': 'training_type, user_id, and status are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = generate_training_report(
            training_type=training_type,
            user_id=user_id,
            status=status_msg,
            use_synthetic_data=use_synthetic_data,
            special_instructions=special_instructions,
            session_duration=session_duration,
            difficulty_level=difficulty_level,
            key_topics_covered=key_topics_covered
        )
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def list_training_reports(request):
    """List user's training reports"""
    try:
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status')
        limit = request.data.get('limit', 10)

        if not all([user_id, status_msg]):
            return Response({'error': 'user_id and status are required'}, status=status.HTTP_400_BAD_REQUEST)

        result = list_recent_training_reports(user_id, limit, status_msg)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def get_training_report(request):
    """Get specific training report"""
    try:
        report_id = request.data.get('report_id')
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status')

        if not all([report_id, user_id, status_msg]):
            return Response(
                {'error': 'report_id, user_id, and status are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = get_training_report_html(report_id, user_id, status_msg)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def build_cv(request):
    """Build personalized CV/resume"""
    try:
        personal_info = request.data.get('personal_info')
        cv_type = request.data.get('cv_type')
        experience_level = request.data.get('experience_level')
        target_industry = request.data.get('target_industry')
        design_style = request.data.get('design_style')
        sections_to_include = request.data.get('sections_to_include')
        primary_focus = request.data.get('primary_focus')
        desired_length = request.data.get('desired_length')
        language = request.data.get('language')
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status')

        # Optional fields
        experience_details = request.data.get('experience_details', None)
        education_details = request.data.get('education_details', None)
        skills_list = request.data.get('skills_list', None)
        projects_list = request.data.get('projects_list', None)
        achievements_list = request.data.get('achievements_list', None)
        languages_list = request.data.get('languages_list', None)
        certifications_list = request.data.get('certifications_list', None)
        additional_sections = request.data.get('additional_sections', None)

        if not all([personal_info, cv_type, experience_level, target_industry, design_style,
                    sections_to_include, primary_focus, desired_length, language, user_id, status_msg]):
            return Response(
                {'error': 'personal_info, cv_type, experience_level, target_industry, design_style, sections_to_include, primary_focus, desired_length, language, user_id, and status are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = cv_builder(
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
            status=status_msg,
            experience_details=experience_details,
            education_details=education_details,
            skills_list=skills_list,
            projects_list=projects_list,
            achievements_list=achievements_list,
            languages_list=languages_list,
            certifications_list=certifications_list,
            additional_sections=additional_sections
        )
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
