## Database Migration Process

This directory manages automated database migrations. This allows us to automatically synchronize code changes with
database changes. While these kinds of changes are done manually in the test environment, they should be automatic in
acceptance and production.

### Making a change to the database

1. The developer adds a migration into the `migration-configmap.yaml` and makes a pull request. This pull request should
   also
   contain code changes (i.e. the updated image of the code which responds to the database changes)
2. Database changes are merged into the main GitHub branch
3. ArgoCD deploys the presync hooks before any other changes are applied. In this case, the `flyway-job` is deployed as
   a kubernetes job.
4. Flyway makes the database changes
5. ArgoCD applies the manifests. Code changes that rely on the new database schema are safely deployed.

### No-change flow

If a pull request is made with no changes to the `migration-configmap`:

1. ArgoCd deploys the presync hook. Flyway is deployed as a kubernetes job.
2. Flyway sees there are no new migrations. No changes are made to the database
3. ArgocCD applies the manifests as normal.

Note: ArgoCD will always run the presync hooks, regardless of whether or not they've changed.

## Naming Migrations

Versioned flyway migrations follow the following naming convention:

`V<Version>__<Description>.sql`

We can align flyway's naming convention with the release naming convention of DiSSCo. When releasing to production or
acceptance, we should make sure the version of the flyway migration always matches the new release version. (e.g.
1.2.1).

To track what is the latest version of the database schema, and thus to manage Flyway versions, the latest migration
script should be kept. This will not trigger any changes in the database if re-run. Older database migration scripts
should be removed to keep the configmap clean.

## Managing the ConfigMap

Once a migration is completed, the migration script in `migration-configmap.yaml` can be removed. Completed migrations
should be moved to the `completed-migrations` directory. To prevent the migration configmap from getting too large, only
the latest release's migration should be stored there. The file should be renamed to the release version, e.g. `database-migration-v1.2.3.yaml`
