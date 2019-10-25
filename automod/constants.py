ERROR_MESSAGES = {"invalid_rule": "`{}` is not a rule."}

ACTION_CONFIRMATION = {
    "third_party": "An event will still fire, but nothing will be actioned",
    "message": "On detection a message will be sent to the assigned role.",
    "add_role": "On detection I will add a role to the offender",
    "kick": "On detection I will kick the offender",
    "ban": "On detection I will ban the offender",
}

DEFAULT_ACTION = "kick"

DEFAULT_OPTIONS = {
    "role_to_add": None,
    "is_ignored": False,
    "whitelist_channels": [],
    "whitelist_roles": [],
    "whitelist_users": [],
    "action_to_take": DEFAULT_ACTION,
    "is_enabled": True,
    "delete_message": True,
    "send_dm": True,
}
