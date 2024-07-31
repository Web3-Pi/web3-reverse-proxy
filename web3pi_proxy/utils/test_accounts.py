from web3pi_proxy.db.models import User, BillingPlan

TEST_ACCOUNT_DATA = {
    "aaa": {
        "num_free_calls": 100_000_000,
        "num_free_bytes": 1500 * 1024 ** 3,
        "user_priority": 0,
        "constant_pool": "",
    },
    "bbb": {
        "num_free_calls": 1_000_000,
        "num_free_bytes": 2 * 1024 ** 3,
        "user_priority": 1,
        "constant_pool": "",
    },
    "ccc": {
        "num_free_calls": 1_000_000,
        "num_free_bytes": 1 * 1024 ** 3,
        "user_priority": 2,
        "constant_pool": "",
    },
}


def init_test_accounts():
    print("Adding test accounts.")
    for api_key, plan_args in TEST_ACCOUNT_DATA.items():
        user, created = User.get_or_create(api_key=api_key)
        if created:
            print(
                f"   Adding user: {api_key}, "
                f"free_calls {plan_args.get('num_free_calls')}, "
                f"free_bytes: {plan_args.get('num_free_bytes')}, "
                f"priority: {plan_args.get('user_priority')}"
            )
            bp = BillingPlan(user=user, **plan_args)
            bp.save()
        else:
            print(f"   User: {api_key} already exists.")
