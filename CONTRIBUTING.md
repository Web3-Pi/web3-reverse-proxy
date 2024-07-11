
# DB

To create a database migration after changes to the models, run:

```
poe create_migrations
```

The resultant migration files are added to `web3pi_proxy/db/migrations` directory. Be sure to add them to the repository alongside the changes to the models' code.

All the migrations are automatically applied when you start the web3pi-proxy.

## Test users

While developing, you may wish to create some test users with some arbitrary billing plans.

Please run:

```
poe init_test_accounts
```

Restart your web3pi-proxy if you had it running.

This should create users with api keys of: `aaa`, `bbb`, `ccc`.
