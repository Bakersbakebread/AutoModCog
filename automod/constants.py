ERROR_MESSAGES = {"invalid_rule": "`{}` is not a rule."}

ACTION_CONFIRMATION = {
    "third_party": "An event will still fire, but nothing will be actioned",
    "message": "On detection a message will be sent to the assigned role.",
    "add_role": "On detection I will add a role to the offender",
    "kick": "On detection I will kick the offender",
    "ban": "On detection I will ban the offender",
}

DEFAULT_ACTION = "third_party"

DEFAULT_OPTIONS = {
    "role_to_add": None,
    "is_ignored": False,
    "whitelist_channels": [],
    "whitelist_roles": [],
    "whitelist_users": [],
    "action_to_take": DEFAULT_ACTION,
    "is_enabled": False,
    "delete_message": False,
    "send_dm": False,
    "rule_specific_announce": None,
}

OPTIONS_MAP = {
    "role_to_add": "Role to add",
    "is_ignored": False,
    "whitelist_channels": "Whitelisted channels",
    "whitelist_roles": "Whitelisted roles",
    "whitelist_users": "Whitelisted users",
    "action_to_take": "Action to take",
    "is_enabled": "Enabled",
    "delete_message": "Delete message",
    "send_dm": "DM User",
    "rule_specific_announce": "Announcing special",
}
