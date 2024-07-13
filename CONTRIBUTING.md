
# DB

To create a database migration after changes to the models, run:

```
poe create_migrations
```

The resultant migration files are added to `web3pi_proxy/db/migrations` directory. Be sure to add them to the repository alongside the changes to the models' code.

All the migrations are automatically applied when you start the web3pi-proxy.
