# Phase 6 - Hardening and VPS Deployment

## Goal

Prepare the application for stable single-user VPS deployment after all core functionality has already been proven locally.

## Scope

- Docker runtime cleanup
- Environment separation for local and VPS
- Reverse proxy setup
- HTTPS plan
- Authentication baseline
- Backups and restore process
- Logging and service monitoring
- Deployment runbook

## Planned Deliverables

- production-ready Dockerfiles
- deployment-oriented `docker-compose` configuration
- VPS environment template
- backup strategy for database and app data
- service restart and logging guidance
- deployment checklist

## Acceptance Criteria

- The app can be started on a fresh VPS from documented steps
- Persistent storage survives restarts
- Authentication protects the UI and API
- Reverse proxy routing works
- Backups and restore steps are documented and tested

## Out of Scope

- Multi-user SaaS features
- Auto-scaling infrastructure
- Managed cloud migration

## Suggested Verification

- Recreate the stack in a VPS-like environment
- Validate login and route protection
- Restart containers and confirm data persistence
- Test backup and restore on a copy of the local database
