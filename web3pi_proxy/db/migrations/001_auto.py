"""Peewee migrations -- 001_auto.py.

Some examples (model - class or model name)::

    > Model = migrator.orm['table_name']            # Return model in current state by name
    > Model = migrator.ModelClass                   # Return model in current state by name

    > migrator.sql(sql)                             # Run custom SQL
    > migrator.run(func, *args, **kwargs)           # Run python function with the given args
    > migrator.create_model(Model)                  # Create a model (could be used as decorator)
    > migrator.remove_model(model, cascade=True)    # Remove a model
    > migrator.add_fields(model, **fields)          # Add fields to a model
    > migrator.change_fields(model, **fields)       # Change fields
    > migrator.remove_fields(model, *field_names, cascade=True)
    > migrator.rename_field(model, old_field_name, new_field_name)
    > migrator.rename_table(model, new_table_name)
    > migrator.add_index(model, *col_names, unique=False)
    > migrator.add_not_null(model, *field_names)
    > migrator.add_default(model, field_name, default)
    > migrator.add_constraint(model, name, sql)
    > migrator.drop_index(model, *col_names)
    > migrator.drop_not_null(model, *field_names)
    > migrator.drop_constraints(model, *constraints)

"""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""
    
    @migrator.create_model
    class User(pw.Model):
        id = pw.AutoField()
        api_key = pw.CharField(max_length=255)

        class Meta:
            table_name = "user"
            indexes = [(('api_key',), True)]

    @migrator.create_model
    class BillingPlan(pw.Model):
        id = pw.AutoField()
        user = pw.ForeignKeyField(column_name='user_id', field='id', model=migrator.orm['user'])
        num_free_calls = pw.IntegerField()
        num_free_bytes = pw.IntegerField()
        glm_call_price = pw.FloatField()
        glm_byte_price = pw.FloatField()
        user_priority = pw.IntegerField()

        class Meta:
            table_name = "billingplan"
            indexes = [(('user',), True)]

    @migrator.create_model
    class CallStats(pw.Model):
        id = pw.AutoField()
        user = pw.ForeignKeyField(column_name='user_id', field='id', model=migrator.orm['user'])
        method = pw.CharField(max_length=255)
        date = pw.DateField()
        request_bytes = pw.IntegerField(default=0)
        response_bytes = pw.IntegerField(default=0)
        num_calls = pw.IntegerField(default=0)

        class Meta:
            table_name = "callstats"
            indexes = [(('user', 'method', 'date'), True)]


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""
    
    migrator.remove_model('callstats')

    migrator.remove_model('billingplan')

    migrator.remove_model('user')
