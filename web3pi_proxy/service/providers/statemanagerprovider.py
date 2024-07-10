import os
import pickle
from io import StringIO

from web3pi_proxy.config.conf import Config
from web3pi_proxy.service.billing.billingplan import SimplestBillingPlan
from web3pi_proxy.service.billing.billingservice import BasicBillingService
from web3pi_proxy.service.ledger.activityledger import SimpleActivityLedger
from web3pi_proxy.state.statemanager import SampleStateManager


class StateManagerProvider:

    @classmethod
    def create_state_manager(
        cls,
        console_buffer: StringIO,
        skip_persistent_db=False,
        db_fn=Config.STATE_STORAGE_FILE,
    ) -> SampleStateManager:
        if os.path.exists(db_fn) and Config.USE_PICKLE_DB and not skip_persistent_db:
            with open(db_fn, "rb") as f:
                print(f"Loading State Manager from basic pickle DB: {db_fn}")
                res = pickle.load(f)
                res.mark_next_startup()
                res.set_console_buffer(console_buffer)
        else:
            print(f"Creating new instance of State Manager")
            res = SampleStateManager(
                BasicBillingService(SimplestBillingPlan), SimpleActivityLedger(), console_buffer
            )

        return res

    @classmethod
    def close_state_manager(
        cls,
        ssm: SampleStateManager,
        skip_persistent_db=False,
        db_fn=Config.STATE_STORAGE_FILE,
    ) -> None:
        if Config.USE_PICKLE_DB and not skip_persistent_db:
            if not os.path.exists(db_fn):
                os.makedirs(os.path.dirname(db_fn), exist_ok=True)

            # These fields are recreated every each proxy launch (they are proxy specific, and not user specific)
            ssm.clear_transient_fields()

            print(f"Writing State Manager to basic pickle DB: {db_fn}")
            with open(db_fn, "wb") as f:
                # TODO: If locks are applied, they cannot be pickled. Store stats data rather than state object.
                pickle.dump(ssm, f)

        print(f"Service uptime for this session: {ssm.get_uptime()}")
