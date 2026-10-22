def user_role_context(request):
    """
    Supplies consistent role flags and capabilities across all rendered Django templates.
    """
    user = request.user
    if not user.is_authenticated:
        return {
            'current_user': None,
            'current_role': None,
            'is_authority': False,
            'is_lead': False,
            'is_member': False,
            'is_learner': False,
            'can_assign_tasks': False,
            'can_verify_proof': False,
        }

    return {
        'current_user': user,
        'current_role': getattr(user, 'role', 'Member'),
        'is_authority': getattr(user, 'is_authority', False),
        'is_lead': getattr(user, 'is_lead', False),
        'is_member': getattr(user, 'is_member', False),
        'is_learner': getattr(user, 'is_learner', False),
        'can_assign_tasks': getattr(user, 'can_assign_tasks', False),
        'can_verify_proof': getattr(user, 'can_verify_proof', False),
    }
