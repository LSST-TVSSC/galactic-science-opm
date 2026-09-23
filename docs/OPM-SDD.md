# Software Design Document
## Galactic Science Observation Priority Manager (OPM)

**Repository:** [LSST-TVSSC/galactic-science-opm](https://github.com/LSST-TVSSC/galactic-science-opm)  
**Reference branch:** `dev`  
**Reference commit:** `2257867` (full commit `2257867948ee47ef3a02aad6888f2f876c9b0991`)  
**Repository commit date:** 2026-08-17  
**Document version:** v1.0  
**Document date:** 2026-09-23 
**Authors/OPM maintainers in alphabetical order:** Markus Hundertmark, Maximilian Kistner, Yiannis Tsapras and Sven Weimann
**LLM Disclosure:** Mistral was used for preparing this revised SDD. Changes were checked and when necessary revised by the authors.

## Revision History

| Date | Version | Author/maintainer | Change |
|---|---:|---|---|
| 2024-01-10 | 0.1 | Markus Hundertmark, Yiannis Tsapras | Initial draft |
| 2024-02-28 | 0.1 | Markus Hundertmark | Updated after TVS microlensing subgroup meeting |
| 2024-03-05 | 0.1 | Markus Hundertmark | Updated after DASH and broker-team discussions |
| 2024-03-18 | 0.1 | Markus Hundertmark | Updated after microlensing subgroup discussions |
| 2024-12-06 | 0.2 | Markus Hundertmark | Updated after broker-team and developer meetings |
| 2025-08-29 | 0.2 | Markus Hundertmark | Updated after initial repository review |
| 2026-08-24 | 1.0 | OPM maintainers | Rebased the SDD on repository commit `2257867`: implemented architecture, models, routes, broker workflows, frontend, testing, deployment, security, and current roadmap |

# Definitions, acronyms, and abbreviations

| Term | Definition |
| :--- | :--- |
| API | Application Programming Interface |
| ALeRCE | Automatic Learning for the Rapid Classification of Events broker |
| ANTARES | Arizona-NOIRLab Temporal Analysis and Response to Events System |
| Django | Python web framework used by the OPM server |
| FITS | Flexible Image Transport System |
| Fink | Alert broker and alert-processing platform |
| Gaia | ESA astrometric survey and its data products |
| HPC | High-Performance Computing |
| LSST | Legacy Survey of Space and Time |
| OPM | Observation Priority Manager. Also described in the repository as Observational Planning/Priority Manager |
| RSP | Rubin Science Platform |
| SED | Spectral Energy Distribution |
| SRS | Software Requirements Specification |
| TOM | Target and Observation Manager |
| TVS / TVSSC | Transients and Variable Stars / Transients and Variable Stars Science Collaboration |
| ZTF | Zwicky Transient Facility |
| IDAC | Independent Data Access Centern |

## 1. Purpose and Scope

The Galactic Science OPM is a Django-based [Target and Observation Manager (TOM)](https://tom-toolkit.readthedocs.io/en/stable/) instance for the TVS galactic-science community. It tracks transient and variable targets, ingests alert and photometric information from external broker and survey services, records classification and prioritization information, and provides target-level scientific visualizations.

The implementation supports microlensing-oriented workflows, including current and historical broker classifications, probability rescaling and radar metrics, light-curve inspection, VizieR SED retrieval, Rubin visit information, and statistical microlensing model products. It is designed for local installation and container deployment. Integration with observatory-facing TOM systems like MOP or BHTOM and remote computing resources can be added without changing the core target model.

### In scope

- Target registration, matching, grouping, sharing, filtering, import, and export through TOM Toolkit functionality.
- Ingestion and normalization of ZTF and LSST alert/photometry products as well as existin survey OGLE, MOA/PRIME, KMTNet, Roman, etc.
- Ingestion of ANTARES, ALeRCE, and Fink classification or event products where the corresponding workflow is enabled.
- Display of target photometry, classifications, SEDs, microlensing model parameters, radar metrics, survey images, and sky context.
- Reproducible tracking of target metadata and updated model/classification records.

### Out of scope

The OPM does not itself replace a broker classifier, run arbitrary user code, provide unrestricted nightly Rubin data access, or perform general-purpose large-scale catalog cross-matching. Computationally intensive fitting is represented by management-command workflows and model products. HPC/iDAC interaction remains under development.

## 2. Stakeholders and Interoperability

Primary users are TVS science-subgroup members who select, rank, inspect, and follow up transient or variable targets. Data providers and collaborating services include alert brokers, survey archives, observatory-facing TOM systems, and future HPC/iDAC services.

The application uses Django and TOM Toolkit conventions for target, observation, photometry, registration, permissions, and sharing. Interoperability with the Rubin Science Platform (RSP) is planned through standards-based service interfaces and RSP Identity and Access Management (IAM). The deployment must respect Rubin data-rights agreements and the access controls of each external data provider.

## 3. Architecture Overview

The system is a modular Django web application backed by PostgreSQL and packaged for Docker Compose deployment.

```text
Broker/survey services
  ALeRCE (ZTF, LSST) | ANTARES | OGLE | Fink
          │
          ▼
Django management commands and broker adapters
          │
          ▼
Django/TOM Toolkit models and services ─── PostgreSQL
          │
          ├── TOM templates and target/observation workflows
          ├── Plotly and Aladin Lite visualization components
          └── health/version/metrics and data-download endpoints (for local admins)
          │
          ▼
     Gunicorn/Django ── Nginx (production-like Compose deployment)
```

### Technology stack

- **Backend:** Python 3.10–3.11, Django, TOM Toolkit, TOM alert-stream and registration packages.
- **Database:** PostgreSQL: the Compose example uses PostgreSQL.
- **Scientific/data services:** ALeRCE client, ANTARES client, TOM Fink integration, OGLE ingestion.
- **Frontend:** Vite, TypeScript, Lit web components, Plotly, and Aladin Lite.
- **Serving/deployment:** Docker, Docker Compose, Gunicorn/gevent, Nginx, and WhiteNoise for static assets.
- **Code conventions:** The OPM adheres to PEP 8, and the project's RUFF pre-hook linter settings ensure this is maintained.

## 4. External Broker and Survey Integrations

Broker adapters in `custom_code/brokers/` implement query, fetch, normalization, ingestion, and photometry workflows:

- **ALeRCE ZTF:** The respective management command fetches ZTF alerts and light curves and ingests normalized photometry and classifications.
- **ALeRCE LSST:** The respective management command provides the corresponding LSST workflow, including alert/light-curve and classification ingestion.
- **ANTARES:** The respective management command retrieves ANTARES loci and combines the workflow with ALeRCE photometry where required.
- **OGLE:** The respective management command supports OGLE event retrieval, lens-model parameter retrieval, event ingestion, and OGLE photometry/light-curve ingestion.

The adapters use matching/validation helpers to avoid duplicate target creation and attach broker-derived classifications, photometry, and model products to the appropriate `GalacticTarget`.

## 5. Data Model

The application extends TOM Toolkit’s `BaseTarget` with domain-specific Django models. The implemented models, rather than generic placeholder tables, are:

| Model | Role |
|---|---|
| `GalacticTarget` | Target identity and coordinates inherited from TOM, plus baseline `u,g,r,i,z,y` magnitudes and errors, target type, expected visits, known variability/extragalactic flags, and ZTF baseline status. |
| `Classification` | Time-stamped broker/source classification probabilities, including up to four classes and master peak/current probabilities. |
| `ClassificationSource` | Classifier name, origin, version, and class-name metadata for generalized classifications. |
| `ClassificationGeneralized` | Normalized target classification linked to a `ClassificationSource`, with probability and update time. |
| `MicrolensingModel` | Microlensing fit parameters and uncertainties, including `t0`, `u0`, `tE`, parallax, finite-source, binary-lens, source, and blend parameters. |
| `BaseParameterModel` | Common target-linked base for timestamped statistical model products. |
| `MicrolensingParameterModel` | Statistical microlensing model parameters derived from the base parameter model. |
| `StatisticalModelImage` | Image products associated with statistical model fits, stored using content-hash-based paths. |
| `MicrolensingRadarData` | Rescaled broker/science metrics, including ALeRCE, ANTARES, Fink, ALeRCE-ATAT, Gaia N-square, planet, probability-ratio, bogus, and aggregate master probability metrics. |
| TOM Toolkit models | Users, observations, reduced/photometric data products, target names/aliases, target lists/groups, sharing, and registration are supplied by TOM Toolkit and Django. |

Foreign keys connect classifications, model products, radar metrics, and images to `GalacticTarget`. Update timestamps support retrieval of the latest model or classification state. Migrations record the schema evolution at the reference commit.

## 6. API and Application Routes

The application primarily exposes authenticated Django views and TOM Toolkit routes rather than a separate REST framework. The functionalities and purposes include:

- **home**: OPM home page with featured targets and current target count.
- **target-detail**: Target detail page with domain-specific context and latest parameter models.
- **share**: Share target data using the customized TOM sharing form.
- **sed_plots:fetch_vizier_sed**: Authenticated POST action to fetch and store a VizieR SED.
- **microlensing_model_view**: List microlensing parameter models.
- **microlensing_rescaled_prob_view**: Display current and queried rescaled probability rankings.
- **microlensing_rescaled_prob_view_lsst**: Display LSST rescaled-probability rankings.
- **microlensing_rescaled_prob_view_ztf25**: Display older ZTF queried rankings.
- **health**: Health check for service/database availability.
- **version**: Report application/repository version information.
- **metrics**: Report application metrics.
- **download_lightcurve_data_for_target**: Download packaged light-curve data for a target.

TOM Toolkit URL inclusions provide the standard target, observation, registration, authentication, list, group, and sharing routes. Ingestion and operational workflows are exposed as Django management commands rather than public HTTP endpoints.

### Ingestion and processing commands

We use Django management commands for tasks like ingesting new targets, cross-matches, photometry, fitting and ranking targets.

## 7. Backend Components

- **Broker adapters:** Convert external event payloads into generic alerts, match targets, ingest photometry, and attach classifications.
- **Matching and validation:** Validators match targets by names and coordinates and prevent duplicate records.
- **Probability and model processing:** Management commands rescale broker/science probabilities, update Rubin visits, ingest VizieR SEDs, run RTModel fits, and migrate model products into statistical-model records.
- **Data products:** TOM photometry/reduced-data models remain the storage layer for observations and light curves. Custom models add galactic-science metadata.

## 8. Frontend Components

The OPM frontend is built using Django Templates for server-side rendering combined with lit-based custom elements, avoiding a single-page application (SPA) architecture. This modular design allows components to be shared seamlessly across different tabs and pages within the application. Key components include interactive target detail views that display light curves and parameter models, probability ranking displays for microlensing events (including LSST and ZTF variants), and specialized visualization elements like SED plots and Earth visibility charts. While these components provide consistent functionality today, please note that their tag names and internal implementations may evolve over time, requiring updates to this documentation.

## 9. Testing Strategy

Testing is organized into three maintained layers:

1. **Unit tests** (`custom_code/tests/unit`): broker alert conversion, classification parsing, photometry conversion, and VizieR SED processing.
2. **Integration tests** (`custom_code/tests/integration`): target creation, matching, and interactions across Django/TOM components and the database.
3. **Playwright end-to-end tests** (`custom_code/tests/e2e`): page-object-driven workflows for home, targets, target details, target groups, alerts, observations, ranking, and user administration. The E2E Compose profile seeds deterministic data and runs the browser test container.

The test settings module is `galactic_science_opm.settings_test`.

## 10. Deployment and Operations

The OPM application relies on Docker Compose to manage and deploy different environments consistently. To minimize configuration duplication while accommodating environment-specific settings, we use a base Compose file combined with environment-specific overrides. This modular approach ensures that common configurations are maintained in a single location while allowing for tailored adjustments across development, testing, and production environments.

In production, Nginx serves `/static/`, `/_static/`, and `/data/` from read-only mounts and forwards application requests with the original host, client, and protocol headers.

### Environment variables

Deployment configuration is supplied through `.env` (derived from `env.example`) and Compose interpolation. Important variables are `PSQL_USER`, `PSQL_PASS`, `PSQL_IMAGE`, `OPM_PSQL_VOLUME`, `DJANGO_DEBUG`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGIN`, `EXT_PORT`, `DJANGO_STATIC_DIR`, `DJANGO_DATA_DIR`, `DJANGO_TEST_DATA_DIR`, `GIT_COMMIT`, `LOCAL`, and `E2E`. Secrets and deployment-specific values must be supplied outside version control. The example file is configuration documentation, not a production secret store.

## 11. Security, Authentication, and Data Protection

- **Current authentication:** Django authentication and TOM Registration provide the initial user-management and approval flow. Django permissions and TOM sharing controls protect target and data-product operations.
- **Planned RSP integration:** RSP IAM is the intended authority for Rubin-proprietary access and federation. The application should map IAM identity and group claims to Django users/groups and enforce least-privilege access before production Rubin data are exposed.
- **Secrets management:** Database passwords, Django secret key, allowed hosts, CSRF trusted origins, and broker/service credentials belong in a deployment secret manager or protected environment/CI configuration. They must not be committed to the repository or copied from the illustrative values in `env.example`.
- **Transport and perimeter:** Production deployment should terminate TLS at the ingress/proxy layer, restrict allowed hosts and CSRF origins, keep PostgreSQL off the public network, and expose only required Nginx routes.
- **Application controls:** Use Django CSRF protection, login-required permissions for sensitive actions such as SED retrieval, validated uploads, parameterized ORM queries, and the TOM Toolkit’s registration/sharing controls. Rate limiting and DoS protection should be provided by the deployment perimeter and TOM/Django-compatible middleware.
- **Data rights:** Rubin and in-kind contributor data must remain subject to the applicable AURA/Rubin agreements, RSP IAM policy, and local institutional security requirements. Backups must receive equivalent access control.

## 12. Backups and Recovery

PostgreSQL data is persisted through the configured Compose volume and should be backed up with regular PostgreSQL dumps or an equivalent managed-database backup. Static assets, uploaded data products, and the `data` directory require separate protected backups. Recovery procedures should include restoring the database, deploying the matching application commit, running migrations, restoring data/static mounts, and validating `/health/`, `/version/`, target detail, and ingestion operations.

## 13. Current Status and Roadmap

The status below is anchored to commit `2257867` on branch `dev` dated 2026-08-17.

### Implemented

- Dockerized Django/TOM Toolkit application with PostgreSQL and local, production-like, and E2E Compose profiles.
- ZTF and LSST ALeRCE workflows for alert/classification/light-curve ingestion.
- ANTARES and OGLE integrations, plus Fink-derived classification/probability workflows.
- Galactic target, classification, generalized classification-source, microlensing, statistical-model, image, and radar-metric models.
- Plotly charts, Aladin Lite target/sky maps, VizieR SED retrieval, target detail views, health/version/metrics routes, and light-curve export.
- Unit, integration, and Playwright E2E test suites.

### In progress

- HPC/iDAC interfaces for remote, computationally intensive microlensing analyses and result exchange.
- RSP IAM integration and production-grade data-rights enforcement.
- Further interoperability with observatory-facing TOM systems and follow-up request services.
- Update to the released TOM toolkit 3
- Adjusting ranking as soon as more classifiers are available
- Update to latest fink version
- Workflow for OGLE and other surveys will be revised.

### Future

- Production deployment with institutional operations, TLS/ingress, managed secrets, monitored backups, and operational service-level procedures. 
- Hardened broker scheduling/listener operation, broader survey/data-product coverage, and scalable background processing for high-volume LSST workflows.
- The spectroscopy/SED element of the project is expected to grow in size and be led by Yiannis Tsapras.

## 14. Maintenance and Release Policy

This SDD is versioned independently from the application. A document revision records the repository commit or release it describes. Application changes that alter models, routes, broker workflows, frontend behavior, deployment, or security controls should update this document and the corresponding tests/migrations. Application release identifiers are exposed through the `/version/` route and may be populated from the `GIT_COMMIT` deployment variable.
