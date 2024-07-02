class RPCAdminCalls:
    QUERY_USER_PLAN = "query_user_plan"
    QUERY_USER_STATE = "query_user_state"
    QUERY_LIST_REGISTERED_USERS = "query_list_registered_users"
    QUERY_LIST_USERS_ACTIVITIES_BASIC = "query_list_users_activities_basic"
    QUERY_LIST_USERS_ACTIVITIES_DETAILED = "query_list_users_activities_detailed"

    REGISTER_USER = "register_user"
    REMOVE_USER = "remove_user"
    UPDATE_USER_PLAN = "update_user_plan"

    QUERY_PROXY_STATS = "query_proxy_stats"
    QUERY_LIST_ENDPOINTS = "query_list_endpoints"
    QUERY_ENDPOINT_STATS = "query_endpoint_stats"

    QUERY_SERVICE_CONSOLE = "query_service_console"

    GET_ENDPOINTS = "get_endpoints"
    ADD_ENDPOINT = "add_endpoint"
    REMOVE_ENDPOINT = "remove_endpoint"
    UPDATE_ENDPOINT = "update_endpoint"

    @classmethod
    def create_method_call_dict(cls, method_str: str, *params) -> dict:
        res = {"jsonrpc": "2.0", "method": f"{method_str}", "params": list(params)}

        return res

    # TODO where are these methods used
    @classmethod
    def get_query_user_plan(cls, user_api_key: str) -> dict:
        return cls.create_method_call_dict(cls.QUERY_USER_PLAN, user_api_key)

    @classmethod
    def get_query_user_state(cls, user_api_key: str) -> dict:
        return cls.create_method_call_dict(cls.QUERY_USER_STATE, user_api_key)

    @classmethod
    def get_query_list_registered_users(cls) -> dict:
        return cls.create_method_call_dict(cls.QUERY_LIST_REGISTERED_USERS)

    @classmethod
    def get_query_list_users_activities_basic(cls) -> dict:
        return cls.create_method_call_dict(cls.QUERY_LIST_USERS_ACTIVITIES_BASIC)

    @classmethod
    def get_query_list_users_activities_detailed(cls) -> dict:
        return cls.create_method_call_dict(cls.QUERY_LIST_USERS_ACTIVITIES_DETAILED)

    @classmethod
    def get_register_user(cls, user_api_key: str, user_plan: dict) -> dict:
        return cls.create_method_call_dict(cls.REGISTER_USER, user_api_key, user_plan)

    @classmethod
    def get_remove_user(cls, user_api_key: str) -> dict:
        return cls.create_method_call_dict(cls.REMOVE_USER, user_api_key)

    @classmethod
    def get_update_user_plan(cls, user_api_key: str, user_plan: dict) -> dict:
        return cls.create_method_call_dict(
            cls.UPDATE_USER_PLAN, user_api_key, user_plan
        )

    @classmethod
    def get_get_endpoints(cls) -> dict:
        return cls.create_method_call_dict(cls.GET_ENDPOINTS)

    @classmethod
    def get_add_endpoint(cls, name: str, url: str) -> dict:
        return cls.create_method_call_dict(cls.ADD_ENDPOINT, name, url)

    @classmethod
    def get_remove_endpoint(cls, name: str) -> dict:
        return cls.create_method_call_dict(cls.REMOVE_ENDPOINT, name)

    @classmethod
    def get_update_endpoint(cls, name: str, url: str) -> dict:
        return cls.create_method_call_dict(cls.UPDATE_ENDPOINT, name, url)
